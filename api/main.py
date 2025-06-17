from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "QTX Backend Running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

async def handler(request: Request):
    path = request.url.path
    if path == "/":
        return JSONResponse(content={"status": "QTX Backend Running"})
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )
