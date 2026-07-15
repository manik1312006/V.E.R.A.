<div align="center">

# V.E.R.A.
### Virtual Entity for Real-time Assistance

**An open-source AI assistant that thinks, decides, and controls your entire machine.**  
*Created by Manik Mehta*

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![Mistral](https://img.shields.io/badge/LLM-Mistral%20Large-orange?logo=mistral)](https://mistral.ai)
[![Ollama](https://img.shields.io/badge/Local-Ollama-green?logo=llama)](https://ollama.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)](https://github.com)

</div>

---

## What is V.E.R.A.?

V.E.R.A. is a local AI assistant that runs in your terminal and has **full control over your machine**. Unlike cloud chatbots, V.E.R.A. actually *does* things:

- 🧠 **Powered by Mistral Large** (or any local Ollama model)
- 🖥️ **Controls your PC** — opens apps, types text, clicks buttons
- 🌐 **Browses the web** — searches Google, plays YouTube, scrapes pages
- 📚 **Builds a knowledge base** — autonomously researches topics and saves them
- 🔬 **Deep Research mode** — pulls 80+ Wikipedia articles + ArXiv papers per topic
- 📁 **Manages your files** — reads, writes, copies, organises
- 🧩 **Writes its own scripts** — creates new automation scripts on the fly when it encounters a task it hasn't seen before
- 🔔 **Notifications** — alerts you when long-running tasks complete

---

## Quick Start

### Requirements
- Python 3.10+
- Windows 10/11
- A free [Mistral API key](https://console.mistral.ai/) — or [Ollama](https://ollama.ai) for fully local/offline use

### Install (one command)

```bash
# 1. Clone the repo
git clone https://github.com/manik1312006/V.E.R.A.git
cd V.E.R.A

# 2. Run the installer
# For Windows:
install.bat

# For Linux / macOS:
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Check your Python version
- ✅ Install all dependencies automatically
- ✅ Create your `config.yaml` from the template
- ✅ Add `vera` to your system PATH so you can run it from **anywhere**

### Launch

Open **any** terminal window and type:

```
vera
```

V.E.R.A. will ask for your Mistral API key on first run and save it automatically.

---

## Usage Examples

Just talk to V.E.R.A. in plain English:

```
You: Open Spotify
You: Search YouTube for lo-fi music and play the first result
You: List all files on my Desktop
You: Run deep research on Quantum Computing
You: What do you know about robotics?
You: Generate a Windows battery report and save it to my Desktop
You: Analyse my battery-report.html and rate it out of 10
You: Create a script that organises my Downloads folder by file type
```

---

## Deep Research

V.E.R.A. can autonomously build a massive local knowledge base:

```
You: Run deep research on Machine Learning
```

This automatically:
1. Searches Wikipedia for 30+ related articles
2. Pulls 50+ academic papers from ArXiv
3. Saves everything to `Knowledge/Machine Learning/`
4. Notifies you when complete (popup + beep)
5. Lets you query it later: *"What do you know about neural networks?"*

---

## Project Structure

```
V.E.R.A/
├── vera.py                  # Main entry point
├── vera.bat                 # Windows launcher (run from anywhere)
├── install.bat              # One-click installer
├── config.yaml              # Your config (not committed — contains API key)
├── config.template.yaml     # Safe template for sharing
├── requirements.txt         # Python dependencies
├── brain/                   # LLM intelligence
│   ├── conversation.py      # System prompt & memory
│   ├── reasoning.py         # Response parser
│   └── llm/                 # Mistral API + Ollama providers
├── engine/                  # Execution engine
│   ├── executor.py          # Runs tools and scripts
│   └── script_creator.py    # Generates new scripts on the fly
├── tools/                   # Built-in Python tools
│   ├── file_manager.py      # File operations
│   ├── browser_control.py   # Web browsing (Playwright)
│   ├── deep_researcher.py   # Autonomous research (Wikipedia + ArXiv)
│   ├── knowledge_manager.py # Knowledge base CRUD
│   ├── system_control.py    # Open/close apps, processes
│   ├── web_scraper.py       # HTML scraping + local file reading
│   └── ...
├── scripts/                 # Pre-built OS automation scripts
│   ├── windows/
│   ├── linux/
│   └── custom/              # Scripts V.E.R.A. generated for you
├── interface/               # CLI & voice interface
│   ├── cli.py               # Terminal UI (Rich)
│   └── voice/               # Voice input/output
└── Knowledge/               # Auto-generated research (not committed)
```

---

## Configuration

After install, edit `config.yaml`:

```yaml
llm:
  provider: "mistral_api"   # or "ollama_local" for offline use
  mistral:
    api_key: ""             # V.E.R.A. will ask on first run
    model: "mistral-large-latest"
```

### Use Ollama (fully local, no API key needed)

```bash
ollama pull mistral
```

Then set in `config.yaml`:
```yaml
llm:
  provider: "ollama_local"
```

---

## Commands

| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `tools` | List available Python tools |
| `scripts` | List automation scripts |
| `history` | Show conversation history |
| `clear` | Clear screen and memory |
| `reset` | Clear conversation memory only |
| `exit` | Quit V.E.R.A. |

---

## Contributing

Pull requests are welcome! Please:
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Add your tool to `tools/` following the existing pattern
4. Submit a PR

---

## Author & License

- **Creator / Author:** Manik Mehta
- **License:** MIT — see [LICENSE](LICENSE)
