"""Ping button type handler."""

import tkinter as tk
import threading
import time
import subprocess
import socket
from src.utils.logger import logger
from src.ui.components.tooltip import Tooltip


class PingHandler:
    """Handles execution of ping buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute a ping button."""
        # This will be called by the button manager, but we need to create a custom button
        # that handles its own execution and display
        pass
    
    def create_ping_button(self, parent, cfg, font_size, cell_width):
        """Create a ping button with live results display."""
        btn_label = cfg.get("label", self.app._("Ping"))
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
        
        # State for ping test
        state = {"running": False, "job": None, "results": None, "clear_job": None}
        
        # Create tooltip
        user_tooltip = cfg.get("tooltip", "").strip()
        if user_tooltip == "":
            tooltip_text = self.app._("Click to ping host")
        else:
            tooltip_text = user_tooltip
        
        btn.tooltip = Tooltip(btn, tooltip_text)
        
        # Add shortcut tooltip if configured
        if cfg.get("shortcut"):
            btn.shortcut_tooltip = Tooltip(btn, f"Shortcut: {cfg['shortcut']}")
        
        def update_label():
            """Update button text based on current state."""
            if state["running"]:
                btn.config(text=self.app._("Pinging..."))
            elif state["results"]:
                ping_time, success, host = state["results"]
                if success:
                    if ping_time < 1:
                        ping_str = f"{ping_time:.0f}ms"
                    else:
                        ping_str = f"{ping_time:.1f}ms"
                    btn.config(text=f"{host}\n{ping_str}")
                else:
                    btn.config(text=f"{host}\n{self.app._('Failed')}")
            else:
                btn.config(text=orig_label)
        
        def run_ping():
            """Run the actual ping in a separate thread."""
            try:
                host = cfg.get("ping_host", "8.8.8.8")
                count = cfg.get("ping_count", 3)
                
                # Try using subprocess ping first (more accurate)
                try:
                    if subprocess.run(["ping", "-n" if subprocess.sys.platform.startswith("win") else "-c", 
                                      str(count), host], 
                                     capture_output=True, text=True, timeout=30).returncode == 0:
                        # Parse ping output to get average time
                        result = subprocess.run(["ping", "-n" if subprocess.sys.platform.startswith("win") else "-c", 
                                               str(count), host], 
                                              capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            # Parse the output to extract ping time
                            output = result.stdout
                            ping_times = []
                            
                            if subprocess.sys.platform.startswith("win"):
                                # Windows ping output parsing
                                for line in output.split('\n'):
                                    if 'time=' in line or 'time<' in line:
                                        try:
                                            if 'time=' in line:
                                                time_str = line.split('time=')[1].split('ms')[0].strip()
                                                ping_times.append(float(time_str))
                                            elif 'time<' in line:
                                                ping_times.append(1.0)  # Less than 1ms
                                        except:
                                            continue
                            else:
                                # Linux/Mac ping output parsing
                                for line in output.split('\n'):
                                    if 'time=' in line:
                                        try:
                                            time_str = line.split('time=')[1].split(' ')[0].strip()
                                            ping_times.append(float(time_str))
                                        except:
                                            continue
                            
                            if ping_times:
                                avg_ping = sum(ping_times) / len(ping_times)
                                state["results"] = (avg_ping, True, host)
                                logger.info(f"Ping completed: {host} - {avg_ping:.1f}ms")
                            else:
                                state["results"] = (None, False, host)
                                logger.warning(f"Ping failed to parse output: {host}")
                        else:
                            state["results"] = (None, False, host)
                            logger.warning(f"Ping command failed: {host}")
                    else:
                        state["results"] = (None, False, host)
                        logger.warning(f"Ping failed: {host}")
                        
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # Fallback to socket-based ping
                    try:
                        start_time = time.time()
                        socket.create_connection((host, 80), timeout=5)
                        ping_time = (time.time() - start_time) * 1000
                        state["results"] = (ping_time, True, host)
                        logger.info(f"Socket ping completed: {host} - {ping_time:.1f}ms")
                    except Exception as e:
                        state["results"] = (None, False, host)
                        logger.warning(f"Socket ping failed: {host} - {e}")
                        
            except Exception as e:
                logger.error(f"Ping error: {e}")
                host = cfg.get("ping_host", "8.8.8.8")
                state["results"] = (None, False, host)
            
            finally:
                state["running"] = False
                # Update UI in main thread
                btn.after(0, update_label)
                
                # Schedule auto-clear after 60 seconds
                if state["clear_job"]:
                    btn.after_cancel(state["clear_job"])
                state["clear_job"] = btn.after(60000, lambda: clear_results())
        
        def clear_results():
            """Clear the results and show original label."""
            state["results"] = None
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            update_label()
        
        def start_ping():
            """Start a new ping test."""
            if state["running"]:
                return
            
            # Cancel any existing clear job
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            
            state["running"] = True
            state["results"] = None
            update_label()
            
            # Run ping in separate thread
            thread = threading.Thread(target=run_ping, daemon=True)
            thread.start()
        
        def on_ping_click(event):
            """Handle ping button click."""
            logger.debug(f"Ping button clicked: {cfg.get('label', 'Ping')}")
            
            # Start ping test
            start_ping()
            
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
                    logger.warning(f"Ping animation failed: {e}")
        
        btn.bind("<Button-1>", on_ping_click)
        btn.bind("<Button-3>", lambda e, i=cfg: self.app.edit_button(i))
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.app.theme["button_hover"]), add="+")
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b.orig_bg), add="+")
        btn.image = None
        
        return btn 