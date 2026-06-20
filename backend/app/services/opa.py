"""
OPA (Open Policy Agent) Rego 평가 — subprocess 어댑터

backend 이미지에 함께 번들된 `opa` 바이너리를 호출해 Rego 정책을 평가.
바이너리가 없으면 graceful disable — UI가 "OPA 미설치" 안내를 보여준다.

설계:
  - 외부 서버(`opa server`) 의존 회피 → 작은 OSS 설치 발자국 유지
  - 임시 파일에 rego 작성 → `opa eval --format json -d <rego> -i <input.json> <query>`
  - input.json은 stdin 대신 임시 파일(macOS · linux 호환)
  - 평가 결과 expressions[0].value를 deny 목록으로 해석

평가 규약:
  - 쿼리는 기본 `data.mond.deny` (deny 룰들의 결과 집합)
  - deny가 비어 있으면 통과, 1건 이상이면 차단
  - deny 각 원소는 문자열(이유) 또는 dict({"msg": "...", ...})
"""

from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

DEFAULT_QUERY = "data.mond.deny"
EVAL_TIMEOUT_S = 8


def opa_binary() -> str | None:
    """OPA 바이너리 경로. 없으면 None."""
    return shutil.which("opa")


def is_available() -> bool:
    return opa_binary() is not None


@dataclass
class RegoResult:
    available: bool
    blocked: bool          # deny가 1개 이상이면 True
    deny: list[str]        # 사람 읽을 수 있는 reason 문자열 목록
    raw: dict | None       # opa의 원시 응답 — 디버깅용
    error: str | None      # 실패 사유 (timeout · syntax error 등)


async def evaluate(rego: str, input_data: dict, query: str = DEFAULT_QUERY) -> RegoResult:
    """Rego 정책을 OPA로 평가.

    Args:
      rego: Rego source 문자열 (`package mond` 권장)
      input_data: 평가에 넘길 input. 보통 {"finding": {...}} 또는 {"findings": [...]}
      query: 결과를 뽑을 OPA 쿼리. 기본 `data.mond.deny`
    """
    bin_path = opa_binary()
    if not bin_path:
        return RegoResult(available=False, blocked=False, deny=[], raw=None,
                          error="OPA 바이너리 미설치 (PATH에 'opa' 없음)")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        rego_file = tmp_path / "policy.rego"
        input_file = tmp_path / "input.json"
        rego_file.write_text(rego, encoding="utf-8")
        input_file.write_text(json.dumps(input_data), encoding="utf-8")

        cmd = [
            bin_path, "eval",
            "--format", "json",
            "--data", str(rego_file),
            "--input", str(input_file),
            query,
        ]
        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=EVAL_TIMEOUT_S,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=EVAL_TIMEOUT_S)
        except asyncio.TimeoutError:
            logger.warning("opa_eval_timeout", query=query)
            return RegoResult(available=True, blocked=False, deny=[], raw=None,
                              error=f"OPA 평가 timeout ({EVAL_TIMEOUT_S}s)")
        except FileNotFoundError:
            return RegoResult(available=False, blocked=False, deny=[], raw=None,
                              error="OPA 실행 실패 — 바이너리 누락")

        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace")[:500]
            logger.warning("opa_eval_failed", returncode=proc.returncode, error=err)
            return RegoResult(available=True, blocked=False, deny=[], raw=None,
                              error=f"OPA returncode={proc.returncode}: {err}")

        try:
            payload = json.loads(stdout.decode("utf-8"))
        except json.JSONDecodeError as e:
            return RegoResult(available=True, blocked=False, deny=[], raw=None,
                              error=f"OPA 응답 JSON 파싱 실패: {e}")

        # 응답 구조 — result[0].expressions[0].value
        deny: list[str] = []
        try:
            results = payload.get("result") or []
            if results:
                exprs = results[0].get("expressions") or []
                if exprs:
                    value = exprs[0].get("value")
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                deny.append(item)
                            elif isinstance(item, dict):
                                deny.append(str(item.get("msg") or item))
                            else:
                                deny.append(str(item))
                    elif isinstance(value, bool):
                        if value:
                            deny.append("policy denied")
                    elif value is not None:
                        deny.append(str(value))
        except (KeyError, IndexError, AttributeError) as e:
            return RegoResult(available=True, blocked=False, deny=[], raw=payload,
                              error=f"OPA 응답 구조 해석 실패: {e}")

        return RegoResult(
            available=True,
            blocked=bool(deny),
            deny=deny,
            raw=payload,
            error=None,
        )
