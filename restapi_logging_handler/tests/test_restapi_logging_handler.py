from unittest import TestCase
from restapi_logging_handler import RestApiHandler


class TestRestApiHandler(TestCase):
    def test_get_endpoint(self):
        handler = RestApiHandler('endpoint/url')
        assert handler._getEndpoint() == 'endpoint/url'
