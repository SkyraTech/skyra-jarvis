"""
Jarvis File System Tools — Phase 1 Expansion
=============================================
Enables Jarvis to read, write, and patch code and text files inside allowed workspaces.
Restricted to user-approved workspace directories for safety.
"""

import os
from pathlib import Path
from loguru import logger

# List of allowed parent workspace directories
# To prevent editing system files or accessing unauthorized folders
ALLOWED_WORKSPACES = [
    Path(r"C:\Users\hp\OneDrive\Documents\My Docs\Personal Projects\Skyra-Tech").resolve()
]

def is_path_allowed(target_path: Path) -> bool:
    """Check if the resolved path falls inside any of the allowed workspace directories."""
    resolved = target_path.resolve()
    for allowed in ALLOWED_WORKSPACES:
        # Check if resolved path is a subpath of allowed path
        try:
            resolved.relative_to(allowed)
            return True
        except ValueError:
            continue
    return False

async def read_workspace_file(file_path: str) -> str:
    """
    Read the contents of any text, code, or configuration file inside the workspace.
    Use this to inspect code, read config values, or inspect local repository settings.
    
    Args:
        file_path: The absolute path of the file to read.
    """
    logger.info(f"📂 Tool Call: Reading file '{file_path}'...")
    path = Path(os.path.expandvars(file_path)).resolve()
    
    if not path.exists():
        return f"Error: File '{file_path}' does not exist."
    if not path.is_file():
        return f"Error: '{file_path}' is not a file (it might be a directory)."
        
    if not is_path_allowed(path):
        return f"Access Denied: The file path '{file_path}' is outside your authorized Skyra-Tech workspaces."
        
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return content
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {e}")
        return f"Failed to read file. Error: {e}"

async def write_workspace_file(file_path: str, content: str) -> str:
    """
    Write or overwrite a file with the specified text content inside the workspace.
    Use this to create new code files, update config files, or generate documentation.
    
    Args:
        file_path: The absolute path of the file to write.
        content: The complete text content to write to the file.
    """
    logger.info(f"📂 Tool Call: Writing file '{file_path}'...")
    path = Path(os.path.expandvars(file_path)).resolve()
    
    if not is_path_allowed(path):
        return f"Access Denied: The destination path '{file_path}' is outside your authorized Skyra-Tech workspaces."
        
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Successfully wrote file: '{file_path}' ({len(content)} characters)."
    except Exception as e:
        logger.error(f"Error writing file '{file_path}': {e}")
        return f"Failed to write file. Error: {e}"

async def patch_workspace_file(file_path: str, search_block: str, replace_block: str) -> str:
    """
    Replace a specific search_block of code with a replace_block inside a file.
    Use this to make targeted edits to a file (like editing a single function or changing a line)
    without rewriting the entire file. The search_block must match the existing file content exactly.
    
    Args:
        file_path: The absolute path of the file to modify.
        search_block: The exact code block currently in the file that you want to replace.
        replace_block: The new code block to replace the search_block with.
    """
    logger.info(f"📂 Tool Call: Patching file '{file_path}'...")
    path = Path(os.path.expandvars(file_path)).resolve()
    
    if not path.exists():
        return f"Error: File '{file_path}' does not exist."
    if not path.is_file():
        return f"Error: '{file_path}' is not a file."
        
    if not is_path_allowed(path):
        return f"Access Denied: The file path '{file_path}' is outside your authorized Skyra-Tech workspaces."
        
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        if search_block not in content:
            return (
                f"Error: The search block was not found in the file. "
                f"Make sure spelling, indentation, and newlines match the file exactly."
            )
            
        # Verify unique match
        if content.count(search_block) > 1:
            return "Error: The search block matches multiple locations in the file. Please provide more surrounding lines of context."
            
        new_content = content.replace(search_block, replace_block)
        path.write_text(new_content, encoding="utf-8")
        return f"Successfully patched file: '{file_path}'."
    except Exception as e:
        logger.error(f"Error patching file '{file_path}': {e}")
        return f"Failed to patch file. Error: {e}"
