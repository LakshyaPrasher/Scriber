Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strCurDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strCurDir

If FSO.FileExists(strCurDir & "\dist\Scriber\Scriber.exe") Then
    WshShell.Run Chr(34) & strCurDir & "\dist\Scriber\Scriber.exe" & Chr(34), 0, False
ElseIf FSO.FileExists(strCurDir & "\.venv\Scripts\pythonw.exe") Then
    WshShell.Run Chr(34) & strCurDir & "\.venv\Scripts\pythonw.exe" & Chr(34) & " " & Chr(34) & strCurDir & "\run_desktop.py" & Chr(34), 0, False
Else
    WshShell.Run "pythonw.exe " & Chr(34) & strCurDir & "\run_desktop.py" & Chr(34), 0, False
End If
