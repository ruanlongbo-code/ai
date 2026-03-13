"""
本地 HTTP 反向代理：将 HTTP 请求转发到 https://litellm.shoplazza.site
用于解决阿里云服务器无法直接访问海外 AWS 服务的问题。

使用方式：
1. 本地启动代理：python3 scripts/litellm_proxy.py
2. SSH 反向隧道：ssh -R 9801:127.0.0.1:9801 -i <key> ecs-user@120.77.168.5 -N
"""

import http.server
import urllib.request
import ssl
import sys

TARGET = "https://litellm.shoplazza.site"
PORT = 9801


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self._proxy()

    def do_GET(self):
        self._proxy()

    def do_OPTIONS(self):
        self._proxy()

    def _proxy(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        url = f"{TARGET}{self.path}"
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in ("host", "transfer-encoding")}

        req = urllib.request.Request(url, data=body, headers=headers, method=self.command)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=300) as resp:
                status = resp.status
                resp_headers = resp.getheaders()
                resp_body = resp.read()

                self.send_response(status)
                for k, v in resp_headers:
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error": "proxy error: {e}"}}'.encode())

    def log_message(self, format, *args):
        print(f"[PROXY] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = http.server.HTTPServer(("127.0.0.1", port), ProxyHandler)
    print(f"LiteLLM 反向代理启动: http://127.0.0.1:{port} -> {TARGET}")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n代理已停止")
        server.server_close()
