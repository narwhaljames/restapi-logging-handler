import json
import uuid
import datetime

try:
    from unittest.mock import patch
except ImportError:
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
        except:
            log.exception('this is an error')
        self.session.return_value.post.assert_called_once()

        request_params = self.session.return_value.post.call_args
        traceback_value = json.loads(request_params[1]['data'])['traceback']
        self.assertEqual(traceback_value[:9], 'Traceback')

    def test_logging_meta(self):
        log = logging.getLogger('testing')
        log.addHandler(self.handler)

        log.info('test message')

        self.session.return_value.post.assert_called_once()

        request_params = self.session.return_value.post.call_args
        payload = json.loads(request_params[1]['data'])

        created = payload['meta'].pop('created')
        process = payload['meta'].pop('process')
        thread = payload['meta'].pop('thread')
        line = payload['meta'].pop('line')

        self.assertTrue(isinstance(created, float))
        self.assertTrue(isinstance(process, int))
        self.assertTrue(isinstance(thread, int))
        self.assertTrue(isinstance(line, int))

        self.assertEquals(
            payload,
            {
                'details': {},
                'level': 'INFO',
                'log': 'testing',
                'message': 'test message',
                'meta': {
                    # 'created': 1484758407.541427,
                    'funcName': 'test_logging_meta',
                    # 'line': 41,
                    # 'process': 60304,
                    # 'thread': 140735191764992
                }
            }
        )

    def test_logging_details(self):
        log = logging.getLogger('testing')
        log.addHandler(self.handler)

        log.info('test message', extra={'this': 1, 'that': None})

        self.session.return_value.post.assert_called_once()

        request_params = self.session.return_value.post.call_args
        payload = json.loads(request_params[1]['data'])

        details = payload.pop('details')

        self.assertEquals(
            details,
            {'this': 1, 'that': None}
        )

    def test_logging_uuid(self):
        log = logging.getLogger('testing')
        log.addHandler(self.handler)

        random_id = uuid.uuid4()

        log.info('test message', extra={'this': random_id, 'that': None})

        self.session.return_value.post.assert_called_once()

        request_params = self.session.return_value.post.call_args
        payload = json.loads(request_params[1]['data'])

        details = payload.pop('details')

        self.assertEquals(
            details,
            {'this': str(random_id), 'that': None}
        )

    def test_logging_datetime(self):
        log = logging.getLogger('testing')
        log.addHandler(self.handler)

        random_date = datetime.datetime.utcnow()

        log.info('test message', extra={'this': random_date, 'that': None})

        self.session.return_value.post.assert_called_once()

        request_params = self.session.return_value.post.call_args
        payload = json.loads(request_params[1]['data'])

        details = payload.pop('details')

        self.assertEquals(
            details,
            {'this': random_date.isoformat(sep='T'), 'that': None}
        )

    def test_logging_thing(self):
        log = logging.getLogger('testing')
        log.addHandler(self.handler)

        class Thing(object):
            def __init__(self):
                self.thing1 = 'Fred'
                self.thing2 = 'Jerry'

        random_thing = Thing()

        log.info('test message', extra={'this': random_thing, 'that': None})

        self.session.return_value.post.assert_called_once()

        request_params = self.session.return_value.post.call_args
        payload = json.loads(request_params[1]['data'])

        details = payload.pop('details')

        self.assertEquals(
            details,
            {'this': {'thing1': 'Fred', 'thing2': 'Jerry'},
             'that': None}
        )

    def test_ignored_record_keys(self):

        self.assertEquals(
            self.handler.ignored_record_keys,
            {
                'levelno',
                'pathname',
                'module',
                'filename',
                'funcName',
                'asctime',
                'msecs',
                'processName',
                'relativeCreated',
                'threadName',
                'stack_info',
                'exc_info',
                'exc_text',
                'args',
                'msg'
            }
        )

    def test_detail_keys(self):

        self.assertEquals(
            self.handler.detail_ignore_set,
            {
                'levelno',
                'pathname',
                'module',
                'filename',
                'funcName',
                'asctime',
                'msecs',
                'processName',
                'relativeCreated',
                'threadName',
                'stack_info',
                'exc_info',
                'exc_text',
                'args',
                'msg',
                'created',
                'levelname',
                'process',
                'thread',
                'name',
                'lineno',
            }
        )
