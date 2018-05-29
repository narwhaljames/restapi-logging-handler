import datetime
import uuid
import logging
import json
import traceback

from requests_futures.sessions import FuturesSession

"""
logrecord attributes
    %(name)s            Name of the logger (logging channel)
    %(levelno)s         Numeric logging level for the message (DEBUG, INFO,
                        WARNING, ERROR, CRITICAL)
    %(levelname)s       Text logging level for the message ("DEBUG", "INFO",
                        "WARNING", "ERROR", "CRITICAL")
    %(pathname)s        Full pathname of the source file where the logging
                        call was issued (if available)
    %(filename)s        Filename portion of pathname
    %(module)s          Module (name portion of filename)
    %(lineno)d          Source line number where the logging call was issued
                        (if available)
    %(funcName)s        Function name
    %(created)f         Time when the LogRecord was created (time.time()
                        return value)
    %(asctime)s         Textual time when the LogRecord was created
    %(msecs)d           Millisecond portion of the creation time
    %(relativeCreated)d Time in milliseconds when the LogRecord was created,
                        relative to the time the logging module was loaded
                        (typically at application startup time)
    %(thread)d          Thread ID (if available)
    %(threadName)s      Thread name (if available)
    %(process)d         Process ID (if available)
    %(message)s         The result of record.getMessage(), computed just as
                        the record is emitted

    snooping
    (Pdb) pprint.pprint([k for k in record.__dict__.keys()])
    ['stack_info',
     'created',
     'threadName',
     'exc_info',
     'process',
     'filename',
     'lineno',
     'pathname',
     'levelno',
     'relativeCreated',
     'levelname',
     'module',
     'msg',
     'msecs',
     'extra',
     'processName',
     'exc_text',
     'name',
     'args',
     'funcName',
     'thread'
     'process',
     'thread'


"""

DEFAULT_IGNORED_KEYS = {
    'process',
    'thread',
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
META_KEYS = {
    'created',
    'funcName',
    'lineno',
}

TOP_KEYS = {
    'levelname',
    'name',
}


def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat(sep='T')
        return serial

    if isinstance(obj, uuid.UUID):
        serial = str(obj)
        return serial

    try:
        return obj.__dict__
    except AttributeError:
        return str(obj)
    except Exception as e:
        strval = 'unknown obj'
        exceptval = 'unknown err'
        try:
            strval = str(obj)
            exceptval = repr(e)
        except Exception:
            pass
        return 'json fail {} {}'.format(exceptval, strval)


# test
def simple_json(obj):
    try:
        return json.dumps(obj, default=serialize)
    except Exception:
        return "cannot serialize {}".format(type(obj))


class RestApiHandler(logging.Handler):
    """
    A handler which does an HTTP POST for each logging event.
    """

    def __init__(self, endpoint, content_type='json',
                 ignored_record_keys=None):
        """
        endpoint: define the fully qualified RESTful API endpoint to POST to.
        content_type: only supports JSON currently
        """
        self.endpoint = endpoint
        self.content_type = content_type
        self.session = FuturesSession(max_workers=32)
        self.ignored_record_keys = (ignored_record_keys if ignored_record_keys
                                    else DEFAULT_IGNORED_KEYS)
        foo = TOP_KEYS.union(META_KEYS)
        self.detail_ignore_set = self.ignored_record_keys.union(foo)

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

        try:
            # top level payload items
            d = record.__dict__
            pid = d.pop('process', 'nopid')
            tid = d.pop('thread', 'notid')

            payload = {
                k: v for (k, v) in d.items()
                if k in TOP_KEYS
            }

            # logging meta attributes
            payload['meta'] = {
                k: v for (k, v) in d.items()
                if k in META_KEYS
            }

            # everything else goes in details
            payload['details'] = {
                k: simple_json(v) for (k, v) in d.items()
                if k not in self.detail_ignore_set
            }

            payload['log'] = payload.pop('name', 'n/a')
            payload['level'] = payload.pop('levelname', 'n/a')
            payload['meta']['line'] = payload['meta'].pop('lineno', 'n/a')

            payload['message'] = record.getMessage()
            tb = self._getTraceback(record)
            if tb:
                payload['traceback'] = tb

        except Exception as e:
            payload = {
                'level': 'ERROR',
                'message': 'could not format',
                'exception': repr(e),
            }
        payload['pid'] = 'p-{}'.format(pid)
        payload['tid'] = 't-{}'.format(tid)
        return payload

    def _prepPayload(self, record):
        """
        record: generated from logger module
        This preps the payload to be formatted in whatever content-type is
        expected from the RESTful API.

        returns: a tuple of the data and the http content-type
        """
        payload = self._getPayload(record)
        json_data = json.dumps(payload, default=serialize)

        return {
            'json': (json_data, 'application/json')
        }.get(self.content_type, (json_data, 'text/plain'))

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
        except Exception:
            self.handleError(record)
