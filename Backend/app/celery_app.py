"""Celery application for background tasks"""

import os
from celery import Celery
from celery.schedules import crontab
from app.logging_config import get_logger

logger = get_logger(__name__)

# Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "sme_costing_copilot",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # Results expire after 1 hour
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'execute-due-scheduled-reports': {
        'task': 'execute_due_scheduled_reports',
        'schedule': 60.0,  # Run every 60 seconds (1 minute)
        'options': {
            'expires': 55,  # Task expires after 55 seconds to avoid overlap
        }
    },
}

logger.info("celery_initialized", broker=REDIS_URL)
