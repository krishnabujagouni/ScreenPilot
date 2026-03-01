import pyautogui
import webbrowser
from langchain_core.tools import tool


# ── YouTube Tools ──────────────────────────────────────────────

@tool
def open_youtube() -> str:
    """Open YouTube in the browser."""
    webbrowser.open("https://youtube.com")
    return "Opened YouTube"

@tool
def play_pause() -> str:
    """Play or pause the current YouTube video."""
    pyautogui.press("space")
    return "Toggled play/pause"

@tool
def volume_up() -> str:
    """Increase the YouTube video volume."""
    pyautogui.press("up")
    return "Volume increased"

@tool
def volume_down() -> str:
    """Decrease the YouTube video volume."""
    pyautogui.press("down")
    return "Volume decreased"

@tool
def mute() -> str:
    """Mute or unmute the YouTube video."""
    pyautogui.press("m")
    return "Toggled mute"

@tool
def fullscreen() -> str:
    """Toggle fullscreen mode on YouTube."""
    pyautogui.press("f")
    return "Toggled fullscreen"

@tool
def skip_forward() -> str:
    """Skip forward 10 seconds in the YouTube video."""
    pyautogui.press("l")
    return "Skipped forward 10s"

@tool
def skip_backward() -> str:
    """Skip backward 10 seconds in the YouTube video."""
    pyautogui.press("j")
    return "Skipped backward 10s"

@tool
def next_video() -> str:
    """Skip to the next video in the playlist or queue."""
    pyautogui.hotkey("shift", "n")
    return "Skipped to next video"

@tool
def previous_video() -> str:
    """Go back to the previous video."""
    pyautogui.hotkey("shift", "p")
    return "Went to previous video"


# ── Browser Tools ──────────────────────────────────────────────

# @tool
# def open_chrome() -> str:
#     """Open Google Chrome browser."""
#     import subprocess
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
#     return "Opened Chrome"
@tool
def open_google(query: str) -> str:
    """Search Google
    """
    webbrowser.open(f"https://www.google.com")
    return f"opened google search"


@tool
def search_google(query: str) -> str:
    """Search Google for a query in the browser.

    Args:
        query: the search term e.g. 'python tutorials'
    """
    webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
    return f"Searched Google for: {query}"

@tool
def open_url(url: str) -> str:
    """Open any specific URL in the browser.

    Args:
        url: the URL to open e.g. 'https://github.com'
    """
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened: {url}"

@tool
def new_tab() -> str:
    """Open a new tab in the browser."""
    pyautogui.hotkey("ctrl", "t")
    return "Opened new tab"

@tool
def close_tab() -> str:
    """Close the current browser tab."""
    pyautogui.hotkey("ctrl", "w")
    return "Closed tab"

@tool
def go_back_browser() -> str:
    """Go back to the previous page in the browser."""
    pyautogui.hotkey("alt", "left")
    return "Went back"

@tool
def go_forward_browser() -> str:
    """Go forward to the next page in the browser."""
    pyautogui.hotkey("alt", "right")
    return "Went forward"

@tool
def refresh_page() -> str:
    """Refresh the current page in the browser."""
    pyautogui.hotkey("ctrl", "r")
    return "Page refreshed"


# ── All tools ──────────────────────────────────────────────────

youtube_tools = [
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
    # Browser
    open_google,
    search_google,
    open_url,
    new_tab,
    close_tab,
    go_back_browser,
    go_forward_browser,
    refresh_page,
]

