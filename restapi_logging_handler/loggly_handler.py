from restapi_logging_handler import RestApiHandler


class LogglyHandler(RestApiHandler):
    """
    A handler which pipes all logs to loggly through HTTP POST requests.
    Some ideas borrowed from github.com/kennedyj/loggly-handler
    """
    def __init__(self, customToken, appTags):
        """
        customToken: The loggly custom token account ID
        appTags: Loggly tags. Can be a tag string or a list of tag strings
        """
        if isinstance(appTags, str):
            self.tags = [appTags]
        else:
            self.tags = appTags
        self.customToken = customToken
        super(LogglyHandler, self).__init__(
            self, "https://logs-01.loggly.com/inputs/{0}/tag/{1}/"
        )

    def _implodeTags(self):
        return ",".join(self.tags)

    def _getEndpoint(self):
        """
        Override Build Loggly's RESTful API endpoint
        """
        return self.endpoint.format(
            self.customToken,
            self._implodeTags()
        )

    def _getPayload(self, record):
        """
        The data that will be sent to loggly.
        """
        payload = super(LogglyHandler, self)._getPayload(record)
        payload['tags'] = self._implodeTags()
        return payload
