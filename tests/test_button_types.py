"""Tests for button type handlers."""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import tkinter as tk

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.button_types.button_handler_factory import ButtonHandlerFactory
from core.button_types.website_handler import WebsiteHandler
from core.button_types.shell_handler import ShellHandler
from core.button_types.music_handler import MusicHandler
from core.button_types.python_script_handler import PythonScriptHandler
from core.button_types.post_handler import PostHandler
from core.button_types.llm_handler import LLMHandler


class TestButtonHandlerFactory(unittest.TestCase):
    """Test cases for ButtonHandlerFactory."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = ButtonHandlerFactory()
        
    def test_get_handler_website(self):
        """Test getting website handler."""
        handler = self.factory.get_handler('website')
        self.assertIsInstance(handler, WebsiteHandler)
    
    def test_get_handler_shell(self):
        """Test getting shell handler."""
        handler = self.factory.get_handler('shell')
        self.assertIsInstance(handler, ShellHandler)
    
    def test_get_handler_music(self):
        """Test getting music handler."""
        handler = self.factory.get_handler('music')
        self.assertIsInstance(handler, MusicHandler)
    
    def test_get_handler_python_script(self):
        """Test getting python script handler."""
        handler = self.factory.get_handler('python_script')
        self.assertIsInstance(handler, PythonScriptHandler)
    
    def test_get_handler_post(self):
        """Test getting post handler."""
        handler = self.factory.get_handler('post')
        self.assertIsInstance(handler, PostHandler)
    
    def test_get_handler_llm(self):
        """Test getting LLM handler."""
        handler = self.factory.get_handler('llm')
        self.assertIsInstance(handler, LLMHandler)
    
    def test_get_handler_invalid(self):
        """Test getting invalid handler."""
        with self.assertRaises(ValueError):
            self.factory.get_handler('invalid_type')


class TestWebsiteHandler(unittest.TestCase):
    """Test cases for WebsiteHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.handler = WebsiteHandler(self.mock_app)
        
    def test_validate_config_valid(self):
        """Test validating valid website config."""
        config = {
            'name': 'Test Website',
            'url': 'https://example.com',
            'icon': '🌐',
            'color': '#ff0000'
        }
        
        result = self.handler.validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_missing_url(self):
        """Test validating config with missing URL."""
        config = {
            'name': 'Test Website',
            'icon': '🌐',
            'color': '#ff0000'
        }
        
        result = self.handler.validate_config(config)
        self.assertFalse(result)
    
    def test_validate_config_invalid_url(self):
        """Test validating config with invalid URL."""
        config = {
            'name': 'Test Website',
            'url': 'not-a-url',
            'icon': '🌐',
            'color': '#ff0000'
        }
        
        result = self.handler.validate_config(config)
        self.assertFalse(result)
    
    def test_execute_action(self):
        """Test executing website action."""
        config = {
            'url': 'https://example.com'
        }
        
        with patch('webbrowser.open') as mock_open:
            self.handler.execute_action(config)
            mock_open.assert_called_once_with('https://example.com')


class TestShellHandler(unittest.TestCase):
    """Test cases for ShellHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.handler = ShellHandler(self.mock_app)
        
    def test_validate_config_valid(self):
        """Test validating valid shell config."""
        config = {
            'name': 'Test Command',
            'command': 'echo "test"',
            'icon': '💻',
            'color': '#00ff00'
        }
        
        result = self.handler.validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_missing_command(self):
        """Test validating config with missing command."""
        config = {
            'name': 'Test Command',
            'icon': '💻',
            'color': '#00ff00'
        }
        
        result = self.handler.validate_config(config)
        self.assertFalse(result)
    
    def test_execute_action(self):
        """Test executing shell action."""
        config = {
            'command': 'echo "test"'
        }
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process
            
            self.handler.execute_action(config)
            
            mock_popen.assert_called_once()
            # Check that command was called with shell=True
            args, kwargs = mock_popen.call_args
            self.assertTrue(kwargs.get('shell', False))


class TestMusicHandler(unittest.TestCase):
    """Test cases for MusicHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.handler = MusicHandler(self.mock_app)
        
    def test_validate_config_valid(self):
        """Test validating valid music config."""
        config = {
            'name': 'Test Music',
            'file_path': '/path/to/music.mp3',
            'icon': '🎵',
            'color': '#ff00ff'
        }
        
        result = self.handler.validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_missing_path(self):
        """Test validating config with missing file path."""
        config = {
            'name': 'Test Music',
            'icon': '🎵',
            'color': '#ff00ff'
        }
        
        result = self.handler.validate_config(config)
        self.assertFalse(result)
    
    def test_execute_action(self):
        """Test executing music action."""
        config = {
            'file_path': '/path/to/music.mp3'
        }
        
        with patch.object(self.mock_app.music_player, 'play') as mock_play:
            self.handler.execute_action(config)
            mock_play.assert_called_once_with('/path/to/music.mp3')


class TestPythonScriptHandler(unittest.TestCase):
    """Test cases for PythonScriptHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.handler = PythonScriptHandler(self.mock_app)
        
    def test_validate_config_valid(self):
        """Test validating valid python script config."""
        config = {
            'name': 'Test Script',
            'script_path': '/path/to/script.py',
            'icon': '🐍',
            'color': '#ffff00'
        }
        
        result = self.handler.validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_missing_path(self):
        """Test validating config with missing script path."""
        config = {
            'name': 'Test Script',
            'icon': '🐍',
            'color': '#ffff00'
        }
        
        result = self.handler.validate_config(config)
        self.assertFalse(result)
    
    def test_execute_action(self):
        """Test executing python script action."""
        config = {
            'script_path': '/path/to/script.py'
        }
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process
            
            self.handler.execute_action(config)
            
            mock_popen.assert_called_once()
            # Check that python was called
            args, kwargs = mock_popen.call_args
            self.assertIn('python', args[0])


class TestPostHandler(unittest.TestCase):
    """Test cases for PostHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.handler = PostHandler(self.mock_app)
        
    def test_validate_config_valid(self):
        """Test validating valid post config."""
        config = {
            'name': 'Test Post',
            'url': 'https://api.example.com/post',
            'data': {'key': 'value'},
            'icon': '📤',
            'color': '#00ffff'
        }
        
        result = self.handler.validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_missing_url(self):
        """Test validating config with missing URL."""
        config = {
            'name': 'Test Post',
            'data': {'key': 'value'},
            'icon': '📤',
            'color': '#00ffff'
        }
        
        result = self.handler.validate_config(config)
        self.assertFalse(result)
    
    def test_execute_action(self):
        """Test executing post action."""
        config = {
            'url': 'https://api.example.com/post',
            'data': {'key': 'value'}
        }
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            self.handler.execute_action(config)
            
            mock_post.assert_called_once_with(
                'https://api.example.com/post',
                json={'key': 'value'}
            )


class TestLLMHandler(unittest.TestCase):
    """Test cases for LLMHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.handler = LLMHandler(self.mock_app)
        
    def test_validate_config_valid(self):
        """Test validating valid LLM config."""
        config = {
            'name': 'Test LLM',
            'prompt': 'Hello, how are you?',
            'icon': '🤖',
            'color': '#ff8800'
        }
        
        result = self.handler.validate_config(config)
        self.assertTrue(result)
    
    def test_validate_config_missing_prompt(self):
        """Test validating config with missing prompt."""
        config = {
            'name': 'Test LLM',
            'icon': '🤖',
            'color': '#ff8800'
        }
        
        result = self.handler.validate_config(config)
        self.assertFalse(result)
    
    def test_execute_action(self):
        """Test executing LLM action."""
        config = {
            'prompt': 'Hello, how are you?'
        }
        
        with patch.object(self.mock_app, 'show_llm_overlay') as mock_show:
            self.handler.execute_action(config)
            mock_show.assert_called_once_with('Hello, how are you?')


if __name__ == '__main__':
    unittest.main() 