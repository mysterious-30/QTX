import json
import os
from typing import Dict, Any

# Load license database
def load_license_db() -> Dict[str, Any]:
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

# License verification logic
def verify_license(license_key: str) -> Dict[str, Any]:
    license_db = load_license_db()
    license_key = license_key.upper().strip()

    if not license_key:
        return {"error": "License key required", "statusCode": 400}

    if license_key in license_db and license_db[license_key].get('active', False):
        return {
            "valid": True,
            "licenseKey": license_key,
            "features": license_db[license_key].get('features', []),
            "statusCode": 200
        }

    return {"error": "Invalid license key", "statusCode": 403}

# Main handler function
def handle_license_verification(request: dict) -> dict:
    try:
        if request['method'] == 'POST':
            body = request.get('body', '{}')
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid JSON"}),
                    "headers": {"Content-Type": "application/json"}
                }

            license_key = data.get('licenseKey', '')
            result = verify_license(license_key)

            return {
                "statusCode": result.get('statusCode', 200),
                "body": json.dumps({k: v for k, v in result.items() if k != 'statusCode'}),
                "headers": {"Content-Type": "application/json"}
            }

        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"}),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception as e:
        print(f"Handler error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {"Content-Type": "application/json"}
        }

# ✅ Exported Vercel-compatible function
handler = handle_license_verification
