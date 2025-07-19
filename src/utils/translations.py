"""Translation management for multilingual support."""

import json
import os
from src.core.constants import TRANSLATIONS_FILE
from .logger import logger

class TranslationManager:
    """Manages application translations."""
    
    def __init__(self):
        self.translations = {}
        self.current_language = "en"
        self.load_translations()
    
    def load_translations(self):
        """Load translations from JSON file."""
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            # Fallback to empty translations
            self.translations = {"en": {}, "nl": {}}
    
    def set_language(self, language_code):
        """Set the current language."""
        if language_code in self.translations:
            self.current_language = language_code
        else:
            logger.warning(f"Language '{language_code}' not available, using English")
            self.current_language = "en"
    
    def get_text(self, text, language=None):
        """Get translated text for the current or specified language."""
        lang = language or self.current_language
        return self.translations.get(lang, self.translations.get("en", {})).get(text, text)
    
    def _(self, text):
        """Shorthand method for getting translated text."""
        return self.get_text(text)

# Global translation manager instance
translation_manager = TranslationManager() 