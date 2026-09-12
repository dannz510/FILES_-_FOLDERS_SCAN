
#define MyAppName "FILES AND FOLDERS MANAGER"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Dannz"

#define MyAppExeName "PentestVaultApp.exe" 
#define SourceDir "D:\Do not open\Obsidian\Dannz\appscan"

[Setup]
AppId={{8F4C2D11-9B3A-4F85-A512-E09871DBC201}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PentestVaultApp
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir={#SourceDir}\installer
OutputBaseFilename=PentestVaultInstaller_v2.0
SetupIconFile={#SourceDir}\assets\app_logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern


LicenseFile={#SourceDir}\LICENSE.txt
InfoAfterFile={#SourceDir}\README.md

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}\logs"; Permissions: users-full

[Files]

Source: "{#SourceDir}\dist\PentestVaultApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "notepad.exe"; Parameters: "{app}\README.md"; Description: "View README & Documentation"; Flags: postinstall skipifsilent unchecked