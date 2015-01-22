import json
from mock import patch
from unittest import TestCase
import logging

from restapi_logging_handler import RestApiHandler


class TestRestApiHandler(TestCase):

    @classmethod
    @patch('restapi_logging_handler.restapi_logging_handler.FuturesSession')
    def setUpClass(cls, session):
        cls.session = session
        cls.handler = RestApiHandler('endpoint/url')

    def test_get_endpoint(self):
        assert self.handler._getEndpoint() == 'endpoint/url'

    def test_logging_exception_with_traceback(self):
        log = logging.getLogger('traceback')
        log.addHandler(self.handler)
        try:
            raise Exception
        except Exception as e:
            log.exception('this is an error')
        self.session.return_value.post.assert_called_once()

        request_params = self.session.return_value.post.call_args
        traceback_value = json.loads(request_params[1]['data'])['traceback']
        self.assertEqual(traceback_value[:9], 'Traceback')
