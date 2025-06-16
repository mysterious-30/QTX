from http.server import BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'QTX Backend Running')
        else:
            self.send_response(404)
            self.end_headers()

def vercel_handler(request):
    # Vercel-specific handler adaptation
    h = Handler(
        request,
        None,  # server
        None,   # client_address
        False   # suppress_log
    )
    h.request = request
    h.handle()
    return {
        'statusCode': h.response.status,
        'headers': dict(h.response.headers),
        'body': h.response.body.decode() if h.response.body else ''
    }
