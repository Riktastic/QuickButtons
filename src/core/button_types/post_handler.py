"""POST request button type handler."""

import tkinter.messagebox as messagebox
from src.utils.logger import logger


class PostHandler:
    """Handles execution of POST request buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def _ensure_requests_loaded(self):
        """Ensure requests module is loaded when needed."""
        try:
            import requests
            return requests
        except ImportError:
            messagebox.showerror("Import Error", "The 'requests' module is required for POST requests. Install with 'pip install requests'")
            return None
    
    def execute(self, cfg):
        """Execute a POST request button."""
        # Defer requests import until needed
        requests = self._ensure_requests_loaded()
        if not requests:
            return
        
        url = self._expand_wildcards(cfg.get("post_url", ""))
        headers = self._parse_headers(self._expand_wildcards(cfg.get("post_headers", "")))
        body = self._expand_wildcards(cfg.get("post_body", ""))
        
        if not url:
            messagebox.showerror(self.app._("No URL"), self.app._("No POST URL configured."))
            return
        
        try:
            resp = requests.post(url, headers=headers, data=body.encode("utf-8"))
            messagebox.showinfo(self.app._("POST Response"), 
                              f"{self.app._('Status')}: {resp.status_code}\n{resp.text[:1000]}")
            logger.info(f"POST request completed: {url} - Status: {resp.status_code}")
        except Exception as e:
            logger.error(f"POST request failed {url}: {e}")
            messagebox.showerror(self.app._("POST Error"), str(e))
    
    def _expand_wildcards(self, text):
        """Expand wildcards like {date}, {time}, {datetime}."""
        from datetime import datetime
        now = datetime.now()
        text = text.replace("{date}", now.strftime("%Y-%m-%d"))
        text = text.replace("{time}", now.strftime("%H:%M:%S"))
        text = text.replace("{datetime}", now.strftime("%Y-%m-%d_%H-%M-%S"))
        return text
    
    def _parse_headers(self, headers_str):
        """Parse headers string into dictionary."""
        headers = {}
        for line in headers_str.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip()] = v.strip()
        return headers 