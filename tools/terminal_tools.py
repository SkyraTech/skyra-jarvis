"""
Jarvis Terminal Execution Tools — Phase 2 Expansion
==================================================
Enables Jarvis to run compiler checks, lint tests, git commands, and deployment scripts.
Restricted to user workspaces for safety.
"""

import os
import asyncio
from pathlib import Path
from loguru import logger

# List of allowed parent workspace directories
ALLOWED_WORKSPACES = [
    Path(r"C:\Users\hp\OneDrive\Documents\My Docs\Personal Projects\Skyra-Tech").resolve()
]

# Blacklisted dangerous command keywords
BLOCKED_COMMANDS = [
    "format", "rmdir /s", "del /s", "erase", "mkfs", "rm -rf", "shred"
]

def is_path_allowed(target_path: Path) -> bool:
    """Check if the resolved path falls inside any of the allowed workspace directories."""
    resolved = target_path.resolve()
    for allowed in ALLOWED_WORKSPACES:
        try:
            resolved.relative_to(allowed)
            return True
        except ValueError:
            continue
    return False

async def run_workspace_command(command: str, cwd: str = "") -> str:
    """
    Run any terminal or command-line task (like npm commands, compile checks, git push, or tests)
    within the allowed workspace directories.
    
    Args:
        command: The shell command line to execute (e.g., 'npm run build', 'git status', 'npm test').
        cwd: The directory path in which to run the command (defaults to workspace root if empty).
    """
    logger.info(f"💻 Tool Call: Running command '{command}' in '{cwd}'...")
    
    # 1. Block dangerous commands
    clean_cmd = command.strip().lower()
    for blocked in BLOCKED_COMMANDS:
        if blocked in clean_cmd:
            return f"Security Exception: Command contains blocked dangerous keyword: '{blocked}'."

    # 2. Check and resolve working directory
    target_cwd = Path(os.path.expandvars(cwd)) if cwd else ALLOWED_WORKSPACES[0]
    target_cwd = target_cwd.resolve()
    
    if not target_cwd.exists():
        return f"Error: The working directory path '{cwd}' does not exist on your computer."
        
    if not is_path_allowed(target_cwd):
        return f"Access Denied: The target directory '{cwd}' is outside your authorized Skyra-Tech workspaces."

    try:
        # Spawn command process asynchronously
        # On Windows, we use shell=True which executes via cmd.exe /c
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=str(target_cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for command to complete (max 30 seconds to prevent hanging tasks)
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            return "Error: Command timed out after 30 seconds."
            
        stdout = stdout_bytes.decode(encoding="utf-8", errors="replace").strip()
        stderr = stderr_bytes.decode(encoding="utf-8", errors="replace").strip()
        exit_code = process.returncode
        
        result_lines = [
            f"Command executed (Exit Code: {exit_code})",
            "",
            "--- Standard Output ---",
            stdout if stdout else "[No Output]",
            "",
            "--- Standard Error ---",
            stderr if stderr else "[No Errors]"
        ]
        
        return "\n".join(result_lines)
    except Exception as e:
        logger.error(f"Error running command '{command}': {e}")
        return f"Failed to run command. Error: {e}"
