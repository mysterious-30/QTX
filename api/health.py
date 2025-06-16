from http.server import BaseHTTPRequestHandler

def handler(request):
    if request.path == '/api/health':
        return {
            'statusCode': 200,
            'body': '{"status": "healthy"}',
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    elif request.path == '/':
        return {
            'statusCode': 200,
            'body': 'Welcome to QTX Backend',
            'headers': {
                'Content-Type': 'text/plain'
            }
        }
    
    return {
        'statusCode': 404,
        'body': 'Not Found'
    }
