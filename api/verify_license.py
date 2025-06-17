from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
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

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
