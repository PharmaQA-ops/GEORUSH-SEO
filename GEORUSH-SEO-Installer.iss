
#define MyAppName "GEORUSH SEO"
#define MyAppVersion "20.0.0"
#define MyAppPublisher "GEORUSH"
#define MyAppExeName "GEORUSH-SEO.exe"

[Setup]
AppId={{D8A9F5E4-4D3C-4C9E-A3A6-9F0B9E5C2020}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\GEORUSH SEO
DefaultGroupName=GEORUSH SEO
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=GEORUSH-SEO-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
Uninstallable=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Files]
Source: "dist\GEORUSH-SEO.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\GEORUSH SEO"; Filename: "{app}\GEORUSH-SEO.exe"
Name: "{group}\GEORUSH SEO"; Filename: "{app}\GEORUSH-SEO.exe"
Name: "{group}\Uninstall GEORUSH SEO"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\GEORUSH-SEO.exe"; Description: "Launch GEORUSH SEO"; Flags: nowait postinstall skipifsilent
