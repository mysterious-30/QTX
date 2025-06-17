import json
import os

def handler(request):
    if request["method"] == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
            "body": ""
        }

    try:
        body = json.loads(request["body"])
        license_key = body.get("license_key")

        # Load from root directory
        with open(os.path.join(os.path.dirname(__file__), "../licenses.json"), "r") as f:
            valid_keys = json.load(f)

        if license_key in valid_keys["keys"]:
            result = {"status": "valid", "message": "License key is valid"}
        else:
            result = {"status": "invalid", "message": "Invalid license key"}

    except Exception as e:
        result = {"status": "error", "message": str(e)}

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Content-Type": "application/json"
        },
        "body": json.dumps(result)
    }
