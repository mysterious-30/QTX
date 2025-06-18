from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import logging
from datetime import datetime
import pytz
from typing import Dict, Any, Optional, List

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
    deviceId: str

class TransferRequest(BaseModel):
    licenseKey: str
    currentDeviceId: str
    newDeviceId: str
    transferCode: str  # For security

class DeviceInfo(BaseModel):
    deviceId: str
    lastActive: str
    platform: Optional[str] = None
    browser: Optional[str] = None

class LicenseResponse(BaseModel):
    valid: bool
    message: str
    timestamp: str
    expires_at: Optional[str] = None
    deviceInfo: Optional[DeviceInfo] = None

class LicenseTransferResponse(BaseModel):
    success: bool
    message: str
    timestamp: str

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

def save_license_db(license_db: Dict[str, Any]) -> None:
    """Save license database to LICENSE_KEYS.json file"""
    try:
        file_path = 'LICENSE_KEYS.json'
        if not os.path.exists(file_path):
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'LICENSE_KEYS.json')
        
        with open(file_path, 'w') as f:
            json.dump(license_db, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving LICENSE_KEYS.json: {str(e)}")

def generate_transfer_code(license_key: str, device_id: str) -> str:
    """Generate a transfer code for license transfer"""
    # In a real implementation, this would be more secure
    # For demo purposes, we'll use a simple hash
    import hashlib
    return hashlib.sha256(f"{license_key}:{device_id}:transfer".encode()).hexdigest()[:8].upper()

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
        device_id = request.deviceId.strip()
        logger.info(f"Verifying license key: {license_key} for device: {device_id}")

        if not license_key:
            raise HTTPException(status_code=400, detail="License key cannot be empty")
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID cannot be empty")

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
            
            # Check device ID
            stored_device_id = license_data.get("device_id")
            if stored_device_id and stored_device_id != device_id:
                logger.warning(f"License key {license_key} is already in use by another device")
                return LicenseResponse(
                    valid=False,
                    message="License key is already in use by another device",
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
            
            # Update device info
            device_info = {
                "deviceId": device_id,
                "lastActive": datetime.now(IST).isoformat(),
                "platform": license_data.get("device_info", {}).get("platform"),
                "browser": license_data.get("device_info", {}).get("browser")
            }
            
            # If this is the first time using the license, store the device ID
            if not stored_device_id:
                license_data["device_id"] = device_id
                license_data["device_info"] = device_info
                license_db[license_key] = license_data
                save_license_db(license_db)
                logger.info(f"License key {license_key} registered to device {device_id}")
            else:
                # Update last active time
                license_data["device_info"] = device_info
                license_db[license_key] = license_data
                save_license_db(license_db)
            
            logger.info(f"Valid license key: {license_key}")
            return LicenseResponse(
                valid=True,
                message="License key is valid",
                timestamp=datetime.now(IST).isoformat(),
                expires_at=expires_at_ist if expires_at else None,
                deviceInfo=DeviceInfo(**device_info)
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

@app.post("/api/license/transfer", response_model=LicenseTransferResponse)
async def transfer_license(request: TransferRequest) -> LicenseTransferResponse:
    """
    Transfer a license from one device to another
    """
    try:
        license_key = request.licenseKey.strip().upper()
        current_device_id = request.currentDeviceId.strip()
        new_device_id = request.newDeviceId.strip()
        transfer_code = request.transferCode.strip().upper()
        
        if not all([license_key, current_device_id, new_device_id, transfer_code]):
            raise HTTPException(status_code=400, detail="All fields are required")

        license_db = get_license_db()
        
        if license_key not in license_db:
            return LicenseTransferResponse(
                success=False,
                message="Invalid license key",
                timestamp=datetime.now(IST).isoformat()
            )
            
        license_data = license_db[license_key]
        stored_device_id = license_data.get("device_id")
        
        if stored_device_id != current_device_id:
            return LicenseTransferResponse(
                success=False,
                message="Current device is not authorized to transfer this license",
                timestamp=datetime.now(IST).isoformat()
            )
            
        # Verify transfer code
        expected_code = generate_transfer_code(license_key, current_device_id)
        if transfer_code != expected_code:
            return LicenseTransferResponse(
                success=False,
                message="Invalid transfer code",
                timestamp=datetime.now(IST).isoformat()
            )
            
        # Update device ID
        license_data["device_id"] = new_device_id
        license_data["device_info"] = {
            "deviceId": new_device_id,
            "lastActive": datetime.now(IST).isoformat(),
            "platform": license_data.get("device_info", {}).get("platform"),
            "browser": license_data.get("device_info", {}).get("browser")
        }
        license_db[license_key] = license_data
        save_license_db(license_db)
        
        return LicenseTransferResponse(
            success=True,
            message="License transferred successfully",
            timestamp=datetime.now(IST).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error during license transfer: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/license/reset-device", response_model=LicenseTransferResponse)
async def reset_device(request: TransferRequest) -> LicenseTransferResponse:
    """
    Reset the device ID for a license (admin function)
    """
    try:
        license_key = request.licenseKey.strip().upper()
        current_device_id = request.currentDeviceId.strip()
        transfer_code = request.transferCode.strip().upper()
        
        if not all([license_key, current_device_id, transfer_code]):
            raise HTTPException(status_code=400, detail="All fields are required")

        license_db = get_license_db()
        
        if license_key not in license_db:
            return LicenseTransferResponse(
                success=False,
                message="Invalid license key",
                timestamp=datetime.now(IST).isoformat()
            )
            
        # Verify transfer code (using a special admin code)
        expected_code = generate_transfer_code(license_key, "ADMIN")
        if transfer_code != expected_code:
            return LicenseTransferResponse(
                success=False,
                message="Invalid admin code",
                timestamp=datetime.now(IST).isoformat()
            )
            
        # Remove device ID
        license_data = license_db[license_key]
        license_data.pop("device_id", None)
        license_data.pop("device_info", None)
        license_db[license_key] = license_data
        save_license_db(license_db)
        
        return LicenseTransferResponse(
            success=True,
            message="Device ID reset successfully",
            timestamp=datetime.now(IST).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error during device reset: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
