import os
from collections import OrderedDict
from errors import HTTPResponseError


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
        filename_css = os.path.join(os.getcwd(), 'static', 'css', 'bootstrap.min.css')
        filename_js = os.path.join(os.getcwd(), 'static', 'js', 'bootstrap.min.js')
        dirs = []
        files = []
        start_dir = os.getcwd()
        title_tag = f"<head>\n<title>Listing for: {path}</title>\n</head>\n"
        doctype = "<!DOCTYPE html><html>\n"
        result = ''
        result += "<!DOCTYPE html>\n"
        result += '<html lang="en">\n'
        result += '<meta charset="UTF-8">\n'
        result += f"<head>\n<title>Listing for: {path}</title>\n"

        result += '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-giJF6kkoqNQ00vy+HMDP7azOuL0xtbfIcaT9wjKHr8RbDVddVHyTfAAsrekwKmP1" crossorigin="anonymous">'
       # result += f'<link rel="stylesheet" type="text/css" href="{filename}">\n'
        result += '</head>\n'
        result += f"<body><h1>Listing for: {path}</h1><hr>\n<ul>"

        result += """<div class="container">
  			<div class="row">
        <table class="table">
  <thead>
    <tr>
      <th scope="col">#</th>
      <th scope="col">First</th>
      <th scope="col">Last</th>
      <th scope="col">Handle</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">1</th>
      <td>{123}</td>
      <td>Otto</td>
      <td>@mdo</td>
    </tr>
    
    <tr>
      <th scope="row">2</th>
      <td>Jacob</td>
      <td>Thornton</td>
      <td>@fat</td>
    </tr>
    
    <tr>
      <th scope="row">3</th>
      <td>Larry the Bird</td>
      <td></td>
      <td>@twitter</td>
    </tr>
    
    
    
    
  </tbody>
</table>
</div>
</div>"""

        body_tag = f"</head>\n<body><h1>Listing for: {path}</h1><hr>\n<ul>"
        page_content = doctype + title_tag + body_tag
        button = "<li><a  href=\"{name}\" {download}>{name}</a>Size:</li>\n"

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

        result += "</ul>\n</body>\n</html>\n"
        page_content += "</ul>\n</body>\n</html>\n"

        body = page_content.encode('utf-8')
        result = result.encode('utf-8')
        headers = {('Content-Type', 'text/html'),
                   ('Content-Length', len(body)),
                   ('Connection', connection)}
        headers = OrderedDict(headers)
        for (header, header_value) in additional_headers or []:
            headers[header] = header_value
        return Response(200, "OK", headers, result)

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