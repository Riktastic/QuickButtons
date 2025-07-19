"""Button actions management functionality for QuickButtons."""

import tkinter as tk
from tkinter import filedialog, messagebox
from src.ui.dialogs import ButtonSettingsDialog
from src.utils.logger import logger


class ButtonActionsManager:
    """Handles button creation and editing actions."""
    
    def __init__(self, app):
        self.app = app
        self.button_settings_dialog = None
    
    def add_button(self):
        """Open the dialog to add a new button, only one at a time."""
        if self.button_settings_dialog is not None and self.button_settings_dialog.winfo_exists():
            self.button_settings_dialog.lift()
            return
        
        self.button_settings_dialog = ButtonSettingsDialog(self.app, self.app.theme, None, self._on_button_save, False)
        self.button_settings_dialog.protocol("WM_DELETE_WINDOW", self._on_button_close)
    
    def edit_button(self, btn_cfg):
        """Open the dialog to edit an existing button, only one at a time."""
        if self.button_settings_dialog is not None and self.button_settings_dialog.winfo_exists():
            self.button_settings_dialog.lift()
            return
        
        # Store the original config for comparison
        self.original_config = btn_cfg.copy()
        self.button_settings_dialog = ButtonSettingsDialog(self.app, self.app.theme, btn_cfg, self._on_button_save, True)
        self.button_settings_dialog.protocol("WM_DELETE_WINDOW", self._on_button_close)
    
    def _on_button_save(self, button_config):
        """Handle button save action."""
        if hasattr(self, 'original_config'):
            # Editing existing button
            try:
                index = self.app.config_data["buttons"].index(self.original_config)
                self.app.config_data["buttons"][index] = button_config
                logger.info(f"Updated button: {button_config.get('label', 'Unknown')}")
            except ValueError:
                logger.warning("Could not find original button config for update")
                self.app.config_data["buttons"].append(button_config)
            # Clear the stored original config
            delattr(self, 'original_config')
        else:
            # Adding new button
            self.app.config_data["buttons"].append(button_config)
            logger.info(f"Added new button: {button_config.get('label', 'Unknown')}")
        
        self.app.save_config()
        self.app.button_manager.refresh_grid()
        self._on_button_close()
    
    def _on_button_cancel(self):
        """Handle button cancel action."""
        self._on_button_close()
    
    def _on_button_close(self):
        """Handle button dialog close."""
        if self.button_settings_dialog is not None and self.button_settings_dialog.winfo_exists():
            self.button_settings_dialog.destroy()
        self.button_settings_dialog = None
    
    def add_buttons_from_files(self):
        """Open file dialog, auto-detect type, and add buttons for selected files."""
        files = filedialog.askopenfilenames(
            title=self.app._("Select files to add as buttons"),
            filetypes=[
                ("All supported", "*.py;*.bat;*.cmd;*.sh;*.exe;*.mp3;*.wav;*.flac;*.m4a;*.txt"),
                ("Python scripts", "*.py"),
                ("Batch files", "*.bat;*.cmd"),
                ("Shell scripts", "*.sh"),
                ("Executables", "*.exe"),
                ("Music files", "*.mp3;*.wav;*.flac;*.m4a"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not files:
            return
        
        added_count = 0
        for file_path in files:
            try:
                button_config = self._create_button_from_file(file_path)
                if button_config:
                    self.app.config_data["buttons"].append(button_config)
                    added_count += 1
                    logger.info(f"Added button from file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to create button from file {file_path}: {e}")
                messagebox.showerror(self.app._("Error"), f"Failed to create button from {os.path.basename(file_path)}: {e}")
        
        if added_count > 0:
            self.app.save_config()
            self.app.button_manager.refresh_grid()
            messagebox.showinfo(self.app._("Success"), f"Added {added_count} button(s) from files.")
    
    def _create_button_from_file(self, file_path):
        """Create a button configuration from a file path."""
        if not os.path.exists(file_path):
            return None
        
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1].lower()
        
        # Auto-detect button type based on file extension
        if ext == ".py":
            return {
                "type": "python_script",
                "label": name_without_ext,
                "script": file_path,
                "args": "",
                "background": False,
                "use_default_colors": True,
                "use_default_animation": True
            }
        elif ext in [".bat", ".cmd"]:
            return {
                "type": "shell",
                "label": name_without_ext,
                "shell_cmd": file_path,
                "use_default_colors": True,
                "use_default_animation": True
            }
        elif ext == ".sh":
            return {
                "type": "shell",
                "label": name_without_ext,
                "shell_cmd": f"bash {file_path}",
                "use_default_colors": True,
                "use_default_animation": True
            }
        elif ext in [".mp3", ".wav", ".flac", ".m4a"]:
            return {
                "type": "music",
                "label": name_without_ext,
                "music": file_path,
                "use_default_colors": True,
                "use_default_animation": True
            }
        elif ext == ".exe":
            return {
                "type": "shell",
                "label": name_without_ext,
                "shell_cmd": file_path,
                "use_default_colors": True,
                "use_default_animation": True
            }
        elif ext == ".txt":
            # Try to detect if it's a URL
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith(('http://', 'https://')):
                        return {
                            "type": "website",
                            "label": name_without_ext,
                            "url": content,
                            "use_default_colors": True,
                            "use_default_animation": True
                        }
            except Exception:
                pass
            
            # Default to shell command to open with default app
            return {
                "type": "shell",
                "label": name_without_ext,
                "shell_cmd": f'start "" "{file_path}"' if os.name == 'nt' else f'xdg-open "{file_path}"',
                "use_default_colors": True,
                "use_default_animation": True
            }
        else:
            # Generic file - open with default application
            return {
                "type": "shell",
                "label": name_without_ext,
                "shell_cmd": f'start "" "{file_path}"' if os.name == 'nt' else f'xdg-open "{file_path}"',
                "use_default_colors": True,
                "use_default_animation": True
            } 