$wshell = New-Object -ComObject WScript.Shell
$icoPath = (Resolve-Path "scriber\assets\icon.ico").Path

$destinations = @(
    [System.IO.Path]::Combine($env:USERPROFILE, "Desktop", "Scriber.lnk"),
    [System.IO.Path]::Combine($env:USERPROFILE, "OneDrive", "Desktop", "Scriber.lnk"),
    [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs", "Scriber.lnk")
)

foreach ($dest in $destinations) {
    if (Test-Path $dest) {
        $shortcut = $wshell.CreateShortcut($dest)
        $shortcut.IconLocation = "$icoPath,0"
        $shortcut.Save()
        Write-Host "Updated shortcut icon: $dest"
    }
}
