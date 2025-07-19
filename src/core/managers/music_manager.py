"""Music management functionality for QuickButtons."""

import pygame
import threading
import time
from src.utils.logger import logger


class MusicManager:
    """Handles music playback and visual effects."""
    
    def __init__(self, app):
        self.app = app
        self._music_glow_job = None
        self._music_glow_state = False
    
    def _start_music_glow(self, btn):
        """Start music glow effect on button."""
        if self._music_glow_job:
            self.app.after_cancel(self._music_glow_job)
        
        self._music_glow_state = True
        self._music_glow_job = self.app.after(500, lambda: self._music_glow_cycle(btn))
        logger.debug("Music glow started")
    
    def _stop_music_glow(self):
        """Stop music glow effect."""
        if self._music_glow_job:
            self.app.after_cancel(self._music_glow_job)
            self._music_glow_job = None
        self._music_glow_state = False
        logger.debug("Music glow stopped")
    
    def _music_glow_cycle(self, btn):
        """Cycle through music glow colors."""
        if not self._music_glow_state or not btn.winfo_exists():
            return
        
        try:
            # Get current background color
            current_bg = btn.cget("bg")
            
            # Cycle through glow colors
            if current_bg == self.app.theme["button_bg"]:
                btn.config(bg="#ff6b6b")  # Red glow
            elif current_bg == "#ff6b6b":
                btn.config(bg="#4ecdc4")  # Cyan glow
            elif current_bg == "#4ecdc4":
                btn.config(bg="#45b7d1")  # Blue glow
            elif current_bg == "#45b7d1":
                btn.config(bg="#96ceb4")  # Green glow
            elif current_bg == "#96ceb4":
                btn.config(bg="#feca57")  # Yellow glow
            elif current_bg == "#feca57":
                btn.config(bg="#ff9ff3")  # Pink glow
            else:
                btn.config(bg=self.app.theme["button_bg"])  # Back to normal
            
            # Schedule next cycle
            self._music_glow_job = self.app.after(500, lambda: self._music_glow_cycle(btn))
            
        except Exception as e:
            logger.warning(f"Music glow cycle failed: {e}")
            self._stop_music_glow()
    
    def update_music_state(self, music_path, button):
        """Update music state when music starts/stops."""
        self.app.current_music_path = music_path
        self.app.current_music_btn = button
        
        if music_path and button:
            self._start_music_glow(button)
        else:
            self._stop_music_glow()
            self.app.current_music_path = None
            self.app.current_music_btn = None
    
    def check_music_status(self):
        """Check if music is still playing and update state accordingly."""
        if self.app.current_music_path and self.app.current_music_btn:
            try:
                if not pygame.mixer.music.get_busy():
                    # Music stopped, reset state
                    self.update_music_state(None, None)
            except Exception as e:
                logger.warning(f"Could not check music status: {e}")
                # Reset state on error
                self.update_music_state(None, None) 