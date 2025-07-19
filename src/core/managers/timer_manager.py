"""Timer management functionality for QuickButtons."""

import tkinter as tk
import re
import time
import os
import pygame
import platform
from src.ui.components.tooltip import Tooltip
from src.utils.logger import logger


class TimerManager:
    """Handles timer button functionality."""
    
    def __init__(self, app):
        self.app = app
    
    def create_timer_button(self, parent, cfg, font_size, cell_width):
        """Create a timer button with countdown functionality."""
        btn_label = cfg.get("label", self.app._("Timer"))
        orig_label = btn_label
        duration_str = cfg.get("timer_duration", "0:01:00")
        
        # Parse h:mm:ss
        m = re.match(r"(?:(\d+):)?(\d{1,2}):(\d{2})", duration_str)
        if m:
            h, m_, s = m.groups()
            total_seconds = int(s) + int(m_)*60 + (int(h) if h else 0)*3600
        else:
            total_seconds = 60
        
        state = {"running": False, "paused": False, "remaining": total_seconds, "job": None, "start_time": None}
        
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
        
        # Create tooltip
        user_tooltip = cfg.get("tooltip", "").strip()
        if user_tooltip == "":
            # Default timer instructions
            tooltip_text = self.app._("Single click: pause timer, Double click: reset timer")
        else:
            tooltip_text = user_tooltip
        
        # Create tooltip and store reference
        logger.debug(f"Creating timer tooltip: '{tooltip_text}'")
        btn.tooltip = Tooltip(btn, tooltip_text)
        logger.debug(f"Timer tooltip created, text property: '{btn.tooltip.text}'")
        
        # Add shortcut tooltip if configured
        if cfg.get("shortcut"):
            logger.debug(f"Creating timer shortcut tooltip: 'Shortcut: {cfg['shortcut']}'")
            btn.shortcut_tooltip = Tooltip(btn, f"Shortcut: {cfg['shortcut']}")
            logger.debug(f"Timer shortcut tooltip created, text property: '{btn.shortcut_tooltip.text}'")
        
        def update_label():
            if state["running"]:
                mins, secs = divmod(state["remaining"], 60)
                hours, mins = divmod(mins, 60)
                btn.config(text=f"{hours}:{mins:02}:{secs:02}")
            else:
                btn.config(text=orig_label)
        
        def tick():
            if not state["running"] or state["paused"]:
                return
            if state["remaining"] > 0:
                state["remaining"] -= 1
                update_label()
                state["job"] = btn.after(1000, tick)
            else:
                state["running"] = False
                update_label()
                # Play sound
                timer_sound = self.app.config_data.get("timer_sound", "")
                if timer_sound and os.path.isfile(timer_sound):
                    try:
                        self.app.music_player.play_music(timer_sound)
                    except Exception:
                        btn.bell()
                else:
                    try:
                        if platform.system() == "Windows":
                            import winsound
                            winsound.MessageBeep(winsound.MB_ICONASTERISK)
                        else:
                            btn.bell()
                    except Exception:
                        btn.bell()
        
        def start_timer():
            if state["running"]:
                return
            state["running"] = True
            state["paused"] = False
            state["remaining"] = total_seconds
            update_label()
            tick()
        
        def pause_resume_timer():
            if not state["running"]:
                start_timer()
            elif not state["paused"]:
                state["paused"] = True
                if state["job"]:
                    btn.after_cancel(state["job"])
                    state["job"] = None
                update_label()
            else:
                state["paused"] = False
                tick()
        
        def stop_timer():
            state["running"] = False
            state["paused"] = False
            if state["job"]:
                btn.after_cancel(state["job"])
                state["job"] = None
            state["remaining"] = total_seconds
            update_label()
        
        def on_timer_click(event):
            logger.debug(f"Timer button clicked: {cfg.get('label', 'Timer')}")
            logger.debug(f"Animation enabled globally: {self.app.config_data.get('animation_enabled', True)}")
            logger.debug(f"Animation disabled for button: {cfg.get('disable_animation', False)}")
            
            # Execute timer action immediately to ensure double-click detection works
            logger.debug("Executing timer action immediately")
            pause_resume_timer()
            
            # Add animation if enabled globally and not disabled for this button
            if self.app.config_data.get("animation_enabled", True) and not cfg.get("disable_animation", False):
                try:
                    from src.utils.animations import animate_button_press
                    logger.debug("Timer animation module imported successfully")
                    
                    # Check if button uses default animation or custom animation
                    use_default_animation = cfg.get("use_default_animation", True)
                    if use_default_animation:
                        # Use global animation setting
                        animation_type = self.app.config_data.get("default_animation_type", "ripple")
                        logger.debug(f"Timer using global animation: {animation_type}")
                    else:
                        # Use button-specific animation
                        animation_type = cfg.get("animation_type", "ripple")
                        logger.debug(f"Timer using button-specific animation: {animation_type}")
                    
                    logger.debug(f"Starting timer animation: {animation_type} at ({event.x}, {event.y})")
                    animate_button_press(event.widget, event.x, event.y, animation_type=animation_type)
                    logger.debug("Timer animation started successfully")
                    
                except Exception as e:
                    logger.warning(f"Timer animation failed: {e}")
                    import traceback
                    traceback.print_exc()
        
        btn.bind("<Button-1>", on_timer_click)
        btn.bind("<Double-Button-1>", lambda e: stop_timer())
        btn.bind("<Button-3>", lambda e, i=cfg: self.app.edit_button(i))
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.app.theme["button_hover"]), add="+")
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b.orig_bg), add="+")
        btn.image = None
        
        return btn 