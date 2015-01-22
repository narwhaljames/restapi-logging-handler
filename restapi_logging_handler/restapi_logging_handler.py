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
        logging.Handler.__init__(self)

    def _getTraceback(self, record):
        """
        Format the traceback of the record, if exists.
        """
        if record.exc_info:
            return traceback.format_exc()
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

    def emit(self, record):
        """
        Override emit() method in handler parent for sending log to RESTful API
        """

        # avoid infinite recursion
        if record.name.startswith('requests'):
            return

        data, header = self._prepPayload(record)
        try:
            self.session.post(self._getEndpoint(),
                              data=data,
                              headers={'content-type': header})
        except:
            self.handleError(record)
