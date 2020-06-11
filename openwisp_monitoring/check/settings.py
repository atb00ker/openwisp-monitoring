from django.conf import settings

CHECK_CLASSES = getattr(
    settings,
    'OPENWISP_MONITORING_CHECK_CLASSES',
    (
        ('openwisp_monitoring.check.classes.Ping', 'Ping'),
        ('openwisp_monitoring.check.classes.ConfigModified', 'Configuration Modified'),
    ),
)
AUTO_PING = getattr(settings, 'OPENWISP_MONITORING_AUTO_PING', True)
AUTO_CONFIG_CHECK = getattr(
    settings, 'OPENWISP_MONITORING_AUTO_DEVICE_CONFIG_CHECK', True
)
# Input in minutes
CONFIG_CHECK_MAX_TIME = getattr(
    settings, 'OPENWISP_MONITORING_DEVICE_CONFIG_CHECK_MAX_TIME', 5
)
CONFIG_CHECK_RETENTION_POLICY = getattr(
    settings, 'OPENWISP_MONITORING_DEVICE_CONFIG_CHECK_RETENTION_POLICY', '48h0m0s',
)
MANAGEMENT_IP_ONLY = getattr(settings, 'OPENWISP_MONITORING_MANAGEMENT_IP_ONLY', True)
