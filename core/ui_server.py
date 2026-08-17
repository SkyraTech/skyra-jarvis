"""
Jarvis UI Server & Thread-Safe State Manager
=============================================
Runs a local FastAPI server to host the 3D Three.js dashboard.
Manages WebSocket connections and thread-safe UI updates.
"""

import asyncio
import json
import threading
from pathlib import Path

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

app = FastAPI()

# Mount spatial assets static directory
_STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

connected_websockets = set()
server_loop = None

# Thread-local recursion guard to prevent log loop overflows
_log_guard = threading.local()

def loguru_websocket_sink(message):
    if getattr(_log_guard, "active", False):
        return
    _log_guard.active = True
    try:
        record = message.record
        msg_text = record["message"]
        # Filter out uvicorn WebSocket routing noise to prevent loops
        if "websocket" in msg_text.lower() or "/ws" in msg_text or "dashboard" in msg_text.lower() or "ui server request" in msg_text.lower():
            return
            
        log_data = {
            "type": "log_stream",
            "timestamp": record["time"].strftime("%H:%M:%S"),
            "level": record["level"].name,
            "message": msg_text
        }
        broadcast_ui_event(log_data)
    except Exception:
        pass
    finally:
        _log_guard.active = False

# Register Loguru custom sink
logger.add(loguru_websocket_sink, level="INFO", format="{message}")


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Global request logging and Express-like error catching middleware."""
    try:
        logger.debug(f"UI Server Request: {request.method} {request.url.path}")
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"HTTP Server Exception on {request.url.path}: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Internal Server Error: {str(e)}"}
        )


@app.get("/")
def read_root():
    """Serve the 3D hologram dashboard.html."""
    dashboard_path = Path(__file__).parent.parent / "dashboard.html"
    return FileResponse(dashboard_path)


@app.get("/health")
def health_check():
    """Service health check endpoint for port health check galaxy nodes."""
    return {"status": "ok", "service": "skyra-jarvis", "port": 8000}


class EventModel(Request):
    # Standard dict payload
    pass


@app.post("/event")
async def post_event(request: Request):
    """Receive an event from a microservice and broadcast to dashboard."""
    try:
        body = await request.json()
        broadcast_ui_event(body)
        return {"success": True}
    except Exception as e:
        logger.error(f"Event broadcast failed: {e}")
        return {"success": False, "error": str(e)}



# Callbacks and loops for routing UI text inputs to the backend thread
text_input_callback = None
backend_loop = None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to synchronize status with the 3D view."""
    global server_loop
    # Capture the server's event loop to schedule updates from other threads safely
    server_loop = asyncio.get_running_loop()
    
    await websocket.accept()
    connected_websockets.add(websocket)
    logger.info("3D Hologram dashboard connected to core.")
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") == "ping":
                    # Respond with pong heartbeat to keep connection alive
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif data.get("type") == "user_message":
                    msg = data.get("message", "")
                    if msg and text_input_callback and backend_loop:
                        asyncio.run_coroutine_threadsafe(
                            text_input_callback(msg), 
                            backend_loop
                        )
            except Exception as e:
                logger.error(f"Error handling UI WebSocket message: {e}")
    except Exception:
        pass
    finally:
        connected_websockets.remove(websocket)
        logger.info("3D Hologram dashboard disconnected.")



def _run_server():
    """Start uvicorn server in a separate thread."""
    import uvicorn
    # Run silently to avoid cluttering terminal logs
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def start_ui_server():
    """Start the FastAPI backend server in a daemon thread."""
    thread = threading.Thread(target=_run_server, daemon=True)
    thread.start()
    logger.info("Local UI server hosting on http://127.0.0.1:8000")


def update_ui_state(state: str):
    """
    Thread-safe state updater. Call this from ANY thread or async loop.
    
    Args:
        state: "speaking", "listening", "idle", or "offline"
    """
    global server_loop
    if not connected_websockets or not server_loop:
        return

    # Coroutine to be scheduled on the server loop
    async def _send_state():
        message = json.dumps({"status": state})
        for ws in list(connected_websockets):
            try:
                await ws.send_text(message)
            except Exception:
                pass

    # Safely schedule the task on the server's event loop
    asyncio.run_coroutine_threadsafe(_send_state(), server_loop)


def change_ui_state(state: str):
    """
    Exposes a safe, non-throwing UI status updater.
    Can be imported and called safely anywhere in the codebase.
    """
    try:
        update_ui_state(state)
    except Exception as e:
        logger.debug(f"Failed to update UI state: {e}")


def broadcast_ui_event(event_data: dict):
    """
    Broadcast an arbitrary JSON event to all connected WebSockets.
    Used for sending real-time agent task/message logs to the dashboard.
    """
    global server_loop
    if not connected_websockets or not server_loop:
        return

    async def _send_event():
        message = json.dumps(event_data)
        for ws in list(connected_websockets):
            try:
                await ws.send_text(message)
            except Exception:
                pass

    asyncio.run_coroutine_threadsafe(_send_event(), server_loop)

