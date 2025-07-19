"""Tests for button management."""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import tkinter as tk

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.managers.button_manager import ButtonManager


class TestButtonManager(unittest.TestCase):
    """Test cases for ButtonManager."""
    
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
            'default_animation_type': 'fade'
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
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        self.root.destroy()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_button_manager_initialization(self):
        """Test ButtonManager initialization."""
        button_manager = ButtonManager(self.mock_app)
        
        self.assertEqual(button_manager.app, self.mock_app)
        self.assertIsNotNone(button_manager.button_frame)
        self.assertIsNotNone(button_manager.canvas)
        self.assertIsNotNone(button_manager.scrollbar)
    
    def test_create_button_grid(self):
        """Test creating the button grid."""
        button_manager = ButtonManager(self.mock_app)
        
        # Mock the canvas and frame creation
        with patch.object(button_manager, 'create_scrollable_frame'):
            button_manager.create_button_grid()
            
            # Check that grid was created
            self.assertIsNotNone(button_manager.button_frame)
    
    def test_add_button_to_grid(self):
        """Test adding a button to the grid."""
        button_manager = ButtonManager(self.mock_app)
        
        # Create a test button configuration
        button_config = {
            'id': 'test_button',
            'name': 'Test Button',
            'type': 'website',
            'url': 'https://example.com',
            'icon': '🌐',
            'color': '#ff0000',
            'animation_type': 'fade'
        }
        
        # Mock the button creation
        with patch.object(button_manager, 'create_button_widget') as mock_create:
            mock_button = MagicMock()
            mock_create.return_value = mock_button
            
            button_manager.add_button_to_grid(button_config)
            
            # Check that button was created
            mock_create.assert_called_once_with(button_config)
    
    def test_create_button_widget(self):
        """Test creating a button widget."""
        button_manager = ButtonManager(self.mock_app)
        
        button_config = {
            'id': 'test_button',
            'name': 'Test Button',
            'type': 'website',
            'url': 'https://example.com',
            'icon': '🌐',
            'color': '#ff0000',
            'animation_type': 'fade'
        }
        
        # Mock the button factory
        with patch('core.managers.button_manager.ButtonHandlerFactory') as mock_factory:
            mock_handler = MagicMock()
            mock_factory.get_handler.return_value = mock_handler
            
            button = button_manager.create_button_widget(button_config)
            
            # Check that button was created with correct properties
            self.assertIsNotNone(button)
            mock_factory.get_handler.assert_called_once_with('website')
    
    def test_refresh_grid(self):
        """Test refreshing the button grid."""
        button_manager = ButtonManager(self.mock_app)
        
        # Add some test buttons to config
        self.mock_app.config_data['buttons'] = [
            {
                'id': 'btn1',
                'name': 'Button 1',
                'type': 'website',
                'url': 'https://example1.com',
                'icon': '🌐',
                'color': '#ff0000',
                'animation_type': 'fade'
            },
            {
                'id': 'btn2',
                'name': 'Button 2',
                'type': 'shell',
                'command': 'echo "test"',
                'icon': '💻',
                'color': '#00ff00',
                'animation_type': 'slide'
            }
        ]
        
        # Mock button creation
        with patch.object(button_manager, 'create_button_widget') as mock_create:
            mock_button = MagicMock()
            mock_create.return_value = mock_button
            
            button_manager.refresh_grid()
            
            # Check that buttons were created
            self.assertEqual(mock_create.call_count, 2)
    
    def test_clear_grid(self):
        """Test clearing the button grid."""
        button_manager = ButtonManager(self.mock_app)
        
        # Mock button frame
        mock_frame = MagicMock()
        button_manager.button_frame = mock_frame
        
        button_manager.clear_grid()
        
        # Check that frame was cleared
        mock_frame.destroy.assert_called_once()
    
    def test_get_button_by_id(self):
        """Test getting a button by ID."""
        button_manager = ButtonManager(self.mock_app)
        
        # Create a test button
        test_button = MagicMock()
        test_button.button_config = {'id': 'test_id'}
        button_manager.buttons = {'test_id': test_button}
        
        found_button = button_manager.get_button_by_id('test_id')
        
        self.assertEqual(found_button, test_button)
    
    def test_remove_button(self):
        """Test removing a button."""
        button_manager = ButtonManager(self.mock_app)
        
        # Create a test button
        test_button = MagicMock()
        button_manager.buttons = {'test_id': test_button}
        
        # Mock config update
        with patch.object(self.mock_app, 'save_config'):
            button_manager.remove_button('test_id')
            
            # Check that button was removed
            self.assertNotIn('test_id', button_manager.buttons)
            test_button.destroy.assert_called_once()
    
    def test_update_button_config(self):
        """Test updating button configuration."""
        button_manager = ButtonManager(self.mock_app)
        
        # Create a test button
        test_button = MagicMock()
        test_button.button_config = {'id': 'test_id', 'name': 'Old Name'}
        button_manager.buttons = {'test_id': test_button}
        
        new_config = {'id': 'test_id', 'name': 'New Name', 'type': 'website'}
        
        with patch.object(self.mock_app, 'save_config'):
            button_manager.update_button_config('test_id', new_config)
            
            # Check that button config was updated
            self.assertEqual(test_button.button_config['name'], 'New Name')
            self.assertEqual(test_button.button_config['type'], 'website')


if __name__ == '__main__':
    unittest.main() 