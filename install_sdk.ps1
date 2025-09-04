# Define install path
$AndroidRoot = "C:\dev\android"
$ToolsURL = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
$ZipFile = "$env:TEMP\cmdline-tools.zip"
$CmdlineTools = "$AndroidRoot\cmdline-tools"
$LatestTools = "$CmdlineTools\latest"
$SdkManager = "$LatestTools\bin\sdkmanager.bat"

# Function: Check for Java
function Check-Java {
    if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
        Write-Warning "⚠ JAVA_HOME is not set or Java is not in PATH!"
        Write-Host "`nYou need to install Java JDK 11 or 17 for Android SDK to work." -ForegroundColor Yellow
        Write-Host "Opening download page in your browser..." -ForegroundColor Cyan
        Start-Process "https://adoptium.net/en-GB/temurin/releases/"
        Read-Host -Prompt "`nPress [Enter] after installing Java and setting JAVA_HOME"
    } else {
        Write-Host "✅ Java detected: $((Get-Command java).Source)" -ForegroundColor Green
    }
}

# Create folders
Write-Host "📁 Creating Android SDK directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $LatestTools | Out-Null

# Download command line tools
Write-Host "🌐 Downloading Android command-line tools..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $ToolsURL -OutFile $ZipFile

# Extract SDK
Write-Host "📦 Extracting SDK tools..." -ForegroundColor Cyan
Expand-Archive -Force -Path $ZipFile -DestinationPath "$CmdlineTools\temp"

# Move to proper location
Move-Item -Path "$CmdlineTools\temp\cmdline-tools\*" -Destination $LatestTools
Remove-Item "$CmdlineTools\temp" -Recurse -Force
Remove-Item $ZipFile

# Java check
Check-Java

# Install SDK components
Write-Host "🔧 Installing platform-tools, build-tools, and Android platform..." -ForegroundColor Cyan
& $SdkManager --sdk_root=$AndroidRoot "platform-tools" "build-tools;34.0.0" "platforms;android-34"

# Accept licenses
Write-Host "📜 Accepting SDK licenses..." -ForegroundColor Cyan
& $SdkManager --licenses

# Set Flutter Android SDK path
Write-Host "⚙ Configuring Flutter to use SDK at $AndroidRoot" -ForegroundColor Cyan
flutter config --android-sdk "$AndroidRoot"

# Add ADB to user PATH if not already there
$EnvPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
$AdbPath = "$AndroidRoot\platform-tools"
if ($EnvPath -notlike "*$AdbPath*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$EnvPath;$AdbPath", "User")
    Write-Host "✅ ADB added to User PATH" -ForegroundColor Green
}

Write-Host "`n🎉 SDK setup complete!"
Write-Host "Run 'flutter doctor' to verify Android toolchain." -ForegroundColor Yellow
