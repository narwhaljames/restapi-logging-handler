import logging
import requests
import json
import traceback


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
        logging.Handler.__init__(self)

    def _getTraceback(self, record):
        """
        Format the traceback of the record, if exists.
        """
        if record.exc_info:
            return '\n'.join(traceback.format_exception(*record.exc_info))
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

    def _prepPayload(record):
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
        data, header = self._prepPayload(record)
        try:
            # Stop infinite loop with requests module logging info
            # inside logging module
            requests_level = logging.getLogger('requests').level
            logging.getLogger('requests').setLevel(logging.CRITICAL)
            r = requests.post(
                self._getEndpoint(),
                data=data, headers={'content-type': header})
            logging.getLogger('requests').setLevel(requests_level)
        except:
            self.handleError(record)
