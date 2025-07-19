"""Web opener action handler."""

import webbrowser
import subprocess
import sys
from src.utils.logger import logger

class WebOpener:
    """Handles opening websites and URLs."""
    
    @staticmethod
    def open_url(url):
        """Open a URL in the default web browser."""
        try:
            if not url:
                logger.warning("No URL provided")
                return False
            
            # Ensure URL has a protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            return False
    
    @staticmethod
    def open_file(file_path):
        """Open a file with the default system application."""
        try:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', file_path])
            elif sys.platform.startswith('win'):  # Windows
                subprocess.run(['start', file_path], shell=True)
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
            
            logger.info(f"Opened file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open file {file_path}: {e}")
            return False 