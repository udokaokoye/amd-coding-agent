"""
Local Coding Agent - Runs on AMD Ryzen AI NPU
Built for AMD collaboration content by Levi Okoye

This agent reads your codebase and answers questions about it,
all running locally on the NPU with zero cloud dependencies.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from foundry_local_sdk import Configuration, FoundryLocalManager

# ============================================================
# Configuration
# ============================================================

MODEL_ALIAS = "phi-3.5-mini"  # Good balance of speed and capability
MAX_FILE_SIZE = 50_000  # Max chars to read from a single file
MAX_CONTEXT_FILES = 10  # Max files to include in context
SUPPORTED_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.html', '.css', '.scss', '.json', '.yaml', '.yml', '.md', '.txt',
    '.sql', '.sh', '.bash', '.zsh', '.ps1', '.dockerfile', '.toml'
}


@dataclass
class FileContent:
    path: str
    content: str
    language: str


# ============================================================
# File System Tools
# ============================================================

def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.jsx': 'jsx', '.tsx': 'tsx', '.java': 'java', '.cpp': 'cpp',
        '.c': 'c', '.h': 'c', '.cs': 'csharp', '.go': 'go', '.rs': 'rust',
        '.rb': 'ruby', '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
        '.scala': 'scala', '.html': 'html', '.css': 'css', '.scss': 'scss',
        '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown',
        '.sql': 'sql', '.sh': 'bash', '.bash': 'bash', '.zsh': 'zsh',
        '.ps1': 'powershell', '.toml': 'toml'
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, 'text')


def read_file(file_path: str, base_path: str) -> Optional[FileContent]:
    """Safely read a file within the project directory."""
    try:
        # Resolve to absolute and check it's within base_path
        full_path = Path(base_path) / file_path
        full_path = full_path.resolve()
        
        if not str(full_path).startswith(str(Path(base_path).resolve())):
            return None  # Path traversal attempt
        
        if not full_path.exists() or not full_path.is_file():
            return None
            
        if full_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return None
            
        content = full_path.read_text(encoding='utf-8', errors='ignore')
        if len(content) > MAX_FILE_SIZE:
            content = content[:MAX_FILE_SIZE] + "\n\n... [truncated]"
            
        return FileContent(
            path=str(file_path),
            content=content,
            language=detect_language(str(file_path))
        )
    except Exception:
        return None


def scan_project(base_path: str) -> list[str]:
    """Scan project directory for code files."""
    files = []
    base = Path(base_path)
    
    # Directories to skip
    skip_dirs = {
        'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env',
        '.env', 'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj',
        '.idea', '.vscode', 'coverage', '.pytest_cache', '.mypy_cache'
    }
    
    for root, dirs, filenames in os.walk(base):
        # Skip hidden and excluded directories
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        
        for filename in filenames:
            if Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS:
                rel_path = os.path.relpath(os.path.join(root, filename), base)
                files.append(rel_path)
    
    return sorted(files)


def get_project_summary(base_path: str, files: list[str]) -> str:
    """Generate a summary of the project structure."""
    # Count files by extension
    ext_counts = {}
    for f in files:
        ext = Path(f).suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    # Build tree structure (simplified)
    tree_lines = []
    dirs_seen = set()
    
    for f in files[:50]:  # Limit to first 50 files for summary
        parts = Path(f).parts
        for i in range(len(parts) - 1):
            dir_path = "/".join(parts[:i+1])
            if dir_path not in dirs_seen:
                dirs_seen.add(dir_path)
                indent = "  " * i
                tree_lines.append(f"{indent}📁 {parts[i]}/")
        
        indent = "  " * (len(parts) - 1)
        tree_lines.append(f"{indent}📄 {parts[-1]}")
    
    if len(files) > 50:
        tree_lines.append(f"\n... and {len(files) - 50} more files")
    
    summary = f"""## Project Overview
Total files: {len(files)}

### File types:
{chr(10).join(f"  {ext}: {count} files" for ext, count in sorted(ext_counts.items()))}

### Structure:
{chr(10).join(tree_lines)}
"""
    return summary


# ============================================================
# Agent Core
# ============================================================

class CodingAgent:
    def __init__(self, project_path: str):
        self.project_path = str(Path(project_path).resolve())
        self.files = scan_project(self.project_path)
        self.project_summary = get_project_summary(self.project_path, self.files)
        self.conversation_history = []
        self.loaded_files: dict[str, FileContent] = {}
        self.chat_client = None
        
    def initialize_model(self):
        """Initialize Foundry Local and load the model."""
        print(f"\n🔧 Initializing Foundry Local...")
        
        FoundryLocalManager.initialize(Configuration(app_name="coding-agent"))
        manager = FoundryLocalManager.instance
        
        print(f"📦 Loading model: {MODEL_ALIAS}")
        model = manager.catalog.get_model(MODEL_ALIAS)
        
        if not model.is_cached():
            print(f"⬇️  Downloading {MODEL_ALIAS}...")
            model.download(lambda p: print(f"\r   Progress: {p:.0f}%", end="", flush=True))
            print()
        
        print(f"🧠 Loading model into memory (NPU acceleration)...")
        model.load()
        
        self.chat_client = model.get_chat_client()
        print(f"✅ Model ready!\n")
        
    def load_file_into_context(self, file_path: str) -> bool:
        """Load a specific file into the agent's context."""
        if file_path in self.loaded_files:
            return True
            
        if len(self.loaded_files) >= MAX_CONTEXT_FILES:
            # Remove oldest file
            oldest = next(iter(self.loaded_files))
            del self.loaded_files[oldest]
            
        file_content = read_file(file_path, self.project_path)
        if file_content:
            self.loaded_files[file_path] = file_content
            return True
        return False
        
    def build_system_prompt(self) -> str:
        """Build the system prompt with project context."""
        files_context = ""
        if self.loaded_files:
            files_context = "\n\n## Currently Loaded Files:\n"
            for path, fc in self.loaded_files.items():
                files_context += f"\n### {path}\n```{fc.language}\n{fc.content}\n```\n"
        
        return f"""You are a local AI coding assistant running on an AMD Ryzen AI processor with NPU acceleration.
You help developers understand, debug, and improve their code.

## Your Capabilities:
- Analyze code structure and logic
- Explain how code works
- Find bugs and suggest fixes
- Propose refactoring improvements
- Answer questions about the codebase

## Project Context:
Working directory: {self.project_path}

{self.project_summary}
{files_context}

## Guidelines:
- Be concise but thorough
- When suggesting code changes, show the specific code
- If you need to see a file to answer, tell the user which file
- Reference specific line numbers when discussing code
- Explain your reasoning

You are running 100% locally - no data leaves this machine."""

    def extract_file_requests(self, user_input: str) -> list[str]:
        """Extract file paths mentioned in user input."""
        requested = []
        
        # Check for explicit file mentions
        for f in self.files:
            if f.lower() in user_input.lower():
                requested.append(f)
            elif Path(f).name.lower() in user_input.lower():
                requested.append(f)
                
        return requested[:MAX_CONTEXT_FILES]

    def chat(self, user_input: str) -> str:
        """Process user input and generate a response."""
        # Auto-load mentioned files
        requested_files = self.extract_file_requests(user_input)
        for f in requested_files:
            if self.load_file_into_context(f):
                print(f"   📂 Loaded: {f}")
        
        # Build messages
        system_prompt = self.build_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history[-10:])  # Keep last 10 turns
        messages.append({"role": "user", "content": user_input})
        
        # Generate response (streaming)
        print("\n🤖 ", end="", flush=True)
        response_text = ""
        
        for chunk in self.chat_client.complete_streaming_chat(messages):
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
            response_text += content
            
        print("\n")
        
        # Update history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        return response_text


# ============================================================
# CLI Interface
# ============================================================

def print_banner():
    """Print the startup banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🧠  LOCAL CODING AGENT                                     ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║   Powered by AMD Ryzen AI NPU                                ║
║   Running 100% locally - your code never leaves this PC      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_help():
    """Print available commands."""
    print("""
📚 Commands:
  /files          - List all project files
  /load <path>    - Load a specific file into context
  /loaded         - Show currently loaded files  
  /clear          - Clear conversation history
  /help           - Show this help message
  /quit           - Exit the agent

💡 Tips:
  - Just ask questions about your code naturally
  - Mention file names and they'll be auto-loaded
  - Ask for explanations, bug fixes, or improvements
""")


def main():
    # Get project path from args or current directory
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()
    
    if not os.path.isdir(project_path):
        print(f"❌ Error: '{project_path}' is not a valid directory")
        sys.exit(1)
    
    print_banner()
    
    # Initialize agent
    agent = CodingAgent(project_path)
    print(f"📁 Project: {agent.project_path}")
    print(f"📄 Found {len(agent.files)} code files")
    
    # Initialize model
    agent.initialize_model()
    
    print_help()
    print("─" * 60)
    
    # Main loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            # Handle commands
            if user_input.startswith('/'):
                cmd = user_input.lower().split()[0]
                
                if cmd == '/quit' or cmd == '/exit':
                    print("\n👋 Goodbye!")
                    break
                    
                elif cmd == '/help':
                    print_help()
                    
                elif cmd == '/files':
                    print("\n📄 Project files:")
                    for f in agent.files:
                        marker = "✓" if f in agent.loaded_files else " "
                        print(f"  [{marker}] {f}")
                    print()
                    
                elif cmd == '/loaded':
                    if agent.loaded_files:
                        print("\n📂 Loaded files:")
                        for f in agent.loaded_files:
                            print(f"  • {f}")
                    else:
                        print("\n📂 No files loaded yet")
                    print()
                    
                elif cmd == '/load':
                    parts = user_input.split(maxsplit=1)
                    if len(parts) > 1:
                        file_path = parts[1]
                        if agent.load_file_into_context(file_path):
                            print(f"✅ Loaded: {file_path}")
                        else:
                            print(f"❌ Could not load: {file_path}")
                    else:
                        print("Usage: /load <file_path>")
                    print()
                    
                elif cmd == '/clear':
                    agent.conversation_history = []
                    agent.loaded_files = {}
                    print("🧹 Cleared conversation and loaded files")
                    print()
                    
                else:
                    print(f"❓ Unknown command: {cmd}")
                    print_help()
                    
            else:
                # Regular chat
                agent.chat(user_input)
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
