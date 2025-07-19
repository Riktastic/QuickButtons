"""Network speed test button type handler."""

import tkinter as tk
import threading
import time
import subprocess
import re
from src.utils.logger import logger
from src.ui.components.tooltip import Tooltip


class NetworkSpeedHandler:
    """Handles execution of network speed test buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute a network speed test button."""
        # This will be called by the button manager, but we need to create a custom button
        # that handles its own execution and display
        pass
    
    def create_speed_test_button(self, parent, cfg, font_size, cell_width):
        """Create a network speed test button with live results display."""
        btn_label = cfg.get("label", self.app._("Speed Test"))
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
        
        # State for speed test
        state = {"running": False, "job": None, "results": None, "clear_job": None}
        
        # Create tooltip
        user_tooltip = cfg.get("tooltip", "").strip()
        if user_tooltip == "":
            tooltip_text = self.app._("Click to run speed test")
        else:
            tooltip_text = user_tooltip
        
        btn.tooltip = Tooltip(btn, tooltip_text)
        
        # Add shortcut tooltip if configured
        if cfg.get("shortcut"):
            btn.shortcut_tooltip = Tooltip(btn, f"Shortcut: {cfg['shortcut']}")
        
        def update_label():
            """Update button text based on current state."""
            if state["running"]:
                btn.config(text=self.app._("Testing..."))
            elif state["results"]:
                download, upload, ping = state["results"]
                if download and upload:
                    # Format speeds nicely
                    if download >= 1000:
                        download_str = f"{download/1000:.1f}G"
                    else:
                        download_str = f"{download:.0f}M"
                    
                    if upload >= 1000:
                        upload_str = f"{upload/1000:.1f}G"
                    else:
                        upload_str = f"{upload:.0f}M"
                    
                    btn.config(text=f"↓{download_str} ↑{upload_str}\n{ping}ms")
                else:
                    btn.config(text=self.app._("Test Failed"))
            else:
                btn.config(text=orig_label)
        
        def run_speed_test():
            """Run the actual speed test in a separate thread."""
            try:
                # Try to use speedtest-cli if available
                try:
                    import speedtest
                    st = speedtest.Speedtest()
                    
                    # Use auto-selection (best server)
                    st.get_best_server()
                    
                    # Test download speed
                    download_speed = st.download() / 1_000_000  # Convert to Mbps
                    
                    # Test upload speed
                    upload_speed = st.upload() / 1_000_000  # Convert to Mbps
                    
                    # Get ping
                    ping = st.results.ping
                    
                    state["results"] = (download_speed, upload_speed, ping)
                    logger.info(f"Speed test completed: {download_speed:.1f}Mbps down, {upload_speed:.1f}Mbps up, {ping:.0f}ms ping")
                    
                except ImportError:
                    # Fallback to command line speedtest if available
                    try:
                        result = subprocess.run(["speedtest", "--simple"], 
                                              capture_output=True, text=True, timeout=60)
                        if result.returncode == 0:
                            # Parse output like:
                            # Ping: 15.234 ms
                            # Download: 45.67 Mbit/s
                            # Upload: 12.34 Mbit/s
                            lines = result.stdout.strip().split('\n')
                            ping = None
                            download = None
                            upload = None
                            
                            for line in lines:
                                if line.startswith('Ping:'):
                                    ping = float(line.split()[1])
                                elif line.startswith('Download:'):
                                    download = float(line.split()[1])
                                elif line.startswith('Upload:'):
                                    upload = float(line.split()[1])
                            
                            state["results"] = (download, upload, ping)
                            logger.info(f"Speed test completed: {download}Mbps down, {upload}Mbps up, {ping}ms ping")
                        else:
                            state["results"] = (None, None, None)
                            logger.error("Speed test failed")
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        # Final fallback - try to estimate based on ping to known servers
                        state["results"] = self._estimate_speed()
                        
            except Exception as e:
                logger.error(f"Speed test error: {e}")
                state["results"] = (None, None, None)
            
            finally:
                state["running"] = False
                # Update UI in main thread
                btn.after(0, update_label)
                
                # Schedule auto-clear after 60 seconds
                if state["clear_job"]:
                    btn.after_cancel(state["clear_job"])
                state["clear_job"] = btn.after(60000, lambda: clear_results())
        
        def _estimate_speed():
            """Estimate speed based on ping to known servers."""
            try:
                import socket
                servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
                pings = []
                
                for server in servers:
                    try:
                        start_time = time.time()
                        socket.create_connection((server, 53), timeout=5)
                        ping_time = (time.time() - start_time) * 1000
                        pings.append(ping_time)
                    except:
                        continue
                
                if pings:
                    avg_ping = sum(pings) / len(pings)
                    # Very rough estimation based on ping
                    if avg_ping < 20:
                        return (100, 50, avg_ping)
                    elif avg_ping < 50:
                        return (50, 25, avg_ping)
                    elif avg_ping < 100:
                        return (25, 10, avg_ping)
                    else:
                        return (10, 5, avg_ping)
                else:
                    return (None, None, None)
            except:
                return (None, None, None)
        
        def clear_results():
            """Clear the results and show original label."""
            state["results"] = None
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            update_label()
        
        def start_speed_test():
            """Start a new speed test."""
            if state["running"]:
                return
            
            # Cancel any existing clear job
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            
            state["running"] = True
            state["results"] = None
            update_label()
            
            # Run speed test in separate thread
            thread = threading.Thread(target=run_speed_test, daemon=True)
            thread.start()
        
        def on_speed_test_click(event):
            """Handle speed test button click."""
            logger.debug(f"Speed test button clicked: {cfg.get('label', 'Speed Test')}")
            
            # Start speed test
            start_speed_test()
            
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
                    logger.warning(f"Speed test animation failed: {e}")
        
        btn.bind("<Button-1>", on_speed_test_click)
        btn.bind("<Button-3>", lambda e, i=cfg: self.app.edit_button(i))
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.app.theme["button_hover"]), add="+")
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b.orig_bg), add="+")
        btn.image = None
        
        return btn 