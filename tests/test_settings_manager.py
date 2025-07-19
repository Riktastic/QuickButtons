"""Tests for settings management."""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import tkinter as tk

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.managers.settings_manager import SettingsManager


class TestSettingsManager(unittest.TestCase):
    """Test cases for SettingsManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
        
        # Create mock app
        self.mock_app = MagicMock()
        self.mock_app.config_data = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'WARNING'
        }
        self.mock_app.theme = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'button_bg': '#3c3f41',
            'button_fg': '#ffffff',
            'button_active_bg': '#4c5052'
        }
        self.mock_app._ = lambda x: x  # Mock translation
        
        # Create root window for testing
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        self.settings_manager = SettingsManager(self.mock_app)
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        self.root.destroy()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_settings_manager_initialization(self):
        """Test SettingsManager initialization."""
        self.assertEqual(self.settings_manager.app, self.mock_app)
        self.assertIsNone(self.settings_manager.settings_dialog)
        self.assertIsNone(self.settings_manager.about_dialog)
    
    def test_open_settings_dialog(self):
        """Test opening settings dialog."""
        with patch('core.managers.settings_manager.SettingsDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog_class.return_value = mock_dialog
            
            self.settings_manager.open_settings()
            
            # Check that dialog was created and shown
            mock_dialog_class.assert_called_once_with(self.mock_app)
            mock_dialog.show.assert_called_once()
    
    def test_open_settings_dialog_already_open(self):
        """Test opening settings dialog when already open."""
        # Create a mock dialog
        mock_dialog = MagicMock()
        self.settings_manager.settings_dialog = mock_dialog
        
        self.settings_manager.open_settings()
        
        # Should focus existing dialog instead of creating new one
        mock_dialog.focus_force.assert_called_once()
    
    def test_open_about_dialog(self):
        """Test opening about dialog."""
        with patch('core.managers.settings_manager.AboutDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog_class.return_value = mock_dialog
            
            self.settings_manager.open_about()
            
            # Check that dialog was created and shown
            mock_dialog_class.assert_called_once_with(self.mock_app)
            mock_dialog.show.assert_called_once()
    
    def test_open_about_dialog_already_open(self):
        """Test opening about dialog when already open."""
        # Create a mock dialog
        mock_dialog = MagicMock()
        self.settings_manager.about_dialog = mock_dialog
        
        self.settings_manager.open_about()
        
        # Should focus existing dialog instead of creating new one
        mock_dialog.focus_force.assert_called_once()
    
    def test_save_settings(self):
        """Test saving settings."""
        new_settings = {
            'button_size': 100,
            'theme': 'light',
            'language': 'es',
            'minimal_mode': True,
            'translucency': 0.8,
            'default_animation_type': 'slide',
            'log_level': 'INFO'
        }
        
        with patch.object(self.mock_app, 'save_config') as mock_save:
            self.settings_manager.save_settings(new_settings)
            
            # Check that config was updated
            self.assertEqual(self.mock_app.config_data['button_size'], 100)
            self.assertEqual(self.mock_app.config_data['theme'], 'light')
            self.assertEqual(self.mock_app.config_data['language'], 'es')
            self.assertEqual(self.mock_app.config_data['minimal_mode'], True)
            self.assertEqual(self.mock_app.config_data['translucency'], 0.8)
            self.assertEqual(self.mock_app.config_data['default_animation_type'], 'slide')
            self.assertEqual(self.mock_app.config_data['log_level'], 'INFO')
            
            # Check that config was saved
            mock_save.assert_called_once()
    
    def test_apply_settings(self):
        """Test applying settings."""
        # Mock the button manager and window manager
        mock_button_manager = MagicMock()
        self.mock_app.button_manager = mock_button_manager
        
        with patch.object(self.mock_app, 'attributes') as mock_attributes:
            self.settings_manager.apply_settings()
            
            # Check that button grid was refreshed
            mock_button_manager.refresh_grid.assert_called_once()
            
            # Check that translucency was applied
            mock_attributes.assert_called_once_with('-alpha', 1.0)
    
    def test_update_theme(self):
        """Test updating theme."""
        # Mock theme loading
        mock_themes = {
            'light': {'bg': '#ffffff', 'fg': '#000000'},
            'dark': {'bg': '#2b2b2b', 'fg': '#ffffff'}
        }
        
        with patch('core.managers.settings_manager.load_themes', return_value=mock_themes):
            self.settings_manager.update_theme()
            
            # Check that theme was updated
            self.assertEqual(self.mock_app.theme, mock_themes['dark'])
            self.assertEqual(self.mock_app.theme_name, 'dark')
    
    def test_validate_settings(self):
        """Test settings validation."""
        # Test valid settings
        valid_settings = {
            'button_size': 80,
            'translucency': 0.8,
            'theme': 'dark',
            'language': 'en'
        }
        
        result = self.settings_manager.validate_settings(valid_settings)
        self.assertTrue(result)
        
        # Test invalid button size
        invalid_size_settings = valid_settings.copy()
        invalid_size_settings['button_size'] = -10
        
        result = self.settings_manager.validate_settings(invalid_size_settings)
        self.assertFalse(result)
        
        # Test invalid translucency
        invalid_alpha_settings = valid_settings.copy()
        invalid_alpha_settings['translucency'] = 2.0
        
        result = self.settings_manager.validate_settings(invalid_alpha_settings)
        self.assertFalse(result)
        
        # Test invalid theme
        invalid_theme_settings = valid_settings.copy()
        invalid_theme_settings['theme'] = 'invalid_theme'
        
        result = self.settings_manager.validate_settings(invalid_theme_settings)
        self.assertFalse(result)
    
    def test_get_default_settings(self):
        """Test getting default settings."""
        defaults = self.settings_manager.get_default_settings()
        
        self.assertIn('button_size', defaults)
        self.assertIn('theme', defaults)
        self.assertIn('language', defaults)
        self.assertIn('minimal_mode', defaults)
        self.assertIn('translucency', defaults)
        self.assertIn('default_animation_type', defaults)
        self.assertIn('log_level', defaults)
    
    def test_apply_language_change(self):
        """Test applying language change."""
        with patch.object(self.mock_app, 'update_topbar_tooltips') as mock_update:
            self.settings_manager.apply_language_change('es')
            
            # Check that language was updated
            self.assertEqual(self.mock_app.config_data['language'], 'es')
            
            # Check that translation manager was updated
            self.mock_app.translation_manager.set_language.assert_called_once_with('es')
            
            # Check that tooltips were updated
            mock_update.assert_called_once()
    
    def test_apply_minimal_mode_change(self):
        """Test applying minimal mode change."""
        with patch.object(self.mock_app, 'apply_minimal_mode') as mock_apply:
            self.settings_manager.apply_minimal_mode_change(True)
            
            # Check that minimal mode was updated
            self.assertEqual(self.mock_app.config_data['minimal_mode'], True)
            
            # Check that minimal mode was applied
            mock_apply.assert_called_once()
    
    def test_cleanup_dialogs(self):
        """Test cleaning up dialogs."""
        # Create mock dialogs
        mock_settings_dialog = MagicMock()
        mock_about_dialog = MagicMock()
        self.settings_manager.settings_dialog = mock_settings_dialog
        self.settings_manager.about_dialog = mock_about_dialog
        
        self.settings_manager.cleanup_dialogs()
        
        # Check that dialogs were destroyed
        mock_settings_dialog.destroy.assert_called_once()
        mock_about_dialog.destroy.assert_called_once()
        
        # Check that references were cleared
        self.assertIsNone(self.settings_manager.settings_dialog)
        self.assertIsNone(self.settings_manager.about_dialog)


if __name__ == '__main__':
    unittest.main() 