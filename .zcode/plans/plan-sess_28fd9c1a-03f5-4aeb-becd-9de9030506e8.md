# V.E.R.A. — Virtual Entity for Real-time Assistance

## Project Structure
```
D:/V.E.R.A/
├── vera.py                    # Main entry point
├── config.yaml                # User configuration (API keys, settings)
├── requirements.txt           # Dependencies
├── README.md                  # Documentation
├── brain/                     # LLM intelligence layer
│   ├── __init__.py
│   ├── llm_provider.py        # Abstract LLM interface
│   ├── mistral_api.py         # Mistral Cloud API
│   ├── ollama_local.py        # Ollama local model
│   ├── reasoning.py           # Task analysis & script generation
│   └── conversation.py        # History & context management
├── engine/                    # Execution engine
│   ├── __init__.py
│   ├── executor.py            # Routes tasks to scripts/tools
│   ├── script_manager.py      # Discovers & manages scripts
│   ├── script_creator.py      # Generates new scripts from LLM
│   └── safety.py              # Optional safety checks
├── scripts/                   # Pre-built automation scripts
│   ├── windows/               # 10 .bat files (open/close apps, youtube, browser, volume, screenshot, etc.)
│   ├── linux/                 # 10 .sh files (same functionality)
│   ├── macos/                 # 10 .sh files (same functionality)
│   └── custom/                # LLM/user generated scripts (saved for reuse)
├── interface/                 # User interaction
│   ├── __init__.py
│   ├── cli.py                 # Rich-powered CLI
│   ├── voice_input.py         # faster-whisper STT
│   └── voice_output.py        # edge-tts + pyttsx3 TTS
├── tools/                     # Python automation tools
│   ├── __init__.py
│   ├── system_control.py      # Process/app management
│   ├── browser_control.py     # Playwright browser automation
│   ├── desktop_automation.py  # pynput/pyautogui click & type
│   ├── file_manager.py        # File operations
│   ├── media_control.py       # YouTube, media playback
│   ├── network_tools.py       # Web search, diagnostics
│   └── app_controller.py      # In-app typing & clicking
└── utils/                     # Shared utilities
    ├── __init__.py
    ├── os_detector.py         # OS detection
    ├── logger.py              # Logging
    └── helpers.py             # Helpers
```

## How It Works
1. **User speaks/types** a request via CLI
2. **LLM (Mistral Large)** analyzes intent → decides execution path:
   - **Path A**: Run existing script from OS-specific folder
   - **Path B**: Generate new script → save to `scripts/custom/` → run it
   - **Path C**: Call a Python tool directly (browser control, desktop automation, etc.)
3. **Executor** runs the action on the machine
4. **Result** displayed in CLI + optionally spoken via TTS

## Implementation Steps (38 files total)
1. Create project skeleton (all folders + `__init__.py` files)
2. Build `config.yaml` + `requirements.txt` + `README.md`
3. Build `utils/` (OS detector, logger, helpers)
4. Build `brain/` (LLM provider, Mistral API, Ollama, reasoning engine, conversation)
5. Build `engine/` (executor, script manager, script creator, safety)
6. Build all `scripts/` (10 scripts × 3 OS = 30 script files)
7. Build `tools/` (6 Python automation modules)
8. Build `interface/` (CLI, voice input, voice output)
9. Build `vera.py` main entry point
10. Test and verify everything runs

## Tech Stack
- **LLM**: `mistralai` (API) + `ollama` (local) — user picks via config
- **CLI**: `typer` + `rich` for beautiful terminal
- **Voice**: `faster-whisper` (STT) + `edge-tts`/`pyttsx3` (TTS)
- **Automation**: `playwright` (browser) + `pynput`/`pyautogui` (desktop)
- **Config**: `pyyaml`

## Pre-built Scripts (10 per OS)
open_app, close_app, search_youtube, play_youtube, open_browser, list_processes, kill_process, volume_control, screenshot, shutdown_restart
