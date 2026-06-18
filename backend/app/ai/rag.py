"""
RAG MVP — Mond 데이터를 검색해 LLM에 context로 주입

검색 대상 (모두 사용자가 등록·시드한 자체 데이터):
  - Finding   : 최근 미해결 finding (severity 가중)
  - Policy    : 활성 정책
  - Knowledge : 카드 (title / summary 매칭)
  - Regulation: 시나리오/규제 가이드 (정적 데이터)

알고리즘 — MVP는 PostgreSQL ILIKE 매칭 (벡터 임베딩은 v0.2).
한국어 토큰화는 simple split (정확도보다 invariant).
각 결과를 `[N]` 번호로 인용해 LLM에 넘기고, frontend가 카드로 출처 노출.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding, FindingStatus, Severity
from app.models.knowledge import KnowledgeCard
from app.models.policy import Policy


@dataclass
class Citation:
    """LLM이 [N]으로 참조하는 출처 한 건."""

    n: int
    kind: str           # "finding" / "policy" / "knowledge"
    title: str
    snippet: str        # 100자 이내 요약
    url: str | None = None  # 클릭 시 이동할 내부 경로 또는 외부 URL

    def to_dict(self) -> dict:
        return {"n": self.n, "kind": self.kind, "title": self.title, "snippet": self.snippet, "url": self.url}


def _tokens(q: str) -> list[str]:
    """alphanumeric + 한글 단어. 1자 토큰은 제거."""
    return [t for t in re.split(r"[^\w가-힣]+", q.lower()) if len(t) > 1][:6]


async def search(db: AsyncSession, query: str, *, limit_per_source: int = 3) -> list[Citation]:
    """질문에서 키워드를 뽑아 Mond DB에서 관련 자료를 검색."""
    toks = _tokens(query)
    if not toks:
        return []

    citations: list[Citation] = []
    n = 1

    # 1) Finding — title/description 매칭 + 미해결 우선
    f_conditions = [Finding.title.ilike(f"%{t}%") | Finding.description.ilike(f"%{t}%") for t in toks]
    f_stmt = (
        select(Finding)
        .where(or_(*f_conditions))
        .where(Finding.status != FindingStatus.RESOLVED)
        .order_by(Finding.severity == Severity.CRITICAL, Finding.created_at.desc())
        .limit(limit_per_source)
    )
    for f in (await db.execute(f_stmt)).scalars().all():
        snippet = (f.description or "")[:120] or f"{f.scanner} · {f.rule_id}"
        citations.append(Citation(
            n=n, kind="finding",
            title=f"#{f.id} {f.title}",
            snippet=snippet,
            url=f"/findings?focus={f.id}",
        ))
        n += 1

    # 2) Policy
    p_conditions = [Policy.name.ilike(f"%{t}%") | Policy.description.ilike(f"%{t}%") for t in toks]
    p_stmt = select(Policy).where(or_(*p_conditions)).limit(limit_per_source)
    for p in (await db.execute(p_stmt)).scalars().all():
        snippet = (p.description or "")[:120] or f"{p.policy_type.value} · threshold={p.severity_threshold}"
        citations.append(Citation(
            n=n, kind="policy",
            title=p.name,
            snippet=snippet,
            url=f"/policies?focus={p.id}",
        ))
        n += 1

    # 3) Knowledge cards
    k_conditions = [
        KnowledgeCard.title_ko.ilike(f"%{t}%") | KnowledgeCard.title_en.ilike(f"%{t}%")
        | KnowledgeCard.summary_ko.ilike(f"%{t}%") | KnowledgeCard.summary_en.ilike(f"%{t}%")
        for t in toks
    ]
    k_stmt = (
        select(KnowledgeCard)
        .where(or_(*k_conditions))
        .where(KnowledgeCard.published.is_(True))
        .limit(limit_per_source)
    )
    for k in (await db.execute(k_stmt)).scalars().all():
        title = k.title_ko or k.title_en or k.slug
        snippet = (k.summary_ko or k.summary_en or "")[:120]
        url = (k.refs or [None])[0] if k.refs else None
        citations.append(Citation(n=n, kind="knowledge", title=title, snippet=snippet, url=url))
        n += 1

    return citations


def build_context_block(citations: list[Citation]) -> str:
    """LLM system prompt에 붙일 컨텍스트 블록."""
    if not citations:
        return ""
    lines = ["다음은 Mond 시스템에서 검색된 관련 자료입니다. 답변할 때 [N] 형식으로 인용하세요:"]
    for c in citations:
        lines.append(f"  [{c.n}] ({c.kind}) {c.title}: {c.snippet}")
    return "\n".join(lines)
