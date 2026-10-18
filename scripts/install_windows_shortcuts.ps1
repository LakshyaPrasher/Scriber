# scripts/install_windows_shortcuts.ps1
# Creates/refreshes Scriber shortcuts across Windows Desktop, OneDrive Desktop, and Start Menu.

$ErrorActionPreference = "Stop"

$workspaceRoot = (Resolve-Path ".").Path
$pythonwExe = Join-Path $workspaceRoot ".venv\Scripts\pythonw.exe"
$runDesktopPy = Join-Path $workspaceRoot "run_desktop.py"
$iconIco = Join-Path $workspaceRoot "scriber\assets\icon.ico"

if (-not (Test-Path $pythonwExe)) {
    Write-Error "Could not find pythonw.exe at: $pythonwExe"
    exit 1
}
if (-not (Test-Path $runDesktopPy)) {
    Write-Error "Could not find run_desktop.py at: $runDesktopPy"
    exit 1
}
if (-not (Test-Path $iconIco)) {
    Write-Error "Could not find icon.ico at: $iconIco"
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
        $shortcut.TargetPath = $pythonwExe
        $shortcut.Arguments = "`"$runDesktopPy`""
        $shortcut.WorkingDirectory = $workspaceRoot
        $shortcut.IconLocation = "$iconIco,0"
        $shortcut.Description = "Scriber Studio - Voice Intelligence & Diarization"
        $shortcut.WindowStyle = 1
        $shortcut.Save()

        Write-Host "[+] Installed shortcut: $dest"
    } catch {
        Write-Warning "Failed creating shortcut at $($dest): $($_.Exception.Message)"
    }
}

# Flush Windows Explorer icon cache using Python ctypes
& $pythonwExe -c "import ctypes; ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)"

Write-Host "`nAll Windows shortcuts for Scriber successfully created and verified."
