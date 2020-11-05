import contextlib
import datetime
import json
import unittest

from qa_utils_subset import ControlledTime
from unittest import mock
from . import lambda_function as lambda_function_module
from .lambda_function import (
    lambda_handler, DEFAULT_EVENT, DEFAULT_DATA, get_calendar_data, CALENDAR_DATA_URL, resolve_environment,
    in_date_range, parse_datetime, hms_now, HMS_TZ,
)


# This basically sets up test cases involving 3 events that can be queried in various ways.
# They occur during two time blocks, in one case with two events sharing the same time block:
#
#         START_SAMPLE_BLOCK1        END_SAMPLE_BLOCK1   START_SAMPLE_BLOCK2           END_SAMPLE_BLOCK2
#              |                          |                   |                             |
#              |<---- SAMPLE BLOCK 1 ---->|                   |<------ SAMPLE BLOCK 2 ----->|
#              |                          |                   |                             |
#              | SAMPLE_FF_SYSTEM_UPGRADE |                   | SAMPLE_FF_SUMMER_NOTICE     |
#              | (various fourfront envs) |                   | (fourfront-mastertest only) |
#              |                          |                   |                             |
#              |                          |                   | SAMPLE_CG_SUMMER_NOTICE     |
#              |                          |                   | (fourfront-cgapwolf only)   |
#  ---------+--+------------+-------------+-+---------------+-+-----------------+-----------+-+-------
#           |               |               |               |                   |             |
#   BEFORE_SAMPLE_BLOCK1    |     AFTER_SAMPLE_BLOCK1   BEFORE_SAMPLE_BLOCK2    |      AFTER_SAMPLE_BLOCK2
#                           |                                                   |
#                 DURING_SAMPLE_BLOCK1                                DURING_SAMPLE_BLOCK2
#
# Note also that the start and end times are given as strings in JSON data that parameterizes the site.
# This code needs to test that the parsing is correct, etc., so some of these variables are assigned as
# strings (the START_SAMPLE_BLOCKn and END_SAMPLE_BLOCKn variables) and some as datetime.datetime objects
# to bypass any parsers and make sure we're testing against an objectively correct measure.
#
# Note further that all times are chosen so that timezone is not in play in testing of the overall mechanism.
# Timezone management is tested separately, but the key things to know are:
#  * Times should be specified with timezone resolved. For dates in the November to March range,

BEFORE_SAMPLE_BLOCK1 = datetime.datetime(2020, 1, 30, 6, 0, 0)
START_SAMPLE_BLOCK1 = "2020-02-01 16:00:00-0500"  # EST
DURING_SAMPLE_BLOCK1 = datetime.datetime(2020, 2, 14, 6, 0, 0)
END_SAMPLE_BLOCK1 = "2020-02-28 12:00:00-0500"  # EST
AFTER_SAMPLE_BLOCK1 = datetime.datetime(2020, 3, 3, 6, 0, 0)

BEFORE_SAMPLE_BLOCK2 = datetime.datetime(2020, 5, 30, 6, 0, 0)
START_SAMPLE_BLOCK2 = "2020-06-01 00:00:00-0400"  # EDT
DURING_SAMPLE_BLOCK2 = datetime.datetime(2020, 7, 1, 6, 0, 0)
END_SAMPLE_BLOCK2 = "2020-09-01 00:00:00-0400"  # EDT
AFTER_SAMPLE_BLOCK2 = datetime.datetime(2020, 9, 15, 6, 0, 0)


SAMPLE_FF_SYSTEM_UPGRADE = {
    "name": "Fourfront System Upgrades",
    "start_time": START_SAMPLE_BLOCK1,
    "end_time": END_SAMPLE_BLOCK1,
    "message": ("Systems may be unavailable."),
    "affects": {
        "name": "All Fourfront Systems",
        "environments": [
            "fourfront-hotseat",
            "fourfront-mastertest",
            "fourfront-webdev",
            "fourfront-webprod",
            "fourfront-webprod2",
        ],
    },
}

SAMPLE_FF_SUMMER_NOTICE = {
    "name": "Fourfront Mastertest Summer Shutdown",
    "start_time": START_SAMPLE_BLOCK2,
    "end_time": END_SAMPLE_BLOCK2,
    "message": "We're all at the beach. Happy Summer!",
    "affects": {
        "name": "Fourfront Mastertest Users",
        "environments": [
            "fourfront-mastertest",
        ],
    },
}

SAMPLE_CG_SUMMER_NOTICE = {
    "name": "CGAP Wolf Summer Shutdown",
    "start_time": START_SAMPLE_BLOCK2,
    "end_time": END_SAMPLE_BLOCK2,
    "message": "We're all at the beach. Happy Summer!",
    "affects": {
        "name": "CGAP Wolf Users",
        "environments": [
            "fourfront-cgapwolf",
        ],
    },
}

SAMPLE_EVENTS = [SAMPLE_FF_SYSTEM_UPGRADE, SAMPLE_FF_SUMMER_NOTICE, SAMPLE_CG_SUMMER_NOTICE]

SAMPLE_DATA = {
    "bgcolor": "#ffcccc",
    "events": SAMPLE_EVENTS
}

# Note that the first two of this is https, and the others are http.

CGAP_PRD_SERVER = "https://cgap.hms.harvard.edu"
FF_PRD_SERVER = "https://data.4dnucleome.org/"
FF_STG_SERVER = "https://staging.4dnucleome.org/"
CGAPWOLF_SERVER = "http://fourfront-cgapwolf.9wzadzju3p.us-east-1.elasticbeanstalk.com/"
CGAPTEST_SERVER = "http://fourfront-cgaptest.9wzadzju3p.us-east-1.elasticbeanstalk.com/"
MASTERTEST_SERVER = "http://fourfront-mastertest.9wzadzju3p.us-east-1.elasticbeanstalk.com/"
MASTERTEST2_SERVER = "http://fourfront-mastertest2.9wzadzju3p.us-east-1.elasticbeanstalk.com/"  # for testing
MASTERTEST_2_SERVER = "http://fourfront-mastertest-2.9wzadzju3p.us-east-1.elasticbeanstalk.com/"  # for testing
WEBDEV_SERVER = "http://fourfront-webdev.9wzadzju3p.us-east-1.elasticbeanstalk.com/"

# In an inevitable asymmetry, there must be a default environment if no context is given.
DEFAULT_PRD_ENVIRONMENT = 'fourfront-webprod'
DEFAULT_PRD_SERVER = FF_PRD_SERVER


class ApiTestCaseBase(unittest.TestCase):

    DEBUG = True

    def debug_print(self, *args):
        if self.DEBUG:
            print(*args)

    maxDiff = 5000

    class FakeResponse:

        def __init__(self, *, json):
            self._json = json

        def json(self):
            return self._json


class ApiTestCase(ApiTestCaseBase):

    def _check_no_error(self, event, *, context=None, expected_code=200):
        self._check_result(event, context, expected_code=expected_code)

    def _check_result(self, event, expected_events=None, expected_result=None, *, context=None, expected_code=200):
        done = False
        res = lambda_handler(event, context=context)
        status_code = res['statusCode']
        actual = res['body']
        self.debug_print("status_code=", status_code)
        self.debug_print("actual=", actual)
        self.assertEqual(status_code, expected_code)
        if expected_result is None and expected_events is None:
            return
        try:
            actual = json.loads(actual)
        except Exception as e:
            print("Failed (%s) with body: %s" % (e.__class__.__name__, actual))
            raise
        if expected_result is not None:
            done = True
            self.debug_print("expected_result=", json.dumps(expected_result, indent=2))
            self.assertEqual(actual, expected_result)
        if expected_events is not None:
            done = True
            self.debug_print("expected_events=",json.dumps(expected_events, indent=2))
            self.assertEqual(actual.get('events'), expected_events)
        print("done=", done)

@contextlib.contextmanager
def sample_data():
    with mock.patch.object(lambda_function_module, "get_calendar_data") as mock_get_data:
        mock_get_data.return_value = SAMPLE_DATA
        yield


@contextlib.contextmanager
def datetime_for_testing(dt):
    dt = ControlledTime(dt)
    with mock.patch("datetime.datetime", dt):
        yield dt


HEADER_PARAMS = ('referer',)


def event_with_qs_params(**params):
    headers = {}
    query_params = {}
    for name, value in params.items():
        if value is None:
            continue
        elif name in HEADER_PARAMS:
            headers[name] = value
        else:
            query_params[name] = value
    return {"queryStringParameters": query_params, "headers": headers}


class TestApi(ApiTestCase):

    def test_empty_event(self):
        self._check_no_error({})

    def test_null_query_params(self):
        self._check_no_error({"queryStringParameters": None})

    def test_empty_query_params(self):
        self._check_no_error(event_with_qs_params())

    def test_query_param_environment(self):
        self._check_no_error(event_with_qs_params(environment="fourfront-cgapdev"))

    def test_query_params_environment_and_format(self):
        self._check_no_error(event_with_qs_params(environment="fourfront-cgapdev", format='json'))

    def test_json_for_regular_hosts_various_ff(self):
        application = 'fourfront'
        scenarios = [
            (1, None, BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (2, None, DURING_SAMPLE_BLOCK1, [SAMPLE_FF_SYSTEM_UPGRADE]),
            (3, None, AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (11, 'fourfront-webprod', BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (22, 'fourfront-webprod', DURING_SAMPLE_BLOCK1, [SAMPLE_FF_SYSTEM_UPGRADE]),
            (33, 'fourfront-webprod', AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (111, 'fourfront-mastertest', BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (222, 'fourfront-mastertest', DURING_SAMPLE_BLOCK1, [SAMPLE_FF_SYSTEM_UPGRADE]),
            (333, 'fourfront-mastertest', AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (1111, 'fourfront-cgap', BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (2222, 'fourfront-cgap', DURING_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (3333, 'fourfront-cgap', AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (4, None, BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (5, None, DURING_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (6, None, AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

            (44, 'fourfront-webprod', BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (55, 'fourfront-webprod', DURING_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (66, 'fourfront-webprod', AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

            (444, 'fourfront-mastertest', BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (555, 'fourfront-mastertest', DURING_SAMPLE_BLOCK2, [SAMPLE_FF_SUMMER_NOTICE]),
            (666, 'fourfront-mastertest', AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

            (4444, 'fourfront-cgap', BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (5555, 'fourfront-cgap', DURING_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (6666, 'fourfront-cgap', AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

            (44444, 'fourfront-cgapwolf', BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (55555, 'fourfront-cgapwolf', DURING_SAMPLE_BLOCK2, [SAMPLE_CG_SUMMER_NOTICE]),
            (66666, 'fourfront-cgapwolf', AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

        ]
        for n, environment, base_time, expected_events in scenarios:
            self.debug_print("n=", n)
            with sample_data():
                with datetime_for_testing(base_time):
                    self.debug_print("environment=", environment, "application=", application)
                    self.debug_print("base_time=", base_time)
                    self.debug_print("expected_events=", expected_events)
                    self._check_result(event_with_qs_params(format='json',
                                                            application=application,
                                                            environment=environment),
                                       expected_events=expected_events)

    def test_json_for_regular_hosts_various_cgap(self):
        application = 'cgap'
        scenarios = [
            (1, None, BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (2, None, DURING_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (3, None, AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (11, 'fourfront-cgap', BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (22, 'fourfront-cgap', DURING_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (33, 'fourfront-cgap', AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (111, 'fourfront-cgapwolf', BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (222, 'fourfront-cgapwolf', DURING_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (333, 'fourfront-cgapwolf', AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (1111, 'fourfront-webprod', BEFORE_SAMPLE_BLOCK1, [DEFAULT_EVENT]),
            (2222, 'fourfront-webprod', DURING_SAMPLE_BLOCK1, [SAMPLE_FF_SYSTEM_UPGRADE]),
            (3333, 'fourfront-webprod', AFTER_SAMPLE_BLOCK1, [DEFAULT_EVENT]),

            (4, None, BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (5, None, DURING_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (6, None, AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

            (44, 'fourfront-cgap', BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (55, 'fourfront-cgap', DURING_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (66, 'fourfront-cgap', AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

            (444, 'fourfront-cgapwolf', BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (555, 'fourfront-cgapwolf', DURING_SAMPLE_BLOCK2, [SAMPLE_CG_SUMMER_NOTICE]),
            (666, 'fourfront-cgapwolf', AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),

            (4444, 'fourfront-webprod', BEFORE_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (5555, 'fourfront-webprod', DURING_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
            (6666, 'fourfront-webprod', AFTER_SAMPLE_BLOCK2, [DEFAULT_EVENT]),
        ]
        for n, environment, base_time, expected_events in scenarios:
            self.debug_print("n=", n)
            with sample_data():
                with datetime_for_testing(base_time):
                    self.debug_print("environment=", environment, "application=", application)
                    self.debug_print("base_time=", base_time)
                    self.debug_print("expected_events=", expected_events)
                    self._check_result(event_with_qs_params(format='json',
                                                            application=application,
                                                            environment=environment),
                                       expected_events=expected_events)

    def test_json_based_on_referer(self):
        # These work in pairs...

        # We want this use of environment fourfront-mastertest:
        with datetime_for_testing(DURING_SAMPLE_BLOCK2):
            with sample_data():
                print(1)
                self._check_result(event_with_qs_params(format='json', environment='fourfront-mastertest'),
                                   expected_events=[SAMPLE_FF_SUMMER_NOTICE])
        # to be the same as this use a the fourfront-mastertest server as a referer:
        with datetime_for_testing(DURING_SAMPLE_BLOCK2):
            with sample_data():
                print(2)
                self._check_result(event_with_qs_params(format='json', referer=MASTERTEST_SERVER),
                                   expected_events=[SAMPLE_FF_SUMMER_NOTICE])

        # We want this use of environment fourfront-cgapwolf
        with datetime_for_testing(DURING_SAMPLE_BLOCK2):
            with sample_data():
                print(3)
                self._check_result(event_with_qs_params(format='json', environment='fourfront-cgapwolf'),
                                   expected_events=[SAMPLE_CG_SUMMER_NOTICE])
        # to be the same as this use a the fourfront-cgapwolf server as a referer:
        with datetime_for_testing(DURING_SAMPLE_BLOCK2):
            with sample_data():
                print(4)
                self._check_result(event_with_qs_params(format='json', referer=CGAPWOLF_SERVER),
                                   expected_events=[SAMPLE_CG_SUMMER_NOTICE])

    # Uncomment this if the corresponding code block in lambda_function.py is also uncommented.
    #
    # LAMBDA_EVENT_FOR_DEBUGGING = {"queryStringParameters": {"echoevent": "true"}}
    #
    # def test_json_for_debugging(self):
    #     self._check_result(self.LAMBDA_EVENT_FOR_DEBUGGING,
    #                        self.LAMBDA_EVENT_FOR_DEBUGGING)


class TestInternals(ApiTestCaseBase):

    def test_get_calendar_data(self):

        with mock.patch("requests.get") as mock_get:

            some_calendar = {"some": "calendar"}
            empty_calendar = {}
            no_calendar = None

            def mocked_get(url):
                self.assertEqual(url, CALENDAR_DATA_URL)
                if mocked_calendar == 'error':
                    raise RuntimeError("Some sort of error happened.")
                return self.FakeResponse(json=mocked_calendar)

            mock_get.side_effect = mocked_get

            mocked_calendar = some_calendar
            self.assertEqual(get_calendar_data(), some_calendar)

            mocked_calendar = empty_calendar
            self.assertEqual(get_calendar_data(), DEFAULT_DATA)

            mocked_calendar = no_calendar
            self.assertEqual(get_calendar_data(), DEFAULT_DATA)

            mocked_calendar = 'error'
            self.assertEqual(get_calendar_data(), DEFAULT_DATA)

    def test_in_date_range(self):

        EST = "-0500"
        EDT = "-0400"

        EDT_ALT = "-04:00"

        CST = "-0600"
        CDT = "-0500"

        with datetime_for_testing(datetime.datetime(2016, 7, 4, 0, 0, 0)):

            now = hms_now()  # This will be converted to HMS time.
            # print("now=", now)
            assert in_date_range(now,
                                 "2016-07-03 23:59:00" + EDT,
                                 "2016-07-04 00:01:00" + EDT)

            assert in_date_range(now,
                                 "2016-07-03 23:59:00" + EDT_ALT,
                                 "2016-07-04 00:01:00" + EDT_ALT)

            assert not in_date_range(now,
                                     "2016-08-03 23:59:00" + EDT,
                                     "2016-08-04 00:01:00" + EDT)

            assert not in_date_range(now,
                                     "2016-06-03 23:59:00" + EDT,
                                     "2016-06-04 00:01:00" + EDT)

            # If no timezone, US/Eastern (for HMS) is assumed.
            # Dates between Sune and August are all in Daylight Time.

            assert in_date_range(now,
                                 "2016-06-03 23:59:00",
                                 "2016-08-04 00:01:00")

            assert in_date_range(now,
                                 "2016-07-03 23:59:00",
                                 "2016-07-04 00:01:00")

            assert not in_date_range(now,
                                     "2016-08-03 23:59:00",
                                     "2016-08-04 00:01:00")

            assert not in_date_range(now,
                                     "2016-06-03 23:59:00",
                                     "2016-06-04 00:01:00")

            assert in_date_range(now,
                                 "2016-06-03 23:59:00",
                                 "2016-08-04 00:01:00")

            # It would be weird to provide anything other than the HMS timezone, but it happens to work to do that.
            assert not in_date_range(now,
                                     "2016-06-03 22:59:00" + CDT,
                                     "2016-06-03 23:01:00" + CDT)

        # This just makes sure that EDT/EST is accommodated by the hms_now() function,
        # though it will be separately tested, too.
        with datetime_for_testing(datetime.datetime(2016, 1, 4, 0, 0, 0)):

            now = hms_now()
            # print("now=", now)
            assert in_date_range(now,
                                 "2016-01-03 23:59:00" + EST,
                                 "2016-01-04 00:01:00" + EST)

            # If no timezone, US/Eastern (for HMS) is assumed.
            # Dates between December and February are all in Standard Time.
            assert in_date_range(now,
                                 "2016-01-03 23:59:00",
                                 "2016-01-04 00:01:00")

            # It would be weird to provide anything other than the HMS timezone, but it happens to work to do that.
            assert not in_date_range(now,
                                     "2016-06-03 22:59:00" + CST,
                                     "2016-06-03 23:01:00" + CST)

    def test_hms_now(self):

        with datetime_for_testing(datetime.datetime(2016, 1, 4, 0, 0, 0)):

            assert str(hms_now()) == "2016-01-04 00:00:01-05:00"

    def test_parse_datetime(self):

        EST = "-0500"
        EDT = "-0400"

        time1 = HMS_TZ.localize(datetime.datetime(2016, 6, 3, 22, 59))
        time_str1 = "2016-06-03 22:59:00"
        assert parse_datetime(time_str1 + EDT) == time1
        assert parse_datetime(time_str1) == time1

        time2 = HMS_TZ.localize(datetime.datetime(2016, 1, 3, 22, 59))
        time_str2 = "2016-01-03 22:59:00"
        assert parse_datetime(time_str2 + EST) == time2
        assert parse_datetime(time_str2) == time2

    def test_resolve_environment(self):

        def test(*, expected, referer=None, application=None, environment=None):
            self.assertEqual(resolve_environment(referer=referer, application=application, environment=environment),
                             expected)

        self.debug_print("Testing for no context.")

        test(expected=DEFAULT_PRD_ENVIRONMENT)

        # The environment is simply returned, and take precedence over other elements like referer and application.

        self.debug_print("Testing for environment (including precedence over referer and application).")

        test(environment='fourfront-mastertest', expected='fourfront-mastertest')
        test(environment='fourfront-cgapwolf', expected='fourfront-cgapwolf')

        test(referer=FF_PRD_SERVER, environment='fourfront-mastertest', expected='fourfront-mastertest')
        test(referer=CGAP_PRD_SERVER, environment='fourfront-cgapwolf', expected='fourfront-cgapwolf')

        test(application='fourfront', environment='fourfront-mastertest', expected='fourfront-mastertest')
        test(application='cgap', environment='fourfront-cgapwolf', expected='fourfront-cgapwolf')

        # The referer does not dominate environment, but still takes precedence over application.

        for application in ('cgap', 'fourfront', None):

            self.debug_print("Testing referers with application=", application)

            test(application=application, referer=MASTERTEST_SERVER, expected='fourfront-mastertest')
            test(application=application, referer=MASTERTEST2_SERVER, expected='fourfront-mastertest')
            test(application=application, referer=MASTERTEST_2_SERVER, expected='fourfront-mastertest')
            test(application=application, referer=WEBDEV_SERVER, expected='fourfront-webdev')
            test(application=application, referer=FF_PRD_SERVER, expected='fourfront-webprod')
            test(application=application, referer=FF_STG_SERVER, expected='fourfront-webprod')
            test(application=application, referer=CGAPWOLF_SERVER, expected='fourfront-cgapwolf')
            test(application=application, referer=CGAPTEST_SERVER, expected='fourfront-cgaptest')
            test(application=application, referer=CGAP_PRD_SERVER, expected='fourfront-cgap')

        # The application can be specified and will take effect if there is no environment or referer.
        self.debug_print("Testing application.", application)

        test(application='cgap', expected='fourfront-cgap')
        test(application='fourfront', expected='fourfront-webprod')
        test(application='something', expected='fourfront-webprod')  # anything not cgap is assumed fourfront
