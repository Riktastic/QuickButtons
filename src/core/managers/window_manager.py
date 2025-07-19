"""Window management functionality for QuickButtons."""

import tkinter as tk
import sys
from src.utils.logger import logger


class WindowManager:
    """Handles window geometry, positioning, and management."""
    
    def __init__(self, app):
        self.app = app
        self._resize_after_id = None
    
    def setup_window(self, config_data, theme):
        """Set up the main window with proper geometry and attributes."""
        # Set window and taskbar icon
        self._set_window_icon()
        
        # Linux-specific window setup
        if sys.platform.startswith("linux"):
            try:
                from src.utils.system import detect_desktop_environment
                desktop = detect_desktop_environment()
                
                # Set window hints for better desktop integration
                if desktop == 'gnome':
                    # GNOME: Set window type hint for better integration
                    self.app.attributes('-type', 'utility')
                elif desktop == 'kde':
                    # KDE: Set window flags for better integration
                    self.app.attributes('-type', 'utility')
                else:
                    # Other DEs: Use utility window type
                    self.app.attributes('-type', 'utility')
                    
                logger.info(f"Applied Linux window setup for {desktop} desktop environment")
            except Exception as e:
                logger.warning(f"Could not apply Linux window setup: {e}")
        
        # Restore last window geometry if present and valid
        geom = config_data.get("window_geometry")
        if geom and self._is_valid_geometry(geom):
            self.app.geometry(geom)
        else:
            # Reset to default geometry if saved position is invalid
            if geom:
                logger.info(f"Saved window geometry '{geom}' is no longer valid, resetting to default")
                config_data["window_geometry"] = "220x110"
            self.app.geometry("220x110")
            # Center the window on screen
            self._center_window()
        
        self.app.minsize(120, 60)
        self.app.resizable(True, True)
        self.app.attributes("-topmost", True)
        self.app.protocol("WM_DELETE_WINDOW", self.app.on_close)
        
        # Window management
        self.app.bind('<Configure>', self._on_window_configure)
        self.app.bind('<Map>', self._on_window_map)  # When window becomes visible
    
    def _set_window_icon(self):
        """Set the window and taskbar icon."""
        try:
            from src.core.constants import ICON_ICO_PATH
            logger.info(f"Setting window icon from: {ICON_ICO_PATH}")
            
            # Try both iconbitmap and iconphoto methods
            try:
                self.app.iconbitmap(ICON_ICO_PATH)
                logger.info("Window icon set with iconbitmap successfully")
            except Exception as e:
                logger.warning(f"iconbitmap failed: {e}")
                # Fallback to iconphoto method
                try:
                    from PIL import Image, ImageTk
                    icon_img = Image.open(ICON_ICO_PATH)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.app.iconphoto(True, icon_photo)
                    logger.info("Window icon set with iconphoto successfully")
                except Exception as e2:
                    logger.warning(f"iconphoto also failed: {e2}")
            

        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")
    
    def _on_window_configure(self, event):
        """Debounce window resize/move events to avoid excessive config writes."""
        if self._resize_after_id:
            self.app.after_cancel(self._resize_after_id)
        self._resize_after_id = self.app.after(400, self._save_window_geometry)
    
    def _save_window_geometry(self):
        """Save the current window geometry to config."""
        geom = self.app.geometry()
        self.app.config_data["window_geometry"] = geom
        self.app.save_config()
        self._resize_after_id = None
    
    def _on_window_map(self, event=None):
        """Handle window becoming visible - validate position and reset if needed."""
        # Check if current position is valid
        current_geom = self.app.geometry()
        if not self._is_valid_geometry(current_geom):
            logger.info("Window position is invalid after becoming visible, centering window")
            self._center_window()
    
    def _is_valid_geometry(self, geometry_string):
        """
        Check if the saved window geometry is still valid (window would be visible on screen).
        
        Args:
            geometry_string (str): Geometry string in format "widthxheight+x+y"
            
        Returns:
            bool: True if geometry is valid, False otherwise
        """
        try:
            # Parse geometry string
            if 'x' not in geometry_string or '+' not in geometry_string:
                return False
            
            # Split into size and position parts
            size_part, pos_part = geometry_string.split('+', 1)
            if 'x' not in size_part:
                return False
            
            width, height = map(int, size_part.split('x'))
            x, y = map(int, pos_part.split('+'))
            
            # Get screen dimensions
            screen_width = self.app.winfo_screenwidth()
            screen_height = self.app.winfo_screenheight()
            
            # Check if window would be completely off-screen
            if x >= screen_width or y >= screen_height:
                return False
            
            # Check if window would be partially off-screen (with some tolerance)
            # Allow window to be partially off-screen by a small amount (50 pixels)
            tolerance = 50
            if x + width < -tolerance or y + height < -tolerance:
                return False
            
            # Check if window is too large for screen (with some tolerance)
            if width > screen_width + tolerance or height > screen_height + tolerance:
                return False
            
            return True
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid geometry string '{geometry_string}': {e}")
            return False
    
    def _center_window(self):
        """Center the window on the primary screen."""
        try:
            # Update window info to get current size
            self.app.update_idletasks()
            
            # Get window and screen dimensions
            window_width = self.app.winfo_width()
            window_height = self.app.winfo_height()
            screen_width = self.app.winfo_screenwidth()
            screen_height = self.app.winfo_screenheight()
            
            # Calculate center position
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # Ensure window is not off-screen
            x = max(0, min(x, screen_width - window_width))
            y = max(0, min(y, screen_height - window_height))
            
            # Apply the new position
            self.app.geometry(f"+{x}+{y}")
            
            logger.info(f"Window centered at ({x}, {y})")
            
        except Exception as e:
            logger.warning(f"Failed to center window: {e}")
            # Fallback to a safe position
            self.app.geometry("+100+100")
    
    def set_icon_delayed(self):
        """Set the icon after the window is fully created (Windows workaround)."""
        try:
            logger.info("Setting icon with delayed method")
            from src.core.constants import ICON_ICO_PATH
            
            # Try both methods in delayed setting too
            try:
                self.app.iconbitmap(ICON_ICO_PATH)
                logger.info("Delayed iconbitmap successful")
            except Exception as e:
                logger.warning(f"Delayed iconbitmap failed: {e}")
                # Fallback to iconphoto method
                try:
                    from PIL import Image, ImageTk
                    icon_img = Image.open(ICON_ICO_PATH)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.app.iconphoto(True, icon_photo)
                    logger.info("Delayed iconphoto successful")
                except Exception as e2:
                    logger.warning(f"Delayed iconphoto also failed: {e2}")
            

        except Exception as e:
            logger.warning(f"Delayed icon setting failed: {e}") 