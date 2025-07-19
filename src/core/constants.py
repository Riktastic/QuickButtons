"""Application constants and configuration."""

import os
import sys

# Application metadata
APP_VERSION = "1.0.0"

# 42 - the answer to life, the universe, and everything

# Configuration file and button size limits
def get_user_data_dir():
    """Get the user data directory for the application."""
    import platform
    app_name = "QuickButtons"
    
    if platform.system() == "Windows":
        # Windows: %APPDATA%\QuickButtons
        app_data = os.getenv('APPDATA')
        if app_data:
            return os.path.join(app_data, app_name)
        else:
            # Fallback to user home directory
            return os.path.join(os.path.expanduser("~"), "AppData", "Roaming", app_name)
    
    elif platform.system() == "Darwin":
        # macOS: ~/Library/Application Support/QuickButtons
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
    
    else:
        # Linux and other Unix-like systems: ~/.config/QuickButtons
        return os.path.join(os.path.expanduser("~"), ".config", app_name)

# Ensure user data directory exists
USER_DATA_DIR = get_user_data_dir()
os.makedirs(USER_DATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(USER_DATA_DIR, "config.json")
LOG_FILE = os.path.join(USER_DATA_DIR, "quickbuttons.log")
MAX_BTN_SIZE = 120
MIN_BTN_SIZE = 64

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource file, works for both development and PyInstaller.
    
    Args:
        relative_path (str): Path relative to the project root
        
    Returns:
        str: Absolute path to the resource file
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not running under PyInstaller, use the current directory
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    return os.path.join(base_path, relative_path)

# File paths (using resource path for PyInstaller compatibility)
ICON_PATH = get_resource_path("assets/quickbuttons.png")
ICON_ICO_PATH = get_resource_path("assets/quickbuttons.ico")
TRANSLATIONS_FILE = get_resource_path("assets/translations.json")
THEMES_FILE = get_resource_path("assets/themes.json")

# Try to import keyboard for global hotkey support
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False 