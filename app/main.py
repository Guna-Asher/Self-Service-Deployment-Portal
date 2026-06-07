from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import auth, applications, versions, deployments

app = FastAPI(title="Deployment Portal", version="1.0.0")

# API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(versions.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve the frontend dashboard
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")