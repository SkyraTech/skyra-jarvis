"""
Jarvis Tools — System & Desktop Automation
===========================================
Defines tool interfaces allowing Gemini to:
  1. Control files (create folders, copy, move)
  2. Launch applications, websites, and File Explorer
  3. Control GUI actions (simulate typing, click mouse, press keys) using PyAutoGUI.

NOTE: Delete and terminal command tools have been deliberately excluded from
Jarvis's capabilities as a safety measure. Jarvis has NO permission to delete
files or execute arbitrary terminal commands.
"""

import os
import shutil
import subprocess
import webbrowser
from pathlib import Path
from loguru import logger
import pyautogui


# ── SECTION 1: APPLICATION & DESKTOP LAUNCHERS ───────────────────────────

async def open_application(app_name: str) -> str:
    """
    Launch a software application on your Windows laptop.
    
    Args:
        app_name: The name of the app to launch (e.g., "notepad", "chrome", "vscode", "excel", "word", "calculator").
    """
    logger.info(f"🔧 Tool Call: Request to open application '{app_name}'...")
    
    app_map = {
        "notepad": "notepad.exe",
        "chrome": "start chrome",
        "vscode": "code",
        "excel": "start excel",
        "word": "start winword",
        "calculator": "calc.exe",
        "cmd": "start cmd.exe",
        "explorer": "explorer.exe"
    }
    
    clean_name = app_name.strip().lower()
    cmd = app_map.get(clean_name)
    
    if not cmd:
        cmd = app_name
        
    try:
        subprocess.Popen(cmd, shell=True)
        return f"Successfully launched {app_name} on your desktop."
    except Exception as e:
        logger.error(f"Failed to launch app '{app_name}': {e}")
        return f"Failed to open application '{app_name}'. Error: {e}"


async def open_website(url: str) -> str:
    """
    Open any website link or URL inside your default web browser.
    
    Args:
        url: The web URL to open (e.g. "https://google.com").
    """
    logger.info(f"🔧 Tool Call: Request to open website '{url}'...")
    
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = f"https://{clean_url}"
        
    try:
        webbrowser.open(clean_url)
        return f"Successfully opened website: {clean_url}"
    except Exception as e:
        logger.error(f"Failed to open website '{url}': {e}")
        return f"Failed to open browser for URL '{url}'. Error: {e}"


async def open_local_directory(folder_path: str) -> str:
    """
    Open any local folder or directory path in Windows File Explorer.
    
    Args:
        folder_path: The absolute folder path directory to open.
    """
    logger.info(f"🔧 Tool Call: Request to open local directory '{folder_path}'...")
    
    resolved_path = Path(os.path.expandvars(folder_path)).resolve()
    
    if not resolved_path.exists():
        return f"Cannot open folder. The path '{resolved_path}' does not exist on your computer."
        
    try:
        os.startfile(str(resolved_path))
        return f"Successfully opened folder: {resolved_path}"
    except Exception as e:
        logger.error(f"Failed to open directory '{folder_path}': {e}")
        return f"Failed to open File Explorer at path '{folder_path}'. Error: {e}"


# ── SECTION 2: FILE SYSTEM OPERATIONS ────────────────────────────────────

async def move_file(source_path: str, destination_path: str) -> str:
    """
    Move a file from one folder path to another.
    
    Args:
        source_path: The absolute file path of the source file to move.
        destination_path: The absolute destination file path or directory path.
    """
    logger.info(f"🔧 Tool Call: Moving '{source_path}' to '{destination_path}'...")
    src = Path(os.path.expandvars(source_path)).resolve()
    dest = Path(os.path.expandvars(destination_path)).resolve()
    
    if not src.exists():
        return f"Error: Source file '{src}' does not exist."
        
    try:
        if dest.is_dir():
            dest_file = dest / src.name
        else:
            dest_file = dest
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
        shutil.move(str(src), str(dest_file))
        return f"Successfully moved file from '{src}' to '{dest_file}'."
    except Exception as e:
        logger.error(f"Move error: {e}")
        return f"Failed to move file. Error: {e}"


async def copy_file(source_path: str, destination_path: str) -> str:
    """
    Copy a file from one folder path to another.
    
    Args:
        source_path: The absolute source file path to copy.
        destination_path: The absolute destination file or directory path.
    """
    logger.info(f"🔧 Tool Call: Copying '{source_path}' to '{destination_path}'...")
    src = Path(os.path.expandvars(source_path)).resolve()
    dest = Path(os.path.expandvars(destination_path)).resolve()
    
    if not src.exists():
        return f"Error: Source file '{src}' does not exist."
        
    try:
        if dest.is_dir():
            dest_file = dest / src.name
        else:
            dest_file = dest
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
        shutil.copy2(str(src), str(dest_file))
        return f"Successfully copied file from '{src}' to '{dest_file}'."
    except Exception as e:
        logger.error(f"Copy error: {e}")
        return f"Failed to copy file. Error: {e}"





async def create_folder(folder_path: str) -> str:
    """
    Create a new directory or folder directory path.
    
    Args:
        folder_path: The absolute path of the folder to create.
    """
    logger.info(f"🔧 Tool Call: Creating directory '{folder_path}'...")
    path = Path(os.path.expandvars(folder_path)).resolve()
    
    try:
        path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created folder: '{path}'."
    except Exception as e:
        logger.error(f"Folder creation error: {e}")
        return f"Failed to create folder. Error: {e}"





# ── SECTION 4: GUI KEYBOARD & MOUSE SIMULATION ─────────────────────────

async def gui_type_text(text: str) -> str:
    """
    Simulate keyboard key typing. Jarvis will write this text into the active window 
    selected on your screen.
    
    Args:
        text: The text characters to write out.
    """
    logger.info(f"🔧 Tool Call: Typing text via GUI...")
    try:
        pyautogui.write(text, interval=0.01)
        return f"Successfully typed text to active screen window."
    except Exception as e:
        logger.error(f"GUI typing error: {e}")
        return f"Failed to type text. Error: {e}"


async def gui_press_key(key: str) -> str:
    """
    Simulate pressing a keyboard shortcut or key.
    
    Args:
        key: The key name (e.g., 'enter', 'tab', 'ctrl', 'space', 'backspace').
             For shortcuts, combine with '+' (e.g., 'ctrl+s' to save, 'alt+tab' to switch).
    """
    logger.info(f"🔧 Tool Call: Pressing key '{key}'...")
    try:
        clean_key = key.strip().lower()
        if "+" in clean_key:
            parts = clean_key.split("+")
            # Run hotkey combination
            pyautogui.hotkey(*parts)
        else:
            pyautogui.press(clean_key)
        return f"Successfully pressed key/shortcut '{key}'."
    except Exception as e:
        logger.error(f"GUI keypress error: {e}")
        return f"Failed to press key. Error: {e}"


async def gui_click_mouse(x: int, y: int) -> str:
    """
    Simulate moving the mouse and left-clicking on a specific coordinate (X, Y) 
    on your screen.
    
    Args:
        x: Horizontal coordinate in pixels.
        y: Vertical coordinate in pixels.
    """
    logger.info(f"🔧 Tool Call: Clicking mouse at ({x}, {y})...")
    try:
        pyautogui.click(x, y)
        return f"Successfully clicked mouse at coordinates ({x}, {y})."
    except Exception as e:
        logger.error(f"GUI click error: {e}")
        return f"Failed to click mouse. Error: {e}"


async def take_desktop_screenshot() -> str:
    """
    Take a screenshot of your actual physical Windows desktop screen.
    This allows Jarvis to see what is currently open on your monitor (apps, code, folders)
    so he can read layout elements and determine X/Y coordinates before clicking.
    """
    logger.info("🔧 Tool Call: Taking desktop screenshot...")
    try:
        # Take screenshot of primary screen
        screenshot = pyautogui.screenshot()
        
        # Save to dashboard assets directory
        dashboard_dir = Path(__file__).parent.parent
        screenshot_path = dashboard_dir / "desktop_screenshot.png"
        screenshot.save(str(screenshot_path))
        
        width, height = screenshot.size
        return (
            f"Successfully captured desktop screenshot ({width}x{height} pixels). "
            f"Saved to {screenshot_path}. I can now see your screen layout and determine coordinates."
        )
    except Exception as e:
        logger.error(f"Desktop screenshot error: {e}")
        return f"Failed to capture desktop screenshot. Error: {e}"
