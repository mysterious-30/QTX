from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
@app.get("/api/health")
async def health_check():
    return JSONResponse(
        content={"status": "healthy"},
        status_code=200
    )
