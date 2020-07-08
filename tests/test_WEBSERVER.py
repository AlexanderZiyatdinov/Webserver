import unittest
import os
import tempfile
import shutil
from web import Webserver, Errors


class TestWebsever(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def test_handle_file(self):
        file = os.path.join(self.test_dir, 'test.html')
        with open(file, 'wb') as f:
            f.write(b'012345')

        app = Webserver()
        result = app.handle_file(file, self.test_dir)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.message, "OK")
        self.assertEqual(result.headers.get('Content-Length'), 6)
        self.assertEqual(result.body, b'012345')

    def test_handle_file_not_found(self):
        app = Webserver()
        result = app.handle_file(os.path.join(self.test_dir, 'not.found'))
        self.assertEqual(result.status, Errors.NOT_FOUND_PAGE.status)
        self.assertEqual(result.message, Errors.NOT_FOUND_PAGE.message)
        self.assertEqual(result.body, Errors.NOT_FOUND_PAGE.body)

    def test_handle_dir(self):
        path = os.path.join(self.test_dir)

        app = Webserver()
        result = app.handle_dir(path)
        act_body = b'<!DOCTYPE html><html>\n<head>\n<title>'
        act_body += f'Listing for: {path}'.encode('utf-8')
        act_body += b'</title>\n</head>\n</head>\n<body><h1>'
        act_body += f'Listing for: {path}'.encode('utf-8')
        act_body += b'</h1><hr>\n<ul><li><a  href="/" '
        act_body += b'None>/</a></li>\n</ul>\n</body>\n</html>\n'
        self.assertEqual(result.status, 200)
        self.assertEqual(result.message, "OK")
        self.assertEqual(result.headers.get('Content-Length'), len(act_body))
        self.assertEqual(result.body, act_body)

    def test_handle_dir_not_found(self):
        app = Webserver()
        result = app.handle_dir(os.path.join(self.test_dir, '/notfound'))
        self.assertEqual(result.status, Errors.NOT_FOUND_PAGE.status)
        self.assertEqual(result.message, Errors.NOT_FOUND_PAGE.message)
        self.assertEqual(result.body, Errors.NOT_FOUND_PAGE.body)

    def test_get(self):
        body = 'body'
        app = Webserver()
        result = app.get(body)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.message, "OK")
        self.assertEqual(result.headers, {})
        self.assertEqual(result.body, b'\r\nbody')

    def test_post(self):
        body = 'body'
        app = Webserver()
        result = app.post(body)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.message, "OK")
        self.assertEqual(result.headers, {'Content-Length': 4})
        self.assertEqual(result.body, b'body')

    def test_post_without_content_length(self):
        body = ''
        app = Webserver()
        result = app.post(body)
        self.assertEqual(result.status, Errors.LENGTH_REQUIRED.status)
        self.assertEqual(result.message, Errors.LENGTH_REQUIRED.message)
        self.assertEqual(result.body, Errors.LENGTH_REQUIRED.body)

    def tearDown(self):
        shutil.rmtree(self.test_dir)


if __name__ == "__main__":
    unittest.main()
