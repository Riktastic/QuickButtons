"""Pomodoro timer button type handler."""

import tkinter as tk
import time
import os
import platform
from src.utils.logger import logger
from src.ui.components.tooltip import Tooltip


class PomodoroHandler:
    """Handles execution of Pomodoro timer buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute a Pomodoro timer button."""
        # This will be called by the button manager, but we need to create a custom button
        # that handles its own execution and display
        pass
    
    def create_pomodoro_button(self, parent, cfg, font_size, cell_width):
        """Create a Pomodoro timer button with full Pomodoro Technique support."""
        btn_label = cfg.get("label", self.app._("Pomodoro"))
        orig_label = btn_label
        
        # Get Pomodoro configuration
        work_duration = cfg.get("work_duration", 25) * 60  # Convert to seconds
        short_break_duration = cfg.get("short_break_duration", 5) * 60
        long_break_duration = cfg.get("long_break_duration", 15) * 60
        sessions_before_long_break = cfg.get("sessions_before_long_break", 4)
        auto_advance = cfg.get("auto_advance", True)
        
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
        
        # State for Pomodoro timer
        state = {
            "running": False,
            "paused": False,
            "job": None,
            "clear_job": None,
            "phase": "ready",  # ready, work, short_break, long_break, complete
            "remaining": work_duration,
            "sessions_completed": 0,
            "current_session": 1
        }
        
        # Create tooltip
        user_tooltip = cfg.get("tooltip", "").strip()
        if user_tooltip == "":
            tooltip_text = self.app._("Click: start/pause, Right-click: skip, Double-click: reset")
        else:
            tooltip_text = user_tooltip
        
        btn.tooltip = Tooltip(btn, tooltip_text)
        
        # Add shortcut tooltip if configured
        if cfg.get("shortcut"):
            btn.shortcut_tooltip = Tooltip(btn, f"Shortcut: {cfg['shortcut']}")
        
        def format_time(seconds):
            """Format seconds to mm:ss display."""
            mins, secs = divmod(seconds, 60)
            return f"{mins:02d}:{secs:02d}"
        
        def update_label():
            """Update button text based on current state."""
            if state["phase"] == "ready":
                btn.config(text=orig_label)
            elif state["phase"] == "work":
                if state["running"] and not state["paused"]:
                    time_str = format_time(state["remaining"])
                    session_str = f"Session {state['current_session']}/{sessions_before_long_break}"
                    btn.config(text=f"Work: {time_str}\n{session_str}")
                else:
                    time_str = format_time(state["remaining"])
                    btn.config(text=f"Work: {time_str}\n{self.app._('Paused')}")
            elif state["phase"] == "short_break":
                if state["running"] and not state["paused"]:
                    time_str = format_time(state["remaining"])
                    btn.config(text=f"{self.app._('Short Break')}: {time_str}")
                else:
                    time_str = format_time(state["remaining"])
                    btn.config(text=f"{self.app._('Short Break')}: {time_str}\n{self.app._('Paused')}")
            elif state["phase"] == "long_break":
                if state["running"] and not state["paused"]:
                    time_str = format_time(state["remaining"])
                    btn.config(text=f"{self.app._('Long Break')}: {time_str}")
                else:
                    time_str = format_time(state["remaining"])
                    btn.config(text=f"{self.app._('Long Break')}: {time_str}\n{self.app._('Paused')}")
            elif state["phase"] == "complete":
                if state["sessions_completed"] > 0:
                    btn.config(text=f"{self.app._('Work Complete!')}\n{state['sessions_completed']} sessions")
                else:
                    btn.config(text=f"{self.app._('Break Complete!')}")
        
        def play_notification_sound():
            """Play notification sound when timer completes."""
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
        
        def clear_complete_message():
            """Clear the completion message and return to ready state."""
            state["phase"] = "ready"
            state["remaining"] = work_duration
            update_label()
        
        def advance_phase():
            """Advance to the next phase in the Pomodoro cycle."""
            if state["phase"] == "work":
                state["sessions_completed"] += 1
                if state["sessions_completed"] % sessions_before_long_break == 0:
                    # Long break after completing sessions_before_long_break work sessions
                    state["phase"] = "long_break"
                    state["remaining"] = long_break_duration
                    logger.info(f"Starting long break after {state['sessions_completed']} work sessions")
                else:
                    # Short break
                    state["phase"] = "short_break"
                    state["remaining"] = short_break_duration
                    logger.info(f"Starting short break after work session {state['sessions_completed']}")
            elif state["phase"] in ["short_break", "long_break"]:
                # Back to work
                state["phase"] = "work"
                state["remaining"] = work_duration
                state["current_session"] = state["sessions_completed"] + 1
                logger.info(f"Starting work session {state['current_session']}")
            
            state["running"] = True
            state["paused"] = False
            update_label()
            tick()
        
        def tick():
            """Timer tick function."""
            if not state["running"] or state["paused"]:
                return
            
            if state["remaining"] > 0:
                state["remaining"] -= 1
                update_label()
                state["job"] = btn.after(1000, tick)
            else:
                # Timer completed
                state["running"] = False
                state["phase"] = "complete"
                update_label()
                
                # Play notification sound
                play_notification_sound()
                
                # Schedule auto-clear after 60 seconds
                if state["clear_job"]:
                    btn.after_cancel(state["clear_job"])
                state["clear_job"] = btn.after(60000, clear_complete_message)
                
                # Auto-advance to next phase if enabled
                if auto_advance:
                    btn.after(3000, advance_phase)  # Wait 3 seconds then auto-advance
        
        def start_pomodoro():
            """Start the Pomodoro timer."""
            if state["phase"] == "ready":
                # Start first work session
                state["phase"] = "work"
                state["remaining"] = work_duration
                state["running"] = True
                state["paused"] = False
                state["current_session"] = 1
                logger.info("Starting Pomodoro work session")
            elif state["paused"]:
                # Resume from pause
                state["paused"] = False
                logger.info("Resuming Pomodoro timer")
            else:
                # Pause current session
                state["paused"] = True
                logger.info("Pausing Pomodoro timer")
            
            update_label()
            if state["running"] and not state["paused"]:
                tick()
        
        def skip_phase():
            """Skip current phase and move to next."""
            if state["running"]:
                if state["job"]:
                    btn.after_cancel(state["job"])
                    state["job"] = None
                advance_phase()
                logger.info("Skipping current Pomodoro phase")
        
        def reset_pomodoro():
            """Reset Pomodoro to initial state."""
            if state["job"]:
                btn.after_cancel(state["job"])
                state["job"] = None
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            
            state["running"] = False
            state["paused"] = False
            state["phase"] = "ready"
            state["remaining"] = work_duration
            state["sessions_completed"] = 0
            state["current_session"] = 1
            update_label()
            logger.info("Resetting Pomodoro timer")
        
        def on_pomodoro_click(event):
            """Handle Pomodoro button click."""
            logger.debug(f"Pomodoro button clicked: {cfg.get('label', 'Pomodoro')}")
            
            # Start/pause/resume Pomodoro
            start_pomodoro()
            
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
                    logger.warning(f"Pomodoro animation failed: {e}")
        
        def on_pomodoro_right_click(event):
            """Handle Pomodoro button right-click (skip phase)."""
            skip_phase()
        
        def on_pomodoro_double_click(event):
            """Handle Pomodoro button double-click (reset)."""
            reset_pomodoro()
        
        btn.bind("<Button-1>", on_pomodoro_click)
        btn.bind("<Button-3>", on_pomodoro_right_click)
        btn.bind("<Double-Button-1>", on_pomodoro_double_click)
        btn.bind("<Button-3>", lambda e, i=cfg: self.app.edit_button(i), add="+")
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.app.theme["button_hover"]), add="+")
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b.orig_bg), add="+")
        btn.image = None
        
        return btn 