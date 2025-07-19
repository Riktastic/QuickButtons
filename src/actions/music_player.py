"""Music player action handler."""

# Defer pygame import to avoid startup delay
pygame = None

from tkinter import messagebox
from src.utils.logger import logger

class MusicPlayer:
    """Handles music playback functionality."""
    
    def __init__(self):
        self.current_music_path = None
        self.current_music_btn = None
        self._music_glow_job = None
        self._music_glow_state = False
        self._pygame_initialized = False
    
    def _ensure_pygame_loaded(self):
        """Ensure pygame is loaded when needed."""
        global pygame
        if pygame is None:
            try:
                import pygame
                self._pygame_initialized = True
            except ImportError:
                logger.error("Pygame not available for music playback")
                return False
        return True
    
    def play_music(self, path, button=None):
        """Play a music file using pygame."""
        if not self._ensure_pygame_loaded():
            messagebox.showerror("Music Error", "Pygame not available for music playback")
            return
            
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.current_music_path = path
            self.current_music_btn = button
            if button:
                self._start_music_glow(button)
            logger.info(f"Playing music: {path}")
        except Exception as e:
            logger.error(f"Could not play music {path}: {e}")
            messagebox.showerror("Music Error", f"Could not play music: {e}")
    
    def stop_music(self):
        """Stop music playback."""
        if not self._ensure_pygame_loaded():
            return
            
        try:
            pygame.mixer.music.stop()
            if self.current_music_btn and self._music_glow_job:
                self._stop_music_glow()
            self.current_music_path = None
            self.current_music_btn = None
            logger.info("Music stopped")
        except Exception as e:
            logger.error(f"Error stopping music: {e}")
    
    def is_playing(self):
        """Check if music is currently playing."""
        if not self._ensure_pygame_loaded():
            return False
            
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False
    
    def _start_music_glow(self, button):
        """Start the visual glow effect for the music button."""
        if not button:
            return
        self._stop_music_glow()  # Stop any existing glow
        self._music_glow_button = button
        self._music_glow_state = False
        self._music_glow()
    
    def _stop_music_glow(self):
        """Stop the visual glow effect."""
        if self._music_glow_job:
            try:
                self._music_glow_button.after_cancel(self._music_glow_job)
            except Exception:
                pass
            self._music_glow_job = None
        if hasattr(self, '_music_glow_button') and self._music_glow_button:
            try:
                self._music_glow_button.config(bg=self._music_glow_button.orig_bg)
            except Exception:
                pass
    
    def _music_glow(self):
        """Animate the glow effect for the music button."""
        if not hasattr(self, '_music_glow_button') or not self._music_glow_button:
            return
        
        try:
            if not self.is_playing():
                self._stop_music_glow()
                return
            
            # Toggle between original color and glow color
            if self._music_glow_state:
                self._music_glow_button.config(bg=self._music_glow_button.orig_bg)
            else:
                self._music_glow_button.config(bg="#4CAF50")  # Green glow
            
            self._music_glow_state = not self._music_glow_state
            self._music_glow_job = self._music_glow_button.after(500, self._music_glow)
        except Exception as e:
            logger.error(f"Error in music glow effect: {e}")
            self._stop_music_glow() 