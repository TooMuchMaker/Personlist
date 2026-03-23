Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\app.py""", 0, False
WScript.Sleep 2000
WshShell.Run "http://127.0.0.1:5003"
