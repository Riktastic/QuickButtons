"""Application launcher button type handler."""

import os
import sys
import subprocess
import tkinter.messagebox as messagebox
from src.utils.logger import logger


class AppLauncherHandler:
    """Handles execution of application launcher buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute an application launcher button."""
        app_path = cfg.get("app_path")
        if not app_path:
            messagebox.showwarning(self.app._("No Application Path"), 
                                 self.app._("No application path configured."))
            return
        
        # Check if application exists
        if not os.path.isfile(app_path) and not os.path.isdir(app_path):
            messagebox.showwarning(self.app._("Application not found"), 
                                 self.app._("The application could not be found: ") + str(app_path))
            return
        
        args = self._expand_args(cfg.get("args", ""))
        background = cfg.get("background", False)
        label = cfg.get("label", "")
        
        try:
            if background:
                # Run in background/minimized
                if sys.platform.startswith("win"):
                    # Windows: minimize window
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = 6  # SW_MINIMIZE
                    subprocess.Popen([app_path] + args, startupinfo=si, 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # Linux/Mac: run detached
                    subprocess.Popen([app_path] + args, start_new_session=True)
                messagebox.showinfo(self.app._("Launch Application"), 
                                  self.app._("Application started in background."))
            else:
                # Run normally
                subprocess.Popen([app_path] + args)
                logger.info(f"Launched application: {app_path}")
                
        except Exception as e:
            logger.error(f"Failed to launch application {app_path}: {e}")
            messagebox.showerror(self.app._("Launch Error"), 
                               f"Failed to launch application: {e}")
    
    def _expand_args(self, argstr):
        """Expand wildcards in arguments."""
        from datetime import datetime
        import re
        
        now = datetime.now()
        argstr = argstr.replace("{date}", now.strftime("%Y-%m-%d"))
        argstr = argstr.replace("{time}", now.strftime("%H:%M:%S"))
        argstr = argstr.replace("{datetime}", now.strftime("%Y-%m-%d_%H-%M-%S"))
        
        # Custom wildcards
        custom_fields = re.findall(r"\{custom:([^}]+)\}", argstr)
        if custom_fields:
            # Only ask once per unique field
            unique_fields = list(dict.fromkeys(custom_fields))
            values = self._prompt_custom_wildcards(unique_fields)
            if values is None:
                return []  # User cancelled
            for field, value in values.items():
                argstr = argstr.replace(f"{{custom:{field}}}", value)
        return argstr.split()
    
    def _prompt_custom_wildcards(self, fields):
        """Show a modal dialog to prompt for all custom wildcard values."""
        import tkinter as tk
        
        dialog = tk.Toplevel(self.app)
        dialog.title(self.app._("Enter values"))
        dialog.grab_set()
        dialog.transient(self.app)
        dialog.resizable(False, False)
        
        # Set window icon
        try:
            from src.core.constants import ICON_ICO_PATH
            dialog.iconbitmap(ICON_ICO_PATH)
        except Exception as e:
            logger.warning(f"Could not set dialog icon: {e}")
        
        tk.Label(dialog, text=self.app._("Please fill in the required values:"), 
                font=("Segoe UI", 11, "bold")).pack(padx=16, pady=(14,6))
        
        entries = {}
        for field in fields:
            frame = tk.Frame(dialog)
            frame.pack(fill=tk.X, padx=16, pady=2)
            tk.Label(frame, text=f"{field}:", width=15, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=30)
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            entries[field] = entry
        
        result = {}
        def on_ok():
            nonlocal result
            result = {field: entry.get() for field, entry in entries.items()}
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=(10,14))
        tk.Button(button_frame, text=self.app._("OK"), command=on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text=self.app._("Cancel"), command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        return result if result else None 