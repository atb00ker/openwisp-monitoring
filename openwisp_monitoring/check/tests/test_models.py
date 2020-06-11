from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TransactionTestCase
from django.utils.timezone import now
from swapper import load_model

from openwisp_controller.config.models import Device

from ...device.tests import TestDeviceMonitoringMixin
from .. import settings as app_settings
from ..classes import ConfigModified, Ping
from ..tasks import auto_create_config_modified, auto_create_ping

Check = load_model('check', 'Check')
Metric = load_model('monitoring', 'Metric')
AlertSettings = load_model('monitoring', 'AlertSettings')


class TestModels(TestDeviceMonitoringMixin, TransactionTestCase):
    _PING = app_settings.CHECK_CLASSES[0][0]
    _CONFIG_MODIFIED = app_settings.CHECK_CLASSES[1][0]

    def test_check_str(self):
        c = Check(name='Test check')
        self.assertEqual(str(c), c.name)

    def test_check_no_content_type(self):
        check = Check(
            name='Configuration Modified',
            check='openwisp_monitoring.check.classes.ConfigModified',
        )
        m = check.check_instance.get_metric()
        self.assertEqual(m, Metric.objects.first())

    def test_check_str_with_relation(self):
        obj = self._create_user()
        c = Check(name='Check', content_object=obj)
        expected = '{0} (User: {1})'.format(c.name, obj)
        self.assertEqual(str(c), expected)

    def test_check_class(self):
        with self.subTest('Test Ping check Class'):
            c = Check(name='Ping class check', check=self._PING)
            self.assertEqual(c.check_class, Ping)
        with self.subTest('Test Configuration Modified check Class'):
            c = Check(
                name='Configuration Modified class check', check=self._CONFIG_MODIFIED
            )
            self.assertEqual(c.check_class, ConfigModified)

    def test_check_instance(self):
        obj = self._create_device(organization=self._create_org())
        with self.subTest('Test Ping check instance'):
            c = Check(
                name='Ping class check', check=self._PING, content_object=obj, params={}
            )
            i = c.check_instance
            self.assertIsInstance(i, Ping)
            self.assertEqual(i.related_object, obj)
            self.assertEqual(i.params, c.params)
        with self.subTest('Test Configuration Modified check instance'):
            c = Check(
                name='Configuration Modified class check',
                check=self._CONFIG_MODIFIED,
                content_object=obj,
                params={},
            )
            i = c.check_instance
            self.assertIsInstance(i, ConfigModified)
            self.assertEqual(i.related_object, obj)
            self.assertEqual(i.params, c.params)

    def test_validation(self):
        with self.subTest('Test Ping check validation'):
            check = Check(name='Ping check', check=self._PING, params={})
            try:
                check.full_clean()
            except ValidationError as e:
                self.assertIn('device', str(e))
            else:
                self.fail('ValidationError not raised')
        with self.subTest('Test Configuration Modified check validation'):
            check = Check(name='Ping check', check=self._CONFIG_MODIFIED, params={})
            try:
                check.full_clean()
            except ValidationError as e:
                self.assertIn('device', str(e))
            else:
                self.fail('ValidationError not raised')

    def test_auto_check_creation(self):
        self.assertEqual(Check.objects.count(), 0)
        d = self._create_device(organization=self._create_org())
        self.assertEqual(Check.objects.count(), 2)
        with self.subTest('Test AUTO_PING'):
            c1 = Check.objects.get(name='Ping')
            self.assertEqual(c1.content_object, d)
            self.assertIn('Ping', c1.check)
        with self.subTest('Test AUTO_CONFIG_CHECK'):
            c2 = Check.objects.get(name='Configuration Modified')
            self.assertEqual(c2.content_object, d)
            self.assertIn('ConfigModified', c2.check)

    def test_device_deleted(self):
        self.assertEqual(Check.objects.count(), 0)
        d = self._create_device(organization=self._create_org())
        self.assertEqual(Check.objects.count(), 2)
        d.delete()
        self.assertEqual(Check.objects.count(), 0)

    @patch('openwisp_monitoring.check.settings.AUTO_PING', False)
    def test_device_modified_problem_config_modified(self):
        self.assertEqual(Check.objects.count(), 0)
        self._create_config(status='modified', organization=self._create_org())
        d = Device.objects.first()
        self.assertEqual(Check.objects.count(), 2)
        self.assertEqual(Metric.objects.count(), 0)
        self.assertEqual(AlertSettings.objects.count(), 0)
        check = Check.objects.get(name='Configuration Modified')
        check.perform_check()
        self.assertEqual(Metric.objects.count(), 1)
        self.assertEqual(AlertSettings.objects.count(), 1)
        m = Metric.objects.first()
        self.assertEqual(m.content_object, d)
        self.assertEqual(m.key, 'configmodified')
        dm = d.monitoring
        # Health status should not change as threshold time not crossed
        self.assertEqual(dm.status, 'ok')
        m.write(1, time=now() - timedelta(minutes=10))
        dm.refresh_from_db()
        self.assertEqual(dm.status, 'problem')

    @patch(
        'openwisp_monitoring.device.base.models.app_settings.CRITICAL_DEVICE_METRICS',
        [{'key': 'configmodified', 'field_name': 'config_modified'}],
    )
    @patch('openwisp_monitoring.check.settings.AUTO_PING', False)
    def test_config_modified_critical_metric(self):
        self._create_config(status='modified', organization=self._create_org())
        self.assertEqual(Check.objects.count(), 2)
        d = Device.objects.first()
        dm = d.monitoring
        check = Check.objects.get(name='Configuration Modified')
        check.perform_check()
        self.assertEqual(Metric.objects.count(), 1)
        self.assertEqual(AlertSettings.objects.count(), 1)
        m = Metric.objects.first()
        self.assertTrue(dm.is_metric_critical(m))
        m.write(1, time=now() - timedelta(minutes=10))
        dm.refresh_from_db()
        self.assertEqual(dm.status, 'critical')

    def test_no_duplicate_check_created(self):
        self._create_config(organization=self._create_org())
        self.assertEqual(Check.objects.count(), 2)
        d = Device.objects.first()
        auto_create_config_modified.delay(
            model=Device.__name__.lower(),
            app_label=Device._meta.app_label,
            object_id=str(d.pk),
        )
        auto_create_ping.delay(
            model=Device.__name__.lower(),
            app_label=Device._meta.app_label,
            object_id=str(d.pk),
        )
        self.assertEqual(Check.objects.count(), 2)
