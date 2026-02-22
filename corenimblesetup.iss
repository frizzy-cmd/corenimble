[Setup]
AppName=Core Nimble
AppVersion=1.0.2-openbeta
DefaultDirName={autopf}\CoreNimble
DefaultGroupName=Core Nimble
UninstallDisplayIcon={app}\CoreNimble.exe
Compression=lzma2/fast
SolidCompression=yes
SetupIconFile=C:\Users\Nyx\Desktop\nimble_core_source\iconn.ico
OutputDir=C:\Users\Nyx\Desktop
OutputBaseFilename=corenimble_installer_v1.0.2-openbeta

[Files]
; changed \Broster\* to \CoreNimble\*
Source: "C:\Users\Nyx\Desktop\nimble_core_source\dist\CoreNimble\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; changed Broster.exe to CoreNimble.exe
Name: "{group}\Core Nimble"; Filename: "{app}\CoreNimble.exe"
Name: "{commondesktop}\Core Nimble"; Filename: "{app}\CoreNimble.exe"

[Run]
; changed Broster.exe to CoreNimble.exe
Filename: "{app}\CoreNimble.exe"; Description: "{cm:LaunchProgram,Core Nimble}"; Flags: nowait postinstall skipifsilent