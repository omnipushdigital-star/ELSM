from app.core.celery_app import celery_app


@celery_app.task
def check_battery_levels():
    """
    Phase 2: Check all deployed e-locks for low battery and trigger alerts.
    Runs every 6 hours via Celery Beat.
    """
    pass


@celery_app.task
def check_device_health():
    """
    Phase 2: Check all e-locks for missed health pings and mark offline.
    Runs daily via Celery Beat.
    """
    pass
