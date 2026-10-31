"""Loopback HTML transport over one already loaded advice Session."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from .webview import page


MAX_FORM_BYTES = 4096
STATIC_TYPES = {"/web.css": "text/css; charset=utf-8",
                "/web.js": "text/javascript; charset=utf-8"}


def create_server(session, port=0):
    """Bind only loopback; every request uses the same dataset and choices."""
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            # Request URLs and form values do not belong in runtime logs.
            pass

        def version_string(self):
            return "llm-ratings"

        def respond(self, status, body, content_type="text/plain; charset=utf-8"):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; "
                             "script-src 'self'; style-src 'self'; connect-src 'self'; "
                             "img-src 'self' data:; base-uri 'none'; "
                             "form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def send_error(self, code, message=None, explain=None):
            self.respond(code, "Request not accepted.\n")

        def local_host(self):
            hosts = self.headers.get_all("Host", [])
            return hosts == [f"127.0.0.1:{self.server.server_port}"]

        def same_origin(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            origins = self.headers.get_all("Origin", [])
            if origins and origins != [origin]:
                return False
            sites = self.headers.get_all("Sec-Fetch-Site", [])
            if sites and sites not in (["same-origin"], ["none"]):
                return False
            referers = self.headers.get_all("Referer", [])
            if len(referers) > 1:
                return False
            if referers:
                try:
                    ref = urlsplit(referers[0])
                except ValueError:
                    return False
                if f"{ref.scheme}://{ref.netloc}" != origin:
                    return False
            return True

        def do_GET(self):
            if not self.local_host():
                self.send_error(403)
            elif self.requestline.split()[1] != self.path:
                self.send_error(404)
            elif self.path == "/":
                self.respond(200, page(session, session.query()), "text/html; charset=utf-8")
            elif self.path in STATIC_TYPES:
                try:
                    body = (Path(__file__).parent / self.path[1:]).read_bytes()
                except OSError:
                    self.send_error(404)
                    return
                self.respond(200, body, STATIC_TYPES[self.path])
            else:
                self.send_error(404)

        def do_POST(self):
            if not self.local_host() or not self.same_origin():
                self.send_error(403)
                return
            if self.path != "/" or self.requestline.split()[1] != "/":
                self.send_error(404)
                return
            lengths = self.headers.get_all("Content-Length", [])
            if not lengths:
                self.send_error(411)
                return
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
                self.send_error(400)
                return
            if len(lengths[0]) > 10:
                self.send_error(413)
                return
            length = int(lengths[0])
            if length > MAX_FORM_BYTES:
                self.send_error(413)
                return
            if (self.headers.get_all("Transfer-Encoding")
                    or self.headers.get_all("Content-Encoding")
                    or len(self.headers.get_all("Content-Type", [])) != 1
                    or self.headers.get_content_type() != "application/x-www-form-urlencoded"
                    or self.headers.get_content_charset("utf-8") != "utf-8"):
                self.send_error(415)
                return
            try:
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError("incomplete form")
                pairs = parse_qsl(body.decode("utf-8"), keep_blank_values=True,
                                  strict_parsing=True, errors="strict", max_num_fields=2)
                values = dict(pairs)
                if len(pairs) != 2 or set(values) != {"action", "value"}:
                    raise ValueError("invalid form")
                action, value = values["action"], values["value"]
                if action == "role":
                    result = session.set_role(value)
                elif action == "objective":
                    result = session.set_objective(value or None)
                elif action == "capability":
                    if value not in ("", "4", "5"):
                        raise ValueError("invalid capability")
                    result = session.set_min_grade(int(value) if value else None)
                elif action == "provider":
                    result = session.set_provider(value or None)
                elif action == "view":
                    result = session.set_view(value)
                elif action == "recover":
                    result = session.recover(value)
                elif action == "details":
                    result = session.request_details(value)
                elif action == "close_details":
                    if value:
                        raise ValueError("invalid close request")
                    result = session.close_details()
                else:
                    raise ValueError("invalid action")
            except (ValueError, OSError):
                self.send_error(400)
                return
            self.respond(200, page(session, result), "text/html; charset=utf-8")

    # ponytail: one local session, serial requests; no concurrent state mutation.
    return HTTPServer(("127.0.0.1", port), Handler)


def serve(session):
    """Print the bound URL, then serve until Ctrl-C closes the listener."""
    with create_server(session) as server:
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
