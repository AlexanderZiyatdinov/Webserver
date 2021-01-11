import os
import socket
import re
import chardet

from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

from router import Router
from request import Request
from response import Response
from errors import Error
from http.server import BaseHTTPRequestHandler, HTTPServer

HTTP_METHODS = ('GET', ' POST')


# TODO обработка keep-alive
# TODO обработка conn
# TODO stop
# TODO обработка keep-alive


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
        """NIY"""
        self._serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._make_regular_routes()

        # print(self._routes)
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
                                      or Error.NOT_FOUND_PAGE)

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
            response = Error.LENGTH_REQUIRED
        return response

    def handle_file(self, filename, root=os.getcwd(), content_type='*/*'):
        path = os.path.join(root, filename)
        if not os.path.exists(path):
            return Error.NOT_FOUND_PAGE
        return Response.response_file(self.request, path, content_type)

    def handle_dir(self, dirname=os.getcwd()):
        path = os.path.abspath(dirname)
        if not os.path.exists(path):
            return Error.NOT_FOUND_PAGE
        return Response.response_dir(self.request, path)

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
                               root=os.path.join(os.getcwd(), 'files',
                                                 'pictures'))


    @app.route('/files/pictures/pugs.png')
    def dog():
        return app.handle_file('pugs.png',
                               root=os.path.join(os.getcwd(), 'files',
                                                 'pictures'))


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
