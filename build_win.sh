#!/bin/bash
# Build QuickButtons Windows executable with PyInstaller (cross-platform)
# Requires: wine, python for windows, pyinstaller for windows

# Path to your Windows Python installation (edit as needed)
WIN_PYTHON=~/.wine/drive_c/Python312/python.exe
WIN_PIP=~/.wine/drive_c/Python312/Scripts/pip.exe
WIN_PYINSTALLER=~/.wine/drive_c/Python312/Scripts/pyinstaller.exe

# Install PyInstaller if needed
wine "$WIN_PIP" install pyinstaller
# Build
wine "$WIN_PYINSTALLER" --onefile --windowed --add-data "translations.json;." --add-data "themes.json;." quickbuttons.py

if [ -f dist/QuickButtons.exe ]; then
    echo "Build successful! Find your executable in the dist folder."
else
    echo "Build failed. Check the output above for errors."
fi 