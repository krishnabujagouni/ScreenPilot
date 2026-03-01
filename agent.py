

import os
import operator
from dotenv import load_dotenv
from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from tools import youtube_tools
from typing import TypedDict, List, Annotated
load_dotenv()

# ── State ─────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    # messages: List[AnyMessage]
    # status: Literal["running", "bye", "waiting"]

# ── LLM ───────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools(youtube_tools)

SYSTEM_PROMPT = """You are a YouTube laptop controller agent.

You receive natural language commands and call the right YouTube tool.

TOOL MAPPING — understand all variations:
- play / resume / start / unpause          → play_pause
- pause / stop / freeze / hold on          → play_pause
- louder / volume up / turn it up          → volume_up
- quieter / volume down / turn it down     → volume_down
- mute / silence / no sound                → mute
- fullscreen / full screen / big screen    → fullscreen
- skip / forward / next 10 / fast forward  → skip_forward
- back / rewind / go back / previous 10    → skip_backward
- next video / skip video / change video   → next_video
- previous video / last video              → previous_video
- open youtube / launch youtube            → open_youtube

Always call a tool. Never reply with plain text.
"""

BYE_WORDS = {"bye", "exit", "quit", "stop", "goodbye", "end", "close", "done"}

# ── Nodes ─────────────────────────────────────────────────────

def agent_node(state: AgentState):
    """Agent reads command and picks a tool."""
    # question = state["messages"][-1].content
    # messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

    response = llm_with_tools.invoke(state["messages"])
    return {
        "messages": state["messages"] + [response],
        
    }

def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END



tool_node = ToolNode(youtube_tools)
builder = StateGraph(AgentState)

# builder.add_node("bye_check", check_bye_node)
builder.add_node("agent", agent_node)
builder.add_node("tool_node", tool_node)

builder.add_edge(START, "agent")
# builder.add_conditional_edges("bye_check", route_after_bye_check, {"agent": "agent", END: END})
builder.add_conditional_edges("agent", should_continue, {"tool_node": "tool_node", END: END})
builder.add_edge("tool_node", "agent")   # ← loop back

graph = builder.compile()


