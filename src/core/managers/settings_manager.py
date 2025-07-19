"""Settings management functionality for QuickButtons."""

import tkinter as tk
import sys
from src.ui.dialogs import SettingsDialog, AboutDialog
from src.utils.logger import logger


class SettingsManager:
    """Handles settings functionality."""
    
    def __init__(self, app):
        self.app = app
        self.settings_dialog = None
        self.about_dialog = None
    
    def open_settings(self):
        """Open the settings dialog, only one at a time."""
        if self.settings_dialog is not None and self.settings_dialog.winfo_exists():
            self.settings_dialog.lift()
            return
        self.settings_dialog = SettingsDialog(self.app, self.app.theme, self.app.config_data, self.save_settings)
        self.settings_dialog.protocol("WM_DELETE_WINDOW", self._on_settings_close)
    
    def save_settings(self, new_settings):
        """Save settings from the settings dialog and apply them."""
        self.app.config_data["translucency"] = new_settings["translucency"]
        language_changed = False
        if "language" in new_settings:
            if self.app.config_data.get("language") != new_settings["language"]:
                language_changed = True
            self.app.config_data["language"] = new_settings["language"]
        if "volume" in new_settings:
            self.app.config_data["volume"] = new_settings["volume"]
        if "min_btn_width" in new_settings:
            self.app.config_data["min_btn_width"] = new_settings["min_btn_width"]
        if "max_btn_width" in new_settings:
            self.app.config_data["max_btn_width"] = new_settings["max_btn_width"]
        if "min_btn_height" in new_settings:
            self.app.config_data["min_btn_height"] = new_settings["min_btn_height"]
        if "max_btn_height" in new_settings:
            self.app.config_data["max_btn_height"] = new_settings["max_btn_height"]
        if "timer_sound" in new_settings:
            self.app.config_data["timer_sound"] = new_settings["timer_sound"]
        if "minimal_mode" in new_settings:
            self.app.config_data["minimal_mode"] = new_settings["minimal_mode"]
        if "log_level" in new_settings:
            self.app.config_data["log_level"] = new_settings["log_level"]
            # Apply logging level change immediately
            self._apply_log_level(new_settings["log_level"])
        if "animation_enabled" in new_settings:
            self.app.config_data["animation_enabled"] = new_settings["animation_enabled"]
        if "default_animation_type" in new_settings:
            self.app.config_data["default_animation_type"] = new_settings["default_animation_type"]
        if "python_executable" in new_settings:
            self.app.config_data["python_executable"] = new_settings["python_executable"]
            logger.info(f"Python executable saved to config: '{new_settings['python_executable']}'")
        
        self.app.save_config()
        self.app.apply_settings()
        self.app.update_theme()
        self.app.button_manager.refresh_grid()
        
        if language_changed:
            self.app.translation_manager.set_language(new_settings["language"])
            self.app.update_topbar_tooltips()
        
        # Apply minimal mode and force refresh if needed
        self.app.apply_minimal_mode()
        if "minimal_mode" in new_settings:
            self.app.after(200, self.app.force_refresh_minimal_mode)
    
    def apply_settings(self):
        """Apply settings such as button size and translucency."""
        self.app.attributes("-alpha", self.app.config_data.get("translucency", 1.0))
        self.app.button_manager.refresh_grid()
    
    def _on_settings_close(self):
        """Handle settings dialog close."""
        if self.settings_dialog is not None and self.settings_dialog.winfo_exists():
            self.settings_dialog.destroy()
        self.settings_dialog = None
    
    def open_about(self):
        """Open the about dialog."""
        if self.about_dialog is not None and self.about_dialog.winfo_exists():
            self.about_dialog.lift()
            return
        self.about_dialog = AboutDialog(self.app, self.app.theme)
        self.about_dialog.protocol("WM_DELETE_WINDOW", self._on_about_close)
    
    def _on_about_close(self):
        """Handle about dialog close."""
        if self.about_dialog is not None:
            self.about_dialog.destroy()
        self.about_dialog = None
    
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
    
    def update_theme(self):
        """Update the application theme."""
        self.app.theme_name = self.app.config_data.get("theme", self.app.detect_system_theme())
        self.app.theme = self.app.themes[self.app.theme_name]
        self.app.configure(bg=self.app.theme["bg"])
        self.app.topbar.config(bg=self.app.theme["topbar_bg"])
        
        # Update grid canvas and frame through button manager
        if hasattr(self.app.button_manager, "grid_canvas"):
            self.app.button_manager.grid_canvas.config(bg=self.app.theme["bg"])
        if hasattr(self.app.button_manager, "grid_frame"):
            self.app.button_manager.grid_frame.config(bg=self.app.theme["bg"])
        
        # Update button colors for use_default_colors buttons
        for idx, btn_cfg in enumerate(self.app.config_data.get("buttons", [])):
            if idx < len(self.app.button_manager.button_widgets):
                use_default = btn_cfg.get("use_default_colors", False)
                if use_default:
                    self.app.button_manager.button_widgets[idx].config(
                        bg=self.app.theme["button_bg"], fg=self.app.theme["button_fg"], 
                        activebackground=self.app.theme["button_hover"], 
                        activeforeground=self.app.theme["button_fg"]
                    )
                    self.app.button_manager.button_widgets[idx].orig_bg = self.app.theme["button_bg"]
                else:
                    self.app.button_manager.button_widgets[idx].config(
                        bg=btn_cfg.get("bg_color", self.app.theme["button_bg"]), 
                        fg=btn_cfg.get("fg_color", self.app.theme["button_fg"]), 
                        activebackground=self.app.theme["button_hover"], 
                        activeforeground=self.app.theme["button_fg"]
                    )
                    self.app.button_manager.button_widgets[idx].orig_bg = btn_cfg.get("bg_color", self.app.theme["button_bg"])
                
                # Update hover bindings for timer buttons to use current theme
                if btn_cfg.get("type") == "timer":
                    # Remove old bindings and add new ones with current theme colors
                    self.app.button_manager.button_widgets[idx].unbind("<Enter>")
                    self.app.button_manager.button_widgets[idx].unbind("<Leave>")
                    
                    # Update orig_bg to current background color
                    current_bg = self.app.button_manager.button_widgets[idx].cget("bg")
                    self.app.button_manager.button_widgets[idx].orig_bg = current_bg
                    
                    # Update button colors if using default colors
                    use_default = btn_cfg.get("use_default_colors", False)
                    if use_default:
                        self.app.button_manager.button_widgets[idx].config(
                            bg=self.app.theme["button_bg"], fg=self.app.theme["button_fg"]
                        )
                        self.app.button_manager.button_widgets[idx].orig_bg = self.app.theme["button_bg"]
                    
                    # Create dynamic hover functions for timer buttons
                    def on_timer_enter(event, button=self.app.button_manager.button_widgets[idx], config=btn_cfg):
                        button.config(bg=self.app.theme["button_hover"])
                    
                    def on_timer_leave(event, button=self.app.button_manager.button_widgets[idx], config=btn_cfg):
                        use_default = config.get("use_default_colors", False)
                        if use_default:
                            button.config(bg=self.app.theme["button_bg"])
                        else:
                            button.config(bg=button.orig_bg)
                    
                    self.app.button_manager.button_widgets[idx].bind("<Enter>", on_timer_enter)
                    self.app.button_manager.button_widgets[idx].bind("<Leave>", on_timer_leave)
        
        # Update all toolbar buttons (only if they exist and we're not in minimal mode)
        if not self.app.config_data.get("minimal_mode", False):
            for btn in [self.app.add_btn, self.app.theme_btn, self.app.settings_btn, self.app.about_btn, self.app.pin_btn, self.app.file_add_btn]:
                if btn and btn.winfo_exists():
                    btn.config(
                        bg=self.app.theme["topbar_bg"], fg=self.app.theme["button_fg"],
                        activebackground=self.app.theme["button_hover"], activeforeground=self.app.theme["button_fg"]
                    )
        
        # Update minimal mode titlebar elements if in minimal mode
        if self.app.config_data.get("minimal_mode", False):
            # Update topbar background
            self.app.topbar.config(bg=self.app.theme["topbar_bg"])
            
            # Update all widgets in the topbar
            for widget in self.app.topbar.winfo_children():
                if isinstance(widget, tk.Label):
                    # Update logo and title labels
                    widget.config(bg=self.app.theme["topbar_bg"], fg=self.app.theme["label_fg"])
                elif isinstance(widget, tk.Button):
                    # Update all buttons in the topbar
                    if widget.cget("text") == "✕":  # Close button
                        widget.config(bg=self.app.theme["topbar_bg"], fg=self.app.theme["label_fg"])
                        # Update close button hover effects
                        widget.unbind("<Enter>")
                        widget.unbind("<Leave>")
                        
                        def on_close_enter(e, btn=widget):
                            btn.config(bg="#e81123", fg="white")
                        
                        def on_close_leave(e, btn=widget):
                            btn.config(bg=self.app.theme["topbar_bg"], fg=self.app.theme["label_fg"])
                        
                        widget.bind("<Enter>", on_close_enter)
                        widget.bind("<Leave>", on_close_leave)
                    else:
                        widget.config(
                            bg=self.app.theme["topbar_bg"], 
                            fg=self.app.theme["button_fg"],
                            activebackground=self.app.theme["button_hover"], 
                            activeforeground=self.app.theme["button_fg"]
                        )
                elif isinstance(widget, tk.Frame):
                    # Update spacer frame
                    widget.config(bg=self.app.theme["topbar_bg"])
        
        # Update scrollbars
        if hasattr(self.app.button_manager, 'grid_scrollbar') and self.app.button_manager.grid_scrollbar.winfo_exists():
            self.app.button_manager.grid_scrollbar.config(
                bg=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                troughcolor=self.app.theme.get("scrollbar_trough", "#f0f0f0"),
                activebackground=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                relief=tk.FLAT, borderwidth=0
            )
        if hasattr(self.app.button_manager, 'grid_hscrollbar') and self.app.button_manager.grid_hscrollbar.winfo_exists():
            self.app.button_manager.grid_hscrollbar.config(
                bg=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                troughcolor=self.app.theme.get("scrollbar_trough", "#f0f0f0"),
                activebackground=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                relief=tk.FLAT, borderwidth=0
            )
        
        # Update resize gripper if it exists
        if hasattr(self.app, 'resize_gripper') and self.app.resize_gripper.winfo_exists():
            self.app.resize_gripper.config(bg=self.app.theme["bg"])
            for child in self.app.resize_gripper.winfo_children():
                if isinstance(child, tk.Canvas):
                    child.config(bg=self.app.theme["bg"])
                    # Redraw gripper lines with new color
                    child.delete("all")
                    gripper_color = self.app.theme.get("label_fg", "#666666")
                    # Draw 4 diagonal lines from bottom-right (original dimensions)
                    for i in range(4):
                        x1 = 24 - (i + 1) * 3
                        y1 = 24
                        x2 = 24
                        y2 = 24 - (i + 1) * 3
                        child.create_line(x1, y1, x2, y2, fill=gripper_color, width=1)
        
        # Update theme button icon
        if hasattr(self.app, 'theme_btn') and self.app.theme_btn.winfo_exists():
            self.app.theme_btn.config(text="☀" if self.app.theme_name=="light" else "🌙")
        if hasattr(self.app, 'pin_btn') and self.app.pin_btn.winfo_exists():
            self.app.pin_btn.config(text="📌" if self.app.always_on_top else "📍")
        self.app.update_topbar_tooltips()
        

        
        logger.info(f"Theme updated to: {self.app.theme_name}") 