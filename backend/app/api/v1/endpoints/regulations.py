"""
Regulations — 사업 시나리오 → 적용 규제 + 시점 가이드
"""

from fastapi import APIRouter, HTTPException, Query

from app.data.regulations import (
    REGULATIONS,
    SCENARIOS,
    TIMING,
    regulation_dict,
    scenario_dict,
)

router = APIRouter()


@router.get("/timings")
async def list_timings(lang: str = Query("ko", pattern="^(ko|en)$")) -> list[dict]:
    return [
        {"key": k, "label": v["ko" if lang == "ko" else "en"]}
        for k, v in TIMING.items()
    ]


@router.get("/regulations")
async def list_regulations(
    jurisdiction: str | None = Query(None, description="KR / EU / US / GLOBAL"),
    lang: str = Query("ko", pattern="^(ko|en)$"),
) -> list[dict]:
    items = [regulation_dict(c, lang) for c in REGULATIONS]
    if jurisdiction:
        items = [r for r in items if r and r["jurisdiction"] == jurisdiction.upper()]
    return [r for r in items if r]


@router.get("/regulations/{code}")
async def get_regulation(code: str, lang: str = Query("ko", pattern="^(ko|en)$")) -> dict:
    r = regulation_dict(code.upper(), lang)
    if not r:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return r


@router.get("/scenarios")
async def list_scenarios(lang: str = Query("ko", pattern="^(ko|en)$")) -> list[dict]:
    return [
        {
            "id": s.id,
            "name": s.name_ko if lang == "ko" else s.name_en,
            "description": s.description_ko if lang == "ko" else s.description_en,
            "applicable": s.applicable,
        }
        for s in SCENARIOS.values()
    ]


@router.get("/scenarios/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    lang: str = Query("ko", pattern="^(ko|en)$"),
) -> dict:
    s = scenario_dict(scenario_id, lang)
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return s
