"""Main entry point for QuickButtons application."""

import sys
import os
from os import environ

# Hide pygame support prompt
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# Add the project root to the Python path so imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """Main entry point for the application."""
    try:
        import time
        start_time = time.time()
        
        from src.core.app import QuickButtonsApp
        from src.utils.logger import logger
        
        logger.info("Starting QuickButtons application")
        app = QuickButtonsApp()
        
        # Log startup time
        startup_time = time.time() - start_time
        logger.info(f"Application startup completed in {startup_time:.2f} seconds")
        
        app.mainloop()
        
    except Exception as e:
        import traceback
        from src.utils.logger import logger
        
        logger.error("[QuickButtons] Startup error:")
        logger.error(str(e))
        logger.error(traceback.format_exc())
        
        # Show error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("QuickButtons Error", f"{e}\n\nSee quickbuttons.log for details.")
            root.destroy()
        except Exception:
            logger.error(f"QuickButtons startup error: {e}")
            traceback.print_exc()
        
        sys.exit(1)

if __name__ == "__main__":
    main() 