import unittest
import tempfile
import os
import shutil
from web import Response, Request


class TestResponse(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def test_status_code(self):
        response = Response(200, "OK")
        expected = f"HTTP/1.1 {response.status} {response.message}"
        actual = response.status_code()
        self.assertEqual(expected, actual)

    def test_get_headers(self):
        response = Response(200, "OK", headers={"Content-Length": 0})
        expected = 'Content-Length: 0\r\n'
        actual = response.get_headers()
        self.assertEqual(expected, actual)

    def test_response_file(self):
        request = Request()

        file = os.path.join(self.test_dir, 'test.html')
        with open(file, 'wb') as f:
            f.write(b'012345')

        response = Response.response_file(request, file, 'text/html')
        self.assertEqual(response.status, 200)
        self.assertEqual(response.message, 'OK')
        self.assertEqual(response.headers.get('Content-Length'), 6)
        self.assertEqual(response.body, b'012345')

    def test_response_file_range(self):
        request = Request()
        request.headers['Range'] = 'bytes=0-6'

        file = os.path.join(self.test_dir, 'test.html')
        with open(file, 'wb') as f:
            f.write(b'012345')

        response = Response.response_file(request, file, 'text/html')
        self.assertEqual(response.status, 206)
        self.assertEqual(response.message, 'Partial Content')
        self.assertEqual(response.headers.get('Content-Length'), 6)
        self.assertEqual(response.body, b'012345')

    def test_response_file_range_without_start(self):
        request = Request()
        request.headers['Range'] = 'bytes=-3'

        file = os.path.join(self.test_dir, 'test.html')
        with open(file, 'wb') as f:
            f.write(b'012345')

        response = Response.response_file(request, file, 'text/html')
        self.assertEqual(response.status, 206)
        self.assertEqual(response.message, 'Partial Content')
        self.assertEqual(response.headers.get('Content-Length'), 3)
        self.assertEqual(response.body, b'345')

    def test_response_file_range_withoud_end(self):
        request = Request()
        request.headers['Range'] = 'bytes=2-'

        file = os.path.join(self.test_dir, 'test.html')
        with open(file, 'wb') as f:
            f.write(b'012345')

        response = Response.response_file(request, file, 'text/html')
        self.assertEqual(response.status, 206)
        self.assertEqual(response.message, 'Partial Content')
        self.assertEqual(response.headers.get('Content-Length'), 4)
        self.assertEqual(response.body, b'2345')

    def test_response_dir(self):
        request = Request()

        path = os.path.join(self.test_dir)
        response = Response.response_dir(request, path)
        act_body = b'<!DOCTYPE html><html>\n<head>\n<title>'
        act_body += f'Listing for: {path}'.encode('utf-8')
        act_body += b'</title>\n</head>\n</head>\n<body><h1>'
        act_body += f'Listing for: {path}'.encode('utf-8')
        act_body += b'</h1><hr>\n<ul><li><a  href="/" '
        act_body += b'None>/</a></li>\n</ul>\n</body>\n</html>\n'
        self.assertEqual(response.status, 200)
        self.assertEqual(response.message, 'OK')
        self.assertEqual(response.headers.get('Content-Length'), len(act_body))
        self.assertEqual(response.body, act_body)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
