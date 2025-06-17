import logging
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        """Set common headers for all responses"""
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
        self.send_header('Content-Type', 'application/json')

    def _send_json_response(self, data, status_code=200):
        """Helper method to send JSON response"""
        self._set_headers(status_code)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        """Handle preflight requests"""
        self._set_headers(204)
        self.end_headers()

    def do_POST(self):
        """Handle POST requests for license verification"""
        try:
            # Read and parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_json_response(
                    {"valid": False, "error": "Empty request body"},
                    status_code=400
                )
                return

            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode())
            except json.JSONDecodeError:
                self._send_json_response(
                    {"valid": False, "error": "Invalid JSON format"},
                    status_code=400
                )
                return

            license_key = data.get("licenseKey", "").upper().strip()
            logging.info(f"Received license key: {license_key}")

            # Validate license key format
            if not license_key or len(license_key) < 5:
                self._send_json_response(
                    {"valid": False, "error": "Invalid license key format"},
                    status_code=400
                )
                return

            # Load license database
            try:
                with open("LICENSE_KEYS.json", "r") as f:
                    license_db = json.load(f)
            except Exception as e:
                logging.error(f"Error loading license DB: {str(e)}")
                license_db = {
                    "DEMO-1234-5678-9012": {
                        "active": True,
                        "features": ["premium"],
                        "created_at": datetime.now().isoformat()
                    }
                }

            # Check license validity
            if license_key in license_db and license_db[license_key].get("active", False):
                response = {
                    "valid": True,
                    "licenseKey": license_key,
                    "features": license_db[license_key].get("features", []),
                    "timestamp": datetime.now().isoformat()
                }
                logging.info(f"Valid license key: {license_key}")
                self._send_json_response(response, status_code=200)
            else:
                response = {
                    "valid": False,
                    "error": "Invalid or inactive license key",
                    "timestamp": datetime.now().isoformat()
                }
                logging.info(f"Invalid license key: {license_key}")
                self._send_json_response(response, status_code=403)

        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            self._send_json_response(
                {
                    "valid": False,
                    "error": "Internal server error",
                    "timestamp": datetime.now().isoformat()
                },
                status_code=500
            )

def run(server_class=HTTPServer, handler_class=handler, port=3000):
    server_address = ('', port)  # Empty string means listen on all available interfaces
    httpd = server_class(server_address, handler_class)
    logging.info(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
