import json
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

class LicenseRequest(BaseModel):
    licenseKey: str

def get_license_db():
    """Get license database from environment variable"""
    license_db_str = os.getenv('LICENSE_KEYS', '{}')
    try:
        return json.loads(license_db_str)
    except json.JSONDecodeError:
        logger.error("Invalid license database format in environment variable")
        return {}

@app.post("/api/license/verify")
async def verify_license(request: LicenseRequest):
    try:
        license_key = request.licenseKey
        logger.info(f"Received license key: {license_key}")

        # Get license database from environment
        license_db = get_license_db()

        # Check if license key exists and is valid
        if license_key in license_db:
            logger.info(f"Valid license key: {license_key}")
            return {
                "valid": True,
                "message": "License key is valid",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.warning(f"Invalid license key: {license_key}")
            return {
                "valid": False,
                "error": "Invalid license key",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
