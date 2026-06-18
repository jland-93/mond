"""
AI Provider 동적 설정 — 관리자가 UI에서 LLM provider 자격증명을 관리.

권한: 모든 엔드포인트 ADMIN 전용.
api_key는 응답에 마스킹("sk-...••••...abcd")으로만 노출되고, 평문은 절대 반환되지 않는다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import client as ai_client
from app.ai.secrets import decrypt, encrypt, mask
from app.auth.deps import require_role
from app.core.database import get_db
from app.models.ai_provider import AIProviderConfig
from app.models.user import Role

router = APIRouter()

SUPPORTED = {"anthropic", "openai", "bedrock", "ollama"}


class AIProviderRead(BaseModel):
    id: int
    provider: str
    enabled: bool
    is_default: bool
    has_api_key: bool
    api_key_masked: str
    base_url: str | None = None
    region: str | None = None
    model_default: str | None = None
    model_deep: str | None = None


class AIProviderUpsert(BaseModel):
    provider: str
    enabled: bool = True
    is_default: bool = False
    # api_key는 변경 시에만 전송; 빈 문자열은 "건드리지 않음"으로 해석한다.
    api_key: str | None = Field(default=None, max_length=4096)
    base_url: str | None = Field(default=None, max_length=512)
    region: str | None = Field(default=None, max_length=32)
    model_default: str | None = Field(default=None, max_length=128)
    model_deep: str | None = Field(default=None, max_length=128)


def _to_read(row: AIProviderConfig) -> AIProviderRead:
    raw = decrypt(row.api_key_encrypted)
    return AIProviderRead(
        id=row.id,
        provider=row.provider,
        enabled=row.enabled,
        is_default=row.is_default,
        has_api_key=bool(raw),
        api_key_masked=mask(raw),
        base_url=row.base_url,
        region=row.region,
        model_default=row.model_default,
        model_deep=row.model_deep,
    )


@router.get(
    "",
    response_model=list[AIProviderRead],
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def list_providers(db: AsyncSession = Depends(get_db)) -> list[AIProviderRead]:
    rows = (
        await db.execute(select(AIProviderConfig).order_by(AIProviderConfig.provider))
    ).scalars().all()
    return [_to_read(r) for r in rows]


@router.put(
    "",
    response_model=AIProviderRead,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def upsert_provider(
    payload: AIProviderUpsert,
    db: AsyncSession = Depends(get_db),
) -> AIProviderRead:
    """provider 1:1 upsert. api_key가 None/빈 문자열이면 기존 값 유지."""
    provider = payload.provider.lower().strip()
    if provider not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"unsupported provider: {provider}")

    row = (
        await db.execute(select(AIProviderConfig).where(AIProviderConfig.provider == provider))
    ).scalar_one_or_none()

    if row is None:
        row = AIProviderConfig(provider=provider)
        db.add(row)

    row.enabled = payload.enabled
    row.base_url = payload.base_url or None
    row.region = payload.region or None
    row.model_default = payload.model_default or None
    row.model_deep = payload.model_deep or None
    if payload.api_key:  # 빈 문자열은 변경 안함으로 해석
        row.api_key_encrypted = encrypt(payload.api_key)

    # is_default=True로 들어오면 다른 행은 모두 False
    if payload.is_default:
        await db.execute(
            update(AIProviderConfig).values(is_default=False)
        )
        row.is_default = True
    else:
        row.is_default = False

    await db.commit()
    await db.refresh(row)
    # lru cache가 있다면 invalidate (현재 client.py는 lru 없음 — 매 호출 DB 조회)
    return _to_read(row)


@router.post(
    "/{provider_id}/activate",
    response_model=AIProviderRead,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def activate_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
) -> AIProviderRead:
    row = (
        await db.execute(select(AIProviderConfig).where(AIProviderConfig.id == provider_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="provider config not found")
    await db.execute(update(AIProviderConfig).values(is_default=False))
    row.is_default = True
    row.enabled = True
    await db.commit()
    await db.refresh(row)
    return _to_read(row)


@router.delete(
    "/{provider_id}",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = (
        await db.execute(select(AIProviderConfig).where(AIProviderConfig.id == provider_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="provider config not found")
    await db.delete(row)
    await db.commit()
    return {"ok": True}


class TestRequest(BaseModel):
    provider: str
    api_key: str | None = None
    base_url: str | None = None
    region: str | None = None
    model: str | None = None


class TestResponse(BaseModel):
    ok: bool
    provider: str
    model: str
    detail: str


@router.post(
    "/test",
    response_model=TestResponse,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def test_provider(payload: TestRequest) -> TestResponse:
    """주어진 자격으로 1회 호출해 연결 가능 여부 확인. 저장은 하지 않음."""
    provider = payload.provider.lower().strip()
    if provider not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"unsupported provider: {provider}")

    # client.py의 내부 호출을 우회해 임시 runtime 구성
    from app.core.config import settings

    model_fallback = {
        "anthropic": settings.AI_MODEL_DEFAULT,
        "openai": settings.OPENAI_MODEL_DEFAULT,
        "bedrock": settings.BEDROCK_MODEL_DEFAULT,
        "ollama": settings.OLLAMA_MODEL_DEFAULT,
    }
    rt = ai_client.ProviderRuntime(
        provider=provider,
        api_key=payload.api_key,
        base_url=payload.base_url,
        region=payload.region or (settings.BEDROCK_REGION if provider == "bedrock" else None),
        model_default=payload.model or model_fallback[provider],
        model_deep=payload.model or model_fallback[provider],
        source="test",
    )
    if not ai_client._has_credentials(rt):
        return TestResponse(ok=False, provider=provider, model=rt.model_default, detail="missing credentials")

    system = "Return strict JSON: {\"ok\": true}"
    user = "ping"
    try:
        if provider == "anthropic":
            result = await ai_client._call_anthropic(rt, system, user, rt.model_default, 64)
        elif provider == "openai":
            result = await ai_client._call_openai(rt, system, user, rt.model_default, 64)
        elif provider == "bedrock":
            result = await ai_client._call_bedrock(rt, system, user, rt.model_default, 64)
        else:
            result = await ai_client._call_ollama(rt, system, user, rt.model_default, 64)
    except Exception as exc:
        return TestResponse(ok=False, provider=provider, model=rt.model_default, detail=str(exc)[:300])

    return TestResponse(ok=True, provider=result.provider, model=result.model, detail="connected")
