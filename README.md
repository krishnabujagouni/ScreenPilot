# 🎬 YouTube Laptop Agent

Control your laptop's YouTube and browser from your phone using **voice or text** — powered by LangGraph + GPT-4o.

```
Phone (voice/text)
      ↓
FastAPI Server (laptop)
      ↓
LangGraph Agent (GPT-4o decides)
      ↓
Tools (pyautogui / webbrowser)
      ↓
YouTube / Chrome executes
```

---

## Features

- 🎤 **Voice control** — speak commands from your phone browser
- ⌨️ **Text control** — type anything natural
- 🤖 **AI-powered** — GPT-4o understands variations like *"make it louder"*, *"go back a bit"*
- 📱 **Phone UI** — open in any phone browser, no app install
- 🔁 **Agent loop** — LangGraph ReAct loop with conditional routing
- 🌐 **Browser control** — open URLs, search Google, manage tabs

---

## Project Structure

```
laptop-agent/
├── main.py          ← FastAPI server + request handling
├── agent.py         ← LangGraph graph (nodes + edges)
├── tools.py         ← pyautogui tool functions
├── ui.html          ← Phone web UI (voice + buttons)
├── .env             ← OpenAI API key (never commit this)
└── requirements.txt ← Dependencies
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/laptop-agent.git
cd laptop-agent
```

### 2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your OpenAI API key
Create a `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

### 5. Run the server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. Open on your phone
Find your laptop IP:
```bash
ipconfig   # Windows — look for IPv4 under Wi-Fi
```
Then open on your phone browser:
```
http://<YOUR_LAPTOP_IP>:8000
```

> ⚠️ Phone and laptop must be on the same WiFi network.

---

## Agent Architecture

```
START
  ↓
[agent] ← GPT-4o reads command, decides tool
  ↓
should_continue()       ← single conditional edge
  ├── tool_calls? → [tool_node] → [agent]   ← loop
  └── no tool?   → END
```

The agent decides everything — no if/else string matching. GPT-4o either makes a tool call (routes to tools) or doesn't (routes to END).

---

## Supported Commands

### YouTube
| Say | Action |
|-----|--------|
| pause / hold on / stop | Pause video |
| play / resume / unpause | Play video |
| louder / volume up / turn it up | Increase volume |
| quieter / volume down / lower | Decrease volume |
| mute / silence | Toggle mute |
| fullscreen / big screen | Toggle fullscreen |
| skip / forward / +10 | Skip forward 10s |
| back / rewind / -10 | Skip back 10s |
| next video | Next in playlist |
| previous video | Previous video |
| open youtube | Open YouTube |

### Browser
| Say | Action |
|-----|--------|
| open chrome | Launch Chrome |
| search [query] | Google search |
| open [url] / go to [url] | Open any URL |
| new tab | Open new tab |
| close tab | Close current tab |
| refresh / reload | Refresh page |
| go back | Browser back |
| go forward | Browser forward |

### Session
| Say | Action |
|-----|--------|
| bye / exit / quit / stop | End session |

---

## API

### POST `/control`
Send a command to the agent.

**Request:**
```json
{ "text": "pause the video" }
```

**Response:**
```json
{ "status": "ok", "command": "pause the video", "result": "Toggled play/pause" }
```

**Bye response:**
```json
{ "status": "bye", "command": "bye", "result": "👋 Goodbye! Send a command anytime to start again." }
```

### GET `/health`
```json
{ "status": "running", "agent": "LangGraph + GPT-4o" }
```

---

## Requirements

```
fastapi
uvicorn
pyautogui
langchain-openai
langgraph
langchain-core
python-dotenv
```

---

## Troubleshooting

**Phone can't reach server**
- Make sure phone and laptop are on the same WiFi
- Run as Administrator: `netsh advfirewall firewall add rule name="FastAPI 8000" dir=in action=allow protocol=TCP localport=8000`

**Commands not working**
- Make sure YouTube is open and focused in the browser before sending commands

**Voice not working on phone**
- Use Chrome browser on Android
- Allow microphone permission when prompted

**OpenAI errors**
- Check your `.env` file has a valid `OPENAI_API_KEY`
- Make sure there are no spaces or quotes around the key

---

## Tech Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — agent graph framework
- **[LangChain OpenAI](https://github.com/langchain-ai/langchain)** — GPT-4o integration
- **[FastAPI](https://fastapi.tiangolo.com)** — API server
- **[pyautogui](https://pyautogui.readthedocs.io)** — keyboard/mouse control
- **Web Speech API** — voice input on phone