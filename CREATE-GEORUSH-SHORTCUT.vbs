Option Explicit
Dim shell, fso, base, desktop, link
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
desktop = shell.SpecialFolders("Desktop")
Set link = shell.CreateShortcut(desktop & "\GEORUSH SEO.lnk")
If fso.FileExists(base & "\GEORUSH-SEO.exe") Then
    link.TargetPath = base & "\GEORUSH-SEO.exe"
    link.WorkingDirectory = base
Else
    link.TargetPath = base & "\GEORUSH-SEO-START.vbs"
    link.WorkingDirectory = base
End If
link.Description = "GEORUSH SEO - Local AI + Deep Research"
link.IconLocation = base & "\GEORUSH-SEO.exe"
link.Save
WScript.Echo "GEORUSH SEO desktop shortcut created."
