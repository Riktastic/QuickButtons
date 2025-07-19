"""Tests for configuration management."""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.managers.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config_creation(self):
        """Test that default config is created when no config file exists."""
        with patch('core.managers.config_manager.CONFIG_FILE', self.config_path):
            config_manager = ConfigManager()
            
            # Check that default values are present
            self.assertIn('buttons', config_manager.config_data)
            self.assertIn('button_size', config_manager.config_data)
            self.assertIn('theme', config_manager.config_data)
            self.assertIn('language', config_manager.config_data)
            self.assertIn('minimal_mode', config_manager.config_data)
            self.assertIn('translucency', config_manager.config_data)
            self.assertIn('default_animation_type', config_manager.config_data)
    
    def test_config_loading(self):
        """Test loading existing config file."""
        test_config = {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': True,
            'translucency': 0.8,
            'default_animation_type': 'fade'
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        with patch('core.managers.config_manager.CONFIG_FILE', self.config_path):
            config_manager = ConfigManager()
            
            self.assertEqual(config_manager.config_data['button_size'], 80)
            self.assertEqual(config_manager.config_data['theme'], 'dark')
            self.assertEqual(config_manager.config_data['minimal_mode'], True)
            self.assertEqual(config_manager.config_data['translucency'], 0.8)
    
    def test_config_saving(self):
        """Test saving config to file."""
        with patch('core.managers.config_manager.CONFIG_FILE', self.config_path):
            config_manager = ConfigManager()
            
            # Modify config
            config_manager.config_data['button_size'] = 100
            config_manager.config_data['theme'] = 'light'
            
            # Save config
            config_manager.save_config()
            
            # Verify file was created and contains correct data
            self.assertTrue(os.path.exists(self.config_path))
            
            with open(self.config_path, 'r') as f:
                saved_config = json.load(f)
            
            self.assertEqual(saved_config['button_size'], 100)
            self.assertEqual(saved_config['theme'], 'light')
    
    def test_config_validation(self):
        """Test config validation and default value application."""
        invalid_config = {
            'button_size': 'invalid',  # Should be int
            'translucency': 2.0,       # Should be 0.0-1.0
            'theme': 'invalid_theme'   # Should be valid theme
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        with patch('core.managers.config_manager.CONFIG_FILE', self.config_path):
            config_manager = ConfigManager()
            
            # Check that invalid values are replaced with defaults
            self.assertIsInstance(config_manager.config_data['button_size'], int)
            self.assertGreaterEqual(config_manager.config_data['translucency'], 0.0)
            self.assertLessEqual(config_manager.config_data['translucency'], 1.0)
            self.assertIn(config_manager.config_data['theme'], ['light', 'dark'])
    
    def test_config_backup_creation(self):
        """Test that backup is created when saving config."""
        with patch('core.managers.config_manager.CONFIG_FILE', self.config_path):
            config_manager = ConfigManager()
            
            # Save config multiple times
            config_manager.save_config()
            config_manager.save_config()
            
            # Check that backup file exists
            backup_path = self.config_path + '.backup'
            self.assertTrue(os.path.exists(backup_path))
    
    def test_config_reload(self):
        """Test reloading config from file."""
        initial_config = {'button_size': 80, 'theme': 'dark'}
        with open(self.config_path, 'w') as f:
            json.dump(initial_config, f)
        
        with patch('core.managers.config_manager.CONFIG_FILE', self.config_path):
            config_manager = ConfigManager()
            
            # Modify config in memory
            config_manager.config_data['button_size'] = 100
            
            # Reload from file
            config_manager.reload_config()
            
            # Should be back to original values
            self.assertEqual(config_manager.config_data['button_size'], 80)
            self.assertEqual(config_manager.config_data['theme'], 'dark')


if __name__ == '__main__':
    unittest.main() 