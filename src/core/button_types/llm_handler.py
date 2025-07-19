"""LLM chat button type handler."""

from src.ui.dialogs import LLMChatOverlay
from src.utils.logger import logger


class LLMHandler:
    """Handles execution of LLM chat buttons."""
    
    def __init__(self, app):
        self.app = app
    
    def execute(self, cfg):
        """Execute an LLM chat button."""
        try:
            LLMChatOverlay(self.app, cfg, btn_label=cfg.get("label"))
            logger.info(f"LLM chat opened for button: {cfg.get('label', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to open LLM chat: {e}")
            # Note: LLMChatOverlay handles its own error display 