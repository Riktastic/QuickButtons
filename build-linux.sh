#!/bin/bash

# ==========================================
#       BUILD PYTHON APP: QuickButtons
#  Uses pip venv + PyInstaller for Linux
#  OPTIMIZED FOR PERFORMANCE & SIZE
# ==========================================

# ---- STEP 0: Set Defaults and Parse Args ----
USER_CHOICE="RESET"  # Default is RESET
if [[ "$1" == "/reuse" ]]; then
  USER_CHOICE="REUSE"
fi

# ---- STEP 1: Decide Whether to Reuse venv ----
echo
echo "=========================================="
echo "        [1] CHECK VIRTUAL ENV"
echo "=========================================="
if [ -d "venv" ]; then
  if [ "$USER_CHOICE" == "REUSE" ]; then
    echo "[AUTO] Reusing existing virtual environment."
  else
    echo "[AUTO] Removing existing virtual environment..."
    rm -rf venv
  fi
fi

# ---- STEP 2: Create Virtual Environment if Needed ----
if [ ! -d "venv" ]; then
  echo
  echo "=========================================="
  echo "      [2] CREATE VIRTUAL ENVIRONMENT"
  echo "=========================================="
  python3 -m venv venv
  if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment. Ensure Python3 is installed and 'python3' is on your PATH."
    exit 1
  fi
fi

# ---- STEP 3: Activate Virtual Environment ----
echo
echo "=========================================="
echo "         [3] ACTIVATE VENV"
echo "=========================================="
# shellcheck disable=SC1091
source venv/bin/activate

# ---- STEP 4: Upgrade pip ----
echo
echo "=========================================="
echo "         [4] UPGRADE PIP"
echo "=========================================="
python -m pip install --upgrade pip

# ---- STEP 5: Install App Dependencies ----
echo
echo "=========================================="
echo "      [5] INSTALL REQUIREMENTS"
echo "=========================================="
pip install -r requirements-build.txt

# ---- STEP 6: Ensure PyInstaller is Installed ----
echo
echo "=========================================="
echo "      [6] ENSURE PYINSTALLER"
echo "=========================================="
pip install pyinstaller

# ---- STEP 7: Clean Previous Builds ----
echo
echo "=========================================="
echo "          [7] CLEAN PREVIOUS BUILDS"
echo "=========================================="
[ -d build ] && rm -rf build
[ -d dist ] && rm -rf dist
[ -d __pycache__ ] && rm -rf __pycache__
[ -d src/__pycache__ ] && rm -rf src/__pycache__
[ -d src/core/__pycache__ ] && rm -rf src/core/__pycache__
[ -d src/ui/__pycache__ ] && rm -rf src/ui/__pycache__
[ -d src/utils/__pycache__ ] && rm -rf src/utils/__pycache__

# ---- STEP 8: Set Environment Variables for Optimization ----
echo
echo "=========================================="
echo "    [8] SET OPTIMIZATION FLAGS"
echo "=========================================="
export PYTHONOPTIMIZE=2
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# ---- STEP 9: Build with PyInstaller (Optimized) ----
echo
echo "=========================================="
echo "   [9] BUILD WITH PYINSTALLER (OPTIMIZED)"
echo "=========================================="
# Use optimized settings for faster build and smaller executable
pyinstaller --clean --noconfirm --log-level=WARN QuickButtons.spec

# ---- STEP 10: Optimize Executable Size ----
echo
echo "=========================================="
echo "     [10] OPTIMIZE EXECUTABLE SIZE"
echo "=========================================="
if [ -f dist/QuickButtons ]; then
  echo "[INFO] Executable size before optimization:"
  ls -lh dist/QuickButtons

  # Remove unnecessary files from dist if they exist
  [ -d dist/QuickButtons/_internal/PIL/Tests ] && rm -rf dist/QuickButtons/_internal/PIL/Tests
  [ -d dist/QuickButtons/_internal/PIL/Tests2 ] && rm -rf dist/QuickButtons/_internal/PIL/Tests2
  [ -f dist/QuickButtons/_internal/PIL/TiffTags.py ] && rm -f dist/QuickButtons/_internal/PIL/TiffTags.py
  [ -f dist/QuickButtons/_internal/PIL/TiffImagePlugin.py ] && rm -f dist/QuickButtons/_internal/PIL/TiffImagePlugin.py

  echo "[INFO] Executable size after optimization:"
  ls -lh dist/QuickButtons
else
  echo "[WARNING] Executable not found in dist folder"
fi

# ---- STEP 11: Deactivate Environment ----
echo
echo "=========================================="
echo "        [11] DEACTIVATE VENV"
echo "=========================================="
deactivate

echo
echo "=========================================="
echo "       BUILD PROCESS COMPLETE!"
echo "       Dist output: ./dist/"
echo "=========================================="
echo
echo "[INFO] Build optimizations applied:"
echo "  - Python optimization level 2"
echo "  - Stripped debug symbols"
echo "  - UPX compression enabled"
echo "  - Extensive module exclusions"
echo "  - Clean build environment"
echo
read -p "Press enter to continue..."
