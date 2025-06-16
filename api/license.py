from http.server import BaseHTTPRequestHandler
import json
import os

class LicenseHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.license_db = self._load_license_db()
        super().__init__(*args, **kwargs)
    
    def _load_license_db(self):
        try:
            with open('LICENSE_KEYS.json') as f:
                return json.load(f)
        except:
            return {
                "DEMO-1234-5678-9012": {
                    "active": True,
                    "user": "demo@example.com",
                    "expires": "2024-12-31",
                    "features": ["premium"]
                }
            }

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        license_data = json.loads(post_data)
        
        license_key = license_data.get('licenseKey', '').upper().strip()
        device_id = license_data.get('deviceId', '')  # For device binding
        
        if not license_key:
            self._send_error(400, "License key required")
            return
            
        if license_key in self.license_db and self.license_db[license_key]['active']:
            response = {
                "valid": True,
                "licenseKey": license_key,
                "expires": self.license_db[license_key]['expires'],
                "features": self.license_db[license_key].get('features', [])
            }
            self._send_response(200, response)
        else:
            self._send_error(403, "Invalid or inactive license key")

    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status_code, message):
        self._send_response(status_code, {"error": message})

def vercel_handler(request):
    handler = LicenseHandler(
        request,
        None,   # server
        None,    # client_address
        False    # suppress_log
    )
    handler.request = request
    handler.handle()
    return {
        'statusCode': handler.response.status,
        'headers': dict(handler.response.headers),
        'body': handler.response.body.decode() if handler.response.body else ''
    }
