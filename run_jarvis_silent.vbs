Set WshShell = CreateObject("WScript.Shell")
' Run pythonw.exe silently so that uvicorn/main.py launches without displaying CMD window popup
WshShell.Run "venv\Scripts\pythonw.exe main.py", 0, False
