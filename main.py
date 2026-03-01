from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent import graph, BYE_WORDS, SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

app = FastAPI(title="YouTube Laptop Agent", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Command(BaseModel):
    text: str

@app.get("/")
def ui():
    return FileResponse("ui.html")

@app.get("/health")
def health():
    return {"status": "running", "agent": "LangGraph + GPT-4o"}

@app.post("/control")
def control(cmd: Command):
    if not cmd.text.strip():
        raise HTTPException(status_code=400, detail="Command text is empty")

    # Handle bye before hitting the graph
    if cmd.text.strip().lower() in BYE_WORDS:
        return {"status": "bye", "command": cmd.text, "result": "👋 Goodbye! Send a command anytime to start again."}

    # Run the graph
    result = graph.invoke({
        "messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=cmd.text.strip())]
    })

    # Extract tool result from messages
    for msg in reversed(result["messages"]):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            continue
        content = getattr(msg, "content", "")
        if isinstance(content, str) and content.strip():
            return {"status": "ok", "command": cmd.text, "result": content}
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("text", "").strip():
                    return {"status": "ok", "command": cmd.text, "result": block["text"]}

    return {"status": "ok", "command": cmd.text, "result": "Command executed"}