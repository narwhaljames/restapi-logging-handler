from restapi_logging_handler import RestApiHandler


class LogglyHandler(RestApiHandler):
    """
    A handler which pipes all logs to loggly through HTTP POST requests.
    Some ideas borrowed from github.com/kennedyj/loggly-handler
    """
    def __init__(self, custom_token, app_tags):
        """
        customToken: The loggly custom token account ID
        appTags: Loggly tags. Can be a tag string or a list of tag strings
        """
        if isinstance(app_tags, str):
            self.tags = [app_tags]
        else:
            self.tags = app_tags
        self.custom_token = custom_token
        super(LogglyHandler, self).__init__(
            "https://logs-01.loggly.com/inputs/{0}/tag/{1}/"
        )

    def _implodeTags(self):
        return ",".join(self.tags)

    def _getEndpoint(self):
        """
        Override Build Loggly's RESTful API endpoint
        """
        return self.endpoint.format(
            self.custom_token,
            self._implodeTags()
        )

    def _getPayload(self, record):
        """
        The data that will be sent to loggly.
        """
        payload = super(LogglyHandler, self)._getPayload(record)
        payload['tags'] = self._implodeTags()
        return payload
