# ⚡ ScreenPilot

**Natural language UI automation agent powered by Gemini 2.5 Flash + Google ADK**

> Google Hackathon Project  
> *Type a command. The agent sees your screen and acts.*

```
Browser Dashboard
      ↓ HTTP POST
FastAPI (local server)
      ↓
ADK Agent Loop
      ↓
Gemini 2.5 Flash via Vertex AI (sees screen + decides action)
      ↓
pyautogui (clicks, types, scrolls)
      ↓
Screen responds → screenshot → back to model
```

---

## ✨ Features

- 👁️ **Vision-based navigation** — Gemini sees your screen via screenshots after every action
- 🎯 **Precise clicking** — agent finds elements and clicks at exact coordinates
- ⌨️ **Natural language input** — type any plain English command
- 📡 **Live step streaming** — every tool call streams to the dashboard in real time via SSE
- 🔁 **Self-correction** — detects repeat loops and injects recovery hints automatically
- 🧹 **Context management** — prunes old screenshots to prevent token overflow on long tasks
- ⚡ **YouTube shortcuts** — media controls use keyboard shortcuts directly, no clicking
- 🔐 **Authentication** — HTTP Basic Auth on dashboard + token-based SSE stream

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│            Browser Dashboard                     │
│     (text input, live step stream via SSE)       │
└─────────────────────┬───────────────────────────┘
                      │ HTTP POST /control
                      ▼
┌─────────────────────────────────────────────────┐
│              FastAPI (local)                     │
│        /control  |  /stream (SSE)  |  /health   │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│           ADK Agent Loop                         │
│  ┌──────────────────────────────────────────┐   │
│  │  capture_screen → Gemini 2.5 Flash       │   │
│  │  (Vertex AI)   → tool call → wait →      │   │
│  │  capture_screen → verify → repeat        │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│                 pyautogui                        │
│    click(x,y) | type() | press() | scroll()     │
└─────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
screenpilot/
├── main.py           ← FastAPI server + SSE stream endpoint
├── agent.py          ← ADK agent loop + Vertex AI setup + streaming
├── tools.py          ← Screen capture + UI control tools
├── dashboard.html    ← Browser dashboard with live step stream
├── requirements.txt  ← Dependencies
└── .env              ← API keys and config (don't commit)
```

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/krishnabujagouni/ScreenPilot
cd ScreenPilot
python -m venv .venv
source .venv/bin/activate       # Mac/Linux
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure `.env`
```env
# Option A — Vertex AI (recommended)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True

# Option B — Gemini API key (fallback)
GOOGLE_API_KEY=your-gemini-api-key

# Dashboard auth
DASHBOARD_USER=admin
DASHBOARD_PASS=changeme
```

### 3. Authenticate with Google Cloud (if using Vertex AI)
```bash
gcloud auth application-default login
```

### 4. Find your IPv4 address
```bash
ipconfig        # Windows — look for IPv4 Address
ifconfig        # Mac/Linux — look for inet under en0 or eth0
```
Example: `192.168.1.100`

### 5. Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. Open dashboard
On any device connected to the **same WiFi network**, open:
```
http://<YOUR_IPv4>:8000
```
Example: `http://192.168.1.100:8000`

> **Note:** Both machines must be on the same WiFi. `localhost` only works on the machine running the server.

---

## 🎮 Usage

Type any plain English command in the dashboard:

- `"Open YouTube and play a lofi video"`
- `"Open Nike and add a shoe to cart"`
- `"Search for Python tutorials on Google"`
- `"Open Gmail and read the latest email"`

Watch the steps stream live as the agent works through the task.

### YouTube shortcuts (instant, no vision needed)
- `"pause"` → space key
- `"volume up"` → arrow up
- `"mute"` → M key
- `"fullscreen"` → F key
- `"skip forward"` → L key

---

## 🛠️ Tools

| Tool | Description |
|------|-------------|
| `capture_screen` | Triggers screenshot injection into model |
| `click_at_position(x, y)` | Click at coordinates |
| `double_click_at_position(x, y)` | Double-click |
| `type_text(text)` | Type text at cursor |
| `press_key(key)` | Press single key |
| `hotkey(keys)` | Keyboard shortcut e.g. `ctrl+a` |
| `select_all_and_type(x, y, text)` | Clear field and type |
| `scroll_screen(direction, amount)` | Scroll up/down |
| `scroll_at_position(x, y, direction)` | Scroll at specific position |
| `open_url(url)` | Open any URL |
| `search_google(query)` | Search Google |
| `open_youtube()` | Open YouTube |
| `new_tab()` | Open new browser tab |
| `go_back_browser()` | Browser back |
| `refresh_page()` | Refresh page |
| `play_pause / mute / volume_up / volume_down` | YouTube shortcuts |
| `skip_forward / skip_backward` | YouTube seek |
| `next_video / previous_video / fullscreen` | YouTube navigation |

---

## 🔧 Tech Stack

| Technology | Role |
|---|---|
| [Google ADK](https://google.github.io/adk-docs/) | Agent loop, tool registration, session management |
| [Gemini 2.5 Flash](https://deepmind.google/gemini/) | Multimodal vision + reasoning |
| [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) | Model inference API |
| [FastAPI](https://fastapi.tiangolo.com) | Local REST API + SSE streaming |
| [pyautogui](https://pyautogui.readthedocs.io) | Mouse, keyboard, screen capture |
| [Pillow](https://pillow.readthedocs.io) | Screenshot resizing + JPEG compression |

---

## 🐛 Troubleshooting

**Can't reach dashboard from another device**
- Make sure both devices are on the same WiFi network
- Use your machine's IPv4 address, not `localhost`
- Windows firewall — allow port 8000:
  ```
  netsh advfirewall firewall add rule name="ScreenPilot" dir=in action=allow protocol=TCP localport=8000
  ```

**Vertex AI not receiving requests**
- Confirm `GOOGLE_GENAI_USE_VERTEXAI=True` is in `.env`
- Run `gcloud auth application-default login`
- Enable the API: `gcloud services enable aiplatform.googleapis.com`

**Agent says DONE too early**
- The model occasionally batches tool calls despite prompt instructions — retry the command

**Screenshots not working**
- Locally make sure the screen is not locked

**Rate limit errors**
- The agent retries automatically with exponential backoff up to 5 times
- If persistent, wait 60 seconds and retry

**Dashboard password prompt keeps appearing**
- Enter the value set in `DASHBOARD_PASS` in your `.env` (default: `changeme`)


## 🧪 Reproducible Testing

### Prerequisites
- Python 3.11+
- A physical display (not headless) — pyautogui requires a screen
- Google Cloud account with Vertex AI API enabled, OR a Gemini API key

### Steps to reproduce

1. **Clone the repo**
```bash
git clone https://github.com/krishnabujagouni/ScreenPilot
cd ScreenPilot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and fill in your credentials
```

4. **Authenticate with Google Cloud**
```bash
gcloud auth application-default login
```

5. **Run the server**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

6. **Open the dashboard**
Find your IPv4 address:
```bash
ipconfig    # Windows
ifconfig    # Mac/Linux
```
Open in browser: `http://<YOUR_IPv4>:8000`

7. **Test a command**
Type in the dashboard:
```
Open YouTube and play a lofi video
```
Expected: agent opens YouTube, finds a video, clicks it, confirms it's playing, returns DONE.

### Verify Vertex AI is being used
Check the terminal — you should see:
```
[agent] ☁️  Vertex AI — project=your-project, model=gemini-2.5-flash
```
---