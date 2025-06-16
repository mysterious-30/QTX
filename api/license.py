from http.server import BaseHTTPRequestHandler
import json
import os

class LicenseVerifier(BaseHTTPRequestHandler):
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
            print(f"License DB error: {str(e)}")
            return {}

    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            license_key = data.get('licenseKey', '').upper().strip()
            self.license_db = self._load_license_db()
            
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
            print(f"Handler error: {str(e)}")
            return self._send_response(500, {"error": "Internal server error"})

    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# Vercel-specific handler wrapper
def vercel_handler(request):
    """Vercel-compatible handler entry point"""
    class VercelWrapper(LicenseVerifier):
        def __init__(self):
            self.request = request
            self.response = type('', (), {})()  # Response placeholder
            
        def handle(self):
            """Process the request"""
            try:
                if self.request.method == 'POST':
                    self.do_POST()
                else:
                    self._send_response(405, {"error": "Method not allowed"})
            except Exception as e:
                print(f"Vercel handler error: {str(e)}")
                self._send_response(500, {"error": "Handler failed"})
    
    handler = VercelWrapper()
    handler.handle()
    return {
        'statusCode': handler.response.status if hasattr(handler.response, 'status') else 500,
        'headers': getattr(handler.response, 'headers', {'Content-Type': 'application/json'}),
        'body': handler.response.body.decode() if hasattr(handler.response, 'body') else json.dumps({"error": "Unknown error"})
    }
