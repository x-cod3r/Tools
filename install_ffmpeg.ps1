# PowerShell script to download, extract, and add FFmpeg to system PATH

$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$downloadPath = "$env:TEMP\ffmpeg-release-essentials.zip"
$extractDir = "C:\ffmpeg_temp_extract"
$installDir = "C:\ffmpeg"
$ffmpegBinPath = Join-Path $installDir "bin"

Write-Host "Starting FFmpeg installation..."

# 1. Download FFmpeg
Write-Host "Downloading FFmpeg from $ffmpegUrl..."
try {
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "FFmpeg downloaded to $downloadPath"
}
catch {
    Write-Error "Failed to download FFmpeg: $($_.Exception.Message)"
    exit 1
}

# 2. Extract FFmpeg
Write-Host "Extracting FFmpeg to $extractDir..."
try {
    Expand-Archive -Path $downloadPath -DestinationPath $extractDir -Force
    
    # Find the actual FFmpeg folder inside the extracted content (e.g., ffmpeg-N.N-essentials_build)
    $extractedRootFolder = Get-ChildItem -Path $extractDir | Where-Object { $_.PSIsContainer -and $_.Name.StartsWith("ffmpeg-") } | Select-Object -First 1
    
    if ($extractedRootFolder) {
        $sourcePath = $extractedRootFolder.FullName
        Write-Host "Moving FFmpeg from $sourcePath to $installDir..."
        Move-Item -Path $sourcePath -Destination $installDir -Force
        Remove-Item -Path $extractDir -Recurse -Force # Clean up temporary extraction directory
        Write-Host "FFmpeg extracted and moved to $installDir"
    } else {
        Write-Error "Could not find the FFmpeg root folder in the extracted archive."
        exit 1
    }
}
catch {
    Write-Error "Failed to extract FFmpeg: $($_.Exception.Message)"
    exit 1
}

# 3. Add FFmpeg to System PATH
Write-Host "Adding $ffmpegBinPath to system PATH..."
try {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$ffmpegBinPath*") {
        $newPath = "$currentPath;$ffmpegBinPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        Write-Host "Successfully added FFmpeg to system PATH."
        Write-Host "Please restart any open PowerShell/CMD windows or VS Code for changes to take effect."
    } else {
        Write-Host "FFmpeg path already exists in system PATH."
    }
}
catch {
    Write-Error "Failed to add FFmpeg to system PATH: $($_.Exception.Message)"
    exit 1
}

Write-Host "FFmpeg installation script finished."
