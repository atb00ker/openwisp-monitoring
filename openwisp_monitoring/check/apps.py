from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from .utils import manage_config_modified_retention_policy


class CheckConfig(AppConfig):
    name = 'openwisp_monitoring.check'
    label = 'check'
    verbose_name = _('Network Monitoring Checks')

    def ready(self):
        manage_config_modified_retention_policy()
