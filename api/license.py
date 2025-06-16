from http.server import BaseHTTPRequestHandler
import json
import os

class LicenseVerifier(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.license_db = self._load_license_db()
        super().__init__(*args, **kwargs)
    
    def _load_license_db(self):
        """Load license keys from file or return demo key"""
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
        """Handle license verification requests"""
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
            else:
                return self._send_response(403, {"error": "Invalid license key"})
                
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return self._send_response(500, {"error": "Internal server error"})

    def _send_response(self, status_code, data):
        """Helper to send JSON responses"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# Vercel-compatible handler function
def handler(request):
    """Entry point for Vercel serverless function"""
    verifier = LicenseVerifier(
        request,
        None,  # server
        None,   # client_address
        False   # suppress_log
    )
    verifier.request = request
    verifier.handle()
    return {
        'statusCode': verifier.response.status,
        'headers': dict(verifier.response.headers),
        'body': verifier.response.body.decode() if hasattr(verifier.response, 'body') else ''
    }
