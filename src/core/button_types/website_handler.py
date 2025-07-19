"""Website button type handler."""

import tkinter.messagebox as messagebox
from src.utils.logger import logger


class WebsiteHandler:
    """Handles execution of website buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def _ensure_web_opener_loaded(self):
        """Ensure web opener is loaded when needed."""
        if not hasattr(self.app, 'web_opener') or self.app.web_opener is None:
            from src.actions.web_opener import WebOpener
            self.app.web_opener = WebOpener()
    
    def execute(self, cfg):
        """Execute a website button."""
        url = cfg.get("url")
        if not url:
            messagebox.showerror("No URL", self.app._("No website URL configured."))
            return
        
        try:
            self._ensure_web_opener_loaded()
            self.app.web_opener.open_url(url)
            logger.info(f"Opened website: {url}")
        except Exception as e:
            logger.error(f"Failed to open website {url}: {e}")
            messagebox.showerror(self.app._("Error"), f"Failed to open website: {e}") 