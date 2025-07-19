"""Main application class for QuickButtons - Refactored Version."""

import tkinter as tk
import sys
import os

from .managers.config_manager import ConfigManager
from .constants import *
from .managers.window_manager import WindowManager
from .managers.topbar_manager import TopbarManager
from .managers.button_manager import ButtonManager
from .managers.timer_manager import TimerManager
from .managers.minimal_mode_manager import MinimalModeManager
from .managers.button_actions_manager import ButtonActionsManager
from .managers.settings_manager import SettingsManager
from .managers.music_manager import MusicManager

from src.ui.themes import load_themes
from src.actions.music_player import MusicPlayer
from src.actions.web_opener import WebOpener
from src.utils.system import detect_system_theme
from src.utils.translations import translation_manager
from src.utils.logger import logger

# Optional imports with keyboard support
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


class QuickButtonsApp(tk.Tk):
    """Main application window for QuickButtons - Refactored Version."""
    
    def __init__(self):
        self.global_hotkeys = []  # Defensive: ensure this always exists before any method calls
        super().__init__()
        
        # Initialize core components (minimal for fast startup)
        self.config_manager = ConfigManager()
        self.config_data = self.config_manager.config_data
        self.translation_manager = translation_manager
        self.translation_manager.set_language(self.config_data.get("language", "en"))
        
        # Apply configured logging level
        log_level = self.config_data.get("log_level", "WARNING")
        self._apply_log_level(log_level)
        
        # Load themes (fast operation)
        self.themes = load_themes()
        
        # Use cached theme only for startup speed - detect later if needed
        cached_theme = self.config_data.get("cached_system_theme", "dark")
        if cached_theme in self.themes:
            self.theme_name = self.config_data.get("theme", cached_theme)
        else:
            self.theme_name = self.config_data.get("theme", "dark")
        
        self.theme = self.themes[self.theme_name]
        
        # Initialize only essential managers for startup
        self.window_manager = WindowManager(self)
        self.topbar_manager = TopbarManager(self)
        self.button_manager = ButtonManager(self)
        
        # Initialize UI immediately
        self.title(self._("QuickButtons"))
        self.configure(bg=self.theme["bg"])
        
        # Set up window
        self.window_manager.setup_window(self.config_data, self.theme)
        
        # Initialize UI components
        self.topbar_manager.create_topbar()
        self.button_manager.create_button_grid()
        self.attributes("-alpha", self.config_data.get("translucency", 1.0))
        
        # Set default language if not present
        if "language" not in self.config_data:
            self.config_data["language"] = "en"
        
        # Apply minimal mode immediately if enabled
        if self.config_data.get("minimal_mode", False):
            self.overrideredirect(True)
            self._lazy_load_minimal_mode_manager()
            self.minimal_mode_manager.modify_topbar_for_minimal_mode()
            self.minimal_mode_manager.create_resize_gripper()
            logger.info("Minimal mode applied during initialization")
        
        # Defer all non-critical operations to background
        self.after(10, self._background_initialization)
        
        logger.info("QuickButtonsApp initialized successfully")
    
    def _lazy_load_minimal_mode_manager(self):
        """Lazy load minimal mode manager."""
        if not hasattr(self, 'minimal_mode_manager'):
            from .managers.minimal_mode_manager import MinimalModeManager
            self.minimal_mode_manager = MinimalModeManager(self)
    
    def _lazy_load_button_actions_manager(self):
        """Lazy load button actions manager."""
        if not hasattr(self, 'button_actions_manager'):
            from .managers.button_actions_manager import ButtonActionsManager
            self.button_actions_manager = ButtonActionsManager(self)
    
    def _lazy_load_settings_manager(self):
        """Lazy load settings manager."""
        if not hasattr(self, 'settings_manager'):
            from .managers.settings_manager import SettingsManager
            self.settings_manager = SettingsManager(self)
    
    def _lazy_load_timer_manager(self):
        """Lazy load timer manager."""
        if not hasattr(self, 'timer_manager'):
            from .managers.timer_manager import TimerManager
            self.timer_manager = TimerManager(self)
    
    def _lazy_load_music_manager(self):
        """Lazy load music manager."""
        if not hasattr(self, 'music_manager'):
            from .managers.music_manager import MusicManager
            self.music_manager = MusicManager(self)
    
    def _background_initialization(self):
        """Initialize non-critical components in background."""
        try:
            # Initialize remaining managers
            from .managers.timer_manager import TimerManager
            from .managers.button_actions_manager import ButtonActionsManager
            from .managers.settings_manager import SettingsManager
            from .managers.music_manager import MusicManager
            from src.actions.music_player import MusicPlayer
            from src.actions.web_opener import WebOpener
            
            self.timer_manager = TimerManager(self)
            self.button_actions_manager = ButtonActionsManager(self)
            self.settings_manager = SettingsManager(self)
            self.music_manager = MusicManager(self)
            self.music_player = MusicPlayer()
            self.web_opener = WebOpener()
            
            # Initialize dialog references
            self.settings_dialog = None
            self.about_dialog = None
            self.button_settings_dialog = None
            
            # Initialize music state
            self.current_music_btn = None
            self.current_music_path = None
            self._music_glow_job = None
            self._music_glow_state = False
            
            # Initialize shortcuts
            self.shortcut_map = {}
            
            # Update theme and refresh grid
            self.settings_manager.update_theme()
            self.button_manager.refresh_grid()
            
            # Detect system theme in background if not cached
            if not self.config_data.get("cached_system_theme"):
                self.after(100, self._detect_system_theme_background)
            
            logger.info("Background initialization completed")
            
        except Exception as e:
            logger.error(f"Background initialization failed: {e}")
    
    def _detect_system_theme_background(self):
        """Detect system theme in background."""
        try:
            detected_theme = detect_system_theme()
            if detected_theme != self.theme_name:
                self.config_data["cached_system_theme"] = detected_theme
                logger.info(f"System theme detected: {detected_theme}")
        except Exception as e:
            logger.warning(f"Background theme detection failed: {e}")
    
    def _(self, text):
        """Get translated text."""
        return self.translation_manager.get_text(text)
    
    def _apply_log_level(self, level_name):
        """Apply the specified logging level."""
        import logging
        from src.utils.logger import update_log_level
        
        level_map = {
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG
        }
        
        level = level_map.get(level_name.upper(), logging.WARNING)
        update_log_level(level)
        logger.info(f"Logging level changed to: {level_name}")
    
    # Delegate methods to managers
    def create_topbar(self):
        """Create the top bar."""
        return self.topbar_manager.create_topbar()
    
    def update_topbar_tooltips(self):
        """Update topbar tooltips after language change."""
        return self.topbar_manager.update_topbar_tooltips()
    
    def toggle_on_top(self):
        """Toggle the always-on-top state and update the pin button."""
        return self.topbar_manager.toggle_on_top()
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        return self.topbar_manager.toggle_theme()
    
    def create_button_grid(self):
        """Create the scrollable button grid area."""
        return self.button_manager.create_button_grid()
    
    def refresh_grid(self):
        """Refresh the button grid."""
        return self.button_manager.refresh_grid()
    
    def apply_minimal_mode(self):
        """Apply minimal mode settings."""
        self._lazy_load_minimal_mode_manager()
        return self.minimal_mode_manager.apply_minimal_mode()
    
    def force_refresh_minimal_mode(self):
        """Force refresh minimal mode - useful for debugging."""
        self._lazy_load_minimal_mode_manager()
        return self.minimal_mode_manager.force_refresh_minimal_mode()
    
    def add_button(self):
        """Open the dialog to add a new button, only one at a time."""
        self._lazy_load_button_actions_manager()
        return self.button_actions_manager.add_button()
    
    def add_buttons_from_files(self):
        """Open file dialog, auto-detect type, and add buttons for selected files."""
        self._lazy_load_button_actions_manager()
        return self.button_actions_manager.add_buttons_from_files()
    
    def edit_button(self, btn_cfg):
        """Open the dialog to edit an existing button, only one at a time."""
        self._lazy_load_button_actions_manager()
        return self.button_actions_manager.edit_button(btn_cfg)
    
    def open_settings(self):
        """Open the settings dialog, only one at a time."""
        self._lazy_load_settings_manager()
        return self.settings_manager.open_settings()
    
    def open_about(self):
        """Open the about dialog."""
        self._lazy_load_settings_manager()
        return self.settings_manager.open_about()
    
    def save_settings(self, new_settings):
        """Save settings from the settings dialog and apply them."""
        self._lazy_load_settings_manager()
        return self.settings_manager.save_settings(new_settings)
    
    def apply_settings(self):
        """Apply settings such as button size and translucency."""
        self._lazy_load_settings_manager()
        return self.settings_manager.apply_settings()
    
    def update_theme(self):
        """Update the application theme."""
        self._lazy_load_settings_manager()
        return self.settings_manager.update_theme()
    
    def detect_system_theme(self):
        """Detect system theme."""
        from src.utils.system import detect_system_theme
        return detect_system_theme()
    
    def _start_music_glow(self, btn):
        """Start music glow effect on button."""
        return self.music_manager._start_music_glow(btn)
    
    def _stop_music_glow(self):
        """Stop music glow effect."""
        return self.music_manager._stop_music_glow()
    
    def unregister_global_hotkeys(self):
        """Remove all registered global hotkeys."""
        if not hasattr(self, "global_hotkeys"):
            self.global_hotkeys = []
        if HAS_KEYBOARD:
            for hotkey in self.global_hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                except Exception:
                    pass
            self.global_hotkeys = []
    
    def save_config(self):
        """Save the current configuration."""
        self.config_manager.save_config()
    
    def on_close(self):
        """Handle window close event: save config and exit."""
        # Clean up custom titlebar if it exists
        if hasattr(self, 'custom_titlebar'):
            self.custom_titlebar.destroy()
        
        # Clean up resize gripper if it exists
        if hasattr(self, 'resize_gripper'):
            self.resize_gripper.destroy()
        
        # Clean up drag state variables
        if hasattr(self, 'drag_start_x'):
            delattr(self, 'drag_start_x')
        if hasattr(self, 'drag_start_y'):
            delattr(self, 'drag_start_y')
        
        # Clean up resize state variables
        if hasattr(self, 'resize_start_x'):
            delattr(self, 'resize_start_x')
        if hasattr(self, 'resize_start_y'):
            delattr(self, 'resize_start_y')
        if hasattr(self, 'resize_start_width'):
            delattr(self, 'resize_start_width')
        if hasattr(self, 'resize_start_height'):
            delattr(self, 'resize_start_height')
        
        self.unregister_global_hotkeys()
        self.save_config()
        logger.info("Application closing")
        self.destroy() 