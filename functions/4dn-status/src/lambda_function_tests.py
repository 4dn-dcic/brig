import json
import unittest

from unittest import mock
from . import lambda_function as lambda_function_module
from .lambda_function import lambda_handler, DEFAULT_DATA, SAMPLE_DATA, get_calendar_data, CALENDAR_DATA_URL


class ApiTestCase(unittest.TestCase):

    VERBOSE = False

    def _check_no_error(self, event, *, context=None, expected_code=200):
        self._check_result(event, context, expected_code=expected_code)

    def _check_result(self, event, expected_result, *, context=None, expected_code=200):
        res = lambda_handler(event, context=context)
        status_code = res['statusCode']
        actual = res['body']
        if self.VERBOSE:
            print("status_code=", status_code)
            print("actual=", actual)
        self.assertEqual(status_code, expected_code)
        # assert status_code == expected_code
        if expected_result is None:
            return
        if self.VERBOSE:
            print("expected=", expected_result)
        # assert json.loads(actual) == expected_result
        try:
            self.assertEqual(json.loads(actual), expected_result)
        except Exception as e:
            print("Failed (%s) with body: %s" % (e.__class__.__name__, actual))
            raise


class TestApi(ApiTestCase):

    def test_empty_event(self):
        self._check_no_error({})

    def test_null_query_params(self):
        self._check_no_error({"queryStringParameters": None})

    def test_empty_query_params(self):
        self._check_no_error({"queryStringParameters": {}})

    def test_query_param_environment(self):
        self._check_no_error({"queryStringParameters": {"environment": "fourfront-cgapdev"}})

    def test_query_params_environment_and_format(self):
        self._check_no_error({"queryStringParameters": {"environment": "fourfront-cgapdev", "format": "json"}})

    def test_json_for_regular_hosts(self):
        with mock.patch.object(lambda_function_module, "get_calendar_data") as mock_get_data:
            mock_get_data.return_value = SAMPLE_DATA
            self._check_result({"queryStringParameters": {"format": "json"}}, SAMPLE_DATA)

    def test_json_for_unexpected_host(self):
        with mock.patch.object(lambda_function_module, "get_calendar_data") as mock_get_data:
            mock_get_data.return_value = SAMPLE_DATA
            self._check_result({"queryStringParameters": {"environment": "fourfront-cgapdev", "format": "json"}},
                               DEFAULT_DATA)

    # Uncomment this if the corresponding code block in lambda_function.py is also uncommented.
    #
    # LAMBDA_EVENT_FOR_DEBUGGING = {"queryStringParameters": {"echoevent": "true"}}
    #
    # def test_json_for_debugging(self):
    #     self._check_result(self.LAMBDA_EVENT_FOR_DEBUGGING,
    #                        self.LAMBDA_EVENT_FOR_DEBUGGING)

class TestInternals(unittest.TestCase):

    class FakeResponse:

        def __init__(self, *, json):
            self._json = json

        def json(self):
            return self._json

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
