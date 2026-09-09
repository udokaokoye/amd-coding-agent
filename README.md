# 🧠 Local Coding Agent

**A coding assistant that runs 100% locally on your AMD Ryzen AI NPU.**

Built for AMD collaboration content by [Levi Okoye](https://twitter.com/levi_okoye).

## What It Does

- Reads your codebase and answers questions about it
- Explains code, finds bugs, suggests improvements
- All inference runs on the dedicated NPU — no cloud, no data leaves your machine
- Uses Microsoft Foundry Local SDK with Phi-3.5-mini

## Requirements

- Windows 11 24H2 or later
- AMD Ryzen AI processor (or any Copilot+ PC)
- Python 3.10+

## Setup

### 1. Install Foundry Local CLI

```powershell
winget install Microsoft.FoundryLocal
```

Restart your terminal, then verify:

```powershell
foundry --version
```

### 2. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the Agent

```powershell
# Run in current directory
python agent.py

# Or specify a project path
python agent.py C:\path\to\your\project
```

## Usage

Once running, just ask questions about your code:

```
You: What does the main function do?
You: Can you explain how the authentication works?
You: Find any bugs in user_service.py
You: How can I improve the error handling in this file?
```

### Commands

| Command | Description |
|---------|-------------|
| `/files` | List all code files in the project |
| `/load <path>` | Load a specific file into context |
| `/loaded` | Show currently loaded files |
| `/clear` | Clear conversation history |
| `/help` | Show help |
| `/quit` | Exit |

## Demo Tips

For video recording:

1. Open Task Manager → Performance tab → NPU to show utilization
2. Run the agent on an interesting codebase (your own project works best)
3. Ask questions that show off the agent's understanding
4. Point out that NPU usage spikes during inference

Good demo questions:
- "Explain what this project does in one paragraph"
- "What's the entry point of this application?"
- "Find potential bugs in [filename]"
- "How would you refactor [function] to be cleaner?"

## How It Works

1. **Scans** your project directory for code files
2. **Loads** Phi-3.5-mini via Foundry Local (auto-selects NPU)
3. **Builds** context from your project structure
4. **Streams** responses as the model generates them

The model automatically uses the AMD NPU for inference through the Foundry Local WinML backend.

## Troubleshooting

**"foundry: command not found"**
→ Restart your terminal after installing Foundry Local

**Model downloads slowly**
→ First run downloads ~2.5GB; subsequent runs use the cached model

**Empty responses**
→ Make sure you're on real hardware (not a VM) with DirectX 12 GPU

## License

MIT — use it however you want.
