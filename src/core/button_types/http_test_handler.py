"""HTTP test button type handler."""

import tkinter as tk
import threading
import time
import requests
import urllib3
from urllib.parse import urlparse
from src.utils.logger import logger
from src.ui.components.tooltip import Tooltip


class HTTPTestHandler:
    """Handles execution of HTTP test buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute an HTTP test button."""
        # This will be called by the button manager, but we need to create a custom button
        # that handles its own execution and display
        pass
    
    def create_http_test_button(self, parent, cfg, font_size, cell_width):
        """Create an HTTP test button with connectivity and certificate status display."""
        btn_label = cfg.get("label", self.app._("HTTP Test"))
        orig_label = btn_label
        
        # Get HTTP test configuration
        test_url = cfg.get("test_url", "https://google.com")
        timeout = cfg.get("timeout", 10)
        
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
        
        # State for HTTP test
        state = {"running": False, "job": None, "clear_job": None, "results": None}
        
        # Create tooltip
        user_tooltip = cfg.get("tooltip", "").strip()
        if user_tooltip == "":
            tooltip_text = self.app._("Click to test HTTP/HTTPS connectivity")
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
                status, response_time, https_status, cert_valid = state["results"]
                if status == "success":
                    # Format response time
                    if response_time < 1:
                        time_str = f"{response_time*1000:.0f}ms"
                    else:
                        time_str = f"{response_time:.1f}s"
                    
                    # Determine lock status
                    if https_status == "https":
                        if cert_valid:
                            lock_icon = "🔒"  # Locked (HTTPS with valid cert)
                        else:
                            lock_icon = "🔓"  # Unlocked (HTTPS with invalid cert)
                    else:
                        lock_icon = "🌐"  # Globe (HTTP only)
                    
                    # Extract domain for display
                    try:
                        domain = urlparse(test_url).netloc
                        if not domain:
                            domain = urlparse(test_url).path.split('/')[0]
                    except:
                        domain = test_url
                    
                    btn.config(text=f"{lock_icon} {domain}\n{time_str}")
                else:
                    btn.config(text=f"❌ {self.app._('Failed')}")
            else:
                btn.config(text=orig_label)
        
        def clear_results():
            """Clear the results and show original label."""
            state["results"] = None
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            update_label()
        
        def run_http_test():
            """Run the actual HTTP test in a separate thread."""
            try:
                start_time = time.time()
                
                # Test HTTPS first
                https_url = test_url
                if not https_url.startswith(('http://', 'https://')):
                    https_url = 'https://' + test_url
                
                https_status = "https"
                cert_valid = True
                
                try:
                    # Test HTTPS with certificate validation
                    response = requests.get(https_url, timeout=timeout, verify=True)
                    response_time = time.time() - start_time
                    
                    if response.status_code < 400:
                        state["results"] = ("success", response_time, https_status, cert_valid)
                        logger.info(f"HTTPS test successful: {https_url} - {response_time:.2f}s")
                    else:
                        state["results"] = ("failed", response_time, https_status, cert_valid)
                        logger.warning(f"HTTPS test failed with status {response.status_code}: {https_url}")
                
                except requests.exceptions.SSLError:
                    # HTTPS failed due to SSL/certificate issues
                    cert_valid = False
                    try:
                        # Try HTTPS without certificate validation
                        response = requests.get(https_url, timeout=timeout, verify=False)
                        response_time = time.time() - start_time
                        
                        if response.status_code < 400:
                            state["results"] = ("success", response_time, https_status, cert_valid)
                            logger.warning(f"HTTPS test successful with invalid certificate: {https_url} - {response_time:.2f}s")
                        else:
                            state["results"] = ("failed", response_time, https_status, cert_valid)
                            logger.warning(f"HTTPS test failed with invalid certificate: {https_url}")
                    except:
                        # HTTPS completely failed, try HTTP
                        https_status = "http"
                        cert_valid = False
                        
                        http_url = test_url
                        if not http_url.startswith('http://'):
                            if http_url.startswith('https://'):
                                http_url = 'http://' + http_url[8:]
                            else:
                                http_url = 'http://' + http_url
                        
                        try:
                            response = requests.get(http_url, timeout=timeout)
                            response_time = time.time() - start_time
                            
                            if response.status_code < 400:
                                state["results"] = ("success", response_time, https_status, cert_valid)
                                logger.info(f"HTTP test successful: {http_url} - {response_time:.2f}s")
                            else:
                                state["results"] = ("failed", response_time, https_status, cert_valid)
                                logger.warning(f"HTTP test failed with status {response.status_code}: {http_url}")
                        except:
                            state["results"] = ("failed", 0, https_status, cert_valid)
                            logger.error(f"HTTP test completely failed: {test_url}")
                
                except requests.exceptions.RequestException as e:
                    # HTTPS failed, try HTTP
                    https_status = "http"
                    cert_valid = False
                    
                    http_url = test_url
                    if not http_url.startswith('http://'):
                        if http_url.startswith('https://'):
                            http_url = 'http://' + http_url[8:]
                        else:
                            http_url = 'http://' + http_url
                    
                    try:
                        response = requests.get(http_url, timeout=timeout)
                        response_time = time.time() - start_time
                        
                        if response.status_code < 400:
                            state["results"] = ("success", response_time, https_status, cert_valid)
                            logger.info(f"HTTP test successful: {http_url} - {response_time:.2f}s")
                        else:
                            state["results"] = ("failed", response_time, https_status, cert_valid)
                            logger.warning(f"HTTP test failed with status {response.status_code}: {http_url}")
                    except:
                        state["results"] = ("failed", 0, https_status, cert_valid)
                        logger.error(f"HTTP test completely failed: {test_url}")
                        
            except Exception as e:
                logger.error(f"HTTP test error: {e}")
                state["results"] = ("failed", 0, "unknown", False)
            
            finally:
                state["running"] = False
                # Update UI in main thread
                btn.after(0, update_label)
                
                # Schedule auto-clear after 60 seconds
                if state["clear_job"]:
                    btn.after_cancel(state["clear_job"])
                state["clear_job"] = btn.after(60000, clear_results)
        
        def start_http_test():
            """Start a new HTTP test."""
            if state["running"]:
                return
            
            # Cancel any existing clear job
            if state["clear_job"]:
                btn.after_cancel(state["clear_job"])
                state["clear_job"] = None
            
            state["running"] = True
            state["results"] = None
            update_label()
            
            # Run HTTP test in separate thread
            thread = threading.Thread(target=run_http_test, daemon=True)
            thread.start()
        
        def on_http_test_click(event):
            """Handle HTTP test button click."""
            logger.debug(f"HTTP test button clicked: {cfg.get('label', 'HTTP Test')}")
            
            # Start HTTP test
            start_http_test()
            
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
                    logger.warning(f"HTTP test animation failed: {e}")
        
        btn.bind("<Button-1>", on_http_test_click)
        btn.bind("<Button-3>", lambda e, i=cfg: self.app.edit_button(i))
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.app.theme["button_hover"]), add="+")
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b.orig_bg), add="+")
        btn.image = None
        
        return btn 