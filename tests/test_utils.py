"""Tests for utility functions."""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import tkinter as tk

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.logger import logger, update_log_level
from utils.translations import translation_manager
from utils.system import detect_system_theme
from utils.animations import fade_in, fade_out, slide_in, slide_out


class TestLogger(unittest.TestCase):
    """Test cases for logging functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset logger to default state
        update_log_level('WARNING')
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'QuickButtons')
    
    def test_update_log_level(self):
        """Test updating log level."""
        # Test different log levels
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        
        for level in levels:
            update_log_level(level)
            self.assertEqual(logger.level, getattr(logger, level))
    
    def test_update_log_level_invalid(self):
        """Test updating log level with invalid value."""
        # Should default to WARNING for invalid levels
        update_log_level('INVALID_LEVEL')
        self.assertEqual(logger.level, logger.WARNING)
    
    def test_logger_output(self):
        """Test logger output."""
        with patch('builtins.print') as mock_print:
            logger.info("Test message")
            mock_print.assert_called()
    
    def test_logger_with_different_levels(self):
        """Test logger with different levels."""
        with patch('builtins.print') as mock_print:
            # Set to INFO level
            update_log_level('INFO')
            
            logger.debug("Debug message")  # Should not print
            logger.info("Info message")    # Should print
            logger.warning("Warning message")  # Should print
            
            # Should have 2 calls (info and warning)
            self.assertEqual(mock_print.call_count, 2)


class TestTranslations(unittest.TestCase):
    """Test cases for translation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset translation manager to default state
        translation_manager.set_language('en')
    
    def test_translation_manager_initialization(self):
        """Test translation manager initialization."""
        self.assertIsNotNone(translation_manager)
        self.assertEqual(translation_manager.current_language, 'en')
    
    def test_set_language(self):
        """Test setting language."""
        translation_manager.set_language('es')
        self.assertEqual(translation_manager.current_language, 'es')
        
        translation_manager.set_language('en')
        self.assertEqual(translation_manager.current_language, 'en')
    
    def test_get_text_english(self):
        """Test getting text in English."""
        translation_manager.set_language('en')
        
        # Test some common translations
        self.assertEqual(translation_manager.get_text('Settings'), 'Settings')
        self.assertEqual(translation_manager.get_text('About'), 'About')
        self.assertEqual(translation_manager.get_text('Add Button'), 'Add Button')
    
    def test_get_text_spanish(self):
        """Test getting text in Spanish."""
        translation_manager.set_language('es')
        
        # Test some Spanish translations
        self.assertEqual(translation_manager.get_text('Settings'), 'Configuración')
        self.assertEqual(translation_manager.get_text('About'), 'Acerca de')
        self.assertEqual(translation_manager.get_text('Add Button'), 'Agregar Botón')
    
    def test_get_text_fallback(self):
        """Test getting text with fallback to English."""
        translation_manager.set_language('es')
        
        # Test unknown text should fallback to English
        unknown_text = "Unknown Text That Doesn't Exist"
        result = translation_manager.get_text(unknown_text)
        self.assertEqual(result, unknown_text)
    
    def test_get_text_with_parameters(self):
        """Test getting text with parameters."""
        translation_manager.set_language('en')
        
        # Test text with parameters (if supported)
        result = translation_manager.get_text('Button {number}', number=1)
        self.assertIn('1', result)
    
    def test_available_languages(self):
        """Test getting available languages."""
        languages = translation_manager.get_available_languages()
        
        self.assertIn('en', languages)
        self.assertIn('es', languages)
        self.assertIsInstance(languages, list)


class TestSystemDetection(unittest.TestCase):
    """Test cases for system detection functionality."""
    
    def test_detect_system_theme_windows(self):
        """Test system theme detection on Windows."""
        with patch('sys.platform', 'win32'):
            with patch('utils.system.ctypes.windll.dwmapi.DwmGetColorizationColor') as mock_dwm:
                mock_dwm.return_value = (0, 0x00FFFFFF)  # Light theme
                theme = detect_system_theme()
                self.assertIn(theme, ['light', 'dark'])
    
    def test_detect_system_theme_linux(self):
        """Test system theme detection on Linux."""
        with patch('sys.platform', 'linux'):
            with patch('os.environ', {'GTK_THEME': 'Adwaita:light'}):
                theme = detect_system_theme()
                self.assertIn(theme, ['light', 'dark'])
    
    def test_detect_system_theme_macos(self):
        """Test system theme detection on macOS."""
        with patch('sys.platform', 'darwin'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = b'Light\n'
                theme = detect_system_theme()
                self.assertIn(theme, ['light', 'dark'])
    
    def test_detect_system_theme_fallback(self):
        """Test system theme detection fallback."""
        with patch('sys.platform', 'unknown'):
            theme = detect_system_theme()
            self.assertIn(theme, ['light', 'dark'])
    
    def test_detect_system_theme_error_handling(self):
        """Test system theme detection error handling."""
        with patch('sys.platform', 'win32'):
            with patch('utils.system.ctypes.windll.dwmapi.DwmGetColorizationColor', side_effect=Exception):
                theme = detect_system_theme()
                self.assertIn(theme, ['light', 'dark'])


class TestAnimations(unittest.TestCase):
    """Test cases for animation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        # Create a test widget
        self.widget = tk.Label(self.root, text="Test")
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_fade_in_animation(self):
        """Test fade in animation."""
        # Set initial alpha to 0
        self.widget.attributes = lambda **kwargs: None
        
        with patch.object(self.widget, 'attributes') as mock_attributes:
            fade_in(self.widget, duration=100)
            
            # Check that attributes were called to set alpha
            mock_attributes.assert_called()
    
    def test_fade_out_animation(self):
        """Test fade out animation."""
        with patch.object(self.widget, 'attributes') as mock_attributes:
            fade_out(self.widget, duration=100)
            
            # Check that attributes were called to set alpha
            mock_attributes.assert_called()
    
    def test_slide_in_animation(self):
        """Test slide in animation."""
        with patch.object(self.widget, 'place') as mock_place:
            slide_in(self.widget, direction='left', duration=100)
            
            # Check that place was called to position widget
            mock_place.assert_called()
    
    def test_slide_out_animation(self):
        """Test slide out animation."""
        with patch.object(self.widget, 'place') as mock_place:
            slide_out(self.widget, direction='right', duration=100)
            
            # Check that place was called to position widget
            mock_place.assert_called()
    
    def test_animation_cancellation(self):
        """Test animation cancellation."""
        with patch.object(self.widget, 'after_cancel') as mock_cancel:
            # Start an animation
            job = fade_in(self.widget, duration=1000)
            
            # Cancel it
            if job:
                self.widget.after_cancel(job)
            
            # Check that cancellation was attempted
            if job:
                mock_cancel.assert_called_once_with(job)
    
    def test_animation_with_invalid_duration(self):
        """Test animation with invalid duration."""
        # Should handle zero or negative duration gracefully
        job = fade_in(self.widget, duration=0)
        self.assertIsNone(job)
        
        job = fade_in(self.widget, duration=-100)
        self.assertIsNone(job)
    
    def test_animation_with_invalid_direction(self):
        """Test slide animation with invalid direction."""
        with patch.object(self.widget, 'place') as mock_place:
            # Should default to 'left' for invalid directions
            slide_in(self.widget, direction='invalid', duration=100)
            
            # Should still call place
            mock_place.assert_called()


class TestEasterEgg(unittest.TestCase):
    """Test cases for easter egg functionality."""
    
    def test_easter_egg_sequence(self):
        """Test easter egg sequence detection."""
        from utils.easter_egg import EasterEggDetector
        
        detector = EasterEggDetector()
        
        # Test sequence detection
        self.assertFalse(detector.check_sequence('a'))
        self.assertFalse(detector.check_sequence('ab'))
        self.assertFalse(detector.check_sequence('abc'))
        self.assertFalse(detector.check_sequence('abcd'))
        
        # Test complete sequence
        result = detector.check_sequence('Konami')
        self.assertTrue(result)
    
    def test_easter_egg_reset(self):
        """Test easter egg sequence reset."""
        from utils.easter_egg import EasterEggDetector
        
        detector = EasterEggDetector()
        
        # Add some characters
        detector.check_sequence('a')
        detector.check_sequence('b')
        
        # Reset
        detector.reset()
        
        # Should start fresh
        self.assertEqual(detector.sequence, '')
    
    def test_easter_egg_timeout(self):
        """Test easter egg sequence timeout."""
        from utils.easter_egg import EasterEggDetector
        import time
        
        detector = EasterEggDetector()
        
        # Add characters with delay
        detector.check_sequence('K')
        time.sleep(0.1)  # Small delay
        detector.check_sequence('o')
        
        # Should still be valid
        self.assertIn('o', detector.sequence)


if __name__ == '__main__':
    unittest.main() 