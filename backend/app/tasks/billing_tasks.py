from app.core.celery_app import celery_app


@celery_app.task
def generate_quarterly_uc():
    """
    Phase 5: Auto-generate Utilization Certificates at end of billing quarter.
    """
    pass
