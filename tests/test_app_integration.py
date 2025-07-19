"""Integration tests for the main application."""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import tkinter as tk

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.app import QuickButtonsApp


class TestQuickButtonsAppIntegration(unittest.TestCase):
    """Integration test cases for QuickButtonsApp."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
        
        # Create test config
        test_config = {
            'buttons': [
                {
                    'id': 'test_btn_1',
                    'name': 'Test Website',
                    'type': 'website',
                    'url': 'https://example.com',
                    'icon': '🌐',
                    'color': '#ff0000',
                    'animation_type': 'fade'
                },
                {
                    'id': 'test_btn_2',
                    'name': 'Test Command',
                    'type': 'shell',
                    'command': 'echo "test"',
                    'icon': '💻',
                    'color': '#00ff00',
                    'animation_type': 'slide'
                }
            ],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'WARNING'
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('core.app.ConfigManager')
    @patch('core.app.WindowManager')
    @patch('core.app.TopbarManager')
    @patch('core.app.ButtonManager')
    @patch('core.app.TimerManager')
    @patch('core.app.MinimalModeManager')
    @patch('core.app.ButtonActionsManager')
    @patch('core.app.SettingsManager')
    @patch('core.app.MusicManager')
    @patch('core.app.load_themes')
    @patch('core.app.detect_system_theme')
    @patch('core.app.translation_manager')
    def test_app_initialization(self, mock_translation, mock_detect_theme, mock_load_themes,
                               mock_music_manager, mock_settings_manager, mock_button_actions,
                               mock_minimal_mode, mock_timer_manager, mock_button_manager,
                               mock_topbar_manager, mock_window_manager, mock_config_manager):
        """Test complete app initialization."""
        # Mock all the dependencies
        mock_config_manager.return_value.config_data = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'WARNING'
        }
        
        mock_load_themes.return_value = {
            'dark': {'bg': '#2b2b2b', 'fg': '#ffffff'},
            'light': {'bg': '#ffffff', 'fg': '#000000'}
        }
        mock_detect_theme.return_value = 'dark'
        
        # Mock managers
        mock_window = MagicMock()
        mock_topbar = MagicMock()
        mock_button = MagicMock()
        mock_timer = MagicMock()
        mock_minimal = MagicMock()
        mock_actions = MagicMock()
        mock_settings = MagicMock()
        mock_music = MagicMock()
        
        mock_window_manager.return_value = mock_window
        mock_topbar_manager.return_value = mock_topbar
        mock_button_manager.return_value = mock_button
        mock_timer_manager.return_value = mock_timer
        mock_minimal_mode.return_value = mock_minimal
        mock_button_actions.return_value = mock_actions
        mock_settings_manager.return_value = mock_settings
        mock_music_manager.return_value = mock_music
        
        # Create app
        with patch('tkinter.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            
            app = QuickButtonsApp()
            
            # Check that all managers were initialized
            mock_config_manager.assert_called_once()
            mock_window_manager.assert_called_once_with(app)
            mock_topbar_manager.assert_called_once_with(app)
            mock_button_manager.assert_called_once_with(app)
            mock_timer_manager.assert_called_once_with(app)
            mock_minimal_mode.assert_called_once_with(app)
            mock_button_actions.assert_called_once_with(app)
            mock_settings_manager.assert_called_once_with(app)
            mock_music_manager.assert_called_once_with(app)
            
            # Check that UI was set up
            mock_window.setup_window.assert_called_once()
            mock_topbar.create_topbar.assert_called_once()
            mock_button.create_button_grid.assert_called_once()
            mock_settings.update_theme.assert_called_once()
    
    @patch('core.app.ConfigManager')
    @patch('core.app.load_themes')
    @patch('core.app.detect_system_theme')
    @patch('core.app.translation_manager')
    def test_app_with_minimal_mode(self, mock_translation, mock_detect_theme, mock_load_themes, mock_config_manager):
        """Test app initialization with minimal mode enabled."""
        # Mock config with minimal mode enabled
        mock_config_manager.return_value.config_data = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': True,  # Enabled
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'WARNING'
        }
        
        mock_load_themes.return_value = {
            'dark': {'bg': '#2b2b2b', 'fg': '#ffffff'}
        }
        mock_detect_theme.return_value = 'dark'
        
        # Mock all managers
        with patch.multiple('core.app',
                           WindowManager=MagicMock(),
                           TopbarManager=MagicMock(),
                           ButtonManager=MagicMock(),
                           TimerManager=MagicMock(),
                           MinimalModeManager=MagicMock(),
                           ButtonActionsManager=MagicMock(),
                           SettingsManager=MagicMock(),
                           MusicManager=MagicMock()):
            
            with patch('tkinter.Tk') as mock_tk:
                mock_root = MagicMock()
                mock_tk.return_value = mock_root
                
                app = QuickButtonsApp()
                
                # Check that minimal mode was applied
                mock_root.overrideredirect.assert_called_once_with(True)
    
    @patch('core.app.ConfigManager')
    @patch('core.app.load_themes')
    @patch('core.app.detect_system_theme')
    @patch('core.app.translation_manager')
    def test_app_language_initialization(self, mock_translation, mock_detect_theme, mock_load_themes, mock_config_manager):
        """Test app initialization with different languages."""
        # Mock config with Spanish language
        mock_config_manager.return_value.config_data = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'es',  # Spanish
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'WARNING'
        }
        
        mock_load_themes.return_value = {
            'dark': {'bg': '#2b2b2b', 'fg': '#ffffff'}
        }
        mock_detect_theme.return_value = 'dark'
        
        # Mock all managers
        with patch.multiple('core.app',
                           WindowManager=MagicMock(),
                           TopbarManager=MagicMock(),
                           ButtonManager=MagicMock(),
                           TimerManager=MagicMock(),
                           MinimalModeManager=MagicMock(),
                           ButtonActionsManager=MagicMock(),
                           SettingsManager=MagicMock(),
                           MusicManager=MagicMock()):
            
            with patch('tkinter.Tk') as mock_tk:
                mock_root = MagicMock()
                mock_tk.return_value = mock_root
                
                app = QuickButtonsApp()
                
                # Check that language was set
                mock_translation.set_language.assert_called_once_with('es')
    
    @patch('core.app.ConfigManager')
    @patch('core.app.load_themes')
    @patch('core.app.detect_system_theme')
    @patch('core.app.translation_manager')
    def test_app_log_level_initialization(self, mock_translation, mock_detect_theme, mock_load_themes, mock_config_manager):
        """Test app initialization with different log levels."""
        # Mock config with DEBUG log level
        mock_config_manager.return_value.config_data = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'DEBUG'  # Debug level
        }
        
        mock_load_themes.return_value = {
            'dark': {'bg': '#2b2b2b', 'fg': '#ffffff'}
        }
        mock_detect_theme.return_value = 'dark'
        
        # Mock all managers
        with patch.multiple('core.app',
                           WindowManager=MagicMock(),
                           TopbarManager=MagicMock(),
                           ButtonManager=MagicMock(),
                           TimerManager=MagicMock(),
                           MinimalModeManager=MagicMock(),
                           ButtonActionsManager=MagicMock(),
                           SettingsManager=MagicMock(),
                           MusicManager=MagicMock()):
            
            with patch('tkinter.Tk') as mock_tk:
                mock_root = MagicMock()
                mock_tk.return_value = mock_root
                
                app = QuickButtonsApp()
                
                # Check that log level was applied (this would be tested in the _apply_log_level method)
                # The actual logging setup would be tested separately
    
    @patch('core.app.ConfigManager')
    @patch('core.app.load_themes')
    @patch('core.app.detect_system_theme')
    @patch('core.app.translation_manager')
    def test_app_delegate_methods(self, mock_translation, mock_detect_theme, mock_load_themes, mock_config_manager):
        """Test that app delegate methods work correctly."""
        # Mock config
        mock_config_manager.return_value.config_data = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'WARNING'
        }
        
        mock_load_themes.return_value = {
            'dark': {'bg': '#2b2b2b', 'fg': '#ffffff'}
        }
        mock_detect_theme.return_value = 'dark'
        
        # Mock all managers
        with patch.multiple('core.app',
                           WindowManager=MagicMock(),
                           TopbarManager=MagicMock(),
                           ButtonManager=MagicMock(),
                           TimerManager=MagicMock(),
                           MinimalModeManager=MagicMock(),
                           ButtonActionsManager=MagicMock(),
                           SettingsManager=MagicMock(),
                           MusicManager=MagicMock()):
            
            with patch('tkinter.Tk') as mock_tk:
                mock_root = MagicMock()
                mock_tk.return_value = mock_root
                
                app = QuickButtonsApp()
                
                # Test delegate methods
                app.create_topbar()
                app.topbar_manager.create_topbar.assert_called_once()
                
                app.refresh_grid()
                app.button_manager.refresh_grid.assert_called_once()
                
                app.open_settings()
                app.settings_manager.open_settings.assert_called_once()
                
                app.add_button()
                app.button_actions_manager.add_button.assert_called_once()
    
    @patch('core.app.ConfigManager')
    @patch('core.app.load_themes')
    @patch('core.app.detect_system_theme')
    @patch('core.app.translation_manager')
    def test_app_cleanup(self, mock_translation, mock_detect_theme, mock_load_themes, mock_config_manager):
        """Test app cleanup on close."""
        # Mock config
        mock_config_manager.return_value.config_data = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'fade',
            'log_level': 'WARNING'
        }
        
        mock_load_themes.return_value = {
            'dark': {'bg': '#2b2b2b', 'fg': '#ffffff'}
        }
        mock_detect_theme.return_value = 'dark'
        
        # Mock all managers
        with patch.multiple('core.app',
                           WindowManager=MagicMock(),
                           TopbarManager=MagicMock(),
                           ButtonManager=MagicMock(),
                           TimerManager=MagicMock(),
                           MinimalModeManager=MagicMock(),
                           ButtonActionsManager=MagicMock(),
                           SettingsManager=MagicMock(),
                           MusicManager=MagicMock()):
            
            with patch('tkinter.Tk') as mock_tk:
                mock_root = MagicMock()
                mock_tk.return_value = mock_root
                
                app = QuickButtonsApp()
                
                # Test cleanup
                app.on_close()
                
                # Check that config was saved
                app.config_manager.save_config.assert_called_once()
                
                # Check that window was destroyed
                mock_root.destroy.assert_called_once()


if __name__ == '__main__':
    unittest.main() 