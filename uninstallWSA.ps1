# Define log function
function Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $message"
    Write-Host $logMessage
}

Log "🟡 Starting WSA full uninstall..."

# Step 1: Uninstall WSA
try {
    Log "🔧 Attempting to uninstall Windows Subsystem for Android..."
    Get-AppxPackage *WindowsSubsystemForAndroid* | Remove-AppxPackage
    Log "✅ WSA uninstall command issued."
} catch {
    Log "❌ Failed to uninstall WSA: $_"
}

# Step 2: Remove user AppData
try {
    $userAppData = "$env:LOCALAPPDATA\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_*"
    Log "🗑️ Attempting to remove AppData: $userAppData"
    Remove-Item -Recurse -Force $userAppData -ErrorAction Stop
    Log "✅ AppData removed."
} catch {
    Log "⚠️ Could not remove AppData (may already be gone): $_"
}

# Step 3: Remove ProgramData
try {
    $programDataPath = "C:\ProgramData\Microsoft\Windows\WSA"
    Log "🗑️ Attempting to remove ProgramData: $programDataPath"
    Remove-Item -Recurse -Force $programDataPath -ErrorAction Stop
    Log "✅ ProgramData removed."
} catch {
    Log "⚠️ Could not remove ProgramData (may already be gone): $_"
}

Log "✅ WSA uninstall complete."
