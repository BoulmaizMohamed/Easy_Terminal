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
    """Compiles CommandCenter using PyInstaller."""
    print("==> Building executable with PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--name",
        "CommandCenter",
        "--add-data",
        f"command_center/styles.tcss{os.pathsep}command_center",
        "--add-data",
        f"command_center/data/seed_library.json{os.pathsep}command_center/data",
        "command_center/__main__.py",
    ]
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
    out_dir = DIST_DIR / "CommandCenter"
    if not (out_dir / "CommandCenter.exe").exists():
        raise RuntimeError("PyInstaller build failed to produce CommandCenter.exe")
    print(f"==> PyInstaller build successful: {out_dir}")
    return out_dir


def make_portable_distribution(source_dir: Path) -> Path:
    """Creates a standalone portable distribution folder and ZIP archive."""
    print("==> Creating Portable distribution...")
    portable_dir = DIST_DIR / "CommandCenter-Portable"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    shutil.copytree(source_dir, portable_dir)

    # 1. Add portable.flag to route data into ./data/ rather than %APPDATA%
    (portable_dir / "portable.flag").write_text(
        "# Marker file indicating Command Center should run in self-contained portable mode.\n",
        encoding="utf-8",
    )

    # 2. Pre-create local data folder
    (portable_dir / "data").mkdir(exist_ok=True)

    # 3. Add Portable README
    readme_content = (
        "Command Center - Portable Edition\n"
        "==================================\n\n"
        "This version is 100% self-contained. It can run from a USB drive,\n"
        "Desktop, or network share without installing or leaving files in AppData.\n\n"
        "HOW TO RUN:\n"
        "1. Double-click CommandCenter.exe to launch.\n"
        "2. All history, settings, and library databases are saved locally in the 'data' folder.\n\n"
        "To return to standard non-portable mode, simply delete 'portable.flag'.\n"
    )
    (portable_dir / "README_PORTABLE.txt").write_text(readme_content, encoding="utf-8")

    # 4. Create ZIP archive
    zip_path = DIST_DIR / "CommandCenter-Portable.zip"
    print(f"==> Compressing to {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in portable_dir.rglob("*"):
            zf.write(file, arcname=file.relative_to(DIST_DIR))

    print(f"==> Portable ZIP created: {zip_path}")
    return zip_path


def make_installer_package(source_dir: Path) -> Path:
    """Prepares the install wizard package with one-click setup & uninstall scripts."""
    print("==> Creating Install Wizard package...")
    setup_dir = DIST_DIR / "CommandCenter-Setup"
    if setup_dir.exists():
        shutil.rmtree(setup_dir)
    shutil.copytree(source_dir, setup_dir)

    # Setup batch launcher
    (setup_dir / "setup.bat").write_text(
        "@echo off\r\n"
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0Setup-CommandCenter.ps1\"\r\n"
        "pause\r\n",
        encoding="utf-8",
    )

    # Uninstall batch launcher
    (setup_dir / "uninstall.bat").write_text(
        "@echo off\r\n"
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0Uninstall-CommandCenter.ps1\"\r\n"
        "pause\r\n",
        encoding="utf-8",
    )

    # Setup PowerShell script
    setup_ps1 = """# Command Center - Windows Setup Wizard
# Installs Command Center per-user without requiring administrative privileges.

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     COMMAND CENTER - SETUP WIZARD      " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SourceDir = $PSScriptRoot
$DefaultDest = Join-Path $env:LOCALAPPDATA "Programs\\CommandCenter"

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
Copy-Item -Path (Join-Path $SourceDir "*") -Destination $TargetDir -Recurse -Force -Exclude "setup.bat","Setup-CommandCenter.ps1"

# Create Shortcuts via WScript.Shell
$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$DesktopOpt = Read-Host "Create Desktop shortcut? (Y/n)"
if ($DesktopOpt -ne "n" -and $DesktopOpt -ne "N") {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $Shortcut = $WshShell.CreateShortcut((Join-Path $DesktopPath "Command Center.lnk"))
    $Shortcut.TargetPath = (Join-Path $TargetDir "CommandCenter.exe")
    $Shortcut.WorkingDirectory = $TargetDir
    $Shortcut.Description = "Command Center Desktop Terminal"
    $Shortcut.Save()
    Write-Host "✓ Desktop shortcut created." -ForegroundColor Green
}

# Start Menu shortcut
$StartMenuPath = [Environment]::GetFolderPath("Programs")
$StartShortcut = $WshShell.CreateShortcut((Join-Path $StartMenuPath "Command Center.lnk"))
$StartShortcut.TargetPath = (Join-Path $TargetDir "CommandCenter.exe")
$StartShortcut.WorkingDirectory = $TargetDir
$StartShortcut.Description = "Command Center Desktop Terminal"
$StartShortcut.Save()
Write-Host "✓ Start Menu shortcut created." -ForegroundColor Green

# Add to user PATH
$PathOpt = Read-Host "Add Command Center to user PATH (run 'commandcenter' from terminal)? (Y/n)"
if ($PathOpt -ne "n" -and $PathOpt -ne "N") {
    $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($CurrentPath -notlike "*$TargetDir*") {
        $NewPath = "$CurrentPath;$TargetDir"
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        Write-Host "✓ Added to User PATH environment variable." -ForegroundColor Green
    }
}

# Windows Add/Remove Programs registry entry
$RegPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CommandCenter"
if (!(Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
}
Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "Command Center"
Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "Command Center Contributors"
Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value $TargetDir
Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value "`"$TargetDir\\uninstall.bat`""

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Installation completed successfully!  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "You can now launch Command Center from your Start Menu, Desktop, or:"
Write-Host "  $TargetDir\\CommandCenter.exe" -ForegroundColor Cyan
"""
    (setup_dir / "Setup-CommandCenter.ps1").write_text(setup_ps1, encoding="utf-8")

    # Uninstall PowerShell script
    uninstall_ps1 = """# Command Center - Uninstaller

$ErrorActionPreference = "SilentlyContinue"
Write-Host "Uninstalling Command Center..." -ForegroundColor Yellow

$InstallDir = $PSScriptRoot

# Remove Desktop & Start Menu shortcuts
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = [Environment]::GetFolderPath("Programs")
Remove-Item (Join-Path $Desktop "Command Center.lnk") -Force
Remove-Item (Join-Path $StartMenu "Command Center.lnk") -Force

# Remove Registry Entry
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
    (setup_dir / "Uninstall-CommandCenter.ps1").write_text(uninstall_ps1, encoding="utf-8")

    print(f"==> Install Wizard package created at: {setup_dir}")
    return setup_dir


def make_inno_setup_script() -> Path:
    """Generates an Inno Setup script (.iss) for optional native installer compilation."""
    iss_dir = ROOT_DIR / "packaging"
    iss_dir.mkdir(exist_ok=True)
    iss_path = iss_dir / "installer.iss"

    iss_content = """#define MyAppName "Command Center"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Command Center Team"
#define MyAppURL "https://github.com/your-username/command-center"
#define MyAppExeName "CommandCenter.exe"

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
OutputBaseFilename=CommandCenter-Setup-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\\dist\\CommandCenter\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
"""
    iss_path.write_text(iss_content, encoding="utf-8")
    print(f"==> Inno Setup script generated at: {iss_path}")
    return iss_path


def main() -> None:
    print("==================================================")
    print("   Command Center - Distribution Builder          ")
    print("==================================================")
    compiled_dir = DIST_DIR / "CommandCenter"
    if not (compiled_dir / "CommandCenter.exe").exists():
        compiled_dir = build_pyinstaller_binary()

    make_portable_distribution(compiled_dir)
    make_installer_package(compiled_dir)
    make_inno_setup_script()

    print("\n[SUCCESS] All distribution targets built successfully:")
    print(f"  1. Portable Package: {DIST_DIR / 'CommandCenter-Portable'}")
    print(f"  2. Portable ZIP:     {DIST_DIR / 'CommandCenter-Portable.zip'}")
    print(f"  3. Install Wizard:   {DIST_DIR / 'CommandCenter-Setup'}")
    print(f"  4. Inno Script:      {ROOT_DIR / 'packaging' / 'installer.iss'}")


if __name__ == "__main__":
    main()
