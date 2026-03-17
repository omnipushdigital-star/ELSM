from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "elsm",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.sla_tasks",
        "app.tasks.alert_tasks",
        "app.tasks.billing_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        # Check SLA breaches every hour
        "check-sla-breaches": {
            "task": "app.tasks.sla_tasks.check_sla_breaches",
            "schedule": 3600.0,
        },
        # Check battery levels every 6 hours
        "check-battery-levels": {
            "task": "app.tasks.alert_tasks.check_battery_levels",
            "schedule": 21600.0,
        },
        # Daily health ping check
        "check-device-health": {
            "task": "app.tasks.alert_tasks.check_device_health",
            "schedule": 86400.0,
        },
    },
)
