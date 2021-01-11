import chardet
from urllib.parse import urlparse

class Request:
    """NYI"""

    def __init__(self, data=None):
        self.data = data
        self.method = None
        self.version = None
        self.target = None
        self.url = None
        self.body = None
        self._headers = {}

    def parse_request(self):
        data = str(self.data, chardet.detect(self.data)["encoding"])
        lines = data.split('\r\n')
        line = lines[0]
        self.method, self.target, self.version = line.split()
        self.url = urlparse(self.target).path

        if self.url.endswith('/') and self.url != '/':
            self.url = self.url[:-1]

        for line in lines[1:-2]:
            header, header_value = line.split(": ")
            self._headers[header] = header_value

    def get_headers(self):
        return self._headers

    def print_headers(self):
        print(self.method, self.target, self.version, sep=' ')
        for header in self._headers:
            print(header + ':', self._headers[header], sep=' ')