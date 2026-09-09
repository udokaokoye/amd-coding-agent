"""
Quick Demo Script - Shows NPU coding agent in action
Perfect for short-form content recording

Run with: python demo.py <project_path>
"""

import os
import sys
import time
from pathlib import Path
from foundry_local_sdk import Configuration, FoundryLocalManager

# ANSI colors for terminal output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_slow(text: str, delay: float = 0.02):
    """Print text with a typewriter effect."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


def main():
    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    # Fancy banner
    print(f"""
{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════╗
    ║  🧠 LOCAL AI CODING AGENT                         ║
    ║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
    ║  Powered by AMD Ryzen AI NPU • 50 TOPS            ║
    ║  100% Local • Zero Cloud • Full Privacy           ║
    ╚═══════════════════════════════════════════════════╝
{Colors.END}""")
    
    print(f"{Colors.YELLOW}📁 Project:{Colors.END} {project_path}")
    
    # Count files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.go', '.rs'}
    files = []
    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in {'node_modules', '.git', '__pycache__', 'venv', '.venv'}]
        for f in filenames:
            if Path(f).suffix.lower() in code_extensions:
                files.append(os.path.join(root, f))
    
    print(f"{Colors.YELLOW}📄 Code files:{Colors.END} {len(files)}")
    print()
    
    # Initialize model
    print(f"{Colors.GREEN}🔧 Initializing NPU acceleration...{Colors.END}")
    FoundryLocalManager.initialize(Configuration(app_name="coding-agent-demo"))
    manager = FoundryLocalManager.instance
    
    model = manager.catalog.get_model("phi-3.5-mini")
    
    if not model.is_cached():
        print(f"{Colors.GREEN}⬇️  Downloading phi-3.5-mini...{Colors.END}")
        model.download(lambda p: print(f"\r   {p:.0f}%", end="", flush=True))
        print()
    
    print(f"{Colors.GREEN}🧠 Loading model onto NPU...{Colors.END}")
    model.load()
    print(f"{Colors.GREEN}✅ Ready!{Colors.END}")
    print()
    
    chat = model.get_chat_client()
    
    # Read a sample file for context
    sample_file = None
    sample_content = ""
    for f in files[:10]:
        try:
            content = Path(f).read_text(encoding='utf-8', errors='ignore')
            if 100 < len(content) < 5000:  # Good size for demo
                sample_file = f
                sample_content = content
                break
        except:
            continue
    
    if sample_file:
        print(f"{Colors.MAGENTA}📂 Analyzing:{Colors.END} {os.path.basename(sample_file)}")
        print("─" * 50)
    
    # Demo conversation
    system_prompt = f"""You are a helpful coding assistant running locally on an AMD Ryzen AI NPU.
Be concise and direct. You're analyzing this project:
Directory: {project_path}
Files: {len(files)} code files

{"Current file content:" + chr(10) + sample_content[:3000] if sample_content else ""}

Keep responses short and punchy - this is for a demo video."""

    questions = [
        "What does this code do? Explain in 2-3 sentences.",
        "Any bugs or improvements you'd suggest?",
    ]
    
    for i, question in enumerate(questions):
        print()
        print(f"{Colors.BOLD}You:{Colors.END} {question}")
        print()
        print(f"{Colors.CYAN}🤖 AI:{Colors.END} ", end="", flush=True)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        for chunk in chat.complete_streaming_chat(messages):
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
        
        print()
        
        if i < len(questions) - 1:
            print()
            input(f"{Colors.YELLOW}[Press Enter for next question]{Colors.END}")
    
    print()
    print(f"{Colors.GREEN}─" * 50)
    print(f"✨ All inference ran locally on the NPU!")
    print(f"   No data left this machine.{Colors.END}")
    print()


if __name__ == "__main__":
    main()
