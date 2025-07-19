"""Button handler factory for routing to appropriate button type handlers."""

from src.utils.logger import logger


class ButtonHandlerFactory:
    """Factory for creating and managing button type handlers with lazy loading."""
    
    def __init__(self, app):
        self.app = app
        self._handlers = {}
        # Don't initialize handlers immediately - load them on first use
    
    def _get_handler_class(self, handler_type):
        """Get handler class with lazy import."""
        try:
            if handler_type == "python_script":
                from .python_script_handler import PythonScriptHandler
                return PythonScriptHandler
            elif handler_type == "website":
                from .website_handler import WebsiteHandler
                return WebsiteHandler
            elif handler_type == "music":
                from .music_handler import MusicHandler
                return MusicHandler
            elif handler_type == "post":
                from .post_handler import PostHandler
                return PostHandler
            elif handler_type == "shell":
                from .shell_handler import ShellHandler
                return ShellHandler
            elif handler_type == "llm":
                from .llm_handler import LLMHandler
                return LLMHandler
            elif handler_type == "app_launcher":
                from .app_launcher_handler import AppLauncherHandler
                return AppLauncherHandler
            elif handler_type == "network_speed":
                from .network_speed_handler import NetworkSpeedHandler
                return NetworkSpeedHandler
            elif handler_type == "ping":
                from .ping_handler import PingHandler
                return PingHandler
            elif handler_type == "pomodoro":
                from .pomodoro_handler import PomodoroHandler
                return PomodoroHandler
            elif handler_type == "http_test":
                from .http_test_handler import HTTPTestHandler
                return HTTPTestHandler
            elif handler_type == "color_picker":
                from .color_picker_handler import ColorPickerHandler
                return ColorPickerHandler
            else:
                logger.warning(f"Unknown handler type: {handler_type}")
                return None
        except ImportError as e:
            logger.error(f"Failed to import handler {handler_type}: {e}")
            return None
    
    def _ensure_handler_loaded(self, handler_type):
        """Ensure a specific handler is loaded."""
        if handler_type not in self._handlers:
            handler_class = self._get_handler_class(handler_type)
            if handler_class:
                self._handlers[handler_type] = handler_class(self.app)
                logger.debug(f"Lazy loaded handler: {handler_type}")
    
    def get_handler(self, button_type):
        """Get the appropriate handler for a button type."""
        self._ensure_handler_loaded(button_type)
        handler = self._handlers.get(button_type)
        if handler is None:
            logger.warning(f"No handler found for button type: {button_type}")
            # Default to python_script handler
            self._ensure_handler_loaded("python_script")
            handler = self._handlers.get("python_script")
        return handler
    
    def execute_button(self, cfg):
        """Execute a button using the appropriate handler."""
        button_type = cfg.get("type", "python_script")
        handler = self.get_handler(button_type)
        
        if handler:
            try:
                handler.execute(cfg)
            except Exception as e:
                logger.error(f"Error executing button {cfg.get('label', 'Unknown')}: {e}")
                raise
        else:
            logger.error(f"No handler available for button type: {button_type}")
    
    def get_supported_types(self):
        """Get list of supported button types."""
        return ["python_script", "website", "music", "post", "shell", "llm", "app_launcher", "network_speed", "ping", "pomodoro", "http_test", "color_picker"]
    
    def preload_all_handlers(self):
        """Preload all handlers (useful for testing or when all handlers are needed)."""
        handler_types = self.get_supported_types()
        for handler_type in handler_types:
            self._ensure_handler_loaded(handler_type)
        logger.info(f"Preloaded {len(handler_types)} handlers") 