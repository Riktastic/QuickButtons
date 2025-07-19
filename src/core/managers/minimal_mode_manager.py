"""Minimal mode management functionality for QuickButtons."""

import tkinter as tk
import os
from src.utils.logger import logger
from src.ui.components.tooltip import Tooltip
from src.core.constants import ICON_PATH


class MinimalModeManager:
    """Handles minimal mode functionality."""
    
    def __init__(self, app):
        self.app = app
        self.drag_start_x = None
        self.drag_start_y = None
        self.resize_start_x = None
        self.resize_start_y = None
        self.resize_start_width = None
        self.resize_start_height = None
    
    def apply_minimal_mode(self):
        """Apply minimal mode settings."""
        minimal = self.app.config_data.get("minimal_mode", False)
        
        if minimal:
            # Remove default titlebar
            self.app.overrideredirect(True)
            
            # Linux-specific window hints for better desktop integration
            if sys.platform.startswith("linux"):
                try:
                    from src.utils.system import detect_desktop_environment
                    desktop = detect_desktop_environment()
                    
                    # Set window hints for better integration
                    if desktop == 'gnome':
                        # GNOME: Set window type hint for better integration
                        self.app.attributes('-type', 'dock')
                    elif desktop == 'kde':
                        # KDE: Set window flags for better integration
                        self.app.attributes('-type', 'dock')
                    else:
                        # Other DEs: Use utility window type
                        self.app.attributes('-type', 'utility')
                        
                    logger.info(f"Applied Linux window hints for {desktop} desktop environment")
                except Exception as e:
                    logger.warning(f"Could not apply Linux window hints: {e}")
            
            # Modify existing topbar for minimal mode
            self.modify_topbar_for_minimal_mode()
            
            # Create resize gripper
            self.create_resize_gripper()
            
            logger.info("Minimal mode enabled")
        else:
            # Remove resize gripper first
            if hasattr(self.app, 'resize_gripper'):
                self.app.resize_gripper.destroy()
                delattr(self.app, 'resize_gripper')
            
            # Clean up drag state variables
            if hasattr(self.app, 'drag_start_x'):
                delattr(self.app, 'drag_start_x')
            if hasattr(self.app, 'drag_start_y'):
                delattr(self.app, 'drag_start_y')
            
            # Restore normal topbar before restoring titlebar
            self.restore_normal_topbar()
            
            # Force update to ensure topbar is displayed
            self.app.update()
            
            # Restore default titlebar last
            self.app.overrideredirect(False)
            
            # Reset window type hints on Linux
            if sys.platform.startswith("linux"):
                try:
                    self.app.attributes('-type', 'normal')
                    logger.info("Reset Linux window hints")
                except Exception as e:
                    logger.warning(f"Could not reset Linux window hints: {e}")
            
            # Force another update to ensure everything is properly displayed
            self.app.update()
            
            logger.info("Minimal mode disabled")
    
    def modify_topbar_for_minimal_mode(self):
        """Modify the existing topbar to include close button, icon, and title for minimal mode."""
        # Clear existing topbar
        for widget in self.app.topbar.winfo_children():
            widget.destroy()
        
        # App logo and title (left side)
        try:
            # Try to load the actual logo image using the proper resource path
            from PIL import Image, ImageTk
            logo_img = Image.open(ICON_PATH)
            logo_img = logo_img.resize((16, 16), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(self.app.topbar, image=logo_photo, 
                                 bg=self.app.theme["topbar_bg"])
            logo_label.image = logo_photo  # Keep a reference
        except Exception as e:
            # Fallback to text if image fails to load
            logger.warning(f"Could not load logo image: {e}")
            logo_label = tk.Label(self.app.topbar, text="Q", 
                                 bg=self.app.theme["topbar_bg"], fg=self.app.theme["label_fg"],
                                 font=("Segoe UI", 10, "bold"))
        
        logo_label.pack(side=tk.LEFT, padx=(5, 2))
        
        title_label = tk.Label(self.app.topbar, text="QuickButtons", 
                              bg=self.app.theme["topbar_bg"], fg=self.app.theme["label_fg"],
                              font=("Segoe UI", 9, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Make title and logo draggable
        def start_drag(event):
            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y
        
        def on_drag(event):
            if hasattr(self.app, 'drag_start_x'):
                x = self.app.winfo_x() + (event.x - self.app.drag_start_x)
                y = self.app.winfo_y() + (event.y - self.app.drag_start_y)
                self.app.geometry(f"+{x}+{y}")
        
        def stop_drag(event):
            if hasattr(self.app, 'drag_start_x'):
                del self.app.drag_start_x
                del self.app.drag_start_y
        
        logo_label.bind("<Button-1>", start_drag)
        logo_label.bind("<B1-Motion>", on_drag)
        logo_label.bind("<ButtonRelease-1>", stop_drag)
        title_label.bind("<Button-1>", start_drag)
        title_label.bind("<B1-Motion>", on_drag)
        title_label.bind("<ButtonRelease-1>", stop_drag)
        
        # Spacer to push other buttons to the right
        tk.Frame(self.app.topbar, bg=self.app.theme["topbar_bg"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Recreate the original buttons (right side) in correct order
        # Note: When using pack(side=tk.RIGHT), buttons appear in reverse order of packing
        # So we pack them in reverse order to get the correct visual order
        
        # Close button (rightmost)
        close_btn = tk.Button(self.app.topbar, text="✕", 
                             bg=self.app.theme["topbar_bg"], fg=self.app.theme["label_fg"],
                             font=("Segoe UI", 9),
                             relief=tk.FLAT, bd=0, highlightthickness=0,
                             command=self.app.on_close,
                             width=3, height=1)
        close_btn.pack(side=tk.RIGHT, padx=(0, 0))
        
        # Theme toggle button
        self.app.theme_btn = tk.Button(self.app.topbar, text="☀️" if self.app.theme_name=="light" else "🌙", 
                                      bg=self.app.theme["topbar_bg"], fg=self.app.theme["button_fg"], 
                                      font=("Segoe UI", 9), relief=tk.FLAT, command=self.app.toggle_theme, 
                                      bd=0, highlightthickness=0, activebackground=self.app.theme["button_hover"], 
                                      activeforeground=self.app.theme["button_fg"])
        self.app.theme_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.theme_btn_tooltip = Tooltip(self.app.theme_btn, self.app._("Toggle theme"))
        
        # Pin (always on top) button
        self.app.pin_btn = tk.Button(self.app.topbar, text="📌" if self.app.always_on_top else "📍", 
                                    bg=self.app.theme["topbar_bg"], fg=self.app.theme["button_fg"], 
                                    font=("Segoe UI", 9), relief=tk.FLAT, command=self.app.toggle_on_top, 
                                    bd=0, highlightthickness=0, activebackground=self.app.theme["button_hover"], 
                                    activeforeground=self.app.theme["button_fg"])
        self.app.pin_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.pin_btn_tooltip = Tooltip(self.app.pin_btn, self.app._("Keep on top") if self.app.always_on_top else self.app._("Do not keep on top"))
        
        # Settings button
        self.app.settings_btn = tk.Button(self.app.topbar, text="⚙️", bg=self.app.theme["topbar_bg"], 
                                         fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                         command=self.app.open_settings, bd=0, highlightthickness=0, 
                                         activebackground=self.app.theme["button_hover"], 
                                         activeforeground=self.app.theme["button_fg"])
        self.app.settings_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.settings_btn_tooltip = Tooltip(self.app.settings_btn, self.app._("Settings"))
        
        # About button
        self.app.about_btn = tk.Button(self.app.topbar, text="❔", bg=self.app.theme["topbar_bg"], 
                                      fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                      command=self.app.open_about, bd=0, highlightthickness=0, 
                                      activebackground=self.app.theme["button_hover"], 
                                      activeforeground=self.app.theme["button_fg"])
        self.app.about_btn.pack(side=tk.RIGHT, padx=(0,2), pady=1)
        self.app.about_btn_tooltip = Tooltip(self.app.about_btn, self.app._("About"))
        
        # File-explorer add button
        self.app.file_add_btn = tk.Button(self.app.topbar, text="📂", bg=self.app.theme["topbar_bg"], 
                                         fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                         command=self.app.add_buttons_from_files, bd=0, highlightthickness=0, 
                                         activebackground=self.app.theme["button_hover"], 
                                         activeforeground=self.app.theme["button_fg"])
        self.app.file_add_btn.pack(side=tk.RIGHT, padx=(2,0), pady=1, ipadx=1, ipady=0)
        self.app.file_add_btn.bind("<Enter>", lambda e: self.app.file_add_btn.config(bg=self.app.theme["button_hover"]))
        self.app.file_add_btn.bind("<Leave>", lambda e: self.app.file_add_btn.config(bg=self.app.theme["topbar_bg"]))
        self.app.file_add_btn_tooltip = Tooltip(self.app.file_add_btn, self.app._("Add from file(s)"))
        
        # Add button
        self.app.add_btn = tk.Button(self.app.topbar, text="✚", bg=self.app.theme["topbar_bg"], 
                                    fg=self.app.theme["button_fg"], font=("Segoe UI", 9), relief=tk.FLAT, 
                                    command=self.app.add_button, bd=0, highlightthickness=0, 
                                    activebackground=self.app.theme["button_hover"], 
                                    activeforeground=self.app.theme["button_fg"])
        self.app.add_btn.pack(side=tk.RIGHT, padx=(2,0), pady=1, ipadx=1, ipady=0)
        self.app.add_btn.bind("<Enter>", lambda e: self.app.add_btn.config(bg=self.app.theme["button_hover"]))
        self.app.add_btn.bind("<Leave>", lambda e: self.app.add_btn.config(bg=self.app.theme["topbar_bg"]))
        self.app.add_btn_tooltip = Tooltip(self.app.add_btn, self.app._("Add new button"))
        
        # Hover effects for close button
        def on_close_enter(e):
            close_btn.config(bg="#e81123", fg="white")
        
        def on_close_leave(e):
            close_btn.config(bg=self.app.theme["topbar_bg"], fg=self.app.theme["label_fg"])
        
        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)
        
        # Store reference to close button for theme updates
        self.app.close_btn = close_btn
        
        logger.info("Topbar modified for minimal mode")
    
    def restore_normal_topbar(self):
        """Restore the normal topbar layout."""
        logger.info("Starting normal topbar restoration")
        
        # Clear existing topbar first
        if hasattr(self.app, 'topbar') and self.app.topbar.winfo_exists():
            logger.info("Destroying existing topbar")
            self.app.topbar.destroy()
        
        # Temporarily unpack the button grid to fix packing order
        self.app.button_manager.unpack_grid()
        
        # Force update to ensure the old topbar is completely removed
        self.app.update()
        
        # Recreate the normal topbar using the topbar manager
        logger.info("Creating new topbar via topbar manager")
        self.app.topbar_manager.create_topbar()
        
        # Repack the button grid in the correct order
        self.app.button_manager.repack_grid()
        
        # Force update to ensure the new topbar is displayed
        self.app.update()
        
        # Verify the topbar was created
        if hasattr(self.app, 'topbar') and self.app.topbar.winfo_exists():
            logger.info("Normal topbar restored successfully")
        else:
            logger.error("Failed to restore normal topbar")
    
    def create_resize_gripper(self):
        """Create a resize gripper for minimal mode."""
        # Create a transparent gripper positioned in bottom-right corner
        self.app.resize_gripper = tk.Frame(self.app, bg=self.app.theme["bg"], width=24, height=24)
        self.app.resize_gripper.place(relx=1.0, rely=1.0, anchor=tk.SE, x=-2, y=-2)
        
        # Create gripper visual (diagonal lines only)
        gripper_canvas = tk.Canvas(self.app.resize_gripper, bg=self.app.theme["bg"], 
                                  width=24, height=24, highlightthickness=0)
        gripper_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw subtle diagonal lines for gripper
        gripper_color = self.app.theme.get("label_fg", "#999999")  # Lighter color
        # Draw 4 diagonal lines from bottom-right (smaller)
        for i in range(4):
            x1 = 24 - (i + 1) * 3
            y1 = 24
            x2 = 24
            y2 = 24 - (i + 1) * 3
            gripper_canvas.create_line(x1, y1, x2, y2, fill=gripper_color, width=1)  # Thinner lines
        
        # Bind resize events
        def start_resize(event):
            self.app.resize_start_x = event.x_root
            self.app.resize_start_y = event.y_root
            self.app.resize_start_width = self.app.winfo_width()
            self.app.resize_start_height = self.app.winfo_height()
        
        def on_resize(event):
            if hasattr(self.app, 'resize_start_x'):
                delta_x = event.x_root - self.app.resize_start_x
                delta_y = event.y_root - self.app.resize_start_y
                new_width = max(120, self.app.resize_start_width + delta_x)
                new_height = max(60, self.app.resize_start_height + delta_y)
                self.app.geometry(f"{new_width}x{new_height}")
        
        def stop_resize(event):
            if hasattr(self.app, 'resize_start_x'):
                delattr(self.app, 'resize_start_x')
                delattr(self.app, 'resize_start_y')
                delattr(self.app, 'resize_start_width')
                delattr(self.app, 'resize_start_height')
        
        # Bind to both frame and canvas
        self.app.resize_gripper.bind("<Button-1>", start_resize)
        self.app.resize_gripper.bind("<B1-Motion>", on_resize)
        self.app.resize_gripper.bind("<ButtonRelease-1>", stop_resize)
        gripper_canvas.bind("<Button-1>", start_resize)
        gripper_canvas.bind("<B1-Motion>", on_resize)
        gripper_canvas.bind("<ButtonRelease-1>", stop_resize)
        
        # Change cursor when hovering over gripper
        def on_gripper_enter(event):
            self.app.resize_gripper.config(cursor="sizing")
            gripper_canvas.config(cursor="sizing")
        
        def on_gripper_leave(event):
            self.app.resize_gripper.config(cursor="")
            gripper_canvas.config(cursor="")
        
        self.app.resize_gripper.bind("<Enter>", on_gripper_enter)
        self.app.resize_gripper.bind("<Leave>", on_gripper_leave)
        gripper_canvas.bind("<Enter>", on_gripper_enter)
        gripper_canvas.bind("<Leave>", on_gripper_leave)
        
        logger.info("Resize gripper created")
    
    def force_refresh_minimal_mode(self):
        """Force refresh minimal mode - useful for debugging."""
        minimal = self.app.config_data.get("minimal_mode", False)
        logger.info(f"Force refreshing minimal mode: {minimal}")
        
        if minimal:
            # Recreate minimal mode topbar
            self.modify_topbar_for_minimal_mode()
            
            # Recreate resize gripper
            if hasattr(self.app, 'resize_gripper'):
                self.app.resize_gripper.destroy()
            self.create_resize_gripper()
            
            logger.info("Minimal mode force refreshed") 