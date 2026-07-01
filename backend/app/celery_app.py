from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "fashion_analyst",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.ingestion_tasks", "app.tasks.scheduled"],
)

# Phase 1 runs the whole ingestion pipeline (crawl -> extract -> verify -> embed -> kg_write) as
# one Celery task per seed query/source, with LangGraph handling the fine-grained agent chaining
# inside it (see app/graph/ingestion_graph.py). Splitting each stage into its own Celery task/queue
# for independent scaling is a Phase 2 optimization once real ingestion volume justifies it - the
# queue names below are reserved for that split and safe to route to today.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.ingestion_tasks.*": {"queue": "crawl"},
        "app.tasks.scheduled.*": {"queue": "crawl"},
    },
    beat_schedule={
        "incremental-crawl-due-sources": {
            "task": "app.tasks.scheduled.crawl_due_sources",
            "schedule": crontab(minute=0),  # hourly check of sources.crawl_frequency
        },
    },
)
