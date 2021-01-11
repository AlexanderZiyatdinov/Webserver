class HTTPResponseError(Exception):
    """NYI"""

    def __init__(self, status, message, body=None):
        self.status = status
        self.message = message
        self.body = body

    def status_code(self):
        return f'HTTP/1.1 {self.status} {self.message}'


class Error(HTTPResponseError):
    """NYI"""
    NOT_FOUND_PAGE = HTTPResponseError(404, 'Not found',
                                       b'\r\n<h1>404</h1><p>Not found</p>')
    LENGTH_REQUIRED = HTTPResponseError(411, 'Length required',
                                        b'\r\n<h1>411</h1><p>Len required</p>')