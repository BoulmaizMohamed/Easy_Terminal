#define MyAppName "Easy_Terminal"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "B.Mohammed_Amin"
#define MyAppURL "https://github.com/your-username/easy-terminal"
#define MyAppExeName "Easy_Terminal.exe"

[Setup]
AppId={{D3A1B5F2-8921-4A55-9B21-82C40B8F91A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Easy_Terminal-Setup-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app.ico
LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "contextmenu"; Description: "Add 'Open in Terminal' to Windows Explorer right-click menu"; GroupDescription: "Windows Explorer Integration:"

[Registry]
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\EasyTerminal"; ValueType: string; ValueName: ""; ValueData: "Open in Terminal"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\EasyTerminal"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\EasyTerminal\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%V"""; Tasks: contextmenu

Root: HKCU; Subkey: "Software\Classes\Directory\shell\EasyTerminal"; ValueType: string; ValueName: ""; ValueData: "Open in Terminal"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Directory\shell\EasyTerminal"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\EasyTerminal\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKCU; Subkey: "Software\Classes\Drive\shell\EasyTerminal"; ValueType: string; ValueName: ""; ValueData: "Open in Terminal"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Drive\shell\EasyTerminal"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Drive\shell\EasyTerminal\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

[Files]
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\Easy_Terminal_User_Guide.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\Easy_Terminal_Guide_Utilisateur.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Easy_Terminal\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app.ico"
Name: "{autoprograms}\Easy_Terminal User Guide (EN)"; Filename: "{app}\Easy_Terminal_User_Guide.pdf"
Name: "{autoprograms}\Easy_Terminal Guide Utilisateur (FR)"; Filename: "{app}\Easy_Terminal_Guide_Utilisateur.pdf"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
