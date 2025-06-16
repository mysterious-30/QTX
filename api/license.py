from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode())
            license_key = data.get("licenseKey", "").upper().strip()
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        # Load license DB
        try:
            with open("LICENSE_KEYS.json", "r") as f:
                license_db = json.load(f)
        except Exception as e:
            license_db = {
                "DEMO-1234-5678-9012": {
                    "active": True,
                    "features": ["premium"]
                }
            }

        if not license_key:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "License key required"}).encode())
            return

        if license_key in license_db and license_db[license_key].get("active", False):
            response = {
                "valid": True,
                "licenseKey": license_key,
                "features": license_db[license_key].get("features", [])
            }
            self.send_response(200)
        else:
            response = {"error": "Invalid license key"}
            self.send_response(403)

        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
