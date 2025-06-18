from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import logging
from datetime import datetime
import pytz
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set IST timezone
IST = pytz.timezone('Asia/Kolkata')

app = FastAPI(title="QTX License Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class LicenseRequest(BaseModel):
    licenseKey: str

class LicenseResponse(BaseModel):
    valid: bool
    message: str
    timestamp: str
    expires_at: Optional[str] = None

def get_license_db() -> Dict[str, Any]:
    """Get license database from LICENSE_KEYS.json file"""
    try:
        # Try to find the file in the current directory first
        file_path = 'LICENSE_KEYS.json'
        if not os.path.exists(file_path):
            # If not found, try the parent directory
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'LICENSE_KEYS.json')
        
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"LICENSE_KEYS.json not found at {file_path}. Please create it.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in LICENSE_KEYS.json at {file_path}")
        return {}

@app.get("/")
@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/license/verify", response_model=LicenseResponse)
async def verify_license(request: LicenseRequest) -> LicenseResponse:
    """
    Verify a license key and check its expiration date
    """
    try:
        license_key = request.licenseKey.strip().upper()
        logger.info(f"Verifying license key: {license_key}")

        if not license_key:
            raise HTTPException(status_code=400, detail="License key cannot be empty")

        license_db = get_license_db()
        
        if license_key in license_db:
            license_data = license_db[license_key]
            
            # Check if license is active
            if not license_data.get("active", False):
                logger.warning(f"Inactive license key: {license_key}")
                return LicenseResponse(
                    valid=False,
                    message="License key is inactive",
                    timestamp=datetime.now(IST).isoformat()
                )
            
            # Check expiration date
            expires_at = license_data.get("expires_at")
            if expires_at:
                try:
                    # Parse the expiration date (already in IST)
                    expiration_date = datetime.fromisoformat(expires_at.replace('Z', '+05:30'))
                    current_time = datetime.now(IST)
                    
                    if current_time > expiration_date:
                        logger.warning(f"Expired license key: {license_key}")
                        return LicenseResponse(
                            valid=False,
                            message="License key has expired",
                            timestamp=current_time.isoformat()
                        )
                    
                    # Format expiration date for response (already in IST)
                    expires_at_ist = expiration_date.isoformat()
                except ValueError as e:
                    logger.error(f"Invalid expiration date format for key {license_key}: {str(e)}")
                    return LicenseResponse(
                        valid=False,
                        message="Invalid license key format",
                        timestamp=datetime.now(IST).isoformat()
                    )
            
            logger.info(f"Valid license key: {license_key}")
            return LicenseResponse(
                valid=True,
                message="License key is valid",
                timestamp=datetime.now(IST).isoformat(),
                expires_at=expires_at_ist if expires_at else None
            )
        
        logger.warning(f"Invalid license key: {license_key}")
        return LicenseResponse(
            valid=False,
            message="Invalid license key",
            timestamp=datetime.now(IST).isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during license verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
