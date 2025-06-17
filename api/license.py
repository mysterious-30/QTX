import json
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept, Origin')
        self.send_header('Access-Control-Max-Age', '86400')  # 24 hours
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def _send_json_response(self, data, status=200):
        self._set_headers(status)
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        try:
            # Log request details
            logger.info(f"Received request from {self.client_address[0]}")
            logger.info(f"Request headers: {dict(self.headers)}")

            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                logger.error("Empty request body")
                self._send_json_response({"error": "Empty request body"}, 400)
                return

            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {str(e)}")
                self._send_json_response({"error": "Invalid JSON format"}, 400)
                return

            license_key = data.get('licenseKey')
            if not license_key:
                logger.error("No license key provided")
                self._send_json_response({"error": "No license key provided"}, 400)
                return

            logger.info(f"Received license key: {license_key}")

            # Load license database
            try:
                with open('LICENSE_KEYS.json', 'r') as f:
                    license_db = json.load(f)
            except FileNotFoundError:
                logger.error("License database not found")
                self._send_json_response({"error": "License database not found"}, 500)
                return
            except json.JSONDecodeError:
                logger.error("Invalid license database format")
                self._send_json_response({"error": "Invalid license database format"}, 500)
                return

            # Check if license key exists and is valid
            if license_key in license_db:
                logger.info(f"Valid license key: {license_key}")
                self._send_json_response({
                    "valid": True,
                    "message": "License key is valid",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.warning(f"Invalid license key: {license_key}")
                self._send_json_response({
                    "valid": False,
                    "error": "Invalid license key",
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self._send_json_response({"error": "Internal server error"}, 500)

def run(server_class=HTTPServer, handler_class=handler, port=3000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
