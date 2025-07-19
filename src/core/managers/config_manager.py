"""Configuration management for QuickButtons."""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.constants import CONFIG_FILE
from src.utils.logger import logger

# Config cache for performance
_config_cache = None
_config_cache_timestamp = None


class ConfigManager:
    """Manages application configuration loading, saving, and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Optional custom path for config file
        """
        self.config_path = config_path or CONFIG_FILE
        self.config_data = self._load_config()
        self._validate_and_fix_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default with caching."""
        global _config_cache, _config_cache_timestamp
        
        try:
            # Check if file has been modified since last load
            current_timestamp = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0
            
            if _config_cache is not None and _config_cache_timestamp == current_timestamp:
                logger.debug(f"Using cached config from {self.config_path}")
                return _config_cache.copy()  # Return a copy to avoid modifying cache
            
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.debug(f"Config loaded from {self.config_path}")
                    logger.debug(f"Python executable in loaded config: '{config.get('python_executable', '')}'")
                    
                    # Cache the config and timestamp
                    _config_cache = config.copy()
                    _config_cache_timestamp = current_timestamp
                    
                    return config
            else:
                # Create default config
                logger.info(f"Config file not found, creating default config")
                default_config = self._get_default_config()
                
                # Cache the default config
                _config_cache = default_config.copy()
                _config_cache_timestamp = current_timestamp
                
                return default_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            default_config = self._get_default_config()
            
            # Cache the default config
            _config_cache = default_config.copy()
            _config_cache_timestamp = current_timestamp
            
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'buttons': [],
            'button_size': 80,
            'theme': 'dark',
            'language': 'en',
            'minimal_mode': False,
            'translucency': 1.0,
            'default_animation_type': 'ripple',
            'log_level': 'WARNING',
            'window_geometry': '220x110',
            'python_executable': '',
            'volume': 1.0,
            'min_btn_width': 80,
            'max_btn_width': 220,
            'min_btn_height': 40,
            'max_btn_height': 110,
            'timer_sound': '',
            'animation_enabled': True
        }
    
    def _validate_and_fix_config(self):
        """Validate and fix configuration values."""
        defaults = self._get_default_config()
        
        # Ensure all required keys exist
        for key, default_value in defaults.items():
            if key not in self.config_data:
                self.config_data[key] = default_value
        
        # Validate specific values
        if not isinstance(self.config_data.get('button_size'), int):
            self.config_data['button_size'] = defaults['button_size']
        
        if not isinstance(self.config_data.get('translucency'), (int, float)):
            self.config_data['translucency'] = defaults['translucency']
        else:
            # Clamp translucency to valid range
            self.config_data['translucency'] = max(0.0, min(1.0, self.config_data['translucency']))
        
        if self.config_data.get('theme') not in ['light', 'dark']:
            self.config_data['theme'] = defaults['theme']
        
        if self.config_data.get('language') not in ['en', 'es']:
            self.config_data['language'] = defaults['language']
        
        valid_animation_types = ['ripple', 'scale', 'glow', 'bounce', 'shake', 'flame', 'confetti', 'sparkle', 'explosion', 'combined']
        if self.config_data.get('default_animation_type') not in valid_animation_types:
            self.config_data['default_animation_type'] = defaults['default_animation_type']
        
        if self.config_data.get('log_level') not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            self.config_data['log_level'] = defaults['log_level']
    
    def save_config(self):
        """Save configuration to file with backup."""
        try:
            # Create backup if config file exists
            if os.path.exists(self.config_path):
                backup_path = self.config_path + '.backup'
                shutil.copy2(self.config_path, backup_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {self.config_path}")
            logger.debug(f"Python executable in saved config: '{self.config_data.get('python_executable', '')}'")
                
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config_data = self._load_config()
        self._validate_and_fix_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config_data[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        self.config_data.update(updates)
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config_data = self._get_default_config()
        self.save_config() 