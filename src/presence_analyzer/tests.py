# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presenceweekday')

    def test_presenceweekday(self):
        """
        Test presence weekday page.
        """
        resp = self.client.get('/chart/presenceweekday')
        self.assertEqual(resp.status_code, 200)

    def test_meantime(self):
        """
        Test meantime page.
        """
        resp = self.client.get('/chart/meantime')
        self.assertEqual(resp.status_code, 200)

    def test_presencestartend(self):
        """
        Test presence start end page.
        """
        resp = self.client.get('/chart/presencestartend')
        self.assertEqual(resp.status_code, 200)

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        details = utils.get_details()
        self.assertEqual(len(data), len(details))
        self.assertDictEqual(data[0], {
            'user_id': 10,
            'name': 'Adam P.',
            'avatar': '/api/images/users/10'
            })

    def test_api_mean_time_weekday(self):
        """
        Test mean time weeklday listing.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/1')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 0)
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertIn('Mon', data[0])
        self.assertIn('Sun', data[-1])

    def test_api_presence_weekday(self):
        """
        Test presence weekday listing.
        """
        resp = self.client.get('/api/v1/presence_weekday/1')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 0)
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertIn('Mon', data[1])
        self.assertIn('Sun', data[-1])

    def test_api_presence_start_end(self):
        """
        Test presence start end listing.
        """
        resp = self.client.get('/api/v1/presence_start_end/1')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 0)
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertIn('Mon', data[0])
        self.assertIn('Sun', data[-1])


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_date]['start'],
                         datetime.time(9, 39, 5))

    def test_get_details(self):
        details = utils.get_details()
        self.assertIsInstance(details, dict)
        self.assertIsInstance(details[10], dict)
        self.assertItemsEqual(details.keys(), [10, 11, 12])
        self.assertItemsEqual(details[10].keys(), ['name', 'avatar'])
        self.assertEqual(details[11]['name'], 'Adrian K.')
        self.assertEqual(details[11]['avatar'], '/api/images/users/11')

    def test_group_by_weekday(self):
        """
        Test weekly grouped.
        """
        data = utils.get_data()
        sample_gbw = utils.group_by_weekday(data[10])
        expected_gbw = {
            0: [],
            1: [30047],
            2: [24465],
            3: [23705],
            4: [],
            5: [],
            6: [],
        }
        self.assertDictEqual(sample_gbw, expected_gbw)

    def test_group_by_weekday_with_points(self):
        """
        Test weekly grouped with points.
        """
        data = utils.get_data()
        sample_gbwp = utils.group_by_weekday_with_points(data[10])
        expected_gbwp = {
            0: [[], []],
            1: [[34745], [64792]],
            2: [[33592], [58057]],
            3: [[38926], [62631]],
            4: [[], []],
            5: [[], []],
            6: [[], []],
        }
        self.assertDictEqual(sample_gbwp, expected_gbwp)

    def test_seconds_since_midnight(self):
        """
        Test calculating seconds since midnight.
        """
        sample_time = datetime.time(0, 0, 0)
        sample_ssm = utils.seconds_since_midnight(sample_time)
        self.assertEqual(sample_ssm, 0)
        self.assertIsInstance(sample_ssm, int)
        sample_time = datetime.time(15, 9, 50)
        sample_ssm = utils.seconds_since_midnight(sample_time)
        self.assertEqual(sample_ssm, 54590)
        self.assertIsInstance(sample_ssm, int)

    def test_interval(self):
        """
        Test interval of time from two points.
        """
        sample_start = datetime.time(5, 0, 0)
        sample_end = datetime.time(15, 0, 0)
        sample_interval = utils.interval(sample_start, sample_end)
        self.assertEqual(sample_interval, 36000)
        self.assertIsInstance(sample_interval, int)
        sample_start = datetime.time(2, 15, 50)
        sample_end = datetime.time(22, 0, 0)
        sample_interval = utils.interval(sample_start, sample_end)
        self.assertEqual(sample_interval, 71050)
        self.assertIsInstance(sample_interval, int)

    def test_mean(self):
        """
        Test mean of list elements.
        """
        sample_mean = utils.mean([])
        self.assertEqual(sample_mean, 0)
        sample_mean = utils.mean([6, 3, 0])
        self.assertEqual(sample_mean, 3.0)
        self.assertIsInstance(sample_mean, float)
        sample_mean = utils.mean([5432.1, 1234.42, 876.23])
        self.assertEqual(sample_mean, 2514.25)
        self.assertIsInstance(sample_mean, float)
        sample_mean = utils.mean([5432.1, 1234.42, 876.23])
        self.assertNotEqual(sample_mean, 7542.75)


def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
