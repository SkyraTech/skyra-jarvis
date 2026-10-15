"""Host-owned transport and real HTTP acceptance for the first website/service template."""
import json

WEB_TEMPLATE = 'python-web-service-v1'
SERVER = '''from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from app import handle

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 <= size <= 65536:
                raise ValueError("Request too large")
            value = {"method": self.command, "path": self.path,
                     "body": self.rfile.read(size).decode("utf-8")}
            result = handle(value)
            status, content_type, body = result["status"], result["content_type"], result["body"]
            if type(status) is not int or not 200 <= status <= 599 or not isinstance(body, str):
                raise ValueError("Invalid response")
            if not isinstance(content_type, str) or len(content_type) > 120 or any(ord(c) < 32 for c in content_type):
                raise ValueError("Invalid content type")
            data = body.encode("utf-8")
        except Exception:
            status, content_type, data = 500, "text/plain; charset=utf-8", b"Request failed"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    do_GET = respond
    do_POST = respond

def serve(port=8000):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server

if __name__ == "__main__":
    with serve() as server:
        server.serve_forever()
'''


def web_files(contract, name):
    for case in contract['cases']:
        value, output = case['input'], case['output']
        if (not isinstance(value, dict) or set(value) != {'method', 'path', 'body'}
                or value['method'] not in {'GET', 'POST'} or not isinstance(value['path'], str)
                or not value['path'].startswith('/') or len(value['path']) > 500
                or any(ord(c) < 33 or ord(c) > 126 for c in value['path'])
                or not isinstance(value['body'], str) or len(value['body']) > 4000
                or not isinstance(output, dict) or set(output) != {'status', 'content_type', 'body'}
                or type(output['status']) is not int or not 200 <= output['status'] <= 599
                or not isinstance(output['content_type'], str) or not output['content_type']
                or len(output['content_type']) > 120 or any(ord(c) < 32 for c in output['content_type'])
                or not isinstance(output['body'], str) or len(output['body']) > 8000):
            raise ValueError('Web cases require method/path/body input and status/content_type/body output')
    if not any(200 <= case['output']['status'] < 300 for case in contract['cases']):
        raise ValueError('Include at least one successful HTTP acceptance case')
    test = ('import http.client, json, sys, threading, unittest\nfrom pathlib import Path\n'
            'sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\nfrom server import serve\n'
            f'CASES = json.loads({json.dumps(contract, sort_keys=True)!r})["cases"]\n'
            'class HttpAcceptanceTests(unittest.TestCase):\n'
            '    def test_http_contract(self):\n'
            '        server = serve(0)\n'
            '        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()\n'
            '        try:\n'
            '            for case in CASES:\n'
            '                with self.subTest(example=case["name"]):\n'
            '                    value = case["input"]; expected = case["output"]\n'
            '                    client = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)\n'
            '                    try:\n'
            '                        client.request(value["method"], value["path"], body=value["body"].encode("utf-8"))\n'
            '                        response = client.getresponse()\n'
            '                        self.assertEqual(expected["status"], response.status)\n'
            '                        self.assertEqual(expected["content_type"], response.getheader("Content-Type"))\n'
            '                        self.assertEqual(expected["body"], response.read().decode("utf-8"))\n'
            '                        if value["method"] == "GET" and value["path"] == "/" and expected["content_type"].startswith("text/html"):\n'
            '                            self.assertEqual(expected["body"], (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8"))\n'
            '                    finally: client.close()\n'
            '        finally:\n'
            '            server.shutdown(); server.server_close(); thread.join(timeout=5)\n')
    return {'server.py': SERVER, 'tests/test_acceptance.py': test,
            'index.html': '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' + name + '</title></head><body><main><h1>Implementation pending</h1></main></body></html>\n'}
