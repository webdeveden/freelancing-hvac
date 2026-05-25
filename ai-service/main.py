"""
main.py — FastAPI application entry point

Registers all routers and starts the Uvicorn server.
The AI service receives Twilio webhooks on port 8000
and communicates with the Node.js backend internally.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings      import settings
from routers.health       import router as health_router
from routers.twilio_voice import router as twilio_router


app = FastAPI(
    title="HVAC AI Voice Receptionist",
    description="Handles inbound Twilio voice calls and books HVAC service appointments via Claude AI",
    version="1.0.0",
)

# Allow CORS from the Node.js backend (internal calls) and dev tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(twilio_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=(settings.environment == "development"),
    )
