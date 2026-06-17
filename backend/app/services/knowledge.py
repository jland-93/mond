"""
🌙 Knowledge 서비스 — CRUD + AI 생성
"""

from __future__ import annotations

import json
import re

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import get_client, is_enabled
from app.core.config import settings
from app.core.logging import get_logger
from app.models.knowledge import KnowledgeCard, KnowledgeCategory, KnowledgeSource
from app.schemas.knowledge import KnowledgeCardCreate, KnowledgeCardUpdate

logger = get_logger(__name__)


async def list_cards(
    db: AsyncSession,
    *,
    category: KnowledgeCategory | None = None,
    published_only: bool = True,
) -> list[KnowledgeCard]:
    stmt = select(KnowledgeCard).order_by(KnowledgeCard.id.desc())
    if category:
        stmt = stmt.where(KnowledgeCard.category == category)
    if published_only:
        stmt = stmt.where(KnowledgeCard.published.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def get_card(db: AsyncSession, card_id: int) -> KnowledgeCard | None:
    return (await db.execute(select(KnowledgeCard).where(KnowledgeCard.id == card_id))).scalar_one_or_none()


async def create_card(db: AsyncSession, payload: KnowledgeCardCreate) -> KnowledgeCard:
    card = KnowledgeCard(**payload.model_dump())
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


async def update_card(db: AsyncSession, card: KnowledgeCard, payload: KnowledgeCardUpdate) -> KnowledgeCard:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, key, value)
    await db.commit()
    await db.refresh(card)
    return card


async def delete_card(db: AsyncSession, card: KnowledgeCard) -> None:
    await db.delete(card)
    await db.commit()


# ── AI 생성 ───────────────────────────────────────────────────────────
GENERATE_SYSTEM = """\
You are Mond's knowledge editor. Produce concise, accurate Knowledge Hub cards
that help engineers learn DevSecOps & security/compliance topics in minutes.

Output STRICT JSON only:
{
  "cards": [
    {
      "slug": "kebab-case-id",
      "title_ko": "한국어 제목",
      "title_en": "English title",
      "summary_ko": "한국어 요약 (2~4문장, 280자 이내)",
      "summary_en": "English summary (2-4 sentences, <= 280 chars)",
      "ask_ko": "Mond AI에게 더 깊이 물어볼 한국어 질문 1개",
      "ask_en": "One follow-up question for Mond AI in English",
      "refs": ["https://...", "https://..."]
    }
  ]
}

Rules:
- Topic must match the requested category strictly.
- summary must be neutral, factual, no marketing tone.
- Provide 1-2 reputable references (OWASP, NIST, KISA, official law sites).
- slug should be unique-ish and human-readable.
- No markdown fences. No prose outside JSON.
"""


async def generate_cards(
    db: AsyncSession,
    *,
    category: KnowledgeCategory,
    topic_hint: str | None,
    count: int,
) -> list[KnowledgeCard]:
    if not is_enabled():
        # AI 비활성 — 사용자에게 명확히 안내하기 위해 빈 리스트 + 경고는 endpoint에서.
        return []

    client = get_client()
    assert client is not None

    user_prompt = json.dumps(
        {
            "category": category.value,
            "count": count,
            "topic_hint": topic_hint or "Pick fresh, currently-relevant topics in this category.",
            "language_note": "Provide both ko (한국어) and en faithfully — do not just translate machine-style.",
        },
        ensure_ascii=False,
    )

    try:
        response = await client.messages.create(
            model=settings.AI_MODEL_DEFAULT,
            max_tokens=4096,
            system=GENERATE_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        logger.warning("knowledge_generate_failed", error=str(exc))
        return []

    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    parsed = _parse_json(text) or {}
    raw_cards = parsed.get("cards", []) if isinstance(parsed, dict) else []

    created: list[KnowledgeCard] = []
    for raw in raw_cards:
        if not isinstance(raw, dict):
            continue
        slug = _safe_slug(str(raw.get("slug", "")))
        if not slug:
            continue
        # 동일 slug 충돌은 카운터 붙여서 회피
        slug = await _unique_slug(db, slug)
        card = KnowledgeCard(
            slug=slug,
            category=category,
            title_ko=str(raw.get("title_ko", "")).strip()[:512] or "Untitled",
            title_en=str(raw.get("title_en", "")).strip()[:512] or "Untitled",
            summary_ko=str(raw.get("summary_ko", "")).strip()[:2000],
            summary_en=str(raw.get("summary_en", "")).strip()[:2000],
            ask_ko=str(raw.get("ask_ko", "")).strip()[:2000],
            ask_en=str(raw.get("ask_en", "")).strip()[:2000],
            refs=[r for r in raw.get("refs", []) if isinstance(r, str)][:5],
            source=KnowledgeSource.AI,
            model=settings.AI_MODEL_DEFAULT,
            published=True,
        )
        db.add(card)
        created.append(card)

    await db.commit()
    for c in created:
        await db.refresh(c)
    return created


def _parse_json(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].lstrip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _safe_slug(raw: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", raw.lower()).strip("-")
    return s[:128]


async def _unique_slug(db: AsyncSession, slug: str) -> str:
    existing = {
        row[0]
        for row in (await db.execute(select(KnowledgeCard.slug).where(KnowledgeCard.slug.startswith(slug)))).all()
    }
    if slug not in existing:
        return slug
    for n in range(2, 100):
        candidate = f"{slug}-{n}"
        if candidate not in existing:
            return candidate
    return slug  # 거의 안 옴
