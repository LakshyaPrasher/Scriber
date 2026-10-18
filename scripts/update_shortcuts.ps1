# scripts/update_shortcuts.ps1
# Wrapper that invokes the comprehensive shortcut installer script.
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $PSScriptRoot "install_windows_shortcuts.ps1")
