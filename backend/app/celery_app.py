"""
Celery 앱 — 스캔 큐.

OSS 기본은 인라인 실행 (SCAN_QUEUE_ENABLED=false).
운영에서 대용량/장시간 스캔의 타임아웃을 피하려면 true로 설정하고
별도 worker 프로세스를 띄운다.

docker compose:
  - SCAN_QUEUE_ENABLED=true 로 backend env 갱신
  - worker 서비스 추가 (entrypoint: celery worker)
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mond",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
)
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="mond_scans",
    task_track_started=True,
)

# task 정의 모듈을 명시적으로 import해야 worker가 task를 인식.
celery_app.autodiscover_tasks(["app.tasks"], force=True)
