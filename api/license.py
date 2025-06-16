from http.server import BaseHTTPRequestHandler
import json
import os

class LicenseHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.license_db = self._load_license_db()
        super().__init__(*args, **kwargs)
    
    def _load_license_db(self):
        """Load license keys from JSON file"""
        try:
            if os.path.exists('LICENSE_KEYS.json'):
                with open('LICENSE_KEYS.json', 'r') as f:
                    return json.load(f)
            return {
                "DEMO-1234-5678-9012": {
                    "active": True,
                    "features": ["premium"]
                }
            }
        except Exception as e:
            print(f"Error loading license DB: {str(e)}")
            return {}

    def do_POST(self):
        """Handle license verification"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            license_key = data.get('licenseKey', '').upper().strip()
            
            if not license_key:
                return self._send_response(400, {"error": "License key required"})
                
            if license_key in self.license_db and self.license_db[license_key].get('active', False):
                return self._send_response(200, {
                    "valid": True,
                    "licenseKey": license_key,
                    "features": self.license_db[license_key].get('features', [])
                })
            return self._send_response(403, {"error": "Invalid license key"})
            
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return self._send_response(500, {"error": "Internal server error"})

    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# Vercel-compatible handler function (REQUIRED)
def handler(request):
    """Entry point for Vercel serverless function"""
    class VercelRequestWrapper:
        def __init__(self, request):
            self.request = request
            self.response = type('obj', (object,), {'status': 500, 'headers': {}, 'body': b''})
            
        def handle(self):
            try:
                if self.request.method == 'POST':
                    LicenseHandler(
                        self.request,
                        None,  # server
                        None,  # client_address
                        False  # suppress_log
                    ).do_POST()
            except Exception as e:
                print(f"Handler error: {str(e)}")
                self.response.status = 500
                self.response.body = json.dumps({"error": "Handler failed"}).encode()
    
    wrapper = VercelRequestWrapper(request)
    wrapper.handle()
    return {
        'statusCode': wrapper.response.status,
        'headers': dict(wrapper.response.headers),
        'body': wrapper.response.body.decode()
    }
