"""
main.py — FastAPI application entry point

Bootstraps FastAPI, wraps it with the Socket.IO ASGI app, registers all
REST routers, and reshapes error responses to `{"error": message}` to
match the API contract the Vue frontend already expects.
"""

import socketio
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from sockets.manager import sio

from routers.auth import router as auth_router
from routers.jobs import router as jobs_router
from routers.dispatches import router as dispatches_router
from routers.techs import router as techs_router
from routers.faq import router as faq_router
from routers.internal import router as internal_router

ALLOWED_ORIGINS = list({settings.frontend_url, "http://localhost:5173"})

app = FastAPI(title="HVAC Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "Invalid request body"})


app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(dispatches_router, prefix="/api/dispatches", tags=["dispatches"])
app.include_router(techs_router, prefix="/api/techs", tags=["techs"])
app.include_router(faq_router, prefix="/api/faq", tags=["faq"])
app.include_router(internal_router, prefix="/api/internal", tags=["internal"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hvac-backend"}


# Wrap the FastAPI app with the Socket.IO ASGI app — this combined app is
# what Uvicorn actually serves (see Dockerfile: `uvicorn main:socket_app`).
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


if __name__ == "__main__":
    print(f"[server] CORS allowed origins: {', '.join(ALLOWED_ORIGINS)}")
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=settings.port,
        reload=(settings.environment == "development"),
    )
