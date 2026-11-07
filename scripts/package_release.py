"""Automated release packager for Command Center.

Generates:
1. Portable version (folder and ZIP) with local data storage.
2. Install Wizard (GUI/CLI setup script, Start Menu/Desktop shortcuts, Add/Remove Programs registry entry).
3. Inno Setup .iss compiler script.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"


def build_pyinstaller_binary() -> Path:
    """Compiles Easy_Terminal using PyInstaller."""
    print("==> Building executable with PyInstaller...")
    icon_path = ROOT_DIR / "assets" / "app.ico"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--name",
        "Easy_Terminal",
        "--add-data",
        f"command_center/styles.tcss{os.pathsep}command_center",
        "--add-data",
        f"command_center/data/seed_library.json{os.pathsep}command_center/data",
    ]
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    cmd.append("command_center/__main__.py")

    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
    out_dir = DIST_DIR / "Easy_Terminal"
    if not (out_dir / "Easy_Terminal.exe").exists():
        raise RuntimeError("PyInstaller build failed to produce Easy_Terminal.exe")
    print(f"==> PyInstaller build successful: {out_dir}")
    return out_dir


def make_portable_distribution(source_dir: Path) -> Path:
    """Creates a standalone portable distribution folder and ZIP archive."""
    print("==> Creating Portable distribution...")
    portable_dir = DIST_DIR / "Easy_Terminal-Portable"
    shutil.copytree(source_dir, portable_dir, dirs_exist_ok=True)

    # 1. Add portable.flag to route data into ./data/ rather than %APPDATA%
    (portable_dir / "portable.flag").write_text(
        "# Marker file indicating Easy_Terminal should run in self-contained portable mode.\n",
        encoding="utf-8",
    )

    # 2. Pre-create local data folder
    (portable_dir / "data").mkdir(exist_ok=True)

    # 3. Add Portable README
    readme_content = (
        "Easy_Terminal - Portable Edition\n"
        "================================\n\n"
        "This version is 100% self-contained. It can run from a USB drive,\n"
        "Desktop, or network share without installing or leaving files in AppData.\n\n"
        "HOW TO RUN:\n"
        "1. Double-click Easy_Terminal.exe to launch.\n"
        "2. All history, settings, and library databases are saved locally in the 'data' folder.\n"
        "3. Optional: Run 'register-context-menu.bat' to add 'Open in Terminal' to right-click menu\n"
        "   (especially handy on Windows 10/8/7!). Run 'unregister-context-menu.bat' to remove.\n\n"
        "To return to standard non-portable mode, simply delete 'portable.flag'.\n"
    )
    (portable_dir / "README_PORTABLE.txt").write_text(readme_content, encoding="utf-8")

    # 4. Context menu helpers for portable users
    (portable_dir / "register-context-menu.bat").write_text(
        "@echo off\r\n"
        "echo Registering 'Open in Terminal' context menu for Easy_Terminal...\r\n"
        "\"%~dp0Easy_Terminal.exe\" --register-context-menu\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    (portable_dir / "unregister-context-menu.bat").write_text(
        "@echo off\r\n"
        "echo Removing 'Open in Terminal' context menu...\r\n"
        "\"%~dp0Easy_Terminal.exe\" --unregister-context-menu\r\n"
        "pause\r\n",
        encoding="utf-8",
    )

    # 5. Create ZIP archive
    zip_path = DIST_DIR / "Easy_Terminal-Portable.zip"
    print(f"==> Compressing to {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in portable_dir.rglob("*"):
            zf.write(file, arcname=file.relative_to(DIST_DIR))

    print(f"==> Portable ZIP created: {zip_path}")
    return zip_path


def make_installer_package(source_dir: Path) -> Path:
    """Prepares the install wizard package with one-click setup & uninstall scripts."""
    print("==> Creating Install Wizard package...")
    setup_dir = DIST_DIR / "Easy_Terminal-Setup"
    shutil.copytree(source_dir, setup_dir, dirs_exist_ok=True)

    # Setup batch launcher
    (setup_dir / "setup.bat").write_text(
        "@echo off\r\n"
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0Setup-EasyTerminal.ps1\"\r\n"
        "pause\r\n",
        encoding="utf-8",
    )

    # Uninstall batch launcher
    (setup_dir / "uninstall.bat").write_text(
        "@echo off\r\n"
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0Uninstall-EasyTerminal.ps1\"\r\n"
        "pause\r\n",
        encoding="utf-8",
    )

    # Setup PowerShell script
    setup_ps1 = """# Easy_Terminal - Windows Setup Wizard
# Installs Easy_Terminal per-user without requiring administrative privileges.

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     EASY_TERMINAL - SETUP WIZARD       " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SourceDir = $PSScriptRoot
$DefaultDest = Join-Path $env:LOCALAPPDATA "Programs\\Easy_Terminal"

Write-Host "Default installation path:" -ForegroundColor Yellow
Write-Host "  $DefaultDest" -ForegroundColor White
Write-Host ""
$UserDest = Read-Host "Enter install directory (Press Enter for default)"
if ([string]::IsNullOrWhiteSpace($UserDest)) {
    $TargetDir = $DefaultDest
} else {
    $TargetDir = $UserDest.Trim()
}

Write-Host "`nInstalling to: $TargetDir" -ForegroundColor Cyan
if (!(Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

Write-Host "Copying application files..." -ForegroundColor Gray
Copy-Item -Path (Join-Path $SourceDir "*") -Destination $TargetDir -Recurse -Force -Exclude "setup.bat","Setup-EasyTerminal.ps1"

# Create Shortcuts via WScript.Shell
$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$DesktopOpt = Read-Host "Create Desktop shortcut? (Y/n)"
if ($DesktopOpt -ne "n" -and $DesktopOpt -ne "N") {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $Shortcut = $WshShell.CreateShortcut((Join-Path $DesktopPath "Easy_Terminal.lnk"))
    $Shortcut.TargetPath = (Join-Path $TargetDir "Easy_Terminal.exe")
    $Shortcut.WorkingDirectory = $TargetDir
    $Shortcut.Description = "Easy_Terminal Modern Windows Terminal"
    $IconPath = Join-Path $TargetDir "assets\\app.ico"
    if (Test-Path $IconPath) { $Shortcut.IconLocation = "$IconPath,0" }
    $Shortcut.Save()
    Write-Host "✓ Desktop shortcut created." -ForegroundColor Green
}

# Start Menu shortcut
$StartMenuPath = [Environment]::GetFolderPath("Programs")
$StartShortcut = $WshShell.CreateShortcut((Join-Path $StartMenuPath "Easy_Terminal.lnk"))
$StartShortcut.TargetPath = (Join-Path $TargetDir "Easy_Terminal.exe")
$StartShortcut.WorkingDirectory = $TargetDir
$StartShortcut.Description = "Easy_Terminal Modern Windows Terminal"
$IconPath = Join-Path $TargetDir "assets\\app.ico"
if (Test-Path $IconPath) { $StartShortcut.IconLocation = "$IconPath,0" }
$StartShortcut.Save()
Write-Host "✓ Start Menu shortcut created." -ForegroundColor Green

# Add to user PATH
$PathOpt = Read-Host "Add Easy_Terminal to user PATH (run 'easy_terminal' from terminal)? (Y/n)"
if ($PathOpt -ne "n" -and $PathOpt -ne "N") {
    $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($CurrentPath -notlike "*$TargetDir*") {
        $NewPath = "$CurrentPath;$TargetDir"
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        Write-Host "✓ Added to User PATH environment variable." -ForegroundColor Green
    }
}

# Add 'Open in Terminal' to Windows Explorer right-click menu
$ContextOpt = Read-Host "Add 'Open in Terminal' to Windows Explorer right-click menu? (Y/n)"
if ($ContextOpt -ne "n" -and $ContextOpt -ne "N") {
    $ExePath = Join-Path $TargetDir "Easy_Terminal.exe"
    & "$ExePath" --register-context-menu
    Write-Host "✓ Added 'Open in Terminal' to Explorer right-click context menu." -ForegroundColor Green
}

# Windows Add/Remove Programs registry entry
$RegPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Easy_Terminal"
if (!(Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
}
Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "Easy_Terminal"
Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "Easy_Terminal Contributors"
Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value $TargetDir
Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value "`"$TargetDir\\uninstall.bat`""

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Installation completed successfully!  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "You can now launch Easy_Terminal from your Start Menu, Desktop, or:"
Write-Host "  $TargetDir\\Easy_Terminal.exe" -ForegroundColor Cyan
"""
    (setup_dir / "Setup-EasyTerminal.ps1").write_text(setup_ps1, encoding="utf-8")

    # Uninstall PowerShell script
    uninstall_ps1 = """# Easy_Terminal - Uninstaller

$ErrorActionPreference = "SilentlyContinue"
Write-Host "Uninstalling Easy_Terminal..." -ForegroundColor Yellow

$InstallDir = $PSScriptRoot

# Remove Desktop & Start Menu shortcuts
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = [Environment]::GetFolderPath("Programs")
Remove-Item (Join-Path $Desktop "Easy_Terminal.lnk") -Force
Remove-Item (Join-Path $StartMenu "Easy_Terminal.lnk") -Force

# Remove Registry Entries
Remove-Item "HKCU:\\Software\\Classes\\Directory\\Background\\shell\\EasyTerminal" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\\Software\\Classes\\Directory\\shell\\EasyTerminal" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\\Software\\Classes\\Drive\\shell\\EasyTerminal" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\\Software\\Classes\\Directory\\Background\\shell\\CommandCenter" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\\Software\\Classes\\Directory\\shell\\CommandCenter" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\\Software\\Classes\\Drive\\shell\\CommandCenter" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Easy_Terminal" -Recurse -Force
Remove-Item "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CommandCenter" -Recurse -Force

# Remove from PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -like "*$InstallDir*") {
    $CleanPath = ($CurrentPath.Split(";") | Where-Object { $_ -ne $InstallDir -and $_ -ne "" }) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $CleanPath, "User")
}

Write-Host "✓ Removed shortcuts and registry keys." -ForegroundColor Green
Write-Host "`nTo complete uninstallation, delete this folder:"
Write-Host "  $InstallDir" -ForegroundColor Cyan
Write-Host "Uninstallation complete." -ForegroundColor Green
"""
    (setup_dir / "Uninstall-EasyTerminal.ps1").write_text(uninstall_ps1, encoding="utf-8")

    print(f"==> Install Wizard package created at: {setup_dir}")
    return setup_dir


def make_inno_setup_script() -> Path:
    """Generates an Inno Setup script (.iss) for optional native installer compilation."""
    iss_dir = ROOT_DIR / "packaging"
    iss_dir.mkdir(exist_ok=True)
    iss_path = iss_dir / "installer.iss"

    iss_content = """#define MyAppName "Easy_Terminal"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Easy_Terminal Contributors"
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
DefaultDirName={localappdata}\\Programs\\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\\dist
OutputBaseFilename=Easy_Terminal-Setup-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\\assets\\app.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "contextmenu"; Description: "Add 'Open in Terminal' to Windows Explorer right-click menu"; GroupDescription: "Windows Explorer Integration:"; Flags: checkablefirst

[Registry]
Root: HKCU; Subkey: "Software\\Classes\\Directory\\Background\\shell\\EasyTerminal"; ValueType: string; ValueName: ""; ValueData: "Open in Terminal"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\\Classes\\Directory\\Background\\shell\\EasyTerminal"; ValueType: string; ValueName: "Icon"; ValueData: "\"{app}\\{#MyAppExeName}\""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\\Classes\\Directory\\Background\\shell\\EasyTerminal\\command"; ValueType: string; ValueName: ""; ValueData: "\"{app}\\{#MyAppExeName}\" \"%V\""; Tasks: contextmenu

Root: HKCU; Subkey: "Software\\Classes\\Directory\\shell\\EasyTerminal"; ValueType: string; ValueName: ""; ValueData: "Open in Terminal"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\\Classes\\Directory\\shell\\EasyTerminal"; ValueType: string; ValueName: "Icon"; ValueData: "\"{app}\\{#MyAppExeName}\""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\\Classes\\Directory\\shell\\EasyTerminal\\command"; ValueType: string; ValueName: ""; ValueData: "\"{app}\\{#MyAppExeName}\" \"%1\""; Tasks: contextmenu

Root: HKCU; Subkey: "Software\\Classes\\Drive\\shell\\EasyTerminal"; ValueType: string; ValueName: ""; ValueData: "Open in Terminal"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\\Classes\\Drive\\shell\\EasyTerminal"; ValueType: string; ValueName: "Icon"; ValueData: "\"{app}\\{#MyAppExeName}\""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\\Classes\\Drive\\shell\\EasyTerminal\\command"; ValueType: string; ValueName: ""; ValueData: "\"{app}\\{#MyAppExeName}\" \"%1\""; Tasks: contextmenu

[Files]
Source: "..\\dist\\Easy_Terminal\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; IconFilename: "{app}\\assets\\app.ico"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; IconFilename: "{app}\\assets\\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
"""
    iss_path.write_text(iss_content, encoding="utf-8")
    print(f"==> Inno Setup script generated at: {iss_path}")
    return iss_path


def main() -> None:
    print("==================================================")
    print("   Easy_Terminal - Distribution Builder           ")
    print("==================================================")
    compiled_dir = DIST_DIR / "Easy_Terminal"
    if "--rebuild" in sys.argv or not (compiled_dir / "Easy_Terminal.exe").exists():
        compiled_dir = build_pyinstaller_binary()

    make_portable_distribution(compiled_dir)
    make_installer_package(compiled_dir)
    make_inno_setup_script()

    print("\n[SUCCESS] All distribution targets built successfully:")
    print(f"  1. Portable Package: {DIST_DIR / 'Easy_Terminal-Portable'}")
    print(f"  2. Portable ZIP:     {DIST_DIR / 'Easy_Terminal-Portable.zip'}")
    print(f"  3. Install Wizard:   {DIST_DIR / 'Easy_Terminal-Setup'}")
    print(f"  4. Inno Script:      {ROOT_DIR / 'packaging' / 'installer.iss'}")


if __name__ == "__main__":
    main()
