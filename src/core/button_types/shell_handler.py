"""Shell command button type handler."""

import subprocess
import tkinter.messagebox as messagebox
from src.utils.logger import logger


class ShellHandler:
    """Handles execution of shell command buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute a shell command button."""
        cmd = cfg.get("shell_cmd", "")
        if not cmd:
            messagebox.showerror(self.app._("No Command"), self.app._("No shell command configured."))
            return
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            messagebox.showinfo(self.app._("Shell Output"), result.stdout[:1000] or self.app._("(No output)"))
            logger.info(f"Shell command executed: {cmd}")
        except Exception as e:
            logger.error(f"Shell command failed {cmd}: {e}")
            messagebox.showerror(self.app._("Shell Error"), str(e)) 