from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import pyotp
import json
import asyncio

app = FastAPI(title="Telemetry Monitor System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2FA Логика (TOTP)
SECRET_KEY = pyotp.random_base32()
totp = pyotp.TOTP(SECRET_KEY)

@app.get("/api/auth/2fa-setup")
async def setup_2fa():
    return {"secret": SECRET_KEY, "qr_uri": totp.provisioning_uri(name="TelemetryUser", issuer_name="TelemetryApp")}

@app.post("/api/auth/verify")
async def verify_2fa(code: str):
    is_valid = totp.verify(code)
    return {"status": "success" if is_valid else "error", "authenticated": is_valid}

# WebSockets для стриминга телеметрии
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Имитация поступления данных телеметрии
            data = {"cpu_load": 42.5, "memory_usage": 68.1, "network_rpm": 1200}
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Client disconnected from telemetry stream")
