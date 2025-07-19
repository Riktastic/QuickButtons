"""Music button type handler."""

import os
import tkinter.messagebox as messagebox
from src.utils.logger import logger


class MusicHandler:
    """Handles execution of music buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def _ensure_music_player_loaded(self):
        """Ensure music player is loaded when needed."""
        if not hasattr(self.app, 'music_player') or self.app.music_player is None:
            from src.actions.music_player import MusicPlayer
            self.app.music_player = MusicPlayer()
    
    def execute(self, cfg):
        """Execute a music button."""
        music = cfg.get("music")
        if not music or not os.path.isfile(music):
            messagebox.showerror("Music not found", self.app._("No music file configured or file missing."))
            return
        
        try:
            self._ensure_music_player_loaded()
            self.app.music_player.play_music(music)
            logger.info(f"Playing music: {music}")
        except Exception as e:
            logger.error(f"Failed to play music {music}: {e}")
            messagebox.showerror(self.app._("Error"), f"Failed to play music: {e}") 