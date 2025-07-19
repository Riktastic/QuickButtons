@echo off
REM ==========================================
REM       BUILD PYTHON APP: QuickButtons
REM  Uses pip venv + PyInstaller for Windows
REM  OPTIMIZED FOR PERFORMANCE & SIZE
REM ==========================================

REM ---- STEP 0: Set Defaults and Parse Args ----
set "USER_CHOICE=RESET"  REM Default is RESET
if /I "%1"=="/reuse" set "USER_CHOICE=REUSE"

REM ---- STEP 1: Decide Whether to Reuse venv ----
echo.
echo ==========================================
echo         [1] CHECK VIRTUAL ENV
echo ==========================================
if exist venv (
    if "%USER_CHOICE%" == "REUSE" (
        echo [AUTO] Reusing existing virtual environment.
    ) else (
        echo [AUTO] Removing existing virtual environment...
        rmdir /s /q venv
    )
)

REM ---- STEP 2: Create Virtual Environment if Needed ----
if not exist venv (
    echo.
    echo ==========================================
    echo       [2] CREATE VIRTUAL ENVIRONMENT
    echo ==========================================
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Ensure Python is installed and 'python' is on your PATH.
        exit /b 1
    )
)

REM ---- STEP 3: Activate Virtual Environment ----
echo.
echo ==========================================
echo          [3] ACTIVATE VENV
echo ==========================================
call venv\Scripts\activate

REM ---- STEP 4: Upgrade pip ----
echo.
echo ==========================================
echo          [4] UPGRADE PIP
echo ==========================================
python -m pip install --upgrade pip

REM ---- STEP 5: Install App Dependencies ----
echo.
echo ==========================================
echo       [5] INSTALL REQUIREMENTS
echo ==========================================
pip install -r requirements-build.txt

REM ---- STEP 6: Ensure PyInstaller is Installed ----
echo.
echo ==========================================
echo       [6] ENSURE PYINSTALLER
echo ==========================================
pip install pyinstaller

REM ---- STEP 7: Clean Previous Builds ----
echo.
echo ==========================================
echo         [7] CLEAN PREVIOUS BUILDS
echo ==========================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist src\__pycache__ rmdir /s /q src\__pycache__
if exist src\core\__pycache__ rmdir /s /q src\core\__pycache__
if exist src\ui\__pycache__ rmdir /s /q src\ui\__pycache__
if exist src\utils\__pycache__ rmdir /s /q src\utils\__pycache__

REM ---- STEP 8: Set Environment Variables for Optimization ----
echo.
echo ==========================================
echo      [8] SET OPTIMIZATION FLAGS
echo ==========================================
set PYTHONOPTIMIZE=2
set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1

REM ---- STEP 9: Build with PyInstaller (Optimized) ----
echo.
echo ==========================================
echo    [9] BUILD WITH PYINSTALLER (OPTIMIZED)
echo ==========================================
REM Use optimized settings for faster build and smaller executable
pyinstaller --clean --noconfirm --log-level=WARN QuickButtons.spec

REM ---- STEP 10: Optimize Executable Size ----
echo.
echo ==========================================
echo      [10] OPTIMIZE EXECUTABLE SIZE
echo ==========================================
if exist dist\QuickButtons.exe (
    echo [INFO] Executable size before optimization:
    dir dist\QuickButtons.exe | find "QuickButtons.exe"
    
    REM Remove unnecessary files from dist
    if exist dist\QuickButtons\_internal\PIL\Tests rmdir /s /q dist\QuickButtons\_internal\PIL\Tests
    if exist dist\QuickButtons\_internal\PIL\Tests2 rmdir /s /q dist\QuickButtons\_internal\PIL\Tests2
    if exist dist\QuickButtons\_internal\PIL\TiffTags.py rmdir /s /q dist\QuickButtons\_internal\PIL\TiffTags.py
    if exist dist\QuickButtons\_internal\PIL\TiffImagePlugin.py rmdir /s /q dist\QuickButtons\_internal\PIL\TiffImagePlugin.py
    
    echo [INFO] Executable size after optimization:
    dir dist\QuickButtons.exe | find "QuickButtons.exe"
) else (
    echo [WARNING] Executable not found in dist folder
)

REM ---- STEP 11: Deactivate Environment ----
echo.
echo ==========================================
echo         [11] DEACTIVATE VENV
echo ==========================================
deactivate

:end
echo.
echo ==========================================
echo        BUILD PROCESS COMPLETE!
echo        Dist output: .\dist\
echo ==========================================
echo.
echo [INFO] Build optimizations applied:
echo   - Python optimization level 2
echo   - Stripped debug symbols
echo   - UPX compression enabled
echo   - Extensive module exclusions
echo   - Clean build environment
echo.
pause
