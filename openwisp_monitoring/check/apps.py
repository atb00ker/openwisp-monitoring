from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from openwisp_monitoring.check import settings as app_settings
from swapper import load_model


class CheckConfig(AppConfig):
    name = 'openwisp_monitoring.check'
    label = 'check'
    verbose_name = _('Network Monitoring Checks')

    def ready(self):
        self._connect_signals()

    def _connect_signals(self):
        if app_settings.AUTO_PING:
            from .base.models import auto_ping_receiver

            post_save.connect(
                auto_ping_receiver,
                sender=load_model('config', 'Device'),
                dispatch_uid='auto_ping',
            )
