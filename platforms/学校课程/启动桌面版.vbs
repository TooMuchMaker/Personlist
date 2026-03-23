Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
strScriptPath = WScript.ScriptFullName
strScriptDir = objFSO.GetParentFolderName(strScriptPath)

' 切换到脚本所在目录
objShell.CurrentDirectory = strScriptDir

' 检查是否安装了 pywebview
On Error Resume Next
Set objExec = objShell.Exec("python -c ""import webview; print('pywebview is installed')""")
strOutput = objExec.StdOut.ReadAll()
If Err.Number <> 0 Then
    ' 安装 pywebview
    objShell.Run "cmd /c pip install pywebview", 1, True
End If
On Error GoTo 0

' 运行桌面应用
objShell.Run "cmd /c python desktop_app.py", 1, False
