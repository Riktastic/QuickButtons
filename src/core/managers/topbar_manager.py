"""Topbar management functionality for QuickButtons."""

import tkinter as tk
from src.ui.components.tooltip import Tooltip
from src.utils.logger import logger


class TopbarManager:
    """Handles topbar functionality."""
    
    def __init__(self, app):
        self.app = app
    
    def create_topbar(self):
        """Create the top bar with add/settings/about/theme/pin buttons, using only icons."""
        logger.info("TopbarManager: Creating topbar")
        
        # Clear existing topbar if it exists
        if hasattr(self.app, 'topbar') and self.app.topbar.winfo_exists():
            logger.info("TopbarManager: Destroying existing topbar")
            self.app.topbar.destroy()
        
        # Create new topbar frame
        self.app.topbar = tk.Frame(self.app, bg=self.app.theme["topbar_bg"], height=18)
        logger.info(f"TopbarManager: Created topbar frame with bg={self.app.theme['topbar_bg']}")
        
        # Pack the topbar at the top
        self.app.topbar.pack(side=tk.TOP, fill=tk.X)
        logger.info("TopbarManager: Packed topbar at top")
        
        # Force update to ensure the frame is created and packed
        self.app.update_idletasks()
        
        # Add button (icon only)
        self.app.add_btn = tk.Button(self.app.topbar, text="✚", bg=self.app.theme["topbar_bg"], 
                                    fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                    command=self.app.add_button, bd=0, highlightthickness=0, 
                                    activebackground=self.app.theme["button_hover"], 
                                    activeforeground=self.app.theme["button_fg"])
        self.app.add_btn.pack(side=tk.LEFT, padx=(2,0), pady=1, ipadx=1, ipady=0)
        self.app.add_btn.bind("<Enter>", lambda e: self.app.add_btn.config(bg=self.app.theme["button_hover"]))
        self.app.add_btn.bind("<Leave>", lambda e: self.app.add_btn.config(bg=self.app.theme["topbar_bg"]))
        self.app.add_btn_tooltip = Tooltip(self.app.add_btn, self.app._("Add new button"))
        
        # File-explorer add button (icon only)
        self.app.file_add_btn = tk.Button(self.app.topbar, text="📂", bg=self.app.theme["topbar_bg"], 
                                         fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                         command=self.app.add_buttons_from_files, bd=0, highlightthickness=0, 
                                         activebackground=self.app.theme["button_hover"], 
                                         activeforeground=self.app.theme["button_fg"])
        self.app.file_add_btn.pack(side=tk.LEFT, padx=(2,0), pady=1, ipadx=1, ipady=0)
        self.app.file_add_btn.bind("<Enter>", lambda e: self.app.file_add_btn.config(bg=self.app.theme["button_hover"]))
        self.app.file_add_btn.bind("<Leave>", lambda e: self.app.file_add_btn.config(bg=self.app.theme["topbar_bg"]))
        self.app.file_add_btn_tooltip = Tooltip(self.app.file_add_btn, self.app._("Add from file(s)"))
        
        # Theme toggle button (icon only)
        self.app.theme_btn = tk.Button(self.app.topbar, text="☀️" if self.app.theme_name=="light" else "🌙", 
                                      bg=self.app.theme["topbar_bg"], fg=self.app.theme["button_fg"], 
                                      font=("Segoe UI", 9), relief=tk.FLAT, command=self.app.toggle_theme, 
                                      bd=0, highlightthickness=0, activebackground=self.app.theme["button_hover"], 
                                      activeforeground=self.app.theme["button_fg"])
        self.app.theme_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.theme_btn_tooltip = Tooltip(self.app.theme_btn, self.app._("Toggle theme"))
        
        # Pin (always on top) button
        self.app.always_on_top = self.app.config_data.get("always_on_top", True)
        self.app.pin_btn = tk.Button(self.app.topbar, text="📌" if self.app.always_on_top else "📍", 
                                    bg=self.app.theme["topbar_bg"], fg=self.app.theme["button_fg"], 
                                    font=("Segoe UI", 9), relief=tk.FLAT, command=self.app.toggle_on_top, 
                                    bd=0, highlightthickness=0, activebackground=self.app.theme["button_hover"], 
                                    activeforeground=self.app.theme["button_fg"])
        self.app.pin_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.pin_btn_tooltip = Tooltip(self.app.pin_btn, self.app._("Keep on top") if self.app.always_on_top else self.app._("Do not keep on top"))
        
        # Settings button (icon only)
        self.app.settings_btn = tk.Button(self.app.topbar, text="⚙️", bg=self.app.theme["topbar_bg"], 
                                         fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                         command=self.app.open_settings, bd=0, highlightthickness=0, 
                                         activebackground=self.app.theme["button_hover"], 
                                         activeforeground=self.app.theme["button_fg"])
        self.app.settings_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.settings_btn_tooltip = Tooltip(self.app.settings_btn, self.app._("Settings"))
        
        # About button (icon only)
        self.app.about_btn = tk.Button(self.app.topbar, text="❔", bg=self.app.theme["topbar_bg"], 
                                      fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                      command=self.app.open_about, bd=0, highlightthickness=0, 
                                      activebackground=self.app.theme["button_hover"], 
                                      activeforeground=self.app.theme["button_fg"])
        self.app.about_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.about_btn_tooltip = Tooltip(self.app.about_btn, self.app._("About"))
        
        self.app.attributes("-topmost", self.app.always_on_top)
        logger.info("TopbarManager: Topbar creation completed with all buttons")
    
    def update_topbar_tooltips(self):
        """Update topbar tooltips after language change."""
        if hasattr(self.app, "add_btn_tooltip"):
            self.app.add_btn_tooltip.text = self.app._("Add new button")
        if hasattr(self.app, "file_add_btn_tooltip"):
            self.app.file_add_btn_tooltip.text = self.app._("Add from file(s)")
        if hasattr(self.app, "theme_btn_tooltip"):
            self.app.theme_btn_tooltip.text = self.app._("Toggle theme")
        if hasattr(self.app, "pin_btn_tooltip"):
            self.app.pin_btn_tooltip.text = self.app._("Keep on top") if self.app.always_on_top else self.app._("Do not keep on top")
        if hasattr(self.app, "settings_btn_tooltip"):
            self.app.settings_btn_tooltip.text = self.app._("Settings")
        if hasattr(self.app, "about_btn_tooltip"):
            self.app.about_btn_tooltip.text = self.app._("About")
    
    def toggle_on_top(self):
        """Toggle the always-on-top state and update the pin button."""
        self.app.always_on_top = not self.app.always_on_top
        self.app.config_data["always_on_top"] = self.app.always_on_top
        self.app.attributes("-topmost", self.app.always_on_top)
        if hasattr(self.app, 'pin_btn') and self.app.pin_btn.winfo_exists():
            self.app.pin_btn.config(text="📌" if self.app.always_on_top else "📍")
        if hasattr(self.app, 'pin_btn_tooltip'):
            self.app.pin_btn_tooltip.text = self.app._("Keep on top") if self.app.always_on_top else self.app._("Do not keep on top")
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.app.theme_name = "light" if self.app.theme_name == "dark" else "dark"
        self.app.theme = self.app.themes[self.app.theme_name]
        self.app.config_data["theme"] = self.app.theme_name
        self.app.save_config()
        self.app.update_theme()
        self.app.button_manager.refresh_grid() 