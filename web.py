import os
import socket
import re
import chardet

from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer

HTTP_METHODS = ('GET', ' POST')


# TODO обработка keep-alive
# TODO обработка conn
# TODO stop
# TODO обработка keep-alive
class Router:
    def __init__(self):
        self._routes = {}

    def __str__(self):
        return "".join(f'{r}: {f}\r\n' for (r, f) in self._routes.items())

    def add_route(self, path):
        if path in self._routes:
            raise AssertionError("Such route already exists.")

        def wrapper(handler):
            self._routes = {**{path: handler}, **self._routes}
            return handler

        return wrapper

    def get_routes(self):
        return self._routes


class Webserver:
    """The main class of this library. It is a web server.

    Allows you to import a simple web server into the project for organizing
    data storage, writing HTTP requests, and so on.

    Attributes
    ----------
    host - Takes on the host value
    port - Takes on the port value
    hostname - Symbolic name assigned to the network device
    max_workers - Max number of active connections
    routes - A dictionary that includes all routes set by the user
    regular_routes - A dictionary that includes all routes with regular
                     expressions set by the user
    request - Current request object
    response - Current response object
    pool - The worker thread pool of size "max_workers"
    serv_socket - Socket of this server
    server_address - Host and port pair

    Methods
    ----------
    route - Decorator for functions of the user. Compiles the routes dictionary
    make_regular_routes - Merges routes and regular_routes
    run - Starts the web server. Starts processing new connections
    handle_request - Main handler for new client connections
    find_custom_function - Searches for user functions in regular_routes.
                   Assigns the self.response value to the object
    set_routes - Allows you to change the dictionary "self.routes"
    get_routes - Allows you to get the dictionary "self.routes"
    get - Executes an HTTP GET request
    post - Executes an HTTP POST request
    handle_file - Returns a file from a folder on the web server
    handle_dir - Represents the selected directory as a list of directories.
                 Allows you to download files"""

    def __init__(self, host="localhost",
                 port=8080,
                 hostname='hostname',
                 workers=os.cpu_count() - 1):
        self._host: str = host
        self._port: int = port
        self._hostname: str = hostname
        self._max_workers: int = workers
        self._routes: Router = Router()
        self._request: Request = Request()
        self._response: Response = Response()
        self._pool: list = []
        self._serv_socket = None
        self._server_address = self._host, self._port

    def route(self, path):
        return self._routes.add_route(path)

    def run(self):
        """NYI"""
        self._serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._make_regular_routes()

        print(self._routes)
        # print(self.regular_routes)

        with self._serv_socket:
            self._serv_socket.bind(self._server_address)
            self._serv_socket.listen(self._max_workers)
            print(f'Start server on {self._host}:{self._port}')

            while True:
                client, addr = self._serv_socket.accept()
                print(f'Got client: {addr}')

                # TODO
                with ThreadPoolExecutor(max_workers=self._max_workers) as ex:
                    if len(self._pool) < self._max_workers:
                        self._pool.append(ex.submit(self._handle_request,
                                                    client, addr))
                    for fut in self._pool:
                        if fut.done():
                            self._pool.remove(fut)

    def _handle_request(self, client: socket.socket, address):
        """Main handler"""
        with client:
            data_end = b'\r\n\r\n'
            while True:
                data = client.recv(1024)
                if data:
                    self.request = Request(data)
                    self.request.parse_request()
                    request_headers = self.request.get_headers()

                    if request_headers.get('Connection') == 'keep-alive':
                        client.setsockopt(socket.SOL_SOCKET,
                                          socket.SO_KEEPALIVE, 1)

                    self._response = (self._find_custom_function()
                                      or Errors.NOT_FOUND_PAGE)

                    self._response.response(client)
                    print(self._response)

                if data_end in data:
                    print(f'Disconnected: {address}')
                    break

    def _find_custom_function(self):
        routes: dict = self._routes.get_routes()
        for reg, custom_function in routes.items():
            match = re.fullmatch(reg, self.request.url)
            if match:
                return custom_function() if len(
                    match.groupdict().items()) == 0 else custom_function(
                    match.group(1))

    def get(self, body, headers=None, params=None):
        body = ("\r\n" + body).encode('utf-8')
        return Response(200, "OK", headers, body=body)

    def post(self, body, headers=None, params=None):
        body = body.encode('utf-8')
        headers = {('Content-Length', len(body))}
        headers = OrderedDict(headers)
        response = Response(200, "OK", headers=headers, body=body)
        if not headers['Content-Length'] or headers['Content-Length'] == 0:
            response = Errors.LENGTH_REQUIRED
        return response

    def handle_file(self, filename, root=os.getcwd(), content_type='*/*'):
        path = os.path.join(root, filename)
        if not os.path.exists(path):
            return Errors.NOT_FOUND_PAGE
        return Response.response_file(self.request, path, content_type)

    def handle_dir(self, dirname=os.getcwd()):
        path = os.path.abspath(dirname)
        if not os.path.exists(path):
            return Errors.NOT_FOUND_PAGE
        return Response.response_dir(self.request, path)


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


class Response:
    """NYI"""

    def __init__(self, status=None, message=None, headers=None, body=None):
        self.status = status
        self.message = message
        self.headers = OrderedDict(headers or {})
        self.body = body

    def __str__(self):
        return self._get_headers()

    def status_code(self):
        return f'HTTP/1.1 {self.status} {self.message}'

    def _get_headers(self):
        return "".join(f'{h}: {hv}\r\n' for (h, hv) in self.headers.items())

    @staticmethod
    def response_dir(request, path, **additional_headers):
        request_headers = request.get_headers()
        connection = request_headers.get('Connection')
        dirs = []
        files = []
        start_dir = os.getcwd()

        doctype = "<!DOCTYPE html><html>\n"
        title_tag = f"<head>\n<title>Listing for: {path}</title>\n</head>\n"
        body_tag = f"</head>\n<body><h1>Listing for: {path}</h1><hr>\n<ul>"
        page_content = doctype + title_tag + body_tag
        button = "<li><a  href=\"{name}\" {download}>{name}</a></li>\n"

        if path != start_dir:
            prev_dirs = request.url.replace('\\', '/').split('/')
            prev_path = '/'
            for directory in prev_dirs[:-1]:
                prev_path = os.path.join(prev_path, directory)

            prev_path = prev_path.replace('\\', '/')

            page_content += button.format(name=prev_path, download=None)

        for name in os.listdir(path):
            join_path = os.path.join(path, name)
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
        request_headers = request.get_headers()
        header_range = request_headers.get("Range")
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
            connection = request_headers.get('Connection')
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

    def response(self, client):
        content = self.status_code().encode('utf-8')
        if type(self) is not HTTPResponseError:
            content += (self._get_headers().encode("utf-8"))
        content += b'\r\n' + self.body or b''

        while content:
            content_sent = client.send(content)
            content = content[content_sent:]


class HTTPResponseError(Exception):
    """NYI"""

    def __init__(self, status, message, body=None):
        self.status = status
        self.message = message
        self.body = body

    def status_code(self):
        return f'HTTP/1.1 {self.status} {self.message}'


class Errors(HTTPResponseError):
    """NYI"""
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
        return app.handle_dir(os.path.join(os.getcwd(), 'files'))


    @app.route('/files/documents')
    def documents():
        return app.handle_dir(os.path.join(os.getcwd(), 'files', 'documents'))


    @app.route('/files/documents/pdffile.pdf')
    def pdf():
        return app.handle_file('pdffile.pdf',
                               os.path.join(os.getcwd(), 'files', 'documents'))


    @app.route('/files/documents/wordfile.docx')
    def word():
        return app.handle_file('wordfile.docx',
                               os.path.join(os.getcwd(), 'files', 'documents'))


    @app.route('/files/media')
    def media():
        return app.handle_dir(os.path.join(os.getcwd(), 'files', 'media'))


    @app.route('/files/media/music.mp3')
    def music():
        return app.handle_file('music.mp3',
                               os.path.join(os.getcwd(), 'files', 'media'))


    @app.route('/files/pages')
    def pages():
        return app.handle_dir(os.path.join(os.getcwd(), 'files', 'pages'))


    @app.route('/files/pages/index.html')
    def index():
        return app.handle_file('index.html',
                               os.path.join(os.getcwd(), 'files', 'pages'))


    @app.route('/files/pictures')
    def pictures():
        return app.handle_dir(os.path.join(os.getcwd(), 'files', 'pictures'))


    @app.route('/files/pictures/dog.jpg')
    def dog():
        return app.handle_file('dog.jpg',
                               root=os.path.join(os.getcwd(), 'files', 'pictures'))


    @app.route('/files/pictures/pugs.png')
    def dog():
        return app.handle_file('pugs.png',
                               root=os.path.join(os.getcwd(), 'files', 'pictures'))


    @app.route('/page/(?P<name>.*)')
    def page(name):
        return app.get(f'Hello, {name}')


    @app.route('/hello/(?P<name>.*)')
    def func(name):
        return app.get(f'Hello, {name}')


    @app.route('/bigtext.txt')
    def txt():
        return app.handle_file('big_text.txt',
                               root=os.path.join(os.getcwd()))


    app.run()
