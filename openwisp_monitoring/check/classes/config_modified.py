from swapper import load_model

from ..settings import CONFIG_CHECK_MAX_TIME
from ..utils import CONFIG_CHECK_RP
from .base import BaseCheck

AlertSettings = load_model('monitoring', 'AlertSettings')


class ConfigModified(BaseCheck):
    def __init__(self, check, params):
        self.check_instance = check
        self.related_object = check.content_object
        self.params = params

    def check(self, store=True):
        if not hasattr(self.related_object, 'config'):
            return
        result = 0 if self.related_object.config.status == 'applied' else 1
        if store:
            self.get_metric().write(
                result, retention_policy=CONFIG_CHECK_RP,
            )
        return result

    def get_metric(self):
        metric, created = self._get_or_create_metric(field_name='config_modified')
        if created:
            self._create_alert_setting(metric)
        return metric

    def _create_alert_setting(self, metric):
        alert_s = AlertSettings(
            metric=metric, operator='>', value=0, seconds=CONFIG_CHECK_MAX_TIME * 60
        )
        alert_s.full_clean()
        alert_s.save()
