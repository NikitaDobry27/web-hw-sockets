import json
import socket
import threading
import pathlib
import urllib.parse
import mimetypes
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "storage", "data.json")


if not os.path.exists(os.path.dirname(DATA_FILE)):
    os.makedirs(os.path.dirname(DATA_FILE))
    with open(DATA_FILE, "w") as file:
        file.write("{}")


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self._render_html("index.html")
        elif url.path == "/message":
            self._render_html("message.html")
        else:
            if pathlib.Path().joinpath(url.path[1:]).exists():
                self.send_static()
            else:
                self._render_html("error.html", 404)

    def do_POST(self):
        data_dict = self._parse_data()
        message = json.dumps(data_dict).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message, ("localhost", 5000))
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()
        self.wfile.write(b"OK")

    def _parse_data(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value for key, value in [param.split("=") for param in data.split("&")]
        }
        return data_dict

    def _render_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        try:
            file_path = os.path.join(BASE_DIR, filename)
            absolute_path = os.path.abspath(file_path)
            with open(absolute_path, "rb") as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            self._render_html("error.html", 404)
        except BrokenPipeError:
            print("Client disconnected before the response was fully sent.")

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-Type", mt[0])
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        try:
            file_path = os.path.join(BASE_DIR, self.path[1:])
            absolute_path = os.path.abspath(file_path)
            with open(absolute_path, "rb") as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            self._render_html("error.html", 404)
        except BrokenPipeError:
            print("Client disconnected before the response was fully sent.")


def write_to_json(data):
    with open(DATA_FILE, "r") as file:
        current_data = json.load(file)

    timestamp = datetime.now().isoformat()
    current_data[timestamp] = data

    with open(DATA_FILE, "w") as file:
        json.dump(current_data, file, indent=1)


def socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("localhost", 5000))

        while True:
            data, addr = sock.recvfrom(1024)
            data_dict = json.loads(data.decode())
            write_to_json(data_dict)


def run(server_class=HTTPServer, handler_class=HTTPHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    http_thread = threading.Thread(target=http.serve_forever)
    socket_thread = threading.Thread(target=socket_server)

    try:
        http_thread.start()
        socket_thread.start()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
