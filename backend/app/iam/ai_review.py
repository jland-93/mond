"""
Access Request AI 1차 자율 판단

Claude가 요청을 평가해 다음 3개 분기로 결정:
  - auto_approve : 위험 낮음, 자동 승인 (사용자에게 즉시 grant 진행)
  - needs_human  : 담당자 검토 필요 (보안 담당자 보드로)
  - deny         : 명백한 거부 사유

API 키 없으면 기본 규칙 fallback (admin/Full = needs_human, read = auto_approve).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import complete_json, is_enabled
from app.core.logging import get_logger
from app.models.iam import IAMIdentity, Permission

logger = get_logger(__name__)


@dataclass
class ReviewResult:
    decision: str          # "auto_approve" | "needs_human" | "deny"
    risk_level: str        # critical / high / medium / low
    reason: str
    model: str
    confidence: float = 0.0


SYSTEM_PROMPT = """\
You are Mond's access review agent. You evaluate IAM permission requests
and decide whether they can be auto-approved, need human review, or should be denied.

Always respond with strict JSON:
{
  "decision": "auto_approve" | "needs_human" | "deny",
  "risk_level": "critical" | "high" | "medium" | "low",
  "reason": "1-3 sentence explanation in the requester's language",
  "confidence": 0.0
}

Default policy:
- admin / Full / wildcard permissions → needs_human or deny
- write-level on production or shared resources → needs_human
- read-only → auto_approve unless reason is suspicious
- short-duration (<= 8h) tilts toward auto_approve when read-only
- if reason is empty, vague, or contradicts the permission → deny

Output ONLY JSON. No markdown fences.
"""


async def review(
    db: AsyncSession,
    *,
    requester: str,
    reason: str,
    duration_hours: int | None,
    identity: IAMIdentity,
    permission: Permission,
) -> ReviewResult:
    if not await is_enabled(db):
        return _heuristic(permission)

    user_prompt = json.dumps(
        {
            "requester": requester,
            "reason": reason,
            "duration_hours": duration_hours,
            "identity": {
                "name": identity.name,
                "type": identity.identity_type.value,
                "external_id": identity.external_id,
            },
            "permission": {
                "name": permission.name,
                "external_id": permission.external_id,
                "description": permission.description,
                "risk_hint": permission.risk_hint,
            },
        },
        ensure_ascii=False,
    )

    result = await complete_json(db, SYSTEM_PROMPT, user_prompt)
    if result is None:
        logger.warning("access_review_failed_or_disabled")
        return _heuristic(permission)

    parsed = _parse(result.text) or {}
    decision = parsed.get("decision", "needs_human")
    if decision not in {"auto_approve", "needs_human", "deny"}:
        decision = "needs_human"

    return ReviewResult(
        decision=decision,
        risk_level=str(parsed.get("risk_level", "medium")),
        reason=str(parsed.get("reason", "AI 응답 파싱 실패 — 담당자 검토로 안내"))[:1000],
        model=f"{result.provider}:{result.model}",
        confidence=float(parsed.get("confidence", 0.0)),
    )


def _parse(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].lstrip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _heuristic(permission: Permission) -> ReviewResult:
    """API 키 없을 때 — 권한 risk_hint 기반 기본 규칙."""
    hint = (permission.risk_hint or "").lower()
    if hint == "read":
        return ReviewResult(
            decision="auto_approve",
            risk_level="low",
            reason="[기본 규칙] 읽기 전용 권한 — 자동 승인. Claude 분석 활성화 시 더 정확한 판단 가능.",
            model="rule-based",
            confidence=0.4,
        )
    if hint == "admin":
        return ReviewResult(
            decision="needs_human",
            risk_level="critical",
            reason="[기본 규칙] 관리자/전권 권한 — 보안 담당자 검토 필요.",
            model="rule-based",
            confidence=0.7,
        )
    return ReviewResult(
        decision="needs_human",
        risk_level="medium",
        reason="[기본 규칙] 위험 등급 미상 — 담당자 검토 권고.",
        model="rule-based",
        confidence=0.3,
    )
