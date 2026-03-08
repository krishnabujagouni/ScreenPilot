
# import time
# import pyautogui
# import webbrowser
# import subprocess
# from langchain_core.tools import tool
# import base64
# from io import BytesIO

# # ── Safety ────────────────────────────────────────────────────
# pyautogui.FAILSAFE = False
# pyautogui.PAUSE = 0.1

# def safe_coords(x: int, y: int):
#     """Clamp coordinates away from screen edges and corners."""
#     screen_w, screen_h = pyautogui.size()
#     x = max(50, min(x, screen_w - 50))
#     y = max(50, min(y, screen_h - 50))
#     return x, y


# # ── Screen Capture ─────────────────────────────────────────────
# def capture_screen_base64() -> str:
#     """Capture the current screen and return as base64 PNG."""
#     screenshot = pyautogui.screenshot()
#     buffer = BytesIO()
#     screenshot.save(buffer, format="PNG")
#     return base64.b64encode(buffer.getvalue()).decode()


# # ── Click Tools ────────────────────────────────────────────────

# @tool
# def click_at_position(x: int, y: int) -> str:
#     """Click at specific x,y screen coordinates.

#     Args:
#         x: horizontal position from left edge
#         y: vertical position from top edge
#     """
#     # Move slowly so the OS registers the focus change
#     pyautogui.moveTo(x, y, duration=0.4)
#     time.sleep(0.2)   # wait for hover state
#     pyautogui.click()
#     time.sleep(0.3)   # wait for UI to react
#     return f"Clicked at ({x}, {y})"


# @tool
# def double_click_at_position(x: int, y: int) -> str:
#     """Double-click at specific x,y coordinates.

#     Args:
#         x: horizontal position from left edge
#         y: vertical position from top edge
#     """
#     pyautogui.moveTo(x, y, duration=0.4)
#     time.sleep(0.2)
#     pyautogui.doubleClick()
#     time.sleep(0.3)
#     return f"Double-clicked at ({x}, {y})"


# @tool
# def move_and_click(x: int, y: int, offset_x: int = 0, offset_y: int = 0) -> str:
#     """Move to position with optional offset and click. Use when click_at_position misses.

#     Args:
#         x: base horizontal position
#         y: base vertical position
#         offset_x: horizontal adjustment (positive = right, negative = left)
#         offset_y: vertical adjustment (positive = down, negative = up)
#     """
#     final_x = x + offset_x
#     final_y = y + offset_y
#     pyautogui.moveTo(final_x, final_y, duration=0.4)
#     time.sleep(0.2)
#     pyautogui.click()
#     time.sleep(0.3)
#     return f"Clicked at ({final_x}, {final_y}) [base=({x},{y}) offset=({offset_x},{offset_y})]"


# # ── Keyboard Tools ─────────────────────────────────────────────

# @tool
# def type_text(text: str) -> str:
#     """Type text using the keyboard.

#     Args:
#         text: the text to type
#     """
#     pyautogui.write(text, interval=0.05)
#     return f"Typed: {text}"


# @tool
# def press_key(key: str) -> str:
#     """Press a single keyboard key.

#     Args:
#         key: key name like 'enter', 'tab', 'escape', 'backspace'
#     """
#     pyautogui.press(key)
#     return f"Pressed: {key}"


# @tool
# def hotkey(key1: str, key2: str) -> str:
#     """Press a keyboard shortcut (two keys together).

#     Args:
#         key1: first key e.g. 'ctrl'
#         key2: second key e.g. 't'
#     """
#     pyautogui.hotkey(key1, key2)
#     return f"Pressed: {key1}+{key2}"


# @tool
# def scroll_screen(direction: str, amount: int = 5) -> str:
#     """Scroll the screen up or down.

#     Args:
#         direction: 'up' or 'down'
#         amount: number of scroll clicks (default 5)
#     """
#     clicks = amount if direction == "up" else -amount
#     pyautogui.scroll(clicks)
#     return f"Scrolled {direction} by {amount}"


# @tool
# def wait_seconds(seconds: int = 1) -> str:
#     """Wait for a number of seconds for UI to load.

#     Args:
#         seconds: how long to wait (default 1)
#     """
#     time.sleep(seconds)
#     return f"Waited {seconds} second(s)"


# # ── YouTube Tools ──────────────────────────────────────────────

# @tool
# def open_youtube() -> str:
#     """Open YouTube in the browser."""
#     webbrowser.open("https://youtube.com")
#     time.sleep(2)
#     return "Opened YouTube"


# @tool
# def play_pause() -> str:
#     """Play or pause the current YouTube video."""
#     pyautogui.press("k")
#     return "Toggled play/pause"


# @tool
# def volume_up() -> str:
#     """Increase the YouTube video volume."""
#     for _ in range(3):
#         pyautogui.press("up")
#         time.sleep(0.05)
#     return "Volume increased"


# @tool
# def volume_down() -> str:
#     """Decrease the YouTube video volume."""
#     for _ in range(3):
#         pyautogui.press("down")
#         time.sleep(0.05)
#     return "Volume decreased"


# @tool
# def mute() -> str:
#     """Mute or unmute the YouTube video."""
#     pyautogui.press("m")
#     return "Toggled mute"


# @tool
# def fullscreen() -> str:
#     """Toggle fullscreen mode on YouTube."""
#     pyautogui.press("f")
#     return "Toggled fullscreen"


# @tool
# def skip_forward() -> str:
#     """Skip forward 10 seconds in the YouTube video."""
#     pyautogui.press("l")
#     return "Skipped forward 10s"


# @tool
# def skip_backward() -> str:
#     """Skip backward 10 seconds in the YouTube video."""
#     pyautogui.press("j")
#     return "Skipped backward 10s"


# @tool
# def next_video() -> str:
#     """Skip to the next video in the playlist or queue."""
#     pyautogui.hotkey("shift", "n")
#     return "Skipped to next video"


# @tool
# def previous_video() -> str:
#     """Go back to the previous video."""
#     pyautogui.hotkey("shift", "p")
#     return "Went to previous video"


# # ── Browser Tools ──────────────────────────────────────────────

# @tool
# def open_chrome() -> str:
#     """Open Google Chrome browser."""
#     try:
#         subprocess.Popen(["chrome"])
#     except FileNotFoundError:
#         for path in [
#             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
#             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
#         ]:
#             try:
#                 subprocess.Popen([path])
#                 break
#             except FileNotFoundError:
#                 continue
#     time.sleep(1.5)
#     return "Opened Chrome"


# @tool
# def search_google(query: str) -> str:
#     """Search Google for a query in the browser.

#     Args:
#         query: the search term e.g. 'python tutorials'
#     """
#     webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
#     return f"Searched Google for: {query}"


# @tool
# def open_url(url: str) -> str:
#     """Open any specific URL in the browser.

#     Args:
#         url: the URL to open e.g. 'https://github.com'
#     """
#     if not url.startswith("http"):
#         url = "https://" + url
#     webbrowser.open(url)
#     time.sleep(1)
#     return f"Opened: {url}"


# @tool
# def new_tab() -> str:
#     """Open a new tab in the browser."""
#     pyautogui.hotkey("ctrl", "t")
#     return "Opened new tab"


# @tool
# def close_tab() -> str:
#     """Close the current browser tab."""
#     pyautogui.hotkey("ctrl", "w")
#     return "Closed tab"


# @tool
# def go_back_browser() -> str:
#     """Go back to the previous page in the browser."""
#     pyautogui.hotkey("alt", "left")
#     return "Went back"


# @tool
# def go_forward_browser() -> str:
#     """Go forward to the next page in the browser."""
#     pyautogui.hotkey("alt", "right")
#     return "Went forward"


# @tool
# def refresh_page() -> str:
#     """Refresh the current page in the browser."""
#     pyautogui.hotkey("ctrl", "r")
#     return "Page refreshed"


# # ── All tools ──────────────────────────────────────────────────

# youtube_tools = [
#     # Click / keyboard
#     click_at_position,
#     double_click_at_position,
#     move_and_click,
#     type_text,
#     press_key,
#     hotkey,
#     scroll_screen,
#     wait_seconds,
#     # YouTube
#     open_youtube,
#     play_pause,
#     volume_up,
#     volume_down,
#     mute,
#     fullscreen,
#     skip_forward,
#     skip_backward,
#     next_video,
#     previous_video,
#     # Browser
#     open_chrome,
#     search_google,
#     open_url,
#     new_tab,
#     close_tab,
#     go_back_browser,
#     go_forward_browser,
#     refresh_page,
# ]


# import pyautogui
# import webbrowser
# import base64
# import time
# from io import BytesIO

# # ── Safety Settings ───────────────────────────────────────────

# pyautogui.FAILSAFE = True
# pyautogui.PAUSE = 0.2  # reduced from 0.3 for faster execution


# # ── Screen Capture ────────────────────────────────────────────

# def capture_screen_base64() -> str:
#     """Capture the current screen and return as base64 PNG string."""
#     screenshot = pyautogui.screenshot()
#     buffer = BytesIO()
#     screenshot.save(buffer, format="PNG")
#     return base64.b64encode(buffer.getvalue()).decode()


# def capture_screen() -> str:
#     """Capture a screenshot of the current screen for visual analysis."""
#     capture_screen_base64()
#     return "Screenshot captured."


# # ── Mouse Control ─────────────────────────────────────────────

# def click_at_position(x: int, y: int) -> str:
#     """Click at the CENTER of a UI element at the given screen coordinates.

#     Args:
#         x: horizontal center coordinate of the target element
#         y: vertical center coordinate of the target element
#     """
#     pyautogui.moveTo(x, y, duration=0.2)
#     time.sleep(0.1)
#     pyautogui.click(x, y)  # pass coords directly — no offset, no drift
#     return f"Clicked at ({x}, {y})"


# def double_click_at_position(x: int, y: int) -> str:
#     """Double-click at the CENTER of a UI element at the given screen coordinates.

#     Args:
#         x: horizontal center coordinate of the target element
#         y: vertical center coordinate of the target element
#     """
#     pyautogui.moveTo(x, y, duration=0.2)
#     time.sleep(0.1)
#     pyautogui.doubleClick(x, y)
#     return f"Double-clicked at ({x}, {y})"


# def click_center(x1: int, y1: int, x2: int, y2: int) -> str:
#     """Click the center of a bounding box defined by its four corners.
#     Use this when you know the bounding box but not the center.

#     Args:
#         x1: left edge of the element
#         y1: top edge of the element
#         x2: right edge of the element
#         y2: bottom edge of the element
#     """
#     cx = int((x1 + x2) / 2)
#     cy = int((y1 + y2) / 2)
#     pyautogui.moveTo(cx, cy, duration=0.2)
#     time.sleep(0.1)
#     pyautogui.click(cx, cy)
#     return f"Clicked center at ({cx}, {cy})"


# def move_mouse(x: int, y: int) -> str:
#     """Move the mouse to a position without clicking.

#     Args:
#         x: horizontal position
#         y: vertical position
#     """
#     pyautogui.moveTo(x, y, duration=0.2)
#     return f"Moved mouse to ({x}, {y})"


# def scroll_screen(direction: str, amount: int = 5) -> str:
#     """Scroll the screen up or down at the current mouse position.

#     Args:
#         direction: 'up' or 'down'
#         amount: number of scroll ticks, default 5
#     """
#     clicks = amount if direction == "up" else -amount
#     pyautogui.scroll(clicks)
#     return f"Scrolled {direction} by {amount}"


# def scroll_at_position(x: int, y: int, direction: str, amount: int = 5) -> str:
#     """Scroll at a specific screen position — useful for scrolling inside a panel or list.

#     Args:
#         x: horizontal position to scroll at
#         y: vertical position to scroll at
#         direction: 'up' or 'down'
#         amount: number of scroll ticks, default 5
#     """
#     pyautogui.moveTo(x, y, duration=0.2)
#     clicks = amount if direction == "up" else -amount
#     pyautogui.scroll(clicks)
#     return f"Scrolled {direction} at ({x}, {y}) by {amount}"


# def wait(seconds: int) -> str:
#     """Wait for UI elements to load or animations to finish.

#     Args:
#         seconds: number of seconds to wait
#     """
#     time.sleep(seconds)
#     return f"Waited {seconds} seconds"


# # ── Keyboard ──────────────────────────────────────────────────

# def type_text(text: str) -> str:
#     """Type text at the current cursor position.
#     Always click the target input field first before calling this.

#     Args:
#         text: the text to type
#     """
#     pyautogui.write(text, interval=0.05)
#     return f"Typed: {text}"


# def press_key(key: str) -> str:
#     """Press a single keyboard key.

#     Args:
#         key: key name e.g. 'enter', 'tab', 'escape', 'backspace', 'space'
#     """
#     pyautogui.press(key)
#     return f"Pressed: {key}"


# def hotkey(keys: str) -> str:
#     """Press a keyboard shortcut combination.

#     Args:
#         keys: keys joined by '+' e.g. 'ctrl+c', 'ctrl+a', 'alt+tab', 'ctrl+shift+t'
#     """
#     parts = [k.strip() for k in keys.split("+")]
#     pyautogui.hotkey(*parts)
#     return f"Hotkey: {keys}"


# def select_all_and_type(x: int, y: int, text: str) -> str:
#     """Click a field, select all existing text, and replace it with new text.
#     Use this to clear and retype in input fields.

#     Args:
#         x: horizontal center of the input field
#         y: vertical center of the input field
#         text: the new text to type
#     """
#     pyautogui.click(x, y)
#     time.sleep(0.2)
#     pyautogui.hotkey("ctrl", "a")
#     time.sleep(0.1)
#     pyautogui.write(text, interval=0.05)
#     return f"Cleared and typed '{text}' at ({x}, {y})"


# # ── YouTube Controls ──────────────────────────────────────────

# def open_youtube() -> str:
#     """Open YouTube in the default browser."""
#     webbrowser.open("https://youtube.com")
#     return "Opened YouTube"


# def play_pause() -> str:
#     """Toggle play or pause on the current YouTube video."""
#     pyautogui.press("space")
#     return "Toggled play/pause"


# def volume_up() -> str:
#     """Increase the YouTube video volume."""
#     pyautogui.press("up")
#     return "Volume increased"


# def volume_down() -> str:
#     """Decrease the YouTube video volume."""
#     pyautogui.press("down")
#     return "Volume decreased"


# def mute() -> str:
#     """Mute or unmute the current YouTube video."""
#     pyautogui.press("m")
#     return "Toggled mute"


# def fullscreen() -> str:
#     """Toggle fullscreen mode on YouTube."""
#     pyautogui.press("f")
#     return "Toggled fullscreen"


# def skip_forward() -> str:
#     """Skip forward 10 seconds in the YouTube video."""
#     pyautogui.press("l")
#     return "Skipped forward 10 seconds"


# def skip_backward() -> str:
#     """Skip backward 10 seconds in the YouTube video."""
#     pyautogui.press("j")
#     return "Skipped backward 10 seconds"


# def next_video() -> str:
#     """Skip to the next video in the YouTube playlist or queue."""
#     pyautogui.hotkey("shift", "n")
#     return "Next video"


# def previous_video() -> str:
#     """Go back to the previous video in the YouTube playlist."""
#     pyautogui.hotkey("shift", "p")
#     return "Previous video"


# # ── Browser Controls ──────────────────────────────────────────

# def open_google() -> str:
#     """Open the Google homepage in the browser."""
#     webbrowser.open("https://www.google.com")
#     return "Opened Google"


# def search_google(query: str) -> str:
#     """Search Google for a query and open results in the browser.

#     Args:
#         query: the search term to look up
#     """
#     webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
#     return f"Searched Google for: {query}"


# def open_url(url: str) -> str:
#     """Open any URL in the browser.

#     Args:
#         url: the full URL to open e.g. https://github.com
#     """
#     if not url.startswith("http"):
#         url = "https://" + url
#     webbrowser.open(url)
#     return f"Opened: {url}"


# def new_tab() -> str:
#     """Open a new tab in the browser."""
#     pyautogui.hotkey("ctrl", "t")
#     return "Opened new tab"


# def close_tab() -> str:
#     """Close the current browser tab."""
#     pyautogui.hotkey("ctrl", "w")
#     return "Closed tab"


# def go_back_browser() -> str:
#     """Go back to the previous page in the browser."""
#     pyautogui.hotkey("alt", "left")
#     return "Went back"


# def go_forward_browser() -> str:
#     """Go forward to the next page in the browser."""
#     pyautogui.hotkey("alt", "right")
#     return "Went forward"


# def refresh_page() -> str:
#     """Refresh the current page in the browser."""
#     pyautogui.hotkey("ctrl", "r")
#     return "Page refreshed"


# # ── Master Tool List ──────────────────────────────────────────

# tools = [
#     # Screen
#     capture_screen,
#     # Mouse
#     click_at_position,
#     double_click_at_position,
#     click_center,
#     move_mouse,
#     scroll_screen,
#     scroll_at_position,
#     wait,
#     # Keyboard tools removed — agent uses clicking and shortcuts only
#     # Browser
#     open_google,
#     search_google,
#     open_url,
#     new_tab,
#     close_tab,
#     go_back_browser,
#     go_forward_browser,
#     refresh_page,
#     # YouTube
#     open_youtube,
#     play_pause,
#     volume_up,
#     volume_down,
#     mute,
#     fullscreen,
#     skip_forward,
#     skip_backward,
#     next_video,
#     previous_video,
# ]




import pyautogui
import webbrowser
import base64
import time
import tempfile
import os
from io import BytesIO
from PIL import Image
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("[tools] cv2 not installed — template matching disabled. Run: pip install opencv-python numpy")

# ── Safety Settings ───────────────────────────────────────────

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2  # reduced from 0.3 for faster execution

VISION_WIDTH = 1024



def _get_screen_info():
    """Returns actual screen size and the scaling factor used for vision."""
    real_w, real_h = pyautogui.size()
    scale = VISION_WIDTH / float(real_w)
    return real_w, real_h, scale

# ── Optimized Tools ───────────────────────────────────────────

def capture_screen() -> str:
    """Signal to capture the current screen state. 
    Always call this before clicking or making decisions."""
    return "Screenshot requested."


def capture_screen_base64() -> str:
    """Capture screen at EXACT click resolution — no scaling artifacts."""
    screen_w, screen_h = pyautogui.size()
    # Take screenshot and resize to match exact pyautogui coordinate space
    screenshot = pyautogui.screenshot()
    if screenshot.size != (screen_w, screen_h):
        from PIL import Image
        screenshot = screenshot.resize((screen_w, screen_h), Image.LANCZOS)
    buffer = BytesIO()
    screenshot.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


# def capture_screen() -> dict:
#     """Capture a screenshot of the current screen.
#     Returns the screen as an image the model can see and analyze.
#     Use this before every click, scroll, or decision.
#     """
#     try:
#         screen_w, screen_h = pyautogui.size()
#         screenshot = pyautogui.screenshot()
#         # Resize to match exact pyautogui coordinate space (fixes DPI scaling)
#         if screenshot.size != (screen_w, screen_h):
#             from PIL import Image
#             screenshot = screenshot.resize((screen_w, screen_h), Image.LANCZOS)
#         buffer = BytesIO()
#         screenshot.save(buffer, format="PNG")
#         return {
#             "type": "image",
#             "data": base64.b64encode(buffer.getvalue()).decode(),
#             "mime_type": "image/png",
#         }
#     except Exception as e:
        # return {"error": str(e)}


def click_at_position(x: int, y: int) -> str:
    """Click at the CENTER of a UI element at the given screen coordinates.

    Coordinates must come directly from the most recent capture_screen() image.
    The image pixels map 1:1 to screen coordinates — no scaling needed.

    Args:
        x: horizontal center coordinate of the target element
        y: vertical center coordinate of the target element
    """
    screen_w, screen_h = pyautogui.size()

    # Hard guard — tab bar
    if y < 80:
        return (
            f"BLOCKED: y={y} is inside the browser tab bar (y < 80). "
            f"Scroll the page or find the element below y=80."
        )
    # Hard guard — off screen
    if x < 0 or x > screen_w or y > screen_h:
        return (
            f"BLOCKED: ({x}, {y}) is outside screen bounds {screen_w}x{screen_h}. "
            f"Re-check coordinates from the latest capture_screen() image."
        )

    # Move first so mouse is visible, then click
    pyautogui.moveTo(x, y, duration=0.3)
    time.sleep(0.15)
    pyautogui.click(x, y)
    time.sleep(0.1)

    # Return context so model knows exactly what happened
    return (
        f"Clicked at ({x}, {y}). "
        f"Call capture_screen() to verify the result."
    )


def double_click_at_position(x: int, y: int) -> str:
    """Double-click at the CENTER of a UI element at the given screen coordinates.

    Args:
        x: horizontal center coordinate of the target element
        y: vertical center coordinate of the target element
    """
    pyautogui.moveTo(x, y, duration=0.2)
    time.sleep(0.1)
    pyautogui.doubleClick(x, y)
    return f"Double-clicked at ({x}, {y})"







def scroll_screen(direction: str, amount: int = 7) -> str:
    """Scroll the screen up or down at the current mouse position.

    Args:
        direction: 'up' or 'down'
        amount: number of scroll ticks, default 7
    """
    clicks = amount if direction == "up" else -amount
    pyautogui.scroll(clicks)
    return f"Scrolled {direction} by {amount}"





def wait(seconds: int) -> str:
    """Wait for UI elements to load or animations to finish.

    Args:
        seconds: number of seconds to wait
    """
    time.sleep(seconds)
    return f"Waited {seconds} seconds"


# ── Keyboard ──────────────────────────────────────────────────

def type_text(text: str) -> str:
    """Type text at the current cursor position.
    Always click the target input field first before calling this.

    Args:
        text: the text to type
    """
    pyautogui.write(text, interval=0.05)
    return f"Typed: {text}"


def press_key(key: str) -> str:
    """Press a single keyboard key.

    Args:
        key: key name e.g. 'enter', 'tab', 'escape', 'backspace', 'space'
    """
    pyautogui.press(key)
    return f"Pressed: {key}"


def hotkey(keys: str) -> str:
    """Press a keyboard shortcut combination.

    Args:
        keys: keys joined by '+' e.g. 'ctrl+c', 'ctrl+a', 'alt+tab', 'ctrl+shift+t'
    """
    parts = [k.strip() for k in keys.split("+")]
    pyautogui.hotkey(*parts)
    return f"Hotkey: {keys}"


def select_all_and_type(x: int, y: int, text: str) -> str:
    """Click a field, select all existing text, and replace it with new text.
    Use this to clear and retype in input fields.

    Args:
        x: horizontal center of the input field
        y: vertical center of the input field
        text: the new text to type
    """
    pyautogui.click(x, y)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.write(text, interval=0.05)
    return f"Cleared and typed '{text}' at ({x}, {y})"


# ── YouTube Controls ──────────────────────────────────────────

def open_youtube() -> str:
    """Open YouTube in the default browser."""
    webbrowser.open("https://youtube.com")
    return "Opened YouTube"


def play_pause() -> str:
    """Toggle play or pause on the current YouTube video."""
    pyautogui.press("space")
    return "Toggled play/pause"


def volume_up() -> str:
    """Increase the YouTube video volume."""
    pyautogui.press("up")
    return "Volume increased"


def volume_down() -> str:
    """Decrease the YouTube video volume."""
    pyautogui.press("down")
    return "Volume decreased"


def mute() -> str:
    """Mute or unmute the current YouTube video."""
    pyautogui.press("m")
    return "Toggled mute"


def fullscreen() -> str:
    """Toggle fullscreen mode on YouTube."""
    pyautogui.press("f")
    return "Toggled fullscreen"


def skip_forward() -> str:
    """Skip forward 10 seconds in the YouTube video."""
    pyautogui.press("l")
    return "Skipped forward 10 seconds"


def skip_backward() -> str:
    """Skip backward 10 seconds in the YouTube video."""
    pyautogui.press("j")
    return "Skipped backward 10 seconds"


def next_video() -> str:
    """Skip to the next video in the YouTube playlist or queue."""
    pyautogui.hotkey("shift", "n")
    return "Next video"


def previous_video() -> str:
    """Go back to the previous video in the YouTube playlist."""
    pyautogui.hotkey("shift", "p")
    return "Previous video"


# ── Browser Controls ──────────────────────────────────────────



def search_google(query: str) -> str:
    """Search Google for a query and open results in the browser.

    Args:
        query: the search term to look up
    """
    webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
    return f"Searched Google for: {query}"


def open_url(url: str) -> str:
    """Open any URL in the browser.

    Args:
        url: the full URL to open e.g. https://github.com
    """
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened: {url}"


def new_tab() -> str:
    """Open a new tab in the browser."""
    pyautogui.hotkey("ctrl", "t")
    return "Opened new tab"


def close_tab() -> str:
    """Close the current browser tab."""
    pyautogui.hotkey("ctrl", "w")
    return "Closed tab"


def go_back_browser() -> str:
    """Go back to the previous page in the browser."""
    pyautogui.hotkey("alt", "left")
    return "Went back"





def refresh_page() -> str:
    """Refresh the current page in the browser."""
    pyautogui.hotkey("ctrl", "r")
    return "Page refreshed"


# ── Master Tool List ──────────────────────────────────────────

tools = [
    capture_screen,
        # ← add this
    # capture_region,      # ← add this  
    # click_image,
    # Mouse
    click_at_position,
    double_click_at_position,
    
    
    scroll_screen,
    
    wait,
    # Keyboard tools removed — agent uses clicking and shortcuts only
    type_text,
    press_key,
    hotkey,
    select_all_and_type,
    # Browser
    
    search_google,
    open_url,
    new_tab,
    close_tab,
    go_back_browser,
    
    refresh_page,
    # YouTube
    open_youtube,
    play_pause,
    volume_up,
    volume_down,
    mute,
    fullscreen,
    skip_forward,
    skip_backward,
    next_video,
    previous_video,
]