"""System utilities and platform-specific functionality."""

import os
import sys
import platform
import subprocess
from .logger import logger

def is_frozen():
    """
    Check if the application is running as a frozen executable (PyInstaller).
    
    Returns:
        bool: True if running as frozen executable, False otherwise
    """
    return getattr(sys, 'frozen', False)

def detect_python_executable():
    """
    Detect the appropriate Python executable to use for running scripts.
    
    When running from source, use sys.executable.
    When running as frozen executable, try to find the system Python.
    
    Returns:
        str: Path to Python executable, or empty string if not found
    """
    if not is_frozen():
        # Running from source, use current Python interpreter
        return sys.executable
    
    # Running as frozen executable, need to find system Python
    if is_windows():
        # On Windows, try common Python locations
        possible_paths = [
            "python.exe",
            "python3.exe",
            r"C:\Python*\python.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python*\python.exe",
            r"C:\Program Files\Python*\python.exe",
            r"C:\Program Files (x86)\Python*\python.exe"
        ]
        
        # First try if python is in PATH (fastest)
        try:
            result = subprocess.run(["python", "--version"], 
                                  capture_output=True, text=True, timeout=2)  # Reduced timeout
            if result.returncode == 0:
                return "python"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            result = subprocess.run(["python3", "--version"], 
                                  capture_output=True, text=True, timeout=2)  # Reduced timeout
            if result.returncode == 0:
                return "python3"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try to find Python in common installation paths (slower, limit search)
        import glob
        for pattern in possible_paths[2:4]:  # Only try first 2 patterns to avoid slow glob searches
            try:
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]
            except Exception:
                continue
        
        # No Python found
        return ""
        
    else:
        # On Linux/Mac, try common commands
        for cmd in ["python3", "python"]:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True, timeout=2)  # Reduced timeout
                if result.returncode == 0:
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        # No Python found
        return ""

def get_python_executable(config=None):
    """
    Get the appropriate Python executable to use for running scripts.
    
    When running from source, use sys.executable.
    When running as frozen executable, try to find the system Python.
    
    Args:
        config: Optional ConfigManager instance to avoid circular imports
    
    Returns:
        str: Path to Python executable, or empty string if no system Python found
    """
    # Check if user has specified a custom Python executable
    if config is None:
        try:
            from src.core.managers.config_manager import ConfigManager
            config = ConfigManager()
        except Exception as e:
            logger.warning(f"Could not load config for Python executable check: {e}")
            config = None
    
    if config:
        user_python = config.get("python_executable", "")
        if user_python and os.path.exists(user_python):
            logger.info(f"Using user-specified Python executable: {user_python}")
            return user_python
    
    # If no user-specified Python or it doesn't exist, use detected one
    detected_python = detect_python_executable()
    if detected_python:
        return detected_python
    
    # Never use the bundled Python - require a proper system Python
    logger.error("No system Python executable found. Script execution requires a proper Python installation.")
    return ""

def get_platform():
    """
    Get the current platform information.
    
    Returns:
        str: Platform name (windows, linux, darwin)
    """
    return platform.system().lower()

def is_windows():
    """
    Check if running on Windows.
    
    Returns:
        bool: True if on Windows, False otherwise
    """
    return get_platform() == 'windows'

def is_linux():
    """
    Check if running on Linux.
    
    Returns:
        bool: True if on Linux, False otherwise
    """
    return get_platform() == 'linux'

def is_macos():
    """
    Check if running on macOS.
    
    Returns:
        bool: True if on macOS, False otherwise
    """
    return get_platform() == 'darwin'

def detect_desktop_environment():
    """
    Detect the current desktop environment on Linux.
    
    Returns:
        str: Desktop environment name (gnome, kde, xfce, etc.) or 'unknown'
    """
    if not is_linux():
        return 'unknown'
    
    # Check environment variables first (fastest)
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    if desktop:
        if 'gnome' in desktop:
            return 'gnome'
        elif 'kde' in desktop:
            return 'kde'
        elif 'xfce' in desktop:
            return 'xfce'
        elif 'mate' in desktop:
            return 'mate'
        elif 'cinnamon' in desktop:
            return 'cinnamon'
        elif 'lxde' in desktop:
            return 'lxde'
        elif 'lxqt' in desktop:
            return 'lxqt'
        elif 'budgie' in desktop:
            return 'budgie'
        elif 'pantheon' in desktop:
            return 'pantheon'
    
    # Check session type (second fastest)
    session = os.environ.get('DESKTOP_SESSION', '').lower()
    if session:
        if 'gnome' in session:
            return 'gnome'
        elif 'kde' in session:
            return 'kde'
        elif 'xfce' in session:
            return 'xfce'
        elif 'mate' in session:
            return 'mate'
        elif 'cinnamon' in session:
            return 'cinnamon'
        elif 'lxde' in session:
            return 'lxde'
        elif 'lxqt' in session:
            return 'lxqt'
        elif 'budgie' in session:
            return 'budgie'
        elif 'pantheon' in session:
            return 'pantheon'
    
    # Try to detect by checking for specific processes (slowest, with timeout)
    try:
        result = subprocess.run(['pgrep', '-f', 'gnome-shell'], capture_output=True, timeout=0.5)
        if result.returncode == 0:
            return 'gnome'
    except Exception:
        pass
    
    try:
        result = subprocess.run(['pgrep', '-f', 'plasmashell'], capture_output=True, timeout=0.5)
        if result.returncode == 0:
            return 'kde'
    except Exception:
        pass
    
    try:
        result = subprocess.run(['pgrep', '-f', 'xfce4-session'], capture_output=True, timeout=0.5)
        if result.returncode == 0:
            return 'xfce'
    except Exception:
        pass
    
    return 'unknown'

def detect_system_theme():
    """Detect system light/dark mode preference for Linux (GNOME/KDE) and Windows."""
    # Linux (GNOME and KDE) - Optimized with faster detection order
    if sys.platform.startswith("linux"):
        # Try environment variables first (fastest)
        gtk_theme = os.environ.get("GTK_THEME", "").lower()
        kde_theme = os.environ.get("KDE_COLOR_SCHEME", "").lower()
        
        if "dark" in gtk_theme or "dark" in kde_theme:
            return "dark"
        elif "light" in gtk_theme or "light" in kde_theme:
            return "light"
        
        # Try GNOME (most common)
        try:
            result = subprocess.run([
                "gsettings", "get", "org.gnome.desktop.interface", "color-scheme"
            ], capture_output=True, text=True, timeout=1)  # Add timeout
            if "prefer-dark" in result.stdout:
                return "dark"
            elif "default" in result.stdout or "prefer-light" in result.stdout:
                return "light"
        except Exception:
            pass
        
        # Try KDE Plasma (second most common)
        try:
            result = subprocess.run([
                "kreadconfig5", "--file", "kcmdisplayrc", "--group", "General", "--key", "ColorScheme"
            ], capture_output=True, text=True, timeout=1)  # Add timeout
            if "BreezeDark" in result.stdout or "Dark" in result.stdout:
                return "dark"
            elif "Breeze" in result.stdout or "Light" in result.stdout:
                return "light"
        except Exception:
            pass
        
        # Try KDE 4 (older versions) - least common, try last
        try:
            result = subprocess.run([
                "kreadconfig", "--file", "kcmdisplayrc", "--group", "General", "--key", "ColorScheme"
            ], capture_output=True, text=True, timeout=1)  # Add timeout
            if "BreezeDark" in result.stdout or "Dark" in result.stdout:
                return "dark"
            elif "Breeze" in result.stdout or "Light" in result.stdout:
                return "light"
        except Exception:
            pass
    
    # Windows
    if sys.platform.startswith("win"):
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if value == 1 else "dark"
        except Exception:
            pass
    
    return "dark" 