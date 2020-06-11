from django.db import migrations
from openwisp_monitoring.check.settings import AUTO_CONFIG_CHECK
from openwisp_monitoring.check.tasks import auto_create_config_modified


def add_config_modified_checks(apps, schema_editor):
    if not AUTO_CONFIG_CHECK:
        return
    Device = apps.get_model('config', 'Device')
    for device in Device.objects.all():
        auto_create_config_modified.delay(
            model=Device.__name__.lower(),
            app_label=Device._meta.app_label,
            object_id=str(device.pk),
        )


def remove_config_modified_checks(apps, schema_editor):
    Check = apps.get_model('config', 'Device')
    Check.objects.filter(name='Configuration Modified').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('check', '0003_create_ping'),
    ]

    operations = [
        migrations.RunPython(
            add_config_modified_checks, reverse_code=remove_config_modified_checks
        ),
    ]
