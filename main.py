

# import logging
# import asyncio
# import time
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from typing import Optional

# from agent import run_agent, BYE_WORDS  # ← ADK, no more LangGraph

# load_dotenv()

# # ── Logging ───────────────────────────────────────────────────

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)-8s | %(message)s",
#     datefmt="%H:%M:%S"
# )
# log = logging.getLogger("main")

# # ── App ───────────────────────────────────────────────────────

# app = FastAPI(title="UI Navigator Agent", version="4.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class Command(BaseModel):
#     text: str
#     use_vision: Optional[bool] = True


# # ── Request logging middleware ────────────────────────────────

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     t0 = time.time()
#     log.info(f"▶  {request.method} {request.url.path}")
#     response = await call_next(request)
#     elapsed = (time.time() - t0) * 1000
#     log.info(f"◀  {request.method} {request.url.path} → {response.status_code}  ({elapsed:.0f}ms)")
#     return response


# # ── Routes ────────────────────────────────────────────────────

# @app.get("/")
# def ui():
#     return FileResponse("ui.html")


# @app.get("/health")
# def health():
#     return {"status": "running", "agent": "Gemini ADK + gemini-2.5-flash"}


# @app.post("/control")
# async def control(cmd: Command):
#     if not cmd.text.strip():
#         raise HTTPException(status_code=400, detail="Command text is empty")

#     log.info("=" * 50)
#     log.info(f"📥 NEW COMMAND  : '{cmd.text}'")
#     log.info(f"   use_vision   : {cmd.use_vision}")

#     # Bye — skip the agent entirely
#     if cmd.text.strip().lower() in BYE_WORDS:
#         log.info("👋 BYE detected — skipping agent")
#         return {
#             "status":  "bye",
#             "command": cmd.text,
#             "result":  "👋 Goodbye! Send a command anytime to start again."
#         }

#     # Run ADK multi-agent pipeline
#     t0 = time.time()
#     loop = asyncio.get_event_loop()
#     result = await loop.run_in_executor(
#         None,
#         lambda: run_agent(command=cmd.text.strip(), use_vision=cmd.use_vision)
#     )
#     elapsed = time.time() - t0

#     log.info(f"✅ AGENT DONE  : {elapsed:.2f}s")
#     log.info(f"📤 RESULT      : '{result}'")

#     return {
#         "status":  "ok",
#         "command": cmd.text,
#         "result":  result,
#     }


# @app.post("/control/quick")
# async def quick_control(cmd: Command):
#     """Quick control without vision — for YouTube shortcuts and keyboard commands."""
#     cmd.use_vision = False
#     return await control(cmd)



import asyncio
import os
import json
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional

from agent import run_agent, BYE_WORDS, stream_subscribe, stream_unsubscribe, set_main_loop

load_dotenv()

# ── Auth ──────────────────────────────────────────────────────

security = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(
        credentials.username.encode(), os.getenv("DASHBOARD_USER", "admin").encode()
    )
    correct_pass = secrets.compare_digest(
        credentials.password.encode(), os.getenv("DASHBOARD_PASS", "changeme").encode()
    )
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

# ── App ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    set_main_loop(asyncio.get_running_loop())
    yield

app = FastAPI(title="ScreenPilot", version="4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────

class Command(BaseModel):
    text: str
    use_vision: Optional[bool] = True

# ── Routes ────────────────────────────────────────────────────

@app.get("/")
def ui(auth=Depends(require_auth)):
    return FileResponse("dashboard.html")


@app.get("/health")
def health():
    return {"status": "running", "agent": "ADK + Gemini 2.5 Flash"}


@app.get("/stream")
async def stream(token: str = ""):
    """SSE endpoint — streams tool log events and done signal to the dashboard."""
    expected = os.getenv("DASHBOARD_PASS", "changeme")
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid token")

    q = stream_subscribe()

    async def event_generator():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=20.0)
                    event_type = event.get("type", "log")
                    yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            stream_unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/control")
def control(cmd: Command, auth=Depends(require_auth)):
    if not cmd.text.strip():
        raise HTTPException(status_code=400, detail="Command text is empty")

    if cmd.text.strip().lower() in BYE_WORDS:
        return {
            "status": "bye",
            "command": cmd.text,
            "result": "👋 Goodbye! Send a command anytime to start again.",
        }

    result = run_agent(cmd.text.strip(), use_vision=cmd.use_vision)
    return {"status": "ok", "command": cmd.text, "result": result}


@app.post("/control/quick")
def quick_control(cmd: Command, auth=Depends(require_auth)):
    """Quick control without vision — for YouTube shortcuts."""
    cmd.use_vision = False
    return control(cmd, auth)
