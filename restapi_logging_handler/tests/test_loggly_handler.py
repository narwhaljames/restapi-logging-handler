import sys

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
        cls.handler = LogglyHandler('LOGGLYKEY', cls.tags, max_attempts=5)
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
        logging.warning(repr(request_params[1]['data']))

        # check each line, as bulk requests send multiple json blocks
        for line in request_params[1]['data'].split('\n'):
            # print("line | ", line, "|")
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
    post_count = 0
    print_count = 0

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
    @patch('restapi_logging_handler.loggly_handler.print')
    def execute(cls, print):
        for index, result in enumerate(cls.results):
            cls.handler.handle_response(
                Mock(), result, batch=[{}], attempt=index + 1)
        cls.print_calls = [
            c for c in print.call_args_list
        ]


class TestNoFailure(_BaseWebRequestFailure):
    def test_web_posting(self):
        self.assert_post_count_is(self.post_count)
        self.assertEqual(self.print_count,
                         len(self.print_calls))


class TestSingleFailure(TestNoFailure):
    results = [
        Mock(status_code=502),
        Mock(status_code=200),
    ]
    post_count = 1


class TestMaxFailures(TestNoFailure):
    results = [
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
    ]
    post_count = 5


class TestMoreThanMaxFailures(TestNoFailure):
    results = [
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
        Mock(status_code=502),
    ]
    post_count = 5
    print_count = 1

    def test_print(self):
        self.assertEqual(sys.stderr,
                         self.print_calls[0][1]['file'])


@patch('restapi_logging_handler.loggly_handler.requests.get')
class TestAwsTagging(TestCase):
    def test_tag_true(self, mock_get):
        mock_get.return_value.content = 'id_test'.encode('utf-8')

        loggly = LogglyHandler('token', ['tag'], max_attempts=1, aws_tag=True)

        self.assertEqual(loggly.tags, ['bulk', 'tag', 'id_test'])

    def test_tag_false(self, mock_get):
        mock_get.return_value.content = 'id_test'.encode('utf-8')

        loggly = LogglyHandler('token', ['tag'], max_attempts=1,
                               aws_tag=False)

        self.assertEqual(loggly.tags, ['bulk', 'tag'])
