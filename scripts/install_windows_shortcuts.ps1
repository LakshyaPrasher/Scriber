# scripts/install_windows_shortcuts.ps1
# Creates/refreshes Scriber shortcuts across Windows Desktop, OneDrive Desktop, and Start Menu.
# Targets the standalone compiled binary executable: dist\Scriber\Scriber.exe

$ErrorActionPreference = "Stop"

$workspaceRoot = (Resolve-Path ".").Path
$exePath = Join-Path $workspaceRoot "dist\Scriber\Scriber.exe"
$workingDir = Join-Path $workspaceRoot "dist\Scriber"
$iconIco = Join-Path $workspaceRoot "scriber\assets\icon.ico"

if (-not (Test-Path $exePath)) {
    # If onedir exe not found, check root dist/Scriber.exe
    $exePath = Join-Path $workspaceRoot "dist\Scriber.exe"
    $workingDir = $workspaceRoot
}

if (-not (Test-Path $exePath)) {
    Write-Error "Could not find compiled binary executable at: $exePath. Please run python build_desktop.py first."
    exit 1
}

$wshell = New-Object -ComObject WScript.Shell

$destinations = @(
    [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "Scriber.lnk"),
    [System.IO.Path]::Combine($env:USERPROFILE, "Desktop", "Scriber.lnk"),
    [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs", "Scriber.lnk")
)

# If OneDrive Desktop exists, add it as well
$oneDriveDesktop = [System.IO.Path]::Combine($env:USERPROFILE, "OneDrive", "Desktop")
if (Test-Path $oneDriveDesktop) {
    $destinations += [System.IO.Path]::Combine($oneDriveDesktop, "Scriber.lnk")
}

$destinations = $destinations | Select-Object -Unique

foreach ($dest in $destinations) {
    try {
        $parentDir = [System.IO.Path]::GetDirectoryName($dest)
        if (-not (Test-Path $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }

        # Remove existing shortcut to ensure clean PropertyStore
        if (Test-Path $dest) {
            Remove-Item $dest -Force -ErrorAction SilentlyContinue
        }

        $shortcut = $wshell.CreateShortcut($dest)
        $shortcut.TargetPath = $exePath
        $shortcut.Arguments = ""
        $shortcut.WorkingDirectory = $workingDir
        $shortcut.IconLocation = "$exePath,0"
        $shortcut.Description = "Scriber - Studio Intelligence and Voice Synthesis"
        $shortcut.WindowStyle = 1
        $shortcut.Save()

        Write-Host "[+] Installed executable shortcut: $dest -> $exePath"
    } catch {
        Write-Warning "Failed creating shortcut at $($dest): $($_.Exception.Message)"
    }
}

# Flush Windows Explorer icon cache using Python ctypes or shell notify
try {
    $pythonExe = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        & $pythonExe -c "import ctypes; ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)"
    }
} catch {
    Start-Process -FilePath "ie4uinit.exe" -ArgumentList "-show" -NoNewWindow -ErrorAction SilentlyContinue
}

Write-Host "`nAll Windows shortcuts now point directly to the native executable Scriber.exe."
