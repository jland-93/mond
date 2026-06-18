"""
AI 인사이트 생성기

Claude를 호출해 Finding을 triage / remediation / explain 한다.
API 키가 없으면 기본 규칙 fallback이 동작하므로 OSS 사용자가 즉시 UI를 볼 수 있다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import complete_json, current_model_label, is_enabled
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


async def analyze_finding(db: AsyncSession, finding: Finding, *, deep: bool = False) -> InsightResult:
    """단일 Finding에 대해 AI 인사이트를 생성한다 (provider-agnostic)."""
    if not await is_enabled(db):
        return _fallback(finding)

    user_prompt = _build_user_prompt(finding)
    result = await complete_json(db, SYSTEM_PROMPT, user_prompt, deep=deep)
    if result is None:
        logger.warning("ai_analyze_failed_or_disabled", finding_id=finding.id)
        return _fallback(finding)

    parsed = _parse_json(result.text) or {}
    return InsightResult(
        summary=parsed.get("summary", "AI 응답 파싱 실패 — 기본 규칙으로 대체.")[:1000],
        confidence=float(parsed.get("confidence", 0.0)),
        recommended_severity=_coerce_severity(parsed.get("recommended_severity"), finding.severity),
        remediation=parsed.get("remediation") or {},
        model=f"{result.provider}:{result.model}",
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )


async def route_query(db: AsyncSession, query: str) -> dict:
    """자연어 쿼리를 받아 RAG로 Mond 데이터를 검색한 뒤 LLM에 context로 주입.

    응답 형식:
      {
        "intent": "scan|list_findings|explain|unknown",
        "summary": "...",
        "citations": [{n, kind, title, snippet, url}, ...],
        "suggested_actions": [...],
        "model": "provider:model"
      }

    citation 노출: LLM이 답변 중 [1][2] 같은 인용 마커를 사용 → 프론트가 참고 카드로 보여줌.
    """
    from app.ai.rag import build_context_block, search

    # 1) Mond DB에서 관련 자료 검색 (RAG retrieve)
    citations = await search(db, query)

    # 2) AI 비활성 시 — 휴리스틱 + 출처만 노출
    if not await is_enabled(db):
        result = _heuristic_route(query)
        result["citations"] = [c.to_dict() for c in citations]
        return result

    # 3) LLM에 context 주입
    context_block = build_context_block(citations)
    system = (
        "You are Mond, an AI-powered self-service DevSecOps assistant. "
        "Classify the user's intent and answer in 1-3 sentences. "
        "When you reference a known item, cite it inline as [N] using the numbered sources below. "
        "Return strict JSON: "
        '{"intent": "scan|list_findings|explain|unknown", '
        '"summary": "answer text with [N] citations if relevant", '
        '"suggested_actions": [{"label": "...", "endpoint": "..."}]}'
    )
    if context_block:
        system = f"{system}\n\n{context_block}"

    result = await complete_json(db, system, query, max_tokens=600)
    if result is None:
        fallback = _heuristic_route(query)
        fallback["citations"] = [c.to_dict() for c in citations]
        return fallback
    parsed = _parse_json(result.text)
    if not parsed:
        fallback = _heuristic_route(query)
        fallback["citations"] = [c.to_dict() for c in citations]
        return fallback
    parsed["model"] = f"{result.provider}:{result.model}"
    parsed["citations"] = [c.to_dict() for c in citations]
    return parsed


# 하위 호환 — UI 라벨 helper. client.current_model_label은 async라 별도 노출.
async def current_label(db: AsyncSession) -> str:
    return await current_model_label(db)


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
        f"{sev_text} 등급 이슈를 발견했습니다. AI provider(.env: AI_PROVIDER + 해당 키)를 "
        f"설정하면 LLM 기반 상세 분석과 조치 코드 제안을 받을 수 있습니다 — "
        f"Anthropic · OpenAI · AWS Bedrock · Ollama(로컬) 지원."
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
        "summary": (
            f"기본 규칙 분류: {intent}. AI provider 설정 시 LLM이 더 정확하게 의도를 해석합니다 "
            f"(Anthropic · OpenAI · Bedrock · Ollama)."
        ),
        "suggested_actions": [],
        "model": "rule-based",
    }
