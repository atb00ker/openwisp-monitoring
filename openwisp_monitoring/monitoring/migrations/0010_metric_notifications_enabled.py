# Generated by Django 3.0.3 on 2020-05-25 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0009_allow_float_threshold'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='notifications_enabled',
            field=models.BooleanField(default=True),
        ),
    ]
