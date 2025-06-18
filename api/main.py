from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import logging
from datetime import datetime
import pytz
import httpx
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set IST timezone
IST = pytz.timezone('Asia/Kolkata')

# VPS API configuration
VPS_API_URL = os.getenv('VPS_API_URL', 'http://79.99.40.71:6401')
VPS_API_KEY = os.getenv('VPS_API_KEY', '696969')

app = FastAPI(title="QTX License Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://xenon-qtx.vercel.app", "chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

class LicenseRequest(BaseModel):
    licenseKey: str
    deviceId: str

class TransferRequest(BaseModel):
    licenseKey: str
    currentDeviceId: str
    newDeviceId: Optional[str] = None
    transferCode: str

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

async def get_license_db() -> Dict[str, Any]:
    """Get license database from VPS"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VPS_API_URL}/api/licenses",
                headers={"X-API-Key": VPS_API_KEY}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching license data from VPS: {str(e)}")
        # Return default demo licenses if VPS is unavailable
        return {
            "DEMO-1234-5678-9012": {
                "active": True,
                "expires_at": "2025-06-18T12:55:00Z",
                "device_id": None,
                "device_info": None
            }
        }

async def save_license_db(license_db: Dict[str, Any]) -> None:
    """Save license database to VPS"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VPS_API_URL}/api/licenses",
                headers={"X-API-Key": VPS_API_KEY},
                json=license_db
            )
            response.raise_for_status()
            logger.info("License database updated on VPS")
    except Exception as e:
        logger.error(f"Error saving license data to VPS: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save license data")

def generate_transfer_code(license_key: str, device_id: str) -> str:
    """Generate a transfer code for license transfer"""
    import hashlib
    return hashlib.sha256(f"{license_key}:{device_id}:transfer".encode()).hexdigest()[:8].upper()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test VPS connection
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VPS_API_URL}/api/health",
                headers={"X-API-Key": VPS_API_KEY},
                timeout=5.0
            )
            response.raise_for_status()
            vps_status = response.json()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(IST).isoformat(),
            "vps_connection": "ok",
            "config": {
                "vps_url": VPS_API_URL,
                "api_key_configured": bool(VPS_API_KEY),
                "allowed_origins": ["https://xenon-qtx.vercel.app", "chrome-extension://*"]
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Health check failed: {str(e)}",
                "error": str(e)
            }
        )

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

        license_db = await get_license_db()
        
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
                await save_license_db(license_db)
                logger.info(f"License key {license_key} registered to device {device_id}")
            else:
                # Update last active time
                license_data["device_info"] = device_info
                license_db[license_key] = license_data
                await save_license_db(license_db)
            
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

        license_db = await get_license_db()
        
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
        await save_license_db(license_db)
        
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

        license_db = await get_license_db()
        
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
        await save_license_db(license_db)
        
        return LicenseTransferResponse(
            success=True,
            message="Device ID reset successfully",
            timestamp=datetime.now(IST).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error during device reset: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )
