from http.server import BaseHTTPRequestHandler
import json
import random

# Mock database of valid license keys
VALID_KEYS = {
    "ABCD-1234-EFGH-5678": {"active": True, "user": "example@example.com"},
    "WXYZ-9876-UVST-5432": {"active": True, "user": "test@test.com"}
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.read(content_length)
        data = json.loads(post_data)
        
        license_key = data.get('licenseKey', '').strip().upper()
        
        if license_key in VALID_KEYS and VALID_KEYS[license_key]['active']:
            response = {
                "valid": True,
                "message": "License key is valid",
                "licenseKey": license_key
            }
            self.send_response(200)
        else:
            response = {
                "valid": False,
                "message": "Invalid or inactive license key"
            }
            self.send_response(401)
        
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def read(self, n):
        return self.rfile.read(n)