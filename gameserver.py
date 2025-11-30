from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
from clock import Clock

import asyncio

app = FastAPI()

clocks = [Clock(0,50), Clock(1, 50)]  # Add more clocks as needed

# Player scores
playerScores = {}
connectedClients = set()

@app.post("/login")
async def login(playerName):
    if playeName not in playerScores:
        playerScores[playerName] = 0
    return {"message": f"Player {playerName} logged in"}
    
@app.websocket("/ws")
async def websocketEndpoint(websocket: WebSocket):
    await websocket.accept()
    connectedClients.add(websocket)
    try:
        while True:
            # This loop only waits for messages from the clients
            # It does NOT drive the game loop.
            data = await websocket.receive_json()
            clockId = data.get("id")
            print("asked to remove clockId")
    except WebSocketDisconnect:
        connectedClients.discard(websocket)
    except Exception:
        # On any other error, just drop the connection
        connectedClients.discard(websocket)
        
async def gameLoop():
    """Update positions and broadcast state ~4 times per second."""
    while True:
        # Step circles
        for c in clocks:
            c.step()

        # Build payload
        clocksPayload = [c.asDict() for c in clocks]
        playersPayload = [
            {"name": name, "score": score}
            for name, score in playerScores.items()
        ]
        payload = {
            "type": "state",
            "clocks": clocksPayload,
            "players": playersPayload,
        }

        # Broadcast to all connected clients
        disconnected: List[WebSocket] = []
        print("sending")
        for ws in list(connectedClients):
            try:
                await ws.send_json(payload)
            except Exception:
                print("disc ", ws)
                disconnected.append(ws)

        # Remove broken connections
        for ws in disconnected:
            connectedClients.discard(ws)

        # 4 times per second
        await asyncio.sleep(0.25)

@app.on_event("startup")
async def start_game():
    asyncio.create_task(gameLoop())