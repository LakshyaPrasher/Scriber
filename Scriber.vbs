Set WshShell = CreateObject("WScript.Shell")
strCurDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strCurDir
WshShell.Run Chr(34) & strCurDir & "\.venv\Scripts\pythonw.exe" & Chr(34) & " " & Chr(34) & strCurDir & "\run_desktop.py" & Chr(34), 0, False
