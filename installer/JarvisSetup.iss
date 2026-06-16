#define MyAppName "Jarvis"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "CoderBoiii"
#define MyAppExeName "Jarvis.cmd"

[Setup]
AppId={{7B81DDA2-0F11-4D73-8F41-2B812F6D4A99}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Jarvis
DefaultGroupName=Jarvis
OutputDir=Output
OutputBaseFilename=JarvisSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\jarvis.ico
PrivilegesRequired=admin
DisableProgramGroupPage=no
SetupLogging=yes
UninstallDisplayIcon={app}\assets\jarvis.ico
LicenseFile=PrivacyPolicy.txt
InfoBeforeFile=InstallationGuide.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "pullollama"; Description: "Download llama3.1:8b model with Ollama after installation"; GroupDescription: "AI model setup:"; Flags: checkedonce

[Files]
Source: "assets\jarvis.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__\*,*.pyc,*.pyo,*.bak*,test_*.py"
Source: "..\frontend\dist\*"; DestDir: "{app}\frontend\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\uv.lock"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "scripts\Jarvis.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "scripts\jarvis_post_install.ps1"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "InstallationGuide.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "PrivacyPolicy.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Jarvis"; Filename: "{app}\Jarvis.cmd"; WorkingDir: "{app}"; IconFilename: "{app}\assets\jarvis.ico"
Name: "{group}\Uninstall Jarvis"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Jarvis"; Filename: "{app}\Jarvis.cmd"; WorkingDir: "{app}"; IconFilename: "{app}\assets\jarvis.ico"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\installer\jarvis_post_install.ps1"" -InstallDir ""{app}"" -PullOllamaModel ""{code:GetPullModelArg}"""; StatusMsg: "Scanning and installing Jarvis dependencies..."; Flags: runhidden waituntilterminated
Filename: "{app}\Jarvis.cmd"; Description: "Launch Jarvis"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\installer"
Type: files; Name: "{app}\install_log.txt"

[Code]
var
  PrivacyCheckBox: TNewCheckBox;

function GetPullModelArg(Param: string): string;
begin
  if WizardIsTaskSelected('pullollama') then
    Result := 'true'
  else
    Result := 'false';
end;

procedure InitializeWizard;
begin
  PrivacyCheckBox := TNewCheckBox.Create(WizardForm);
  PrivacyCheckBox.Parent := WizardForm.SelectDirPage;
  PrivacyCheckBox.Left := WizardForm.DirEdit.Left;
  PrivacyCheckBox.Top := WizardForm.DirEdit.Top + WizardForm.DirEdit.Height + ScaleY(16);
  PrivacyCheckBox.Width := WizardForm.DirEdit.Width;
  PrivacyCheckBox.Height := ScaleY(48);
  PrivacyCheckBox.Caption := 'I have manually read and accept the Jarvis Privacy Policy and installation terms.';
  PrivacyCheckBox.Checked := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = wpSelectDir then
  begin
    if not PrivacyCheckBox.Checked then
    begin
      MsgBox('You must manually tick the privacy policy checkbox before installing Jarvis.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;
