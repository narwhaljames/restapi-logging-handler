from __future__ import absolute_import
import atexit
import json
import threading

from restapi_logging_handler.restapi_logging_handler import RestApiHandler


class LogglyHandler(RestApiHandler):
    """
    A handler which pipes all logs to loggly through HTTP POST requests.
    Some ideas borrowed from github.com/kennedyj/loggly-handler
    """
    def __init__(self, custom_token, app_tags, interval=1.0):
        """
        customToken: The loggly custom token account ID
        appTags: Loggly tags. Can be a tag string or a list of tag strings
        """
        self.tags = self._getTags(app_tags)
        self.custom_token = custom_token
        super(LogglyHandler, self).__init__(self._getEndpoint())
        self.interval = interval
        self.timer = None
        self.logs = []
        self._startFlushTimer()
        atexit.register(self._stopFlushTimer)

    def _startFlushTimer(self):
        self.timer = threading.Timer(self.interval, self._flushAndRepeatTimer)
        self.timer.start()

    def _flushAndRepeatTimer(self):
        self.flush()
        if self.timer.finished.is_set():
            self._startFlushTimer()

    def _stopFlushTimer(self):
        self.timer.cancel()
        self.flush()

    def _getTags(self, app_tags):
        if isinstance(app_tags, str):
            tags = app_tags.split(',')
        else:
            tags = app_tags
        tags.insert(0, 'bulk')
        return tags

    def _implodeTags(self):
        return ",".join(self.tags)

    def _getEndpoint(self):
        """
        Override Build Loggly's RESTful API endpoint
        """
        return 'https://logs-01.loggly.com/bulk/{0}/tag/{1}/'.format(
            self.custom_token,
            self._implodeTags()
        )

    def _prepPayload(self, record):
        """
        record: generated from logger module
        This preps the payload to be formatted in whatever content-type is
        expected from the RESTful API.
        """
        return json.dumps(self._getPayload(record))

    def _getPayload(self, record):
        """
        The data that will be sent to loggly.
        """
        payload = super(LogglyHandler, self)._getPayload(record)
        payload['tags'] = self._implodeTags()
        return payload

    @staticmethod
    def handle_response(sess, resp):
        pass

    def flush(self):
        self.logs, current_batch = [], self.logs
        if current_batch:
            data = '\n'.join(current_batch)
            self.session.post(self._getEndpoint(),
                              data=data,
                              headers={'content-type': 'application/json'},
                              background_callback=self.handle_response)

    def emit(self, record):
        """
        Override emit() method in handler parent for sending log to RESTful API
        """

        # avoid infinite recursion
        if record.name.startswith('requests'):
            return

        self.logs.append(self._prepPayload(record))
