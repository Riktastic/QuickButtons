"""Python script button type handler."""

import os
import sys
import subprocess
import tkinter.messagebox as messagebox
from src.utils.system import get_python_executable
from src.ui.dialogs import OutputOverlay
from src.utils.logger import logger


class PythonScriptHandler:
    """Handles execution of Python script buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute a Python script button."""
        script = cfg.get("script")
        if not script or not os.path.isfile(script):
            messagebox.showwarning(self.app._("Script not found"), 
                                 self.app._("The script file could not be found: ") + str(script))
            return
        
        # Check if Python executable is configured
        python_executable = self.app.config_manager.get("python_executable", "")
        if not python_executable:
            result = messagebox.askyesno(
                self.app._("Python Executable Required"),
                self.app._("No Python executable is configured. Would you like to configure it now?")
            )
            if result:
                self.app.open_settings()
            return
        
        args = self._expand_args(cfg.get("args", ""))
        ext = os.path.splitext(script)[1].lower()
        label = cfg.get("label", "")
        background = cfg.get("background", False)
        
        if ext == ".py" and background:
            # Run in background/minimized
            python_exe = get_python_executable(self.app.config_manager)
            if not python_exe:
                messagebox.showerror(self.app._("Error"), 
                                   self.app._("No Python executable found. Please configure Python in settings."))
                return
            
            if sys.platform.startswith("win"):
                # Windows: minimize window
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 6  # SW_MINIMIZE
                subprocess.Popen([python_exe, script] + args, startupinfo=si, 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # Linux/Mac: run detached
                subprocess.Popen([python_exe, script] + args, start_new_session=True)
            messagebox.showinfo(self.app._("Run Script"), self.app._("Script started in background."))
            return
        
        if ext == ".py":
            OutputOverlay(self.app, script, args, btn_label=label, config=self.app.config_manager)
        elif ext == ".sh":
            try:
                result = subprocess.run(["bash", script] + args, capture_output=True, text=True)
                messagebox.showinfo(self.app._("Shell Output"), result.stdout[:1000] or self.app._("(No output)"))
            except Exception as e:
                messagebox.showerror(self.app._("Shell Error"), str(e))
        elif ext in [".bat", ".cmd"]:
            try:
                result = subprocess.run(["cmd.exe", "/c", script] + args, capture_output=True, text=True)
                messagebox.showinfo(self.app._("Shell Output"), result.stdout[:1000] or self.app._("(No output)"))
            except Exception as e:
                messagebox.showerror(self.app._("Shell Error"), str(e))
        else:
            # Try to execute directly
            try:
                result = subprocess.run([script] + args, capture_output=True, text=True)
                messagebox.showinfo(self.app._("Shell Output"), result.stdout[:1000] or self.app._("(No output)"))
            except Exception as e:
                messagebox.showerror(self.app._("Shell Error"), str(e))
    
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
            from src.utils.logger import logger
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