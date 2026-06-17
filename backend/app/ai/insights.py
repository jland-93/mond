"""
🌙 AI 인사이트 생성기

Claude를 호출해 Finding을 triage / remediation / explain 한다.
API 키가 없으면 기본 규칙 fallback이 동작하므로 OSS 사용자가 즉시 UI를 볼 수 있다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.ai.client import get_client, is_enabled
from app.core.config import settings
from app.core.logging import get_logger
from app.models.finding import Finding, Severity

logger = get_logger(__name__)


SYSTEM_PROMPT = """\
You are Mond, an AI assistant for a DevSecOps platform. You analyze security findings
from scanners (Trivy, Semgrep, Nuclei, ...) and produce concise, actionable insights.

Always respond with strict JSON matching this schema:
{
  "summary": "1-2 sentence plain-language explanation of the risk",
  "recommended_severity": "critical|high|medium|low|info",
  "confidence": 0.0,
  "remediation": {
    "steps": ["step 1", "step 2"],
    "code": "optional code snippet for the fix",
    "references": ["url1", "url2"]
  }
}

Rules:
- Output ONLY the JSON. No markdown fences, no prose before/after.
- Keep summary under 280 characters.
- Use the lowest credible severity; do not inflate.
- If unsure, set confidence below 0.5 and explain in the summary.
"""


@dataclass
class InsightResult:
    summary: str
    confidence: float
    recommended_severity: Severity
    remediation: dict
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


async def analyze_finding(finding: Finding, *, deep: bool = False) -> InsightResult:
    """단일 Finding에 대해 AI 인사이트를 생성한다."""
    if not is_enabled():
        return _fallback(finding)

    model = settings.AI_MODEL_DEEP if deep else settings.AI_MODEL_DEFAULT
    client = get_client()
    assert client is not None

    user_prompt = _build_user_prompt(finding)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=settings.AI_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:  # 네트워크/쿼터/모델 거부
        logger.warning("ai_analyze_failed", finding_id=finding.id, error=str(exc))
        return _fallback(finding)

    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    parsed = _parse_json(text) or {}

    return InsightResult(
        summary=parsed.get("summary", "AI 응답 파싱 실패 — 기본 규칙으로 대체.")[:1000],
        confidence=float(parsed.get("confidence", 0.0)),
        recommended_severity=_coerce_severity(parsed.get("recommended_severity"), finding.severity),
        remediation=parsed.get("remediation") or {},
        model=model,
        input_tokens=getattr(response.usage, "input_tokens", None),
        output_tokens=getattr(response.usage, "output_tokens", None),
    )


async def route_query(query: str) -> dict:
    """자연어 쿼리를 받아 의도(scan/list/explain/unknown)를 분류한다."""
    if not is_enabled():
        return _heuristic_route(query)

    client = get_client()
    assert client is not None

    try:
        response = await client.messages.create(
            model=settings.AI_MODEL_DEFAULT,
            max_tokens=512,
            system=(
                "You classify DevSecOps user requests. Return strict JSON: "
                '{"intent": "scan|list_findings|explain|unknown", '
                '"summary": "what user wants", "suggested_actions": [{"label": "...", "endpoint": "..."}]}'
            ),
            messages=[{"role": "user", "content": query}],
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return _parse_json(text) or _heuristic_route(query)
    except Exception as exc:
        logger.warning("ai_route_failed", error=str(exc))
        return _heuristic_route(query)


def _build_user_prompt(finding: Finding) -> str:
    return json.dumps(
        {
            "scanner": finding.scanner,
            "rule_id": finding.rule_id,
            "title": finding.title,
            "description": finding.description,
            "severity_from_scanner": finding.severity.value,
            "location": finding.location,
            "references": finding.references,
            "extra": finding.extra,
        },
        ensure_ascii=False,
    )


def _parse_json(text: str) -> dict | None:
    text = text.strip()
    # 모델이 코드펜스를 붙인 경우 제거
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].lstrip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _coerce_severity(value, fallback: Severity) -> Severity:
    if isinstance(value, str):
        try:
            return Severity(value.lower())
        except ValueError:
            return fallback
    return fallback


def _fallback(finding: Finding) -> InsightResult:
    """LLM 비활성 시: 기본 규칙으로 OSS 사용자에게 '쓸만한' 결과를 준다."""
    sev_text = finding.severity.value
    summary = (
        f"[기본 규칙] {finding.scanner.title()}가 '{finding.rule_id}' 룰을 위반한 "
        f"{sev_text} 등급 이슈를 발견했습니다. ANTHROPIC_API_KEY를 설정하면 "
        f"Claude 기반 상세 분석과 조치 코드 제안을 받을 수 있습니다."
    )
    return InsightResult(
        summary=summary,
        confidence=0.3,
        recommended_severity=finding.severity,
        remediation={
            "steps": [
                f"`{finding.rule_id}` 룰의 공식 문서를 확인하세요.",
                "관련 참조 링크를 검토하고 우선순위를 결정하세요.",
            ],
            "references": finding.references or [],
        },
        model="rule-based",
    )


def _heuristic_route(query: str) -> dict:
    q = query.lower()
    if any(k in q for k in ("스캔", "scan", "검사", "점검")):
        intent = "scan"
    elif any(k in q for k in ("finding", "이슈", "취약점", "vulnerability")):
        intent = "list_findings"
    elif any(k in q for k in ("설명", "explain", "왜", "why")):
        intent = "explain"
    else:
        intent = "unknown"
    return {
        "intent": intent,
        "summary": f"기본 규칙 분류: {intent}. ANTHROPIC_API_KEY 설정 시 Claude가 더 정확하게 의도를 해석합니다.",
        "suggested_actions": [],
    }
