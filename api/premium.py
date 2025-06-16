from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/premium/feature")
async def premium_feature(request: Request):
    data = await request.json()
    license_key = data.get('licenseKey', '').upper().strip()
    
    # In production, verify license key against database
    if not license_key:
        raise HTTPException(status_code=403, detail="License key required")
    
    # Your premium feature logic here
    result = f"Premium feature executed for license {license_key}"
    
    return {
        "success": True,
        "result": result,
        "featureData": {
            "used": True,
            "remaining": 999  # Example usage tracking
        }
    }

async def handler(request: Request):
    if request.method == 'POST':
        return await premium_feature(request)
    return JSONResponse(
        status_code=405,
        content={"error": "Method not allowed"}
    )
