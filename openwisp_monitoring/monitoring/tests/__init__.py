from datetime import timedelta

from django.utils.timezone import now
from swapper import load_model

from openwisp_users.tests.utils import TestOrganizationMixin

from ...db import timeseries_db
from ...db.backends import TIMESERIES_DB
from .. import register_chart, unregister_chart

start_time = now()
ten_minutes_ago = start_time - timedelta(minutes=10)
Chart = load_model('monitoring', 'Chart')
Metric = load_model('monitoring', 'Metric')
AlertSettings = load_model('monitoring', 'AlertSettings')

# chart configuration queries of InfluxDB for automated tests
test_query = {
    'histogram': {
        'influxdb': (
            "SELECT {fields|SUM|/ 1} FROM {key} "
            "WHERE time >= '{time}' AND content_type = "
            "'{content_type}' AND object_id = '{object_id}'"
        )
    },
    'bad_test': {'influxdb': "BAD"},
    'default': {
        'influxdb': (
            "SELECT {field_name} FROM {key} WHERE time >= '{time}' AND "
            "content_type = '{content_type}' AND object_id = '{object_id}'"
        )
    },
    'multiple_test': {
        'influxdb': (
            "SELECT {field_name}, value2 FROM {key} WHERE time >= '{time}' AND "
            "content_type = '{content_type}' AND object_id = '{object_id}'"
        )
    },
    'mean_test': {
        'influxdb': (
            "SELECT MEAN({field_name}) AS {field_name} FROM {key} WHERE time >= '{time}' AND "
            "content_type = '{content_type}' AND object_id = '{object_id}'"
        )
    },
    'sum_test': {
        'influxdb': (
            "SELECT SUM({field_name}) AS {field_name} FROM {key} WHERE time >= '{time}' AND "
            "content_type = '{content_type}' AND object_id = '{object_id}'"
        )
    },
    'top_fields_mean': {
        'influxdb': (
            "SELECT {fields|MEAN} FROM {key} "
            "WHERE time >= '{time}' AND content_type = "
            "'{content_type}' AND object_id = '{object_id}'"
        )
    },
}

# this custom chart configuration is used for automated testing purposes
charts = {
    'histogram': {
        'type': 'histogram',
        'title': 'Histogram',
        'description': 'Histogram',
        'top_fields': 2,
        'order': 999,
        'query': test_query['histogram'],
    },
    'dummy': {
        'type': 'line',
        'title': 'Dummy chart',
        'description': 'Dummy chart for testing purposes.',
        'unit': 'candies',
        'order': 999,
        'query': None,
    },
    'bad_test': {
        'type': 'line',
        'title': 'Bugged chart for testing purposes',
        'description': 'Bugged chart for testing purposes.',
        'unit': 'bugs',
        'order': 999,
        'query': test_query['bad_test'],
    },
    'default': {
        'type': 'line',
        'title': 'Default query for testing purposes',
        'description': 'Default query for testing purposes',
        'unit': 'n.',
        'order': 999,
        'query': test_query['default'],
    },
    'multiple_test': {
        'type': 'line',
        'title': 'Multiple test',
        'description': 'For testing purposes',
        'unit': 'n.',
        'order': 999,
        'query': test_query['multiple_test'],
    },
    'mean_test': {
        'type': 'line',
        'title': 'Mean test',
        'description': 'For testing purposes',
        'unit': 'n.',
        'order': 999,
        'query': test_query['mean_test'],
    },
    'sum_test': {
        'type': 'line',
        'title': 'Sum test',
        'description': 'For testing purposes',
        'unit': 'n.',
        'order': 999,
        'query': test_query['sum_test'],
    },
    'top_fields_mean': {
        'type': 'histogram',
        'title': 'Top fields mean test',
        'description': 'For testing purposes',
        'top_fields': 2,
        'order': 999,
        'query': test_query['top_fields_mean'],
    },
}


class TestMonitoringMixin(TestOrganizationMixin):
    ORIGINAL_DB = TIMESERIES_DB['NAME']
    TEST_DB = f'{ORIGINAL_DB}_test'

    @classmethod
    def setUpClass(cls):
        # By default timeseries_db.get_db shall connect to the database
        # defined in settings when apps are loaded. We don't want that while testing
        timeseries_db.db_name = cls.TEST_DB
        del timeseries_db.get_db
        timeseries_db.create_database()
        for key, value in charts.items():
            register_chart(key, value)

    @classmethod
    def tearDownClass(cls):
        timeseries_db.drop_database()
        for key in charts.keys():
            unregister_chart(key)

    def tearDown(self):
        timeseries_db.delete_metric_data()

    def _create_general_metric(self, **kwargs):
        opts = {
            'name': 'test_metric',
            'is_healthy': True,  # backward compatibility with old tests
        }
        opts.update(kwargs)
        m = Metric(**opts)
        m.full_clean()
        m.save()
        return m

    def _create_object_metric(self, **kwargs):
        opts = kwargs.copy()
        if 'content_object' not in opts:
            opts['content_object'] = self._create_user()
        if 'is_healthy' not in kwargs:
            kwargs['is_healthy'] = True  # backward compatibility with old tests
        return self._create_general_metric(**opts)

    def _create_alert_settings(self, **kwargs):
        alert_s = AlertSettings(**kwargs)
        alert_s.full_clean()
        alert_s.save()
        return alert_s

    def _create_chart(
        self, metric=None, test_data=True, configuration='dummy',
    ):
        m = metric or self._create_object_metric()
        if test_data:
            m.write(3, time=now() - timedelta(days=2))
            m.write(6, time=now() - timedelta(days=1))
            m.write(9, time=now())
        c = Chart(metric=m, configuration=configuration,)
        c.full_clean()
        c.save()
        return c
