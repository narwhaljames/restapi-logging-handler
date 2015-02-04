from mock import patch, Mock
from unittest import TestCase
import json
import logging
import time

from restapi_logging_handler import LogglyHandler


class _BaseLogglyHandler(TestCase):
    tags = ['tag1', 'tag2']

    @classmethod
    @patch('restapi_logging_handler.restapi_logging_handler.FuturesSession')
    def setUpClass(cls, session):
        cls.session = session
        cls.configure()
        cls.execute()

    @classmethod
    def configure(cls):
        cls.handler = LogglyHandler('LOGGLYKEY', cls.tags, 0.01)
        logging.root.addHandler(cls.handler)

    @classmethod
    def execute(cls):
        pass

    @classmethod
    def log_now(cls, message):
        logging.warning(message)
        cls.flush()

    @classmethod
    def flush(cls):
        cls.handler.flush()

    def assert_post_count_is(self, count):
       self.assertEqual(self.session.return_value.post.call_count, count)


class _BaseLogglyLoggingHandler(_BaseLogglyHandler):

    def test_tags_are_correct(self):
        request_params = self.session.return_value.post.call_args
        logging.warn(repr(request_params[1]['data']))

        # check each line, as bulk requests send multiple json blocks
        for line in request_params[1]['data'].split('\n'):
            tags = json.loads(line)['tags']
            self.assertEqual('bulk,tag1,tag2', tags)


class TestLogglyHandlerTimerStops(_BaseLogglyLoggingHandler):
    @classmethod
    def execute(cls):
        cls.log_now('something')
        cls.handler._stopFlushTimer()

        # this message should not get sent
        logging.warning('something')
        time.sleep(0.2)

    def test_stops_calling_flush(self):
        self.assert_post_count_is(1)

    def test_marks_timer_finished(self):
        self.assertTrue(self.handler.timer.is_set())


class TestLogglyHandlerRepeats(_BaseLogglyLoggingHandler):
    @classmethod
    def execute(cls):
        cls.log_now('something')
        cls.log_now('something')

    def test_stops_calling_flush(self):
        self.assert_post_count_is(2)

    def test_timer_not_finished(self):
        self.assertFalse(self.handler.timer.is_set())


class TestLogglyHandlerSendsMultipleMessages(_BaseLogglyLoggingHandler):
    @classmethod
    def execute(cls):
        for i in range(10):
            logging.warning('something')
        cls.handler.flush()

    def test_stops_calling_flush(self):
        self.assert_post_count_is(1)

    def test_timer_not_finished(self):
        self.assertFalse(self.handler.timer.is_set())


class TestAcceptsTextTags(_BaseLogglyLoggingHandler):
    @classmethod
    def configure(cls):
        cls.tags = 'tag1,tag2'
        super(TestAcceptsTextTags, cls).configure()

    @classmethod
    def execute(cls):
        cls.log_now('something')


class _BaseWebRequestFailure(_BaseLogglyHandler):
    results = [Mock(status_code=200)]

    @classmethod
    @patch('restapi_logging_handler.restapi_logging_handler.FuturesSession')
    def setUpClass(cls, session):
        cls.session = session
        cls.configure()
        cls.execute()

    @classmethod
    def configure(cls):
        super(_BaseWebRequestFailure, cls).configure()

    @classmethod
    def execute(cls):
        for index, result in enumerate(cls.results):
            # Expect an exception if attempt > max_attempts
            if index + 1 > cls.handler.max_attempts:
                try:
                    cls.handler.handle_response(['{}'], index + 1, Mock(),
                                                result)
                except Exception:
                    pass
                else:
                    cls.assertTrue(False)
            else:
                cls.handler.handle_response(['{}'], index + 1, Mock(), result)


class TestNoFailure(_BaseWebRequestFailure):
    def test_should_succeed(self):
        self.assert_post_count_is(0)


class TestSingleFailure(_BaseWebRequestFailure):
    results = [
        Mock(status_code=502),
        Mock(status_code=200),
    ]

    def test_post_twice(self):
        self.assert_post_count_is(1)


class TestMaxFailures(_BaseWebRequestFailure):
    results = [
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
    ]

    def test_post_twice(self):
        self.assert_post_count_is(5)


class TestMoreThanMaxFailures(_BaseWebRequestFailure):
    results = [
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
    ]

    def test_post_twice(self):
        self.assert_post_count_is(5)
