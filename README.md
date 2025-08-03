# Tools

This repository contains a collection of useful Python and PowerShell scripts.

## Scripts

### 1. PDF to High-Quality Image Converter (`pdf_converter_gui.py`)

A Python-based GUI application built with Tkinter that allows users to convert PDF files into high-quality images (PNG, JPEG, TIFF, BMP). It provides options for selecting PDF files, output directories, image formats, and various quality (DPI) presets.

**Features:**
- Convert PDF pages to individual image files.
- Supports PNG, JPEG, TIFF, and BMP output formats.
- Adjustable quality/zoom factor (DPI) with presets (Screen, High, Print, Ultra).
- Progress bar and status updates during conversion.
- Error handling and user-friendly interface.

**Dependencies:**
- `tkinter` (built-in Python library)
- `PyMuPDF` (fitz)
- `Pillow` (PIL)
- `pathlib` (built-in Python library)
- `queue` (built-in Python library)
- `threading` (built-in Python library)

**How to Run:**
1. Ensure you have Python installed.
2. Install the required libraries:
   ```bash
   pip install PyMuPDF Pillow
   ```
3. Run the script:
   ```bash
   python pdf_converter_gui.py
   ```

### 2. Voice Recorder (`sound_recorder.py`)

A simple voice recorder application built with Tkinter. It allows users to record audio, apply noise cancellation, adjust volume, and save recordings in various formats (WAV, FLAC, OGG, MP3). It also features a basic real-time waveform visualization.

**Features:**
- Record audio from your microphone.
- Adjustable volume control.
- Optional noise cancellation with adjustable level.
- Save recordings in WAV, FLAC, OGG, or MP3 formats.
- Real-time audio waveform visualization.

**Dependencies:**
- `tkinter` (built-in Python library)
- `sounddevice`
- `numpy`
- `scipy`
- `soundfile`
- `pydub`

**How to Run:**
1. Ensure you have Python installed.
2. Install the required libraries:
   ```bash
   pip install sounddevice numpy scipy soundfile pydub
   ```
   You might also need to install `portaudio` for `sounddevice` to work correctly. On Windows, you can often install it via `pipwin install pyaudio` or by installing the appropriate C++ build tools.
   For MP3 export, `pydub` requires `ffmpeg`. See the `install_ffmpeg.ps1` script for an automated way to install FFmpeg on Windows.
3. Run the script:
   ```bash
   python sound_recorder.py
   ```

### 3. FFmpeg Installer (`install_ffmpeg.ps1`)

A PowerShell script designed to automate the download, extraction, and addition of FFmpeg to the system's PATH environment variable on Windows. This script is particularly useful for setting up FFmpeg, which is a prerequisite for certain functionalities in `sound_recorder.py` (e.g., MP3 export).

**Features:**
- Downloads the latest FFmpeg essentials build from `gyan.dev`.
- Extracts FFmpeg to a specified directory.
- Adds the FFmpeg `bin` directory to the system's PATH, making `ffmpeg` commands accessible from any terminal.
- Includes error handling for download and extraction processes.

**How to Run:**
1. Open PowerShell as an Administrator.
2. Navigate to the directory containing `install_ffmpeg.ps1`.
3. Run the script:
   ```powershell
   .\install_ffmpeg.ps1
   ```
   You might need to adjust your PowerShell execution policy to run local scripts:
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   (Choose 'Y' to confirm)

**Note:** After running the FFmpeg installer, you may need to restart your terminal or VS Code for the PATH changes to take effect.
