"""About dialog for QuickButtons."""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from src.core.constants import ICON_PATH, APP_VERSION
from src.ui.themes import apply_theme_recursive
from src.utils.logger import logger

class AboutDialog(tk.Toplevel):
    """Dialog showing information about QuickButtons."""
    
    def __init__(self, master, theme):
        super().__init__(master)
        self.title(master._("About QuickButtons"))
        self.geometry("340x240+340+340")
        self.configure(bg=theme["dialog_bg"])
        self.resizable(False, False)
        
        # Set window icon
        try:
            from src.core.constants import ICON_ICO_PATH
            self.iconbitmap(ICON_ICO_PATH)
        except Exception as e:
            logger.warning(f"Could not set about dialog icon: {e}")
        
        # App icon (if available)
        try:
            icon_img = Image.open(ICON_PATH)
            icon_img = icon_img.resize((48, 48), Image.LANCZOS)
            icon_img = ImageTk.PhotoImage(icon_img)
            icon_label = tk.Label(self, image=icon_img, bg=theme["dialog_bg"])
            icon_label.image = icon_img
            icon_label.pack(pady=(18, 6))
        except Exception as e:
            logger.warning(f"Could not load icon for about dialog: {e}")
            pass
        
        # App name and version
        name_label = tk.Label(self, text=master._("QuickButtons"), font=("Segoe UI", 16, "bold"), 
                             bg=theme["dialog_bg"], fg=theme["button_fg"])
        name_label.pack(pady=(0, 2))
        
        version_label = tk.Label(self, text=master._("Version: {version}").format(version=APP_VERSION), 
                                font=("Segoe UI", 10), bg=theme["dialog_bg"], fg=theme["label_fg"])
        version_label.pack()
        
        # Author
        author_label = tk.Label(self, text=master._("Made by Rik Heijmann"), font=("Segoe UI", 10), 
                               bg=theme["dialog_bg"], fg=theme["label_fg"])
        author_label.pack(pady=(2, 2))
        
        # Website link
        website_label = tk.Label(self, text="https://Rik.blue", font=("Segoe UI", 9), 
                                bg=theme["dialog_bg"], fg="#0066cc", cursor="hand2")
        website_label.pack(pady=(0, 8))
        
        # Make website clickable
        def open_website(event):
            import webbrowser
            webbrowser.open("https://Rik.blue")
        
        website_label.bind("<Button-1>", open_website)
        website_label.bind("<Enter>", lambda e: website_label.config(fg="#0033aa"))
        website_label.bind("<Leave>", lambda e: website_label.config(fg="#0066cc"))
        
        # Description
        desc_label = tk.Label(self, text=master._("A modern floating button panel for scripts."), 
                             font=("Segoe UI", 10), bg=theme["dialog_bg"], fg=theme["label_fg"], 
                             wraplength=300, justify="center")
        desc_label.pack(pady=(0, 10))
        
        
        self.grab_set()
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())
        self.apply_theme(theme)

    def apply_theme(self, theme):
        """Apply theme to the dialog."""
        apply_theme_recursive(self, theme) 