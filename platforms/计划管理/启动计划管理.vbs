Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strScriptPath = WScript.ScriptFullName
strScriptDir = objFSO.GetParentFolderName(strScriptPath)

strAppPath = strScriptDir & "\web_app.py"

If objFSO.FileExists(strAppPath) Then
    objShell.Run "pythonw.exe " & Chr(34) & strAppPath & Chr(34), 0, False
    
    WScript.Sleep 2000
    objShell.Run "http://127.0.0.1:5001", 1, False
Else
    objShell.Popup "未找到 web_app.py 文件", 5, "错误", 48
End If
