"""Button management functionality for QuickButtons.

Performance Optimizations Implemented:
1. Icon Caching: Icons are cached by path+size to avoid reloading
2. Font Size Caching: Font calculations are cached by cell width + labels
3. Grid Refresh Debouncing: Resize events are debounced (300ms delay, 15px threshold)
4. Memory Management: Periodic memory checks and cache cleanup (every 30s)
5. Cache Limits: Icon cache limited to 50 entries, font cache to 20 entries
6. Lazy Loading: Heavy modules (pygame, requests) are imported only when needed
7. Background Initialization: Non-critical components load in background
"""

import tkinter as tk
import tkinter.font as tkfont
import os
import sys
import subprocess
import re
from PIL import Image, ImageTk
from tkinter import messagebox

# Defer heavy imports to avoid startup delay
requests = None
pygame = None

from src.ui.components.tooltip import Tooltip
from src.utils.logger import logger
from src.utils.system import get_python_executable
from src.ui.dialogs import OutputOverlay, LLMChatOverlay
from .timer_manager import TimerManager
from src.core.button_types.button_handler_factory import ButtonHandlerFactory

# Optional imports with keyboard support
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


class ButtonManager:
    """Handles button creation, grid management, and button actions."""
    
    def __init__(self, app):
        self.app = app
        self.button_widgets = []
        self.shortcut_map = {}
        # Defer timer manager initialization
        self.timer_manager = None
        # Defer network speed manager initialization
        self.network_speed_manager = None
        # Defer ping manager initialization
        self.ping_manager = None
        # Defer pomodoro manager initialization
        self.pomodoro_manager = None
        # Defer http test manager initialization
        self.http_test_manager = None
        # Defer color picker manager initialization
        self.color_picker_manager = None
        self.button_handler_factory = ButtonHandlerFactory(app)
        self._resize_grid_after_id = None
        # Icon cache for performance
        self._icon_cache = {}
        self._icon_cache_sizes = {}
    
    def _get_cached_icon(self, icon_path, size):
        """Get cached icon or load and cache it."""
        cache_key = f"{icon_path}_{size}"
        
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        if os.path.isfile(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.convert("RGBA")
                min_side = min(img.width, img.height)
                left = (img.width - min_side) // 2
                top = (img.height - min_side) // 2
                img = img.crop((left, top, left+min_side, top+min_side))
                img = img.resize((size, size), Image.LANCZOS)
                icon = ImageTk.PhotoImage(img)
                
                # Cache the icon
                self._icon_cache[cache_key] = icon
                self._icon_cache_sizes[cache_key] = size
                
                return icon
            except Exception as e:
                logger.warning(f"Could not load icon {icon_path}: {e}")
        
        return None
    
    def _clear_icon_cache(self):
        """Clear icon cache to free memory."""
        self._icon_cache.clear()
        self._icon_cache_sizes.clear()
    
    def clear_caches(self):
        """Clear all caches to free memory."""
        self._clear_icon_cache()
        if hasattr(self, '_font_size_cache'):
            self._font_size_cache.clear()
        logger.debug("Button manager caches cleared")
    
    def _check_memory_usage(self):
        """Check memory usage and clear caches if needed."""
        try:
            import psutil
            import gc
            
            # Get memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Clear caches if memory usage is high (over 100MB)
            if memory_mb > 100:
                logger.info(f"High memory usage detected ({memory_mb:.1f}MB), clearing caches")
                self.clear_caches()
                gc.collect()  # Force garbage collection
                
        except ImportError:
            # psutil not available, skip memory check
            pass
        except Exception as e:
            logger.debug(f"Memory check failed: {e}")
    
    def _schedule_periodic_memory_check(self):
        """Schedule periodic memory checks."""
        try:
            # Check memory every 30 seconds
            self.app.after(30000, self._periodic_memory_check)
        except Exception as e:
            logger.debug(f"Failed to schedule memory check: {e}")
    
    def _periodic_memory_check(self):
        """Periodic memory check and cache cleanup."""
        try:
            # Check memory usage
            self._check_memory_usage()
            
            # Clean up old cache entries (keep only recent ones)
            self._cleanup_old_cache_entries()
            
            # Schedule next check
            self._schedule_periodic_memory_check()
            
        except Exception as e:
            logger.debug(f"Periodic memory check failed: {e}")
    
    def _cleanup_old_cache_entries(self):
        """Clean up old cache entries to prevent unbounded growth."""
        try:
            # Limit icon cache to 50 entries
            if len(self._icon_cache) > 50:
                # Remove oldest entries (simple FIFO)
                keys_to_remove = list(self._icon_cache.keys())[:-50]
                for key in keys_to_remove:
                    del self._icon_cache[key]
                    if key in self._icon_cache_sizes:
                        del self._icon_cache_sizes[key]
                logger.debug(f"Cleaned up {len(keys_to_remove)} old icon cache entries")
            
            # Limit font cache to 20 entries
            if hasattr(self, '_font_size_cache') and len(self._font_size_cache) > 20:
                keys_to_remove = list(self._font_size_cache.keys())[:-20]
                for key in keys_to_remove:
                    del self._font_size_cache[key]
                logger.debug(f"Cleaned up {len(keys_to_remove)} old font cache entries")
                
        except Exception as e:
            logger.debug(f"Cache cleanup failed: {e}")
    
    def create_button_grid(self):
        """Create the scrollable button grid area."""
        self.grid_canvas = tk.Canvas(self.app, bg=self.app.theme["bg"], highlightthickness=0, borderwidth=0)
        self.grid_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))
        
        self.grid_scrollbar = tk.Scrollbar(self.app, orient=tk.VERTICAL, command=self.grid_canvas.yview,
                                          bg=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                                          troughcolor=self.app.theme.get("scrollbar_trough", "#f0f0f0"),
                                          activebackground=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                                          highlightthickness=0, relief=tk.FLAT, borderwidth=0)
        self.grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.grid_hscrollbar = tk.Scrollbar(self.app, orient=tk.HORIZONTAL, command=self.grid_canvas.xview,
                                           bg=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                                           troughcolor=self.app.theme.get("scrollbar_trough", "#f0f0f0"),
                                           activebackground=self.app.theme.get("scrollbar_bg", "#c0c0c0"),
                                           highlightthickness=0, relief=tk.FLAT, borderwidth=0)
        self.grid_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.grid_frame = tk.Frame(self.grid_canvas, bg=self.app.theme["bg"])
        self.grid_window = self.grid_canvas.create_window((0,0), window=self.grid_frame, anchor="nw")
        self.grid_canvas.configure(yscrollcommand=self.grid_scrollbar.set, xscrollcommand=self.grid_hscrollbar.set)
        
        self.grid_frame.bind("<Configure>", lambda e: self._on_grid_configure())
        self.grid_canvas.bind("<Configure>", self._on_canvas_resize_and_refresh)
        
        self.button_widgets = []
        self._resize_grid_after_id = None
        self.refresh_grid()
        
        # Start periodic memory checks
        self._schedule_periodic_memory_check()
        
        logger.info("Button grid created")
    
    def _on_canvas_resize_and_refresh(self, event):
        """Handle canvas resize and refresh with improved debouncing."""
        # Only refresh if width actually changed significantly (threshold of 15 pixels)
        current_width = self.grid_canvas.winfo_width()
        if hasattr(self, '_last_canvas_width') and abs(current_width - self._last_canvas_width) < 15:
            return
        
        # Store the new width
        self._last_canvas_width = current_width
        self.grid_canvas.itemconfig(self.grid_window, width=current_width)
        
        # Improved debouncing: cancel previous refresh and schedule new one
        if self._resize_grid_after_id:
            self.app.after_cancel(self._resize_grid_after_id)
        
        # Schedule refresh with longer delay for better performance
        self._resize_grid_after_id = self.app.after(300, self._debounced_refresh_grid)
    
    def _debounced_refresh_grid(self):
        """Debounced grid refresh with memory check."""
        # Check memory usage before refresh
        self._check_memory_usage()
        
        # Clear the after ID
        self._resize_grid_after_id = None
        
        # Perform the actual refresh
        self.refresh_grid()
    
    def _on_grid_configure(self):
        """Update the scroll region and show/hide scrollbar as needed."""
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        # Show scrollbar only if needed
        frame_height = self.grid_frame.winfo_height()
        canvas_height = self.grid_canvas.winfo_height()
        if frame_height > canvas_height:
            self.grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.grid_scrollbar.pack_forget()
    
    def refresh_grid(self):
        """Refresh the button grid."""
        # Remove all widgets from grid_frame
        for w in self.grid_frame.winfo_children():
            w.destroy()
        
        # Get settings
        min_btn_width = self.app.config_data.get("min_btn_width", 80)
        max_btn_width = self.app.config_data.get("max_btn_width", 120)
        min_btn_height = self.app.config_data.get("min_btn_height", 40)
        max_btn_height = self.app.config_data.get("max_btn_height", 80)
        btn_hpad = 4
        btn_vpad = 4
        btns = self.app.config_data.get("buttons", [])
        width = self.grid_frame.winfo_width() or self.grid_canvas.winfo_width() or 220
        n = len(btns)
        
        # Calculate columns and cell size
        if n == 0:
            per_row = 1
        else:
            max_cols = max(1, width // (max_btn_width + 2*btn_hpad))
            per_row = min(n, max_cols)
        
        # Calculate cell width so all columns are equal
        if per_row > 0:
            cell_width = min(max_btn_width, max(min_btn_width, (width - (per_row+1)*btn_hpad*2) // per_row))
        else:
            cell_width = max_btn_width
        
        cell_height = max(min_btn_height, min(max_btn_height, cell_width))
        
        # Find the largest font size that fits the longest label in cell_width
        labels = [cfg.get("label", "Run Script") for cfg in btns]
        
        # Cache font size calculation
        font_cache_key = f"{cell_width}_{hash(tuple(sorted(labels)))}"
        if hasattr(self, '_font_size_cache') and font_cache_key in self._font_size_cache:
            font_size = self._font_size_cache[font_cache_key]
        else:
            font_size = self.find_grid_font_size(labels, cell_width)
            if not hasattr(self, '_font_size_cache'):
                self._font_size_cache = {}
            self._font_size_cache[font_cache_key] = font_size
        
        # Center the grid
        total_grid_width = per_row * (cell_width + 2*btn_hpad)
        extra_space = max(0, width - total_grid_width)
        left_pad = extra_space // 2
        
        # Set grid_frame width for horizontal scrolling if needed
        if total_grid_width > width:
            self.grid_canvas.itemconfig(self.grid_window, width=total_grid_width)
            self.grid_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            self.grid_canvas.itemconfig(self.grid_window, width=width)
            self.grid_hscrollbar.pack_forget()
        
        # Configure grid columns and rows for even distribution
        for c in range(per_row):
            self.grid_frame.grid_columnconfigure(c, weight=1)
        num_rows = (n + per_row - 1) // per_row if per_row else 1
        for r in range(num_rows):
            self.grid_frame.grid_rowconfigure(r, weight=1)
        
        # Add left padding column if needed
        if left_pad > 0:
            self.grid_frame.grid_columnconfigure(per_row, weight=0, minsize=left_pad)
        
        self.button_widgets = []
        for idx, btn_cfg in enumerate(btns):
            row, col = divmod(idx, per_row)
            cell = tk.Frame(self.grid_frame, width=cell_width, height=cell_height, bg=self.app.theme["bg"])
            cell.grid(row=row, column=col, padx=btn_hpad, pady=btn_vpad, sticky="nsew")
            cell.grid_propagate(False)
            
            btn = self.create_button(cell, btn_cfg, font_size, cell_width)
            btn.place(x=0, y=0, relwidth=1, relheight=1)
            self.button_widgets.append(btn)
            
            # Set up shortcuts
            shortcut = btn_cfg.get("shortcut", "").strip()
            if shortcut:
                keyseq = self.parse_shortcut(shortcut)
                if keyseq:
                    self.shortcut_map[keyseq] = lambda c=btn_cfg: self.run_script(c)
                    self.app.bind_all(keyseq, lambda e, c=btn_cfg: self.run_script(c))
                
                if HAS_KEYBOARD and shortcut:
                    try:
                        keyboard.add_hotkey(shortcut, lambda c=btn_cfg: self.run_script(c))
                        self.app.global_hotkeys.append(shortcut)
                    except Exception as e:
                        logger.warning(f"Could not register global hotkey {shortcut}: {e}")
        
        if not HAS_KEYBOARD:
            logger.info("Global hotkeys require the 'keyboard' module. Install with 'pip install keyboard'.")
        elif sys.platform.startswith("linux") and os.geteuid() != 0:
            logger.info("On Linux, global hotkeys require root or uinput access.")
        
        self.grid_frame.update_idletasks()
        self._on_grid_configure()
        logger.info(f"Grid refreshed: {n} buttons in {per_row} columns, cell_width={cell_width}")
    
    def _ensure_timer_manager_loaded(self):
        """Ensure timer manager is loaded when needed."""
        if self.timer_manager is None:
            self.timer_manager = TimerManager(self.app)
    
    def _ensure_network_speed_manager_loaded(self):
        """Ensure network speed manager is loaded when needed."""
        if self.network_speed_manager is None:
            from src.core.button_types.network_speed_handler import NetworkSpeedHandler
            self.network_speed_manager = NetworkSpeedHandler(self.app)
    
    def _ensure_ping_manager_loaded(self):
        """Ensure ping manager is loaded when needed."""
        if self.ping_manager is None:
            from src.core.button_types.ping_handler import PingHandler
            self.ping_manager = PingHandler(self.app)
    
    def _ensure_pomodoro_manager_loaded(self):
        """Ensure pomodoro manager is loaded when needed."""
        if self.pomodoro_manager is None:
            from src.core.button_types.pomodoro_handler import PomodoroHandler
            self.pomodoro_manager = PomodoroHandler(self.app)
    
    def _ensure_http_test_manager_loaded(self):
        """Ensure http test manager is loaded when needed."""
        if self.http_test_manager is None:
            from src.core.button_types.http_test_handler import HTTPTestHandler
            self.http_test_manager = HTTPTestHandler(self.app)
    
    def _ensure_color_picker_manager_loaded(self):
        """Ensure color picker manager is loaded when needed."""
        if self.color_picker_manager is None:
            from src.core.button_types.color_picker_handler import ColorPickerHandler
            self.color_picker_manager = ColorPickerHandler(self.app)
    

    
    def repack_grid(self):
        """Repack the button grid in the correct order."""
        if hasattr(self, 'grid_canvas') and self.grid_canvas.winfo_exists():
            self.grid_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))
            if hasattr(self, 'grid_scrollbar') and self.grid_scrollbar.winfo_exists():
                self.grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            if hasattr(self, 'grid_hscrollbar') and self.grid_hscrollbar.winfo_exists():
                self.grid_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            logger.info("Button grid repacked")
    
    def unpack_grid(self):
        """Temporarily unpack the button grid."""
        if hasattr(self, 'grid_canvas') and self.grid_canvas.winfo_exists():
            self.grid_canvas.pack_forget()
            if hasattr(self, 'grid_scrollbar') and self.grid_scrollbar.winfo_exists():
                self.grid_scrollbar.pack_forget()
            if hasattr(self, 'grid_hscrollbar') and self.grid_hscrollbar.winfo_exists():
                self.grid_hscrollbar.pack_forget()
            logger.info("Button grid unpacked")
    
    def find_grid_font_size(self, labels, cell_width, max_font=20, min_font=7):
        """Find the largest font size that fits all labels in the given cell width."""
        font_size = max_font
        test_font = tkfont.Font(family="Segoe UI", size=font_size, weight="bold")
        while font_size > min_font:
            fits = True
            for label in labels:
                lines = label.split("\n")
                max_line = max(lines, key=len) if lines else label
                width = test_font.measure(max_line)
                if width > cell_width - 10:
                    fits = False
                    break
            if fits:
                break
            font_size -= 1
            test_font.configure(size=font_size)
        return font_size
    
    def parse_shortcut(self, shortcut):
        """Parse a shortcut string into a tkinter key sequence."""
        # Simple implementation - could be enhanced
        return f"<{shortcut.replace('+', '-')}>"
    
    def create_button(self, parent, cfg, font_size, cell_width):
        """Create a single button in the grid, with icon, label, and right-click edit."""
        if not hasattr(self.app, 'current_music_path'):
            self.app.current_music_path = None
        if not hasattr(self.app, 'current_music_btn'):
            self.app.current_music_btn = None
        
        icon = None
        if cfg.get("icon"):
            icon = self._get_cached_icon(cfg["icon"], cell_width-18)
        
        label = cfg.get("label", "Run Script")
        
        # Default color logic
        use_default = cfg.get("use_default_colors", False)
        if use_default:
            btn_bg = self.app.theme["button_bg"]
            btn_fg = self.app.theme["button_fg"]
        else:
            btn_bg = cfg.get("bg_color", self.app.theme["button_bg"])
            btn_fg = cfg.get("fg_color", self.app.theme["button_fg"])
        
        btn = tk.Button(parent, text=label, image=icon, compound=tk.TOP if icon else tk.NONE,
                        bg=btn_bg, fg=btn_fg, font=("Segoe UI", font_size),
                        relief=tk.FLAT, bd=0, highlightthickness=0,
                        activebackground=self.app.theme["button_hover"],
                        activeforeground=btn_fg,
                        wraplength=cell_width-10, justify="center")
        
        # Add animation support
        btn.bind("<Button-1>", lambda e, c=cfg: self._on_button_click(e, c))
        
        btn.bind("<Button-3>", lambda e, i=cfg: self.app.edit_button(i))
        
        # Create dynamic hover functions that respect use_default_colors
        def on_enter(event, button=btn, config=cfg):
            button.config(bg=self.app.theme["button_hover"])
        
        def on_leave(event, button=btn, config=cfg):
            use_default = config.get("use_default_colors", False)
            if use_default:
                button.config(bg=self.app.theme["button_bg"])
            else:
                button.config(bg=button.orig_bg)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        btn.image = icon
        
        # Music glow effect (deferred to avoid pygame import during startup)
        if cfg.get("type") == "music" and hasattr(self.app, 'current_music_path') and self.app.current_music_path == cfg.get("music"):
            # Check pygame availability and music status safely
            try:
                import pygame
                if pygame.mixer.music.get_busy():
                    if hasattr(self.app, 'music_manager') and self.app.music_manager:
                        self.app.music_manager._start_music_glow(btn)
            except (ImportError, AttributeError):
                pass  # pygame not available or not initialized
        
        # Create default tooltip if none configured (but not for timer buttons)
        if cfg.get("type") != "timer":
            configured_tooltip = cfg.get("tooltip", "").strip()
            if configured_tooltip:
                tooltip_text = configured_tooltip
            else:
                # Default tooltip: "Run {button name}"
                tooltip_text = self.app._("Run") + f" {label}"
            Tooltip(btn, tooltip_text)
            
            if cfg.get("shortcut"):
                Tooltip(btn, f"Shortcut: {cfg['shortcut']}")
        # Timer buttons handle their own tooltips in timer_manager.py
        
        btn.orig_bg = btn_bg  # Store for glow
        
        if cfg.get("type") == "timer":
            self._ensure_timer_manager_loaded()
            return self.timer_manager.create_timer_button(parent, cfg, font_size, cell_width)
        elif cfg.get("type") == "network_speed":
            self._ensure_network_speed_manager_loaded()
            return self.network_speed_manager.create_speed_test_button(parent, cfg, font_size, cell_width)
        elif cfg.get("type") == "ping":
            self._ensure_ping_manager_loaded()
            return self.ping_manager.create_ping_button(parent, cfg, font_size, cell_width)
        elif cfg.get("type") == "pomodoro":
            self._ensure_pomodoro_manager_loaded()
            return self.pomodoro_manager.create_pomodoro_button(parent, cfg, font_size, cell_width)
        elif cfg.get("type") == "http_test":
            self._ensure_http_test_manager_loaded()
            return self.http_test_manager.create_http_test_button(parent, cfg, font_size, cell_width)
        elif cfg.get("type") == "color_picker":
            self._ensure_color_picker_manager_loaded()
            return self.color_picker_manager.create_color_picker_button(parent, cfg, font_size, cell_width)
        
        return btn
    
    def _on_button_click(self, event, cfg):
        """Handle button click with animation."""
        logger.debug(f"Button clicked: {cfg.get('label', 'Unknown')}")
        logger.debug(f"Animation enabled globally: {self.app.config_data.get('animation_enabled', True)}")
        logger.debug(f"Animation disabled for button: {cfg.get('disable_animation', False)}")
        
        # Check if animations are enabled globally and not disabled for this button
        if self.app.config_data.get("animation_enabled", True) and not cfg.get("disable_animation", False):
            try:
                from src.utils.animations import animate_button_press
                logger.debug("Animation module imported successfully")
                
                # Check if button uses default animation or custom animation
                use_default_animation = cfg.get("use_default_animation", True)
                if use_default_animation:
                    # Use global animation setting
                    animation_type = self.app.config_data.get("default_animation_type", "ripple")
                    logger.debug(f"Using global animation: {animation_type}")
                else:
                    # Use button-specific animation
                    animation_type = cfg.get("animation_type", "ripple")
                    logger.debug(f"Using button-specific animation: {animation_type}")
                
                logger.debug(f"Starting animation: {animation_type} at ({event.x}, {event.y})")
                animate_button_press(event.widget, event.x, event.y, animation_type=animation_type)
                logger.debug("Animation started successfully")
                
                # Add a small delay before executing the action to allow animation to be visible
                self.app.after(100, lambda: self.run_script(cfg))
                return  # Don't execute action immediately
            except Exception as e:
                logger.warning(f"Animation failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Execute the button action (if no animation or animation failed)
        logger.debug("Executing button action immediately")
        self.run_script(cfg)

    def run_script(self, cfg):
        """Execute a button's action using the appropriate handler."""
        try:
            self.button_handler_factory.execute_button(cfg)
        except Exception as e:
            logger.error(f"Failed to execute button {cfg.get('label', 'Unknown')}: {e}")
            messagebox.showerror(self.app._("Error"), f"Failed to execute button: {e}")
    
 