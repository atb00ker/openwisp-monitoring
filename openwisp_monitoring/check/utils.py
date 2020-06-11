from ..db import timeseries_db
from . import settings as app_settings

CONFIG_CHECK_RP = 'config_modified'


def run_checks_async():
    """
    Calls celery task run_checks
    is run in a background worker
    """
    from .tasks import run_checks

    run_checks.delay()


def manage_config_modified_retention_policy():
    """
    creates or updates the ``config_modified`` retention policy
    """
    duration = app_settings.CONFIG_CHECK_RETENTION_POLICY
    timeseries_db.create_or_alter_retention_policy(CONFIG_CHECK_RP, duration)
