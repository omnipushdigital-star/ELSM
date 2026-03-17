from app.core.celery_app import celery_app


@celery_app.task
def check_sla_breaches():
    """
    Phase 3: Check all open ESE/EUE requests and mark SLA breaches.
    Runs every hour via Celery Beat.
    """
    # Implementation in Phase 3
    pass
