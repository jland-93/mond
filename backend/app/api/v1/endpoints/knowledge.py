"""
Knowledge 엔드포인트 — 카드 CRUD + AI 생성
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import is_enabled as ai_enabled  # async — db 인자 필요
from app.auth.deps import current_user, require_role
from app.core.database import get_db
from app.models.knowledge import KnowledgeCategory
from app.models.user import Role, User
from app.schemas.knowledge import (
    GenerateRequest,
    KnowledgeCardCreate,
    KnowledgeCardRead,
    KnowledgeCardUpdate,
)
from app.services import knowledge as knowledge_service

router = APIRouter()


@router.get("/cards", response_model=list[KnowledgeCardRead])
async def list_cards(
    category: KnowledgeCategory | None = Query(None),
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeCardRead]:
    items = await knowledge_service.list_cards(db, category=category)
    return [KnowledgeCardRead.model_validate(i) for i in items]


@router.post(
    "/cards",
    response_model=KnowledgeCardRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def create_card(payload: KnowledgeCardCreate, db: AsyncSession = Depends(get_db)) -> KnowledgeCardRead:
    card = await knowledge_service.create_card(db, payload)
    return KnowledgeCardRead.model_validate(card)


@router.patch(
    "/cards/{card_id}",
    response_model=KnowledgeCardRead,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def update_card(
    card_id: int,
    payload: KnowledgeCardUpdate,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeCardRead:
    card = await knowledge_service.get_card(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="card not found")
    updated = await knowledge_service.update_card(db, card, payload)
    return KnowledgeCardRead.model_validate(updated)


@router.delete(
    "/cards/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def delete_card(card_id: int, db: AsyncSession = Depends(get_db)) -> None:
    card = await knowledge_service.get_card(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="card not found")
    await knowledge_service.delete_card(db, card)


@router.post(
    "/cards/generate",
    response_model=list[KnowledgeCardRead],
    # AI 생성 카드는 검토 없이 사내 지식으로 노출되므로 ADMIN으로 좁힌다.
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def generate_cards(
    payload: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeCardRead]:
    if not await ai_enabled(db):
        raise HTTPException(
            status_code=503,
            detail="AI provider 미설정 — 관리자 → 연동 관리에서 AI key를 등록하거나 .env에 설정 후 사용하세요.",
        )
    cards = await knowledge_service.generate_cards(
        db,
        category=payload.category,
        topic_hint=payload.topic_hint,
        count=payload.count,
    )
    return [KnowledgeCardRead.model_validate(c) for c in cards]
