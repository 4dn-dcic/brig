import json
import unittest

from .lambda_function import lambda_handler, DEFAULT_DATA, SAMPLE_DATA


class ApiTestCase(unittest.TestCase):

    VERBOSE = False

    def _check_no_error(self, event, *, context=None, expected_code=200, override_data=None):
        self._check_result(event, context, expected_code=expected_code, override_data=override_data)

    def _check_result(self, event, expected_result, *, context=None, expected_code=200, override_data=None):
        res = lambda_handler(event, context=context, override_data=override_data)
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
        self._check_result({"queryStringParameters": {"format": "json"}},
                           SAMPLE_DATA,
                           override_data=SAMPLE_DATA)

    def test_json_for_unexpected_host(self):
        self._check_result({"queryStringParameters": {"environment": "fourfront-cgapdev", "format": "json"}},
                           DEFAULT_DATA,
                           override_data=SAMPLE_DATA)

    # Uncomment this if the corresponding code block in lambda_function.py is also uncommented.
    #
    # LAMBDA_EVENT_FOR_DEBUGGING = {"queryStringParameters": {"echoevent": "true"}}
    #
    # def test_json_for_debugging(self):
    #     self._check_result(self.LAMBDA_EVENT_FOR_DEBUGGING,
    #                        self.LAMBDA_EVENT_FOR_DEBUGGING)
