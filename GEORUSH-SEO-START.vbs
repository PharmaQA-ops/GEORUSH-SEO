Option Explicit
Dim shell, fso, base, pyw, exe
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)

If fso.FileExists(base & "\GEORUSH-SEO.exe") Then
    shell.Run Chr(34) & base & "\GEORUSH-SEO.exe" & Chr(34), 0, False
ElseIf fso.FileExists(base & "\.venv\Scripts\pythonw.exe") Then
    pyw = base & "\.venv\Scripts\pythonw.exe"
    shell.Run Chr(34) & pyw & Chr(34) & " " & Chr(34) & base & "\georush_desktop.py" & Chr(34), 0, False
Else
    shell.Run "cmd /c " & Chr(34) & base & "\GEORUSH-SEO-START.bat" & Chr(34), 0, False
End If
