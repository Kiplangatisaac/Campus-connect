[Setup]
AppName=KyU Campus Connect
AppVersion=1.0.0
AppPublisher=Kirinyaga University
AppPublisherURL=https://kyu.ac.ke
DefaultDirName={autopf}\CampusConnect
DefaultGroupName=KyU Campus Connect
OutputDir=installer
OutputBaseFilename=campus-connect-setup-1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\frontend\build\*"; DestDir: "{app}\frontend\build"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "stop.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\KyU Campus Connect"; Filename: "{app}\start.bat"
Name: "{group}\{cm:UninstallProgram,KyU Campus Connect}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\KyU Campus Connect"; Filename: "{app}\start.bat"; Tasks: desktopicon

[Run]
Filename: "{app}\start.bat"; Description: "Start Campus Connect"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    Exec(ExpandConstant('{cmd}'), '/c python -m venv "' + ExpandConstant('{app}') + '\venv"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec(ExpandConstant('{app}\venv\Scripts\pip.exe'), 'install -r "' + ExpandConstant('{app}') + '\backend\requirements.txt"', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
  end;
end;
