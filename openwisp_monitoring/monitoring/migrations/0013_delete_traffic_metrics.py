from django.db import migrations


def delete_traffic_metrics(apps, schema_editor):
    Metric = apps.get_model('monitoring', 'Metric')
    Metric.objects.filter(field_name='rx_bytes').delete()
    Metric.objects.filter(field_name='tx_bytes').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0012_rename_graph_chart'),
    ]

    operations = [
        migrations.RunPython(
            delete_traffic_metrics, reverse_code=migrations.RunPython.noop
        ),
    ]
