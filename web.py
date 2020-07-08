import os
import socket
import threading
import re
import chardet
import concurrent.futures
from collections import OrderedDict
from urllib.parse import urlparse

HTTP_METHODS = ('GET', ' POST')


class Webserver:
    def __init__(self, host="localhost", port=8080, hostname='hostname',
                 workers=os.cpu_count() - 1):
        self.host = host
        self.port = port
        self.hostname = hostname
        self.max_workers = workers
        self.routes = {}
        self.regular_routes = {}
        self._request = Request()
        self._response = None

    def set_routes(self, routes):
        self.routes = {**routes, **self.routes}

    def get_routes(self):
        return self.routes

    def handle_file(self, filename, root=os.getcwd(), content_type='*/*'):
        print(os.getcwd())
        print(filename)
        path = os.path.join(root, filename)
        print("PATH " + path)
        if not os.path.exists(path):
            return Errors.NOT_FOUND_PAGE
        response = Response.response_file(self._request, path, content_type)

        return response

    def get(self, body, headers=None, params=None):
        body = ("\r\n" + body).encode('utf-8')
        print("body=", body)
        response = Response(200, "OK", headers, body=body)
        return response

    def post(self, body, headers=None, params=None):
        body = body.encode('utf-8')
        print("body=", body)
        headers = {('Content-Length', len(body))}
        headers = OrderedDict(headers)
        response = Response(200, "OK", headers=headers, body=body)
        if not headers['Content-Length'] or headers['Content-Length'] == 0:
            response = Errors.LENGTH_REQUIRED

        return response
        pass

    def handle_dir(self, dirname=os.getcwd()):

        path = os.path.abspath(dirname)
        print('handle_dir: ' + path)
        if not os.path.exists(path):
            return Errors.NOT_FOUND_PAGE
        response = Response.response_dir(self._request, path)

        return response

    def find_handler(self):
        for reg, handler in self.regular_routes.items():
            match = re.fullmatch(reg, self._request.url)
            print(match, 'reg: ', reg, 'url: ', self._request.url)
            print('handler: ', handler)
            if match:
                print(match.groupdict())
                if len(match.groupdict().items()) == 0:
                    self._response = handler()
                else:
                    # TODO match.groupdict[groupname from decorator
                    self._response = handler(match.group(1))
                break

    def handle(self, client, address):
        with client:
            data_end = b'\r\n\r\n'

            while True:
                data = client.recv(1024)
                if data:
                    self._request = Request(data)
                    self._request.parse_request()
                    self._request.print_headers()

                    if self._request.headers.get('Connection') == 'keep-alive':
                        client.setsockopt(socket.SOL_SOCKET,
                                          socket.SO_KEEPALIVE, 1)

                    self._response = Errors.NOT_FOUND_PAGE
                    self.find_handler()

                    print(type(self._response))
                    Response.response(client, self._response)

                if data_end in data:
                    print(f'Disconnected: {address}')
                    break

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.make_regular_routes()

        with server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(socket.SOMAXCONN)
            print(f'Start server on {self.host}:{self.port}')

            while True:
                client, address = server_socket.accept()
                print(f'Got client: {address}')

                th = (threading.
                      Thread(target=lambda: self.handle(client, address)))
                th.daemon = True
                th.start()

    def route(self, path, method='GET'):
        if path in self.routes:
            raise AssertionError("Such route already exists.")

        def wrapper(handler):
            self.set_routes({path: handler})
            return handler

        return wrapper

    def make_regular_routes(self):
        for route in self.routes:
            reg = re.compile(route)
            self.regular_routes[reg] = self.routes[route]


class Request:
    def __init__(self, data=None):
        self.data = data
        self.method = None
        self.version = None
        self.target = None
        self.url = None
        self.body = None
        self.headers = {}

    def parse_request(self):
        data = str(self.data, chardet.detect(self.data)["encoding"])
        lines = data.split('\r\n')
        line = lines[0]
        self.method, self.target, self.version = line.split()
        self.url = urlparse(self.target).path
        for line in lines[1:-2]:
            header, header_value = line.split(": ")
            self.headers[header] = header_value

    def print_headers(self):
        print(self.method, self.target, self.version, sep=' ')
        for header in self.headers:
            print(header + ':', self.headers[header], sep=' ')


class Response:

    def __init__(self, status, message, headers=None, body=None):
        self.status = status
        self.message = message
        self.headers = OrderedDict(headers or {})
        self.body = body

    def status_code(self):
        return f'HTTP/1.1 {self.status} {self.message}'

    def get_headers(self):
        return "".join(f'{h}: {hv}\r\n' for (h, hv) in self.headers.items())

    @staticmethod
    def response_dir(request, path, **additional_headers):
        connection = request.headers.get('Connection')
        dirs = []
        files = []
        start_dir = os.getcwd()

        doctype = "<!DOCTYPE html><html>\n"
        title_tag = f"<head>\n<title>Listing for: {path}</title>\n</head>\n"
        body_tag = f"</head>\n<body><h1>Listing for: {path}</h1><hr>\n<ul>"
        page_content = doctype + title_tag + body_tag
        button = "<li><a  href=\"{name}\" {download}>{name}</a></li>\n"

        if path != start_dir:
            page_content += button.format(name='/', download=None)

        for name in os.listdir(path):
            join_path = os.path.join(path, name)
            print("IN DIR ", path)
            print(os.path.isdir(join_path))
            bname = name
            if os.path.basename(path) != os.path.basename(os.getcwd()):
                bname = os.path.join(os.path.basename(path), name)

            if os.path.isfile(join_path):
                page_content += button.format(name=bname, download='download')
                files.append(name)
            else:
                page_content += button.format(name=bname, download=None)
                dirs.append(name.upper() + "/")

        dirs.sort()
        dirs.extend(files)

        page_content += "</ul>\n</body>\n</html>\n"

        body = page_content.encode('utf-8')
        headers = {('Content-Type', 'text/html'),
                   ('Content-Length', len(body)),
                   ('Connection', connection)}
        headers = OrderedDict(headers)
        for (header, header_value) in additional_headers or []:
            headers[header] = header_value
        return Response(200, "OK", headers, body)

    @staticmethod
    def response_file(request, path, content_type, **additional_headers):
        start, end, size = None, None, None
        header_range = request.headers.get("Range")
        print("PATH in rESPO ", path)
        with open(path, 'rb') as file:
            if header_range:
                _, value = header_range.split('=')
                start, end = value.split('-', maxsplit=1)
                if not end:
                    end = os.path.getsize(path)
                if not start:
                    start = int(end)
                    end = os.path.getsize(path)
                    start = end - start
                start, end = int(start), int(end)
                file.seek(start, 0)
                body = file.read(end - start)
            else:
                body = file.read()
            filename = os.path.basename(path)
            print("FILE " + path)
            print(filename)
            connection = request.headers.get('Connection')
            size = os.stat(path).st_size
            headers = {('Content-Type', f'{content_type}'),
                       ('Content-Length', len(body)),
                       ('Connection', connection)}
            if header_range:
                headers.add(('Content-Range', f'{start}-{end}/{size}'))
            headers = OrderedDict(headers)

            for (header, header_value) in additional_headers or []:
                headers[header] = header_value
            if header_range:
                return Response(206, "Partial Content", headers, body)
            return Response(200, "OK", headers, body)

    @staticmethod
    def response(client, response):
        content = response.status_code().encode('utf-8')
        if type(response) is not HTTPResponseError:
            content += (response.get_headers().encode("utf-8"))
        content += b'\r\n' + response.body or b''

        while content:
            content_sent = client.send(content)
            content = content[content_sent:]


class HTTPResponseError(Exception):
    def __init__(self, status, message, body=None):
        self.status = status
        self.message = message
        self.body = body

    def status_code(self):
        return f'HTTP/1.1 {self.status} {self.message}'


class Errors(HTTPResponseError):
    NOT_FOUND_PAGE = HTTPResponseError(404, 'Not found',
                                       b'\r\n<h1>404</h1><p>Not found</p>')
    LENGTH_REQUIRED = HTTPResponseError(411, 'Length required',
                                        b'\r\n<h1>411</h1><p>Len required</p>')


if __name__ == "__main__":
    app = Webserver()


    @app.route('/')
    def start():
        return app.handle_dir(os.getcwd())


    @app.route('/files')
    def files():
        return app.handle_dir('D:\PyProjects\web\web\\files')


    @app.route('/files/documents')
    def documents():
        return app.handle_dir('D:\PyProjects\web\web\\files\documents')


    @app.route('/files/documents/pdffile.pdf')
    def pdf():
        return app.handle_file('pdffile.pdf',
                               'D:\PyProjects\web\web\\files\documents')


    @app.route('/files/documents/wordfile.docx')
    def word():
        return app.handle_file('wordfile.docx',
                               'D:\PyProjects\web\web\\files\documents')


    @app.route('/files/media')
    def media():
        return app.handle_dir('D:\PyProjects\web\web\\files\media')


    @app.route('/files/media/music.mp3')
    def music():
        return app.handle_file('music.mp3',
                               'D:\PyProjects\web\web\\files\media')


    @app.route('/files/pages')
    def pages():
        return app.handle_dir('D:\PyProjects\web\web\\files\pages')


    @app.route('/files/pages/index.html')
    def index():
        return app.handle_file('index.html',
                               'D:\PyProjects\web\web\\files\pages')


    @app.route('/files/pictures')
    def pictures():
        return app.handle_dir('D:\PyProjects\web\web\\files\pictures')


    @app.route('/files/pictures/dog.jpg')
    def dog():
        return app.handle_file('dog.jpg',
                               root='D:\PyProjects\web\web\\files\pictures')


    @app.route('/files/pictures/pugs.png')
    def dog():
        return app.handle_file('pugs.png',
                               root='D:\PyProjects\web\web\\files\pictures')


    @app.route('/page/(?P<name>.*)')
    def page(name):
        return app.get(f'Hello, {name}')


    @app.route('/hello/(?P<name>.*)')
    def func(name):
        return app.get(f'Hello, {name}')


    app.run()
