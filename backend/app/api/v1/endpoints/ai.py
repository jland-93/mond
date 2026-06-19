"""
AI 엔드포인트 — Finding triage / 자연어 쿼리
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import insights as ai_insights
from app.ai.client import current_model_label, get_provider as ai_provider, is_enabled as ai_enabled
from app.auth.deps import current_user
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.models.ai_insight import InsightKind
from app.models.user import User
from app.schemas.ai_insight import AIInsightRead, AnalyzeRequest, AnalyzeResponse
from app.services import ai as ai_service
from app.services import finding as finding_service

router = APIRouter()


@router.get("/status")
async def ai_status(db: AsyncSession = Depends(get_db)) -> dict:
    """현재 활성화된 AI provider와 모델을 노출. UI가 사용자에게 출처를 명시할 때 사용."""
    return {
        "enabled": await ai_enabled(db),
        "provider": await ai_provider(db),  # anthropic / openai / bedrock / ollama / null
        "model": await current_model_label(db),
    }


@router.post("/findings/{finding_id}/triage", response_model=AIInsightRead)
async def triage_finding(
    finding_id: int,
    deep: bool = Query(False, description="claude-sonnet-4-6 사용 여부"),
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> AIInsightRead:
    finding = await finding_service.get_finding(db, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    insight = await ai_service.analyze_and_store(
        db, finding, kind=InsightKind.TRIAGE, deep=deep
    )
    return AIInsightRead.model_validate(insight)


@router.get("/findings/{finding_id}/insights", response_model=list[AIInsightRead])
async def list_finding_insights(
    finding_id: int,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AIInsightRead]:
    items = await ai_service.list_insights_for_finding(db, finding_id)
    return [AIInsightRead.model_validate(i) for i in items]


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(RateLimiter("ai_analyze", 20, 60, "user"))],
)
async def analyze_query(
    payload: AnalyzeRequest,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    """자연어 쿼리를 분류한다. 'scan' 의도이면 클라이언트가 후속 호출을 만든다."""
    result = await ai_insights.route_query(db, payload.query)
    return AnalyzeResponse(
        intent=result.get("intent", "unknown"),
        summary=result.get("summary", ""),
        suggested_actions=result.get("suggested_actions", []) or [],
        model=result.get("model") or await current_model_label(db),
        citations=result.get("citations") or [],
        redactions=result.get("redactions") or {},
    )
