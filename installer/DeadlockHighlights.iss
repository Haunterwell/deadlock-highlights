; Instalador do Deadlock Highlights (Inno Setup 6)
; Gere com build.bat, que primeiro cria o .exe com o PyInstaller.
#define AppName "Deadlock Highlights"
#define AppVersion "1.0.2"
#ifndef DistDir
  #define DistDir "..\build\dist\DeadlockHighlights"
#endif

[Setup]
AppId={{6E2B7C1A-4F3D-4C1E-9B2A-D1E7A0C5F8B3}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=DeadlockHighlights-Setup-{#AppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\DeadlockHighlights.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\docs\TUTORIAL.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_LICENSES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\DeadlockHighlights.exe"
Name: "{autoprograms}\Tutorial do {#AppName}"; Filename: "{app}\TUTORIAL.html"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\DeadlockHighlights.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TUTORIAL.html"; Description: "Abrir o tutorial"; Flags: postinstall shellexec skipifsilent unchecked
Filename: "{app}\DeadlockHighlights.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: postinstall nowait skipifsilent
