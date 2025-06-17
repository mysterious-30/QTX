from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data)
            license_key = body.get("license_key")

            with open("licenses.json", "r") as f:
                valid_keys = json.load(f)

            if license_key in valid_keys["keys"]:
                response = {"status": "valid", "message": "License key is valid"}
            else:
                response = {"status": "invalid", "message": "Invalid license key"}

        except Exception as e:
            response = {"status": "error", "message": str(e)}

        self.wfile.write(json.dumps(response).encode())
