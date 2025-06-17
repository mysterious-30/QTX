from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="QTX License Server")

class LicenseRequest(BaseModel):
    licenseKey: str

class LicenseResponse(BaseModel):
    valid: bool
    message: str
    timestamp: str

def get_license_db() -> Dict[str, Any]:
    """Get license database from environment variable"""
    try:
        license_db_str = os.getenv('LICENSE_KEYS', '{}')
        return json.loads(license_db_str)
    except json.JSONDecodeError:
        logger.error("Invalid license database format in environment variable")
        return {}

@app.get("/")
@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/license/verify", response_model=LicenseResponse)
async def verify_license(request: LicenseRequest) -> LicenseResponse:
    """
    Verify a license key
    """
    try:
        license_key = request.licenseKey.strip().upper()
        logger.info(f"Verifying license key: {license_key}")

        if not license_key:
            raise HTTPException(status_code=400, detail="License key cannot be empty")

        license_db = get_license_db()
        
        if license_key in license_db:
            logger.info(f"Valid license key: {license_key}")
            return LicenseResponse(
                valid=True,
                message="License key is valid",
                timestamp=datetime.now().isoformat()
            )
        
        logger.warning(f"Invalid license key: {license_key}")
        return LicenseResponse(
            valid=False,
            message="Invalid license key",
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during license verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
