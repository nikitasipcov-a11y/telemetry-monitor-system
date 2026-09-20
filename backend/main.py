from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import pyotp
import json
import asyncio
import psutil

app = FastAPI(title="Telemetry Monitor System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = pyotp.random_base32()
totp = pyotp.TOTP(SECRET_KEY)

@app.get("/api/auth/2fa-setup")
async def setup_2fa():
    return {"secret": SECRET_KEY, "qr_uri": totp.provisioning_uri(name="TelemetryUser", issuer_name="TelemetryApp")}

@app.post("/api/auth/verify")
async def verify_2fa(code: str):
    is_valid = totp.verify(code)
    return {"status": "success" if is_valid else "error", "authenticated": is_valid}

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Сбор реальных данных вашего ПК
            data = {
                "cpu_load": psutil.cpu_percent(interval=None),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Client disconnected from telemetry stream")
