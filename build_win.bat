@echo off
REM Build QuickButtons Windows executable with PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "translations.json;." --add-data "themes.json;." quickbuttons.py
if exist dist\QuickButtons.exe (
    echo Build successful! Find your executable in the dist folder.
) else (
    echo Build failed. Check the output above for errors.
) 