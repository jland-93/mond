"""
Celery 스캔 태스크 — async 코어를 sync wrapper로 감싸 실행.
"""

from __future__ import annotations

import asyncio

from app.celery_app import celery_app
from app.core.logging import get_logger
from app.services import scan as scan_service

logger = get_logger(__name__)


@celery_app.task(name="mond.run_scan", bind=True, max_retries=2)
def run_scan(self, scan_id: int) -> dict:
    """worker가 호출하는 entrypoint.

    pending Scan 객체를 받아서 스캐너 실행 + Finding 저장 + 알림까지.
    """
    try:
        return asyncio.run(scan_service.execute_pending_scan(scan_id))
    except Exception as exc:
        logger.exception("celery_scan_failed", scan_id=scan_id)
        raise self.retry(exc=exc, countdown=30)
