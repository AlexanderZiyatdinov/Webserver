import unittest
import tempfile
import shutil

from web import HTTPResponseError


class TestHTTPResponseError(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def test_status_code(self):
        error = HTTPResponseError(404, 'Not found',
                                  b'\r\n<h1>404</h1><p>Not found</p>')
        expected = f"HTTP/1.1 {error.status} {error.message}"
        actual = error.status_code()
        self.assertEqual(expected, actual)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
