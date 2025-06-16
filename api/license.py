from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
import os

app = FastAPI()

# Load license keys (in production, use a database)
LICENSE_DB = {}
if os.path.exists('LICENSE_KEYS.json'):
    with open('LICENSE_KEYS.json') as f:
        LICENSE_DB = json.load(f)

@app.post("/license/verify")
async def verify_license(request: Request):
    data = await request.json()
    license_key = data.get('licenseKey', '').upper().strip()
    
    if not license_key:
        raise HTTPException(status_code=400, detail="License key required")
    
    if license_key in LICENSE_DB:
        if LICENSE_DB[license_key]['active']:
            return {
                "valid": True,
                "message": "License activated",
                "licenseData": LICENSE_DB[license_key]
            }
    
    return JSONResponse(
        status_code=403,
        content={"valid": False, "message": "Invalid license key"}
    )

async def handler(request: Request):
    if request.method == 'POST':
        return await verify_license(request)
    return JSONResponse(
        status_code=405,
        content={"error": "Method not allowed"}
    )
