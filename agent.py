import os
import asyncio
import concurrent.futures
import threading as _threading
import re as _re
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from tools import tools, capture_screen_base64

load_dotenv()

# ── Vertex AI Setup ───────────────────────────────────────────

_GCP_PROJECT  = os.getenv("GOOGLE_CLOUD_PROJECT")
_GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if _GCP_PROJECT:
    import vertexai
    vertexai.init(project=_GCP_PROJECT, location=_GCP_LOCATION)
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    _MODEL = "gemini-2.5-flash"
    print(f"[agent] ☁️  Vertex AI — project={_GCP_PROJECT}, model={_MODEL}")
else:
    _MODEL = "gemini-2.5-flash"
    print(f"[agent] ⚠️  GOOGLE_CLOUD_PROJECT not set — using Gemini API key")

# ── SSE Stream (log events only, no screenshots) ──────────────

_stream_subscribers: list = []
_main_loop: "asyncio.AbstractEventLoop | None" = None

def set_main_loop(loop):
    global _main_loop
    _main_loop = loop

def stream_emit(event: dict):
    loop = _main_loop
    if loop is None or not loop.is_running():
        return
    dead = []
    for q in list(_stream_subscribers):
        try:
            asyncio.run_coroutine_threadsafe(_safe_put(q, event), loop)
        except Exception:
            dead.append(q)
    for q in dead:
        try:
            _stream_subscribers.remove(q)
        except ValueError:
            pass

async def _safe_put(q, event):
    try:
        q.put_nowait(event)
    except (asyncio.QueueFull, Exception):
        pass

def stream_subscribe() -> "asyncio.Queue":
    q = asyncio.Queue(maxsize=100)
    _stream_subscribers.append(q)
    return q

def stream_unsubscribe(q):
    try:
        _stream_subscribers.remove(q)
    except ValueError:
        pass

# ── Constants ─────────────────────────────────────────────────

BYE_WORDS = {"bye", "exit", "quit", "stop", "goodbye", "end", "close", "done"}

MAX_STEPS = 25

NAV_TOOLS = {
    "open_url", "search_google", "open_youtube",
    "go_back_browser", "refresh_page", "new_tab", "wait",
}

SYSTEM_PROMPT = """
You are a precise UI automation agent that controls a computer screen.

You interact with the computer ONLY by calling the provided tools.

You CANNOT execute Python code, print statements, or write tool calls as text.
Tools must be invoked directly.


 
CORE RULES
 

• Only use the tools provided to you.
• Never invent tool names.
• Never output Python code.
• Never describe an action instead of performing it.
• Only perform actions the user explicitly asked for.
- Call EXACTLY ONE tool per turn, then stop completely.
- After open_url or open_youtube, your NEXT turn must be capture_screen() only.
- NEVER call a navigation tool and capture_screen in the same response.
When the task is fully complete, reply with exactly:

DONE


 
SCREEN UNDERSTANDING
 

You receive a screenshot of the current screen every step.

The screenshot is scaled to a width of **1024 pixels**.

All coordinates you produce must match the pixels in that image.

Example:
Pixel (400,300) in the screenshot = click_at_position(400,300)

Do NOT guess screen resolution.


 
TASK EXECUTION PROCESS
 

When a command is received:

1. Break the task into an ordered checklist.
2. Execute ONE step at a time.
3. After each action, analyze the next screenshot.
4. Continue until the goal is visually confirmed.

NEVER perform multiple steps in one response.


Workflow:

observe → act → observe → act


 
CLICKING PRECISION
 

To click an element:

1. Locate the element visually.
2. Determine its bounding box:

   left, top, right, bottom

3. Compute the center:

   x = (left + right) / 2  
   y = (top + bottom) / 2

4. Click the center using:

click_at_position(x, y)

Always click the element itself, not nearby text.


Precision tips:

• Buttons are usually 30–50px tall  
• Links are usually ~20px tall  
• Aim for the vertical center of elements  


 
BROWSER UI SAFETY
 

Never click inside browser chrome.

Forbidden zone:

y < 80

This area contains browser tabs and controls.





 
YOUTUBE CONTROLS
 

Use keyboard tools instead of clicking:

play_pause()
mute()
volume_up()
volume_down()
skip_forward()
skip_backward()
next_video()
previous_video()
fullscreen()


 
WHEN STUCK
 

If an action has no effect:

• Re-analyze the screenshot
• Choose a different UI element
• Do NOT repeat the same coordinates


 
COMPLETION
 

DONE ONLY when screenshot confirms:
- Play video → video player is visible and playing (progress bar visible).
- Add to cart → cart badge count OR "Added to Cart" message visible.
- Any other task → result visible in screenshot.
- NEVER say DONE immediately after a click — always call capture_screen() first to verify.
- Reply with exactly: DONE (no tool call in the same response).

Examples:

Open website → page is visibly loaded  
Add to cart → cart badge or confirmation appears  

When confirmed, respond with:

DONE
"""

# ── ADK Agent ─────────────────────────────────────────────────

navigator_agent = Agent(
    name="ui_navigator",
    model=_MODEL,
    description="Automates computer screen interactions using screenshots and tools.",
    instruction=SYSTEM_PROMPT,
    tools=tools,
)

session_service = InMemorySessionService()

runner = Runner(
    agent=navigator_agent,
    app_name="ui_navigator",
    session_service=session_service,
)

# ── Helpers ───────────────────────────────────────────────────

_TASK_KEYWORDS = {
    "open", "go", "search", "find", "click", "type", "play", "add",
    "buy", "scroll", "download", "upload", "close", "refresh", "navigate",
    "fill", "submit", "login", "logout", "copy", "paste", "select",
}

def _is_automation_task(command: str) -> bool:
    first_word = command.strip().lower().split()[0] if command.strip() else ""
    return first_word in _TASK_KEYWORDS or len(command.split()) > 4

def _make_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part.from_text(text=text)])

def _make_first_message(command: str) -> types.Content:
    if _is_automation_task(command):
        text = (f"Task: {command}\n\n"
                f"Do ONLY what this task asks — nothing more.\n"
                f"Call capture_screen() first, then act ONE step at a time.")
    else:
        text = (f"User message: {command}\n\n"
                f"If this is a greeting or casual message, reply with short friendly text and say DONE.\n"
                f"Do NOT call any tools.")
    return types.Content(role="user", parts=[types.Part.from_text(text=text)])

def _clean_response(text: str) -> str:
    if not text:
        return "Done."
    lines = text.strip().split("\n")
    clean = []
    for l in lines:
        l = l.strip()
        if not l:
            continue
        if _re.match(r"^\[.?\]", l):
            continue
        if _re.match(r"^\d+\.\s", l):
            continue
        if l.lower().startswith(("checklist", "current screen")):
            continue
        clean.append(l)
    result = " ".join(clean[-2:]) if clean else "Done."
    result = _re.sub(r"\bDONE\b\.?", "", result, flags=_re.IGNORECASE).strip().strip(".")
    return result.strip() or "Done."

# ── Image History Pruner ──────────────────────────────────────

async def _prune_session_images(session_id: str, keep_last: int = 1):
    try:
        session = await session_service.get_session(
            app_name="ui_navigator", user_id="user", session_id=session_id,
        )
        if not session or not hasattr(session, "events"):
            return
        image_event_indices = []
        for i, event in enumerate(session.events):
            if not hasattr(event, "content") or not event.content:
                continue
            for part in (event.content.parts or []):
                if hasattr(part, "inline_data") and part.inline_data:
                    image_event_indices.append(i)
                    break
        to_prune = image_event_indices[:-keep_last] if len(image_event_indices) > keep_last else []
        pruned = 0
        for i in to_prune:
            event = session.events[i]
            new_parts = []
            for part in (event.content.parts or []):
                if hasattr(part, "inline_data") and part.inline_data:
                    new_parts.append(types.Part.from_text(text="[screenshot — pruned]"))
                else:
                    new_parts.append(part)
            event.content.parts = new_parts
            pruned += 1
        if pruned:
            print(f"[agent] 🧹 Pruned {pruned} screenshot(s)")
    except Exception as e:
        print(f"[agent] ⚠️  Prune failed: {e}")

# ── Async Core ────────────────────────────────────────────────

async def _run_agent_async(command: str) -> str:

    session = await session_service.create_session(
        app_name="ui_navigator", user_id="user",
    )

    final_response = ""
    step = 0
    last_tool = None
    last_args = None
    repeat_count = 0

    current_message = _make_first_message(command)

    for iteration in range(MAX_STEPS):
        tool_called = None
        tool_args = {}
        is_done = False

        if iteration > 0 and iteration % 8 == 0:
            try:
                await session_service.delete_session(
                    app_name="ui_navigator", user_id="user", session_id=session.id,
                )
                session = await session_service.create_session(
                    app_name="ui_navigator", user_id="user",
                )
                print(f"[agent] ♻️  Session recycled at turn {iteration}")
                current_message = _make_message(
                    f"Session refreshed. Original task: {command}\n"
                    f"Call capture_screen() and continue from where you left off."
                )
            except Exception as e:
                print(f"[agent] ⚠️  Session recycle failed: {e}")

        print(f"[agent] 🔄 Turn {iteration + 1}")

        retry_count = 0
        events = []
        while True:
            try:
                async for event in runner.run_async(
                    user_id="user",
                    session_id=session.id,
                    new_message=current_message,
                ):
                    events.append(event)
                    if hasattr(event, "content") and event.content:
                        for part in (event.content.parts or []):
                            if hasattr(part, "function_call") and part.function_call:
                                break
                break
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    retry_count += 1
                    if retry_count > 5:
                        raise
                    wait = min(20 * retry_count, 60)
                    print(f"[agent] ⏳ Rate limited — waiting {wait}s ({retry_count}/5)")
                    await asyncio.sleep(wait)
                else:
                    raise

        for event in events:
            author = getattr(event, "author", "?")
            try:
                if (hasattr(event, "content") and event.content
                        and hasattr(event.content, "parts") and event.content.parts):
                    for part in event.content.parts:
                        try:
                            if hasattr(part, "function_call") and part.function_call:
                                if tool_called is None and not is_done:
                                    tool_called = part.function_call.name
                                    tool_args = dict(part.function_call.args)
                                fn = part.function_call.name
                                args = dict(part.function_call.args)
                                print(f"[step {step}] {author} → {fn}({args})")
                                # Stream log event — skip capture_screen (not useful to show)
                                if fn != "capture_screen":
                                    stream_emit({"type": "log", "step": step, "tool": fn, "args": args})
                                step += 1
                            elif hasattr(part, "text") and part.text:
                                text = part.text.strip()
                                if text:
                                    print(f"[turn {iteration+1}] {author} 💬 {text[:120]}")
                                if "DONE" in text.upper():
                                    is_done = True
                                    final_response = text
                        except Exception:
                            continue
            except Exception:
                continue

            try:
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part and hasattr(part, "text") and part.text:
                                final_response = part.text
                                if "DONE" in part.text.upper():
                                    is_done = True
            except Exception:
                pass

        if is_done:
            print(f"[agent] ✅ Task complete in {step} steps.")
            stream_emit({"type": "done", "message": _clean_response(final_response)})
            break

        if not tool_called:
            print(f"[agent] ⏹️  No tool called — stopping.")
            stream_emit({"type": "done", "message": _clean_response(final_response) or "Task complete."})
            break

        if tool_called != "capture_screen":
            current_sig = str(tool_args)
            if tool_called == last_tool and current_sig == last_args:
                repeat_count += 1
            else:
                repeat_count = 0
                last_tool = tool_called
                last_args = current_sig

            if repeat_count >= 1:
                print(f"[agent] 🔁 Stuck on '{tool_called}' x{repeat_count + 1} — injecting hint")
                await asyncio.sleep(1.0)
                current_message = _make_message(
                    f"WARNING: '{tool_called}' was called {repeat_count + 1} times with no progress.\n"
                    f"Try a completely different approach.\n"
                    f"- y < 80 is the browser tab bar — look below y=80\n"
                    f"- Call capture_screen() and re-examine the screen."
                )
                repeat_count = 0
                last_tool = None
                last_args = None
                continue

        wait_time = 3.0 if tool_called in NAV_TOOLS else 1.5
        await asyncio.sleep(wait_time)
        print(f"[agent] ⏳ Waited {wait_time}s after '{tool_called}'")

        await _prune_session_images(session.id, keep_last=1)

        if tool_called == "capture_screen":
            try:
                import base64 as _b64
                img_b64 = capture_screen_base64()
                current_message = types.Content(role="user", parts=[
                    types.Part.from_text(
                        text="Here is the current screenshot. "
                             "Analyze it carefully and continue the task. "
                             "Call EXACTLY ONE tool, then stop. "
                             "If fully done, reply with only: DONE (no tool call)."
                    ),
                    types.Part.from_bytes(
                        data=_b64.b64decode(img_b64),
                        mime_type="image/jpeg",
                    ),
                ])
            except Exception as e:
                print(f"[agent] ⚠️  Screenshot inject failed: {e}")
                current_message = _make_message(
                    "Screenshot captured. Analyze it and continue. "
                    "Call ONE tool only. If done, reply: DONE."
                )
        else:
            current_message = _make_message(
                f"Action '{tool_called}' completed. "
                f"Do ONLY what the original task asked — nothing more. "
                f"Call capture_screen() to verify, then continue ONE step at a time. "
                f"If fully done, reply with only: DONE (no tool call)."
            )

    try:
        await session_service.delete_session(
            app_name="ui_navigator", user_id="user", session_id=session.id,
        )
    except Exception:
        pass

    return _clean_response(final_response)

# ── Public Sync Wrapper ───────────────────────────────────────

_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def run_agent(command: str, use_vision: bool = True) -> str:
    def _in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run_agent_async(command))
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                stream_emit({"type": "done", "message": "⚠️ Rate limit reached. Please wait a minute and try again."})
                return "Rate limit reached. Please wait a minute and try again."
            if "1048576" in err or "token count exceeds" in err.lower():
                stream_emit({"type": "done", "message": "⚠️ Context limit hit. Please try a simpler command."})
                return "Context limit hit. Please try a simpler command."
            stream_emit({"type": "done", "message": f"⚠️ Error: {err[:120]}"})
            return f"Error: {err[:120]}"
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    return _thread_pool.submit(_in_thread).result()




























# import os
# import asyncio
# import base64
# import concurrent.futures
# from dotenv import load_dotenv

# from google.adk.agents import Agent
# from google.adk.runners import Runner
# from google.adk.sessions import InMemorySessionService
# from google.genai import types

# from tools import tools

# load_dotenv()

# BYE_WORDS = {"bye", "exit", "quit", "stop", "goodbye", "end", "close", "done"}

# SYSTEM_PROMPT = """
# You are a precise UI automation agent that controls a computer screen.
# You control the screen by calling tools. You CANNOT see the screen unless you call capture_screen() first.

#  ═══════════════
# UNDERSTAND THE TASK
#  ═══════════════
# When you receive a command, first break it into an ordered checklist.


# Examples:
# - "Open Old Navy" → navigate to oldnavy.com → DONE. Do NOT search for products.
# - "Open YouTube" → navigate to youtube.com → DONE. Do NOT play anything.


# Example: "Open a website and add a shoe to cart"
#   [ ] 1. Navigate to the website
#   [ ] 2. Find a shoe product
#   [ ] 3. Open the product page
#   [ ] 4. Click Add to Cart
#   [ ] 5. Confirm item is in cart

# After each action, tick off what is done and identify the next step.
# Do NOT do any unnecessary steps. For example, if the command is to open a website, TOP PRIORITY is to confirm the website is open in the screenshot. Do NOT search for products or click around — that is not part of the task.
# Do NOT try to do multiple steps at once. Do NOT move to the next step until the current one is visually confirmed as complete in the screenshot.

#  ═══════════════
# SCREENSHOT RULE — MOST IMPORTANT
#  ═══════════════
# - The screenshots you receive are scaled to a width of **1024 pixels**.
# - You MUST provide coordinates (x, y) based on this 1024px grid.
# - Do NOT guess the user's actual screen resolution. The tools handle the scaling for you.
# - Always use the most recent capture_screen() image for coordinates.

# Before EVERY action:
# 1. Call capture_screen() to see the current screen
# 2. Analyze what you see
# 3. Then call the action tool

# NEVER act without calling capture_screen() first.
# NEVER reuse coordinates from a previous screenshot.
# NEVER guess what is on screen.

#  ═══════════════
# CLICKING — COORDINATE PRECISION
#  ═══════════════
# The capture_screen() image pixels map 1:1 to click coordinates.
# Pixel at (x, y) in the image = click_at_position(x, y). No scaling.

# To click an element accurately:
# 1. Call capture_screen().
# 2. Find the target (button, link, field).
# 3. Identify its pixel boundaries in the 1024px image: [Left, Top, Right, Bottom].
# 4. Calculate the center: x = (Left + Right) / 2, y = (Top + Bottom) / 2.
# 5. Call click_at_position(x, y).
# 6. Call capture_screen() — confirm the result

# PRECISION TIPS:
# - Buttons: 30-50px tall — y center is the vertical midpoint
# - Links: ~20px tall — aim for vertical center, not top edge
# - Wrong click? Coordinates were off — re-examine edges more carefully
# - Click the button itself, not text outside its border


# WHEN TO USE EACH:
# - click_at_position(x, y)  → fast, good for large/obvious elements
# - capture_region() + click_at_position  → when element is small or crowded

# FORBIDDEN ZONE y < 80 (browser chrome):
# - y=44 or y=60 is ALWAYS a browser tab — never a webpage element
# - ALL webpage content starts at y >= 80
# - Tool BLOCKS clicks at y < 80 and returns an error


# WHEN STUCK

# If a button is greyed out or disabled (e.g. Add to Cart):
# - Look for a required selection first (size, color, quantity)
# - Click an available option, then try the button again

# If clicking same element twice with no change:
# - Call capture_screen() and pick a completely different approach


# YOUTUBE SHORTCUTS — use these, never click

# play/pause → play_pause()    | mute → mute()
# volume up → volume_up()      | volume down → volume_down()
# skip +10s → skip_forward()   | skip -10s → skip_backward()
# next → next_video()          | previous → previous_video()
# fullscreen → fullscreen()


# EXECUTION RULES — CRITICAL

# - Call EXACTLY ONE tool then stop and wait
# - Do NOT chain multiple tools in one response
# - Workflow: capture_screen → action → capture_screen → action → ...
# - When the full task is complete, reply with exactly: DONE
# - Never call a tool and say DONE in the same response


# CRITICAL CONSTRAINTS
# - DO NOT try to click, type, or search once the page is open.
# - DO NOT call any tool that is not in your list of tools.
# - Verify the screen shot and if its done, the task is finished.


# COMPLETION — VISUAL PROOF REQUIRED

# Call capture_screen() and confirm success before saying DONE.
# Never say DONE from memory or assumption.

# Add to cart — DONE only when screenshot shows:
#   - Cart icon with item count badge  (e.g. "1")
#   - OR "Added to Cart" / "Added to Basket" message
#   - OR cart page listing the product

# Any other task — result must be visible in the screenshot.

# Reply with exactly: DONE
# Never call a tool and say DONE in the same response.
# """

# # ── ADK Agent ─────────────────────────────────────────────────

# navigator_agent = Agent(
#     name="ui_navigator",
#     model="gemini-2.5-flash-lite",
#     description="Automates computer screen interactions using screenshots and tools.",
#     instruction=SYSTEM_PROMPT,
#     tools=tools,
# )

# session_service = InMemorySessionService()

# runner = Runner(
#     agent=navigator_agent,
#     app_name="ui_navigator",
#     session_service=session_service,
# )

# # ── Constants ─────────────────────────────────────────────────

# MAX_STEPS = 30

# # Navigation tools need longer wait for page load
# NAV_TOOLS = {
#     "open_url", "search_google", "open_google", "open_youtube",
#     "go_back_browser", "go_forward_browser", "refresh_page", "new_tab"
# }


# # ── Helpers ───────────────────────────────────────────────────

# def _make_message(text: str) -> types.Content:
#     """Plain text message — screenshots come from capture_screen() tool calls."""
#     return types.Content(role="user", parts=[types.Part.from_text(text=text)])


# def _make_first_message(command: str) -> types.Content:
#     """First message — plain text only. Agent calls capture_screen() as first action."""
#     return types.Content(role="user", parts=[types.Part.from_text(
#         text=f"Task: {command}\n\n"
#              f"Start by calling capture_screen() to see the current screen, "
#              f"then build your checklist and begin."
#     )])


# # ── Async core ────────────────────────────────────────────────

# async def _run_agent_async(command: str) -> str:

#     session = await session_service.create_session(
#         app_name="ui_navigator",
#         user_id="user",
#     )

#     final_response = ""
#     step = 0
#     last_tool = None
#     last_args = None
#     repeat_count = 0

#     current_message = _make_first_message(command)

#     for iteration in range(MAX_STEPS):
#         tool_called = None
#         tool_args = {}
#         is_done = False

#         print(f"[agent] 🔄 Turn {iteration + 1}")

#         async for event in runner.run_async(
#             user_id="user",
#             session_id=session.id,
#             new_message=current_message,
#         ):
#             author = getattr(event, "author", "?")
#             try:
#                 if (hasattr(event, "content") and event.content
#                         and hasattr(event.content, "parts") and event.content.parts):
#                     for part in event.content.parts:
#                         try:
#                             if hasattr(part, "function_call") and part.function_call:
#                                 if tool_called is None:
#                                     tool_called = part.function_call.name
#                                     tool_args = dict(part.function_call.args)
#                                 print(f"[step {step}] {author} → "
#                                       f"{part.function_call.name}"
#                                       f"({dict(part.function_call.args)})")
#                                 step += 1
#                             elif hasattr(part, "text") and part.text:
#                                 text = part.text.strip()
#                                 if text:
#                                     print(f"[step {step}] {author} → {text[:120]}")
#                                 if "DONE" in text.upper() and tool_called is None:
#                                     is_done = True
#                                     final_response = text
#                         except Exception:
#                             continue
#             except Exception:
#                 continue

#             try:
#                 if event.is_final_response():
#                     if event.content and event.content.parts:
#                         for part in event.content.parts:
#                             if part and hasattr(part, "text") and part.text:
#                                 final_response = part.text
#                                 if "DONE" in part.text.upper() and tool_called is None:
#                                     is_done = True
#             except Exception:
#                 pass

#         if is_done:
#             print(f"[agent] ✅ Task complete in {step} steps.")
#             break

#         if not tool_called:
#             print(f"[agent] ⏹️  No tool called — stopping.")
#             break

#         # Repeat loop detection (skip for capture_screen — it's always repeated)
#         if tool_called != "capture_screen":
#             current_sig = str(tool_args)
#             if tool_called == last_tool and current_sig == last_args:
#                 repeat_count += 1
#             else:
#                 repeat_count = 0
#                 last_tool = tool_called
#                 last_args = current_sig

#             if repeat_count >= 2:
#                 print(f"[agent] 🔁 Repeat on '{tool_called}' x{repeat_count + 1} — injecting hint")
#                 await asyncio.sleep(1.0)
#                 current_message = _make_message(
#                     f"WARNING: You are stuck in a loop. '{tool_called}' has been called "
#                     f"{repeat_count + 1} times with the same arguments and no progress. "
#                     f"STOP this approach entirely. Call capture_screen() and look carefully:\n"
#                     f"- Is y < 80? That is the tab bar — find the real element BELOW y=80\n"
#                     f"- Is there a popup or modal blocking the page?\n"
#                     f"- Is the button disabled — do you need to select size/color first?\n"
#                     f"Choose a completely different action."
#                 )
#                 repeat_count = 0
#                 last_tool = None
#                 last_args = None
#                 continue

#         # Longer wait for navigation tools so page fully loads
#         wait_time = 2.5 if tool_called in NAV_TOOLS else 1.0
#         await asyncio.sleep(wait_time)
#         print(f"[agent] ⏳ Waited {wait_time}s after '{tool_called}'")

#         current_message = _make_message(
#             f"Action '{tool_called}' completed. "
#             f"Continue with the next checklist step. "
#             f"Call capture_screen() to see the current state, then act. "
#             f"Reply DONE only when the task is fully complete with visual proof."
#         )

#     return final_response.strip() or "Command executed."


# # ── Public sync wrapper ───────────────────────────────────────

# _thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)


# def run_agent(command: str, use_vision: bool = True) -> str:
#     def _in_thread():
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             return loop.run_until_complete(_run_agent_async(command))
#         finally:
#             pending = asyncio.all_tasks(loop)
#             for task in pending:
#                 task.cancel()
#             if pending:
#                 loop.run_until_complete(
#                     asyncio.gather(*pending, return_exceptions=True)
#                 )
#             loop.close()

#     return _thread_pool.submit(_in_thread).result()








# import os
# import operator
# import logging
# import time
# from dotenv import load_dotenv
# from typing import TypedDict, Literal, Annotated
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, AnyMessage
# from langgraph.graph import StateGraph, START, END
# from langgraph.prebuilt import ToolNode
# from tools import youtube_tools, capture_screen_base64

# load_dotenv()

# # ── LangSmith observability ────────────────────────────────────
# # Set these in your .env file:
# #   LANGCHAIN_TRACING_V2=true
# #   LANGCHAIN_API_KEY=your-langsmith-key
# #   LANGCHAIN_PROJECT=youtube-agent
# os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "false"))
# os.environ.setdefault("LANGCHAIN_PROJECT",    os.getenv("LANGCHAIN_PROJECT", "youtube-agent"))

# # ── Logging setup ──────────────────────────────────────────────
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)-8s | %(message)s",
#     datefmt="%H:%M:%S"
# )
# log = logging.getLogger("agent")

# # ── State ─────────────────────────────────────────────────────
# class AgentState(TypedDict):
#     messages:   Annotated[list[AnyMessage], operator.add]
#     use_vision: bool
#     loop_count: int     # tracks how many times the loop has run

# # ── LLM ───────────────────────────────────────────────────────
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0,
#     google_api_key=os.getenv("GOOGLE_API_KEY")
# )
# llm_with_tools = llm.bind_tools(youtube_tools)

# SYSTEM_PROMPT = """You are a UI Navigator agent that controls a computer screen.

# You can SEE the screen via screenshots and execute actions using mouse/keyboard.

# CAPABILITIES:
# 1. Visual Understanding: Analyze screenshots to find UI elements
# 2. Precise Clicking: Use click_at_position(x, y) when you can see element coordinates
# 3. Keyboard Input: Use type_text() and press_key() for text entry
# 4. Quick YouTube: Use youtube shortcuts (play_pause, volume_up, etc.) when on YouTube

# WORKFLOW:
# - Look at the screenshot to understand what's on screen
# - Identify the element the user wants to interact with
# - Calculate approximate x,y coordinates based on what you see
# - Execute the appropriate action

# COORDINATE ESTIMATION:
# - Screen is typically 1920x1080 or similar
# - Top-left is (0,0), bottom-right is (width, height)
# - Estimate element centers based on their visual position
# - NEVER use coordinates near screen corners (avoid x<50, y<50, x>1870, y>1030)
# - Always aim for the CENTER of elements, never edges

# TOOL MAPPING for YouTube (use when on YouTube):
# - play / pause / resume         → play_pause
# - louder / volume up            → volume_up
# - quieter / volume down         → volume_down
# - mute                          → mute
# - fullscreen                    → fullscreen
# - skip forward / +10s           → skip_forward
# - skip back / -10s              → skip_backward
# - next video                    → next_video
# - previous video                → previous_video

# For general UI tasks use: click_at_position, type_text, scroll_screen, etc.

# CLICKING RULES:
# - Always click the CENTER of the element
# - For song titles/thumbnails, prefer clicking the TITLE TEXT not the image
# - If a click does not produce the expected result, try clicking slightly different coordinates
# - After clicking, always take a new screenshot to verify the action worked

# IMPORTANT VIDEO RULES:
# - After clicking a video thumbnail or title, the video will START PLAYING automatically
# - Do NOT call play_pause after clicking a video — it will pause the already-playing video
# - Only call play_pause if the user explicitly says "pause" or the video is visibly paused
# - A freshly clicked video = already playing = do NOT touch play_pause

# Always call a tool. Never reply with plain text only.
# """

# BYE_WORDS = {"bye", "exit", "quit", "stop", "goodbye", "end", "close", "done"}

# # ── Nodes ─────────────────────────────────────────────────────

# def agent_node(state: AgentState):
#     """Agent analyzes screen (if vision enabled) and picks an action."""
#     loop = state.get("loop_count", 0) + 1
#     messages = list(state["messages"])

#     log.info("─" * 50)
#     log.info(f"🤖 AGENT NODE  |  loop #{loop}")
#     log.info(f"   messages in state : {len(messages)}")
#     log.info(f"   vision enabled    : {state.get('use_vision', False)}")

#     # Vision: replace last HumanMessage with screenshot + text
#     if state.get("use_vision", False):
#         try:
#             t0 = time.time()
#             screenshot_b64 = capture_screen_base64()
#             log.info(f"   📸 screenshot captured in {time.time()-t0:.2f}s  ({len(screenshot_b64)//1024}KB)")

#             for i in range(len(messages) - 1, -1, -1):
#                 if isinstance(messages[i], HumanMessage):
#                     original_text = messages[i].content
#                     if isinstance(original_text, str):
#                         messages[i] = HumanMessage(content=[
#                             {"type": "text",      "text": f"Current screen state. User command: {original_text}"},
#                             {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
#                         ])
#                         log.info(f"   💬 injected screenshot into HumanMessage")
#                     break
#         except Exception as e:
#             log.warning(f"   ⚠️  screenshot failed: {e}")

#     # Call LLM
#     t0 = time.time()
#     log.info(f"   ⏳ calling Gemini...")
#     response = llm_with_tools.invoke(messages)
#     elapsed = time.time() - t0

#     # Log what the LLM decided
#     if hasattr(response, "tool_calls") and response.tool_calls:
#         tool_names = [tc["name"] for tc in response.tool_calls]
#         log.info(f"   ✅ LLM response in {elapsed:.2f}s → TOOL CALLS: {tool_names}")
#     else:
#         content_preview = str(response.content)[:80]
#         log.info(f"   ✅ LLM response in {elapsed:.2f}s → TEXT: '{content_preview}'")

#     return {
#         "messages":   [response],
#         "loop_count": loop
#     }


# def tool_node_wrapper(state: AgentState):
#     """Wrapper around ToolNode that adds logging."""
#     loop = state.get("loop_count", 0)
#     last = state["messages"][-1]

#     tool_calls = getattr(last, "tool_calls", [])
#     log.info("─" * 50)
#     log.info(f"🔧 TOOL NODE  |  loop #{loop}")

#     for tc in tool_calls:
#         log.info(f"   → executing tool : {tc['name']}")
#         log.info(f"     args           : {tc.get('args', {})}")

#     # Run actual tools
#     t0 = time.time()
#     result = _tool_node.invoke(state)
#     log.info(f"   ⏱  tools finished in {time.time()-t0:.2f}s")

#     # Log tool results
#     new_msgs = result.get("messages", [])
#     for msg in new_msgs:
#         content = getattr(msg, "content", "")
#         log.info(f"   ← tool result : '{content}'")

#     return result


# # ── Conditional edge ───────────────────────────────────────────

# def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
#     """Decide if we should continue the loop or stop based on whether the LLM made a tool call."""
#     last_message = state["messages"][-1]
#     loop = state.get("loop_count", 0)

#     if last_message.tool_calls:
#         log.info(f"   🔁 should_continue → tool_node  (loop #{loop})")
#         return "tool_node"

#     log.info(f"   🏁 should_continue → END  (loop #{loop}, total loops: {loop})")
#     return END


# # ── Build Graph ────────────────────────────────────────────────

# _tool_node = ToolNode(youtube_tools)   # internal — used by wrapper

# builder = StateGraph(AgentState)
# builder.add_node("agent",     agent_node)
# builder.add_node("tool_node", tool_node_wrapper)

# builder.add_edge(START, "agent")
# builder.add_conditional_edges(
#     "agent",
#     should_continue,
#     {"tool_node": "tool_node", END: END}
# )
# builder.add_edge("tool_node", "agent")

# graph = builder.compile()

# log.info("✅ LangGraph compiled successfully")
# log.info(f"   LangSmith tracing : {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
# log.info(f"   LangSmith project : {os.getenv('LANGCHAIN_PROJECT', 'youtube-agent')}")






