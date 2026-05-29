"""HTTP 桥接：接收识别结果 POST，写入 current_video_path.txt（供 TD 轮询）。"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from _bootstrap import *  # noqa: F403

from paths import OUTPUT_FILE

PORT = 8765


class StateHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        payload = f"{body['label']},{body['x']},{body['y']},{body['asset_path']}"
        OUTPUT_FILE.write_text(payload, encoding="utf-8")
        print(f"[bridge] {payload}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        return


def main() -> None:
    print(f"HTTP bridge: http://127.0.0.1:{PORT}/state")
    HTTPServer(("127.0.0.1", PORT), StateHandler).serve_forever()


if __name__ == "__main__":
    main()
