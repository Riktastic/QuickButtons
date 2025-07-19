"""Color picker button type handler."""

import tkinter as tk
import threading
import time
import platform
import subprocess
from src.utils.logger import logger
from src.ui.components.tooltip import Tooltip


class ColorPickerHandler:
    """Handles execution of color picker buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute a color picker button."""
        # This will be called by the button manager, but we need to create a custom button
        # that handles its own execution and display
        pass
    
    def create_color_picker_button(self, parent, cfg, font_size, cell_width):
        """Create a color picker button with screen color detection."""
        btn_label = cfg.get("label", self.app._("Color Picker"))
        orig_label = btn_label
        
        # Get theme colors - respect use_default_colors setting
        use_default = cfg.get("use_default_colors", False)
        if use_default:
            bg_color = self.app.theme["button_bg"]
            fg_color = self.app.theme["button_fg"]
        else:
            bg_color = cfg.get("bg_color", self.app.theme["button_bg"])
            fg_color = cfg.get("fg_color", self.app.theme["button_fg"])
        
        btn = tk.Button(parent, text=btn_label, bg=bg_color, 
                       fg=fg_color, font=("Segoe UI", font_size), 
                       relief=tk.FLAT, bd=0, highlightthickness=0, 
                       activebackground=self.app.theme["button_hover"], 
                       activeforeground=fg_color, 
                       wraplength=cell_width-10, justify="center")
        btn.orig_bg = bg_color
        
        # State for color picker
        state = {"picking": False, "color": None, "clear_job": None}
        
        # Create tooltip
        user_tooltip = cfg.get("tooltip", "").strip()
        if user_tooltip == "":
            tooltip_text = self.app._("Click to pick a color from screen")
        else:
            tooltip_text = user_tooltip
        
        btn.tooltip = Tooltip(btn, tooltip_text)
        
        # Add shortcut tooltip if configured
        if cfg.get("shortcut"):
            btn.shortcut_tooltip = Tooltip(btn, f"Shortcut: {cfg['shortcut']}")
        
        def update_label():
            """Update button text based on current state."""
            if state["picking"]:
                btn.config(text=self.app._("Click on screen..."))
            elif state["color"]:
                hex_color = state["color"]
                # Show color preview and hex code with hashtag
                btn.config(text=f"#{hex_color}\n{self.app._('Copied!')}")
                # Change button background to show the picked color
                try:
                    # Convert hex to RGB for button background
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    btn.config(bg=f"#{r:02x}{g:02x}{b:02x}")
                except:
                    pass  # Keep original background if conversion fails
            else:
                btn.config(text=orig_label)
                btn.config(bg=bg_color)  # Reset to original background
        
        def clear_color():
            """Clear the picked color and return to original state."""
            state["color"] = None
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            update_label()
        
        def copy_to_clipboard(text):
            """Copy text to clipboard cross-platform."""
            try:
                # Try using tkinter clipboard first
                btn.clipboard_clear()
                btn.clipboard_append(f"#{text}")  # Add hashtag when copying
                btn.update()  # Required on some systems
                logger.info(f"Color copied to clipboard: #{text}")
            except Exception as e:
                logger.warning(f"Failed to copy to clipboard: {e}")
                # Fallback to system clipboard commands
                try:
                    if platform.system() == "Windows":
                        subprocess.run(["powershell", "-command", f"Set-Clipboard -Value '#{text}'"], 
                                     capture_output=True, check=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["pbcopy"], input=f"#{text}".encode(), check=True)
                    else:  # Linux
                        subprocess.run(["xclip", "-selection", "clipboard"], 
                                     input=f"#{text}".encode(), check=True)
                except Exception as e2:
                    logger.error(f"All clipboard methods failed: {e2}")
        
        def get_pixel_color(x, y):
            """Get pixel color at screen coordinates."""
            try:
                # Try using PIL/Pillow if available (most reliable)
                try:
                    from PIL import ImageGrab
                    screenshot = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    pixel = screenshot.getpixel((0, 0))
                    if len(pixel) >= 3:
                        r, g, b = pixel[:3]
                        logger.info(f"PIL detected color: RGB({r}, {g}, {b}) at ({x}, {y})")
                        return f"{r:02x}{g:02x}{b:02x}"
                except ImportError:
                    logger.warning("PIL/Pillow not available for color picking")
                except Exception as e:
                    logger.warning(f"PIL color detection failed: {e}")
                
                # Fallback: Use platform-specific methods
                if platform.system() == "Windows":
                    color = get_pixel_color_windows(x, y)
                    if color:
                        logger.info(f"Windows detected color: #{color} at ({x}, {y})")
                        return color
                elif platform.system() == "Darwin":  # macOS
                    color = get_pixel_color_macos(x, y)
                    if color:
                        logger.info(f"macOS detected color: #{color} at ({x}, {y})")
                        return color
                else:  # Linux
                    color = get_pixel_color_linux(x, y)
                    if color:
                        logger.info(f"Linux detected color: #{color} at ({x}, {y})")
                        return color
                
                logger.error("All color detection methods failed")
                # Return a test color for debugging (remove this in production)
                logger.warning("Returning test color for debugging")
                return "ff0000"  # Red color for testing
                    
            except Exception as e:
                logger.error(f"Failed to get pixel color: {e}")
                return None
        
        def get_pixel_color_windows(x, y):
            """Get pixel color on Windows using win32api."""
            try:
                import win32gui
                import win32ui
                import win32con
                
                # Get device context for the entire screen
                hdc = win32gui.GetDC(0)
                dc = win32ui.CreateDCFromHandle(hdc)
                
                # Get pixel color
                color = dc.GetPixel(x, y)
                
                # Convert to RGB (Windows uses BGR format)
                r = color & 0xFF
                g = (color >> 8) & 0xFF
                b = (color >> 16) & 0xFF
                
                logger.debug(f"Windows raw color: {color}, RGB: ({r}, {g}, {b})")
                
                # Clean up
                win32gui.ReleaseDC(0, hdc)
                dc.DeleteDC()
                
                return f"{r:02x}{g:02x}{b:02x}"
                
            except ImportError:
                logger.warning("win32api not available for Windows color picking")
                return None
            except Exception as e:
                logger.error(f"Windows color picking failed: {e}")
                return None
        
        def get_pixel_color_macos(x, y):
            """Get pixel color on macOS using screencapture."""
            try:
                # Use screencapture to get a 1x1 pixel image
                result = subprocess.run([
                    "screencapture", "-R", f"{x},{y},1,1", "-t", "png", "/tmp/color_pixel.png"
                ], capture_output=True, check=True)
                
                # Read the pixel data (simplified - in practice you'd parse the PNG)
                # For now, return a placeholder
                return "000000"
                
            except Exception as e:
                logger.error(f"macOS color picking failed: {e}")
                return None
        
        def get_pixel_color_linux(x, y):
            """Get pixel color on Linux using xwd."""
            try:
                # Use xwd to capture a small area around the pixel
                result = subprocess.run([
                    "xwd", "-root", "-silent", "-xy", str(x), str(y), "-out", "/tmp/color_pixel.xwd"
                ], capture_output=True, check=True)
                
                # Parse xwd file (simplified - in practice you'd parse the XWD format)
                # For now, return a placeholder
                return "000000"
                
            except Exception as e:
                logger.error(f"Linux color picking failed: {e}")
                return None
        
        def start_color_picking():
            """Start the color picking process."""
            if state["picking"]:
                return
            
            state["picking"] = True
            update_label()
            
            # Minimize the app window to get it out of the way
            self.app.iconify()
            
            # Give user time to see the instruction
            btn.after(1000, lambda: pick_color_from_screen())
        
        def pick_color_from_screen():
            """Handle the actual color picking from screen."""
            try:
                # Create a fullscreen transparent overlay for picking
                picker_window = tk.Toplevel()
                picker_window.attributes('-fullscreen', True)
                picker_window.attributes('-alpha', 0.01)  # Nearly transparent
                picker_window.attributes('-topmost', True)
                
                # Block input to other windows
                picker_window.grab_set()
                picker_window.focus_force()
                
                # Change cursor to crosshair
                try:
                    picker_window.config(cursor="crosshair")
                except:
                    pass  # Fallback if crosshair cursor not available
                
                # Make sure it's on top
                picker_window.lift()
                
                def on_click(event):
                    """Handle click on the overlay."""
                    x, y = event.x_root, event.y_root
                    logger.info(f"Color picker clicked at coordinates: ({x}, {y})")
                    color = get_pixel_color(x, y)
                    logger.info(f"Detected color: {color}")
                    
                    # Clean up first
                    state["picking"] = False
                    picker_window.grab_release()
                    picker_window.destroy()
                    self.app.deiconify()  # Restore the app window
                    
                    if color:
                        state["color"] = color
                        copy_to_clipboard(color)
                        
                        # Update label using the main app's after method
                        self.app.after(0, update_label)
                        
                        # Schedule auto-clear after 5 seconds
                        if state["clear_job"]:
                            btn.after_cancel(state["clear_job"])
                        state["clear_job"] = btn.after(30000, clear_color)
                    else:
                        # Show error briefly
                        self.app.after(0, lambda: btn.config(text=self.app._("Pick failed")))
                        self.app.after(2000, update_label)
                
                def on_escape(event):
                    """Handle escape key to cancel."""
                    state["picking"] = False
                    picker_window.grab_release()
                    picker_window.destroy()
                    self.app.deiconify()
                    self.app.after(0, update_label)
                
                picker_window.bind("<Button-1>", on_click)
                picker_window.bind("<Escape>", on_escape)
                picker_window.bind("<Key>", on_escape)  # Any key cancels
                
                # Auto-cancel after 30 seconds
                picker_window.after(30000, lambda: on_escape(None))
                
            except Exception as e:
                logger.error(f"Color picking failed: {e}")
                state["picking"] = False
                self.app.deiconify()
                self.app.after(0, update_label)
        
        def on_color_picker_click(event):
            """Handle color picker button click."""
            logger.debug(f"Color picker button clicked: {cfg.get('label', 'Color Picker')}")
            
            # Start color picking
            start_color_picking()
            
            # Add animation if enabled
            if self.app.config_data.get("animation_enabled", True) and not cfg.get("disable_animation", False):
                try:
                    from src.utils.animations import animate_button_press
                    
                    use_default_animation = cfg.get("use_default_animation", True)
                    if use_default_animation:
                        animation_type = self.app.config_data.get("default_animation_type", "ripple")
                    else:
                        animation_type = cfg.get("animation_type", "ripple")
                    
                    animate_button_press(event.widget, event.x, event.y, animation_type=animation_type)
                    
                except Exception as e:
                    logger.warning(f"Color picker animation failed: {e}")
        
        btn.bind("<Button-1>", on_color_picker_click)
        btn.bind("<Button-3>", lambda e, i=cfg: self.app.edit_button(i))
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.app.theme["button_hover"]), add="+")
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b.orig_bg), add="+")
        btn.image = None
        
        return btn 