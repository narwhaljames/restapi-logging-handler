import logging
import json
import traceback

from requests_futures.sessions import FuturesSession


class RestApiHandler(logging.Handler):
    """
    A handler which does an HTTP POST for each logging event.
    """
    def __init__(self, endpoint, content_type='json'):
        """
        endpoint: define the fully qualified RESTful API endpoint to POST to.
        content_type: only supports JSON currently
        """
        self.endpoint = endpoint
        self.content_type = content_type
        self.session = FuturesSession(max_workers=32)
        self.requests_level = logging.getLogger('requests').level
        self.record_count = 0
        logging.Handler.__init__(self)

    def _getTraceback(self, record):
        """
        Format the traceback of the record, if exists.
        """
        if record.exc_info:
            return '\n'.join(traceback.format_exception(*record.exc_info()))
        return None

    def _getEndpoint(self):
        """
        Build RESTful API endpoint.
        Can override in child classes to add parameters.
        """
        return self.endpoint

    def _getPayload(self, record):
        """
        The data that will be sent to the RESTful API
        """
        payload = {
            'log': record.name,
            'level': logging.getLevelName(record.levelno),
            'message': record.getMessage()
        }
        tb = self._getTraceback(record)
        if tb:
            payload['traceback'] = tb
        return payload

    def _prepPayload(self, record):
        """
        record: generated from logger module
        This preps the payload to be formatted in whatever content-type is
        expected from the RESTful API.

        returns: a tuple of the data and the http content-type
        """
        payload = self._getPayload(record)
        return {
            'json': (json.dumps(payload), 'application/json')
        }.get(self.content_type, (json.dumps(payload), 'text/plain'))

    def restore_request_logging_if_done(self, sess, resp):
        self.record_count = self.record_count - 1
        if self.record_count == 0:
            logging.getLogger('requests').setLevel(self.requests_level)

    def emit(self, record):
        """
        Override emit() method in handler parent for sending log to RESTful API
        """
        data, header = self._prepPayload(record)
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        self.record_count = self.record_count + 1
        try:
            # Stop infinite loop with grequests module logging info
            # inside logging module
            self.session.post(
                self._getEndpoint(),
                data=data, headers={'content-type': header},
                background_callback=self.restore_request_logging_if_done
            )
        except:
            self.restore_request_logging_if_done()
            self.handleError(record)
