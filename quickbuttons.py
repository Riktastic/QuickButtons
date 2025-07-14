"""
QuickButtons - A modern, floating, always-on-top button panel for running scripts, opening websites, and playing music.
Author: Rik Heijmann (https://Rik.blue)
"""
# Import standard and third-party libraries
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from tkinter import ttk
import tkinter.font as tkfont
import subprocess
import threading
import json
import os
import sys
from PIL import Image, ImageTk
import datetime
import pygame
import requests
import re
import argparse

# Try to import keyboard for global hotkey support
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# Configuration file and button size limits
CONFIG_FILE = "config.json"
MAX_BTN_SIZE = 120
MIN_BTN_SIZE = 64

# Load translations from JSON file
with open("translations.json", "r", encoding="utf-8") as f:
    TRANSLATIONS = json.load(f)
# Load themes from JSON file
with open("themes.json", "r", encoding="utf-8") as f:
    THEMES = json.load(f)

# Translation function
# Use as self._("string") in class, or _(string) globally if needed

def _(self, text):
    lang = getattr(self, 'config_data', {}).get("language", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(text, text)

def detect_system_theme():
    """Detect system light/dark mode preference for Linux (GNOME) and Windows."""
    # Linux (GNOME)
    if sys.platform.startswith("linux"):
        try:
            import subprocess
            result = subprocess.run([
                "gsettings", "get", "org.gnome.desktop.interface", "color-scheme"
            ], capture_output=True, text=True)
            if "prefer-dark" in result.stdout:
                return "dark"
            elif "default" in result.stdout or "prefer-light" in result.stdout:
                return "light"
        except Exception:
            pass
    # Windows
    if sys.platform.startswith("win"):
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize") as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if value == 1 else "dark"
        except Exception:
            pass
    return "dark"

def play_music(path):
    """Play a music file using pygame."""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    except Exception as e:
        messagebox.showerror("Music Error", f"Could not play music: {e}")

APP_VERSION = "1.0.0"

class QuickButtonsApp(tk.Tk):
    """Main application window for QuickButtons."""
    def __init__(self):
        super().__init__()
        self.title(self._("QuickButtons"))
        self.config_data = self.load_config()
        self.theme_name = self.config_data.get("theme", detect_system_theme())
        self.theme = THEMES[self.theme_name]
        self.configure(bg=self.theme["bg"])
        # Restore last window geometry if present
        geom = self.config_data.get("window_geometry")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("220x110")
        self.minsize(120, 60)
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.create_topbar()
        self.create_button_grid()
        self.update_theme()
        self.after(200, self.refresh_grid)
        self.attributes("-alpha", self.config_data.get("translucency", 1.0))
        self._resize_after_id = None
        self.bind('<Configure>', self._on_window_configure)
        self.global_hotkeys = []
        self.settings_dialog = None
        self.about_dialog = None
        self.button_settings_dialog = None
        self.current_music_btn = None
        self.current_music_path = None
        self._music_glow_job = None
        self._music_glow_state = False
        # In QuickButtonsApp.__init__, set default language if not present
        if "language" not in self.config_data:
            self.config_data["language"] = "en"

    def _on_window_configure(self, event):
        """Debounce window resize/move events to avoid excessive config writes."""
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(400, self._save_window_geometry)

    def _save_window_geometry(self):
        """Save the current window geometry to config."""
        geom = self.geometry()
        self.config_data["window_geometry"] = geom
        self.save_config()
        self._resize_after_id = None

    def create_topbar(self):
        """Create the top bar with add/settings/about/theme/pin buttons, using only icons."""
        self.topbar = tk.Frame(self, bg=self.theme["topbar"], height=28)
        self.topbar.pack(side=tk.TOP, fill=tk.X)
        # Add button (icon only)
        self.add_btn = tk.Button(self.topbar, text="+", bg=self.theme["topbar"], fg=self.theme["button_fg"], font=("Segoe UI", 10, "bold"), relief=tk.FLAT, command=self.add_button, bd=0, highlightthickness=0, activebackground=self.theme["button_hover"], activeforeground=self.theme["button_fg"])
        self.add_btn.pack(side=tk.RIGHT, padx=(0,2), pady=2, ipadx=2, ipady=0)
        self.add_btn.bind("<Enter>", lambda e: self.add_btn.config(bg=self.theme["button_hover"]))
        self.add_btn.bind("<Leave>", lambda e: self.add_btn.config(bg=self.theme["topbar"]))
        # Theme toggle button (icon only)
        self.theme_btn = tk.Button(self.topbar, text="☀" if self.theme_name=="light" else "🌙", bg=self.theme["topbar"], fg=self.theme["button_fg"], font=("Segoe UI", 10), relief=tk.FLAT, command=self.toggle_theme, bd=0, highlightthickness=0, activebackground=self.theme["button_hover"], activeforeground=self.theme["button_fg"])
        self.theme_btn.pack(side=tk.RIGHT, padx=(0,2), pady=2)
        # Pin (always on top) button
        self.always_on_top = self.config_data.get("always_on_top", True)
        self.pin_btn = tk.Button(self.topbar, text="📌" if self.always_on_top else "📍", bg=self.theme["topbar"], fg=self.theme["button_fg"], font=("Segoe UI", 10), relief=tk.FLAT, command=self.toggle_on_top, bd=0, highlightthickness=0, activebackground=self.theme["button_hover"], activeforeground=self.theme["button_fg"])
        self.pin_btn.pack(side=tk.RIGHT, padx=(0,2), pady=2)
        Tooltip(self.pin_btn, self._("Keep on top") if self.always_on_top else self._("Do not keep on top"))
        # Settings button (icon only)
        self.settings_btn = tk.Button(self.topbar, text="⚙", bg=self.theme["topbar"], fg=self.theme["button_fg"], font=("Segoe UI", 10), relief=tk.FLAT, command=self.open_settings, bd=0, highlightthickness=0, activebackground=self.theme["button_hover"], activeforeground=self.theme["button_fg"])
        self.settings_btn.pack(side=tk.RIGHT, padx=(0,2), pady=2)
        # About button (icon only)
        self.about_btn = tk.Button(self.topbar, text="?", bg=self.theme["topbar"], fg=self.theme["button_fg"], font=("Segoe UI", 10), relief=tk.FLAT, command=self.open_about, bd=0, highlightthickness=0, activebackground=self.theme["button_hover"], activeforeground=self.theme["button_fg"])
        self.about_btn.pack(side=tk.RIGHT, padx=(0,2), pady=2)
        # Set initial always-on-top state
        self.attributes("-topmost", self.always_on_top)

    def toggle_on_top(self):
        """Toggle the always-on-top state and update the pin button."""
        self.always_on_top = not self.always_on_top
        self.config_data["always_on_top"] = self.always_on_top
        self.attributes("-topmost", self.always_on_top)
        self.pin_btn.config(text="📌" if self.always_on_top else "📍")
        Tooltip(self.pin_btn, self._("Keep on top") if self.always_on_top else self._("Do not keep on top"))
    def create_button_grid(self):
        """Create the scrollable button grid area."""
        self.grid_canvas = tk.Canvas(self, bg=self.theme["bg"], highlightthickness=0, borderwidth=0)
        self.grid_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))
        self.grid_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.grid_canvas.yview)
        self.grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.grid_frame = tk.Frame(self.grid_canvas, bg=self.theme["bg"])
        self.grid_window = self.grid_canvas.create_window((0,0), window=self.grid_frame, anchor="nw")
        self.grid_canvas.configure(yscrollcommand=self.grid_scrollbar.set)
        self.grid_frame.bind("<Configure>", lambda e: self._on_grid_configure())
        self.grid_canvas.bind("<Configure>", lambda e: self._on_canvas_configure())
        self.button_widgets = []
        self.refresh_grid()

    def _on_grid_configure(self):
        """Update the scroll region and show/hide scrollbar as needed."""
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        # Show scrollbar only if needed
        frame_height = self.grid_frame.winfo_height()
        canvas_height = self.grid_canvas.winfo_height()
        if frame_height > canvas_height:
            self.grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.grid_scrollbar.pack_forget()

    def _on_canvas_configure(self):
        """Resize the grid window to match the canvas width."""
        self.grid_canvas.itemconfig(self.grid_window, width=self.grid_canvas.winfo_width())

    def refresh_grid(self):
        """Refresh the button grid layout and bind shortcuts/hotkeys."""
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.button_widgets = []
        btns = self.config_data.get("buttons", [])
        size = min(max(self.config_data.get("panel_size", MAX_BTN_SIZE), MIN_BTN_SIZE), MAX_BTN_SIZE)
        width = self.grid_frame.winfo_width() or 220
        max_per_row = max(1, width // (size+8))
        per_row = min(len(btns), max_per_row) if btns else 1
        self.shortcut_map = {}
        self.unregister_global_hotkeys()
        for idx, btn_cfg in enumerate(btns):
            row, col = divmod(idx, per_row)
            btn = self.create_button(self.grid_frame, btn_cfg, size, row, col)
            self.button_widgets.append(btn)
            # Bind shortcut
            shortcut = btn_cfg.get("shortcut", "").strip()
            if shortcut:
                keyseq = self.parse_shortcut(shortcut)
                if keyseq:
                    self.shortcut_map[keyseq] = lambda c=btn_cfg: self.run_script(c)
                    self.bind_all(keyseq, lambda e, c=btn_cfg: self.run_script(c))
            if HAS_KEYBOARD and shortcut:
                try:
                    keyboard.add_hotkey(shortcut, lambda c=btn_cfg: self.run_script(c))
                    self.global_hotkeys.append(shortcut)
                except Exception as e:
                    print(f"Could not register global hotkey {shortcut}: {e}")
        if not HAS_KEYBOARD:
            print("[QuickButtons] Global hotkeys require the 'keyboard' module. Install with 'pip install keyboard'.")
        elif sys.platform.startswith("linux") and os.geteuid() != 0:
            print("[QuickButtons] On Linux, global hotkeys require root or uinput access.")
        self.grid_frame.update_idletasks()
        self._on_grid_configure()

    def parse_shortcut(self, shortcut):
        """Convert shortcut string to Tkinter key sequence."""
        # Convert e.g. Ctrl+1 to <Control-1>, Alt+Q to <Alt-q>, F5 to <F5>
        s = shortcut.replace("Ctrl", "Control").replace("ctrl", "Control").replace("ALT", "Alt").replace("alt", "Alt")
        s = s.replace("+", "-").replace(" ", "")
        if s.startswith("F") and s[1:].isdigit():
            return f"<{s}>"
        if "-" in s:
            return f"<{s}>"
        return None

    def create_button(self, parent, cfg, size, row, col):
        """Create a single button in the grid, with icon, label, and right-click edit."""
        # Defensive: ensure music attributes exist
        if not hasattr(self, 'current_music_path'):
            self.current_music_path = None
        if not hasattr(self, 'current_music_btn'):
            self.current_music_btn = None
        icon = None
        if cfg.get("icon") and os.path.isfile(cfg["icon"]):
            img = Image.open(cfg["icon"])
            img = img.convert("RGBA")
            min_side = min(img.width, img.height)
            left = (img.width - min_side) // 2
            top = (img.height - min_side) // 2
            img = img.crop((left, top, left+min_side, top+min_side))
            img = img.resize((size-18, size-18), Image.ANTIALIAS)
            icon = ImageTk.PhotoImage(img)
        label = cfg.get("label", "Run Script")
        font_size = self.fit_font_size(label, size)
        btn = tk.Button(parent, text=label, image=icon, compound=tk.TOP if icon else tk.NONE,
                        bg=cfg.get("bg_color", self.theme["button_bg"]),
                        fg=cfg.get("fg_color", self.theme["button_fg"]),
                        font=("Segoe UI", font_size, "bold"),
                        relief=tk.FLAT, bd=0, highlightthickness=0,
                        activebackground=self.theme["button_hover"],
                        activeforeground=cfg.get("fg_color", self.theme["button_fg"]),
                        command=lambda c=cfg: self.run_script(c), wraplength=size-10, justify="center")
        btn.grid(row=row, column=col, padx=4, pady=4, ipadx=0, ipady=0, sticky="nsew")
        btn.bind("<Button-3>", lambda e, i=cfg: self.edit_button(i))
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.theme["button_hover"]))
        btn.bind("<Leave>", lambda e, b=btn, c=cfg.get("bg_color", self.theme["button_bg"]): b.config(bg=c))
        btn.image = icon
        parent.grid_columnconfigure(col, weight=1)
        # Indicate if this button is currently playing music
        if cfg.get("type") == "music" and self.current_music_path == cfg.get("music") and pygame.mixer.music.get_busy():
            self._start_music_glow(btn)
        # Tooltip for full label if truncated
        if self.fit_font_size(label, size) < 10:
            Tooltip(btn, label)
        if cfg.get("shortcut"):
            Tooltip(btn, f"Shortcut: {cfg['shortcut']}")
        return btn

    def fit_font_size(self, text, size, max_font=16, min_font=7):
        """Find the largest font size that fits the button width."""
        font_size = max_font
        test_font = tkfont.Font(family="Segoe UI", size=font_size, weight="bold")
        while font_size > min_font:
            width = test_font.measure(text)
            if width < size-10:
                break
            font_size -= 1
            test_font.configure(size=font_size)
        return font_size

    def run_script(self, cfg):
        """Run the action for a button (script, website, music, post request, or shell command)."""
        t = cfg.get("type", "script")
        if t == "script":
            script = cfg.get("script")
            if not script or not os.path.isfile(script):
                messagebox.showerror("Script not found", self._("No script configured or file missing."))
                return
            args = self.expand_args(cfg.get("args", ""))
            ext = os.path.splitext(script)[1].lower()
            if ext == ".py":
                OutputOverlay(self, script, args)
            elif ext == ".sh":
                import subprocess
                try:
                    result = subprocess.run(["bash", script] + args, capture_output=True, text=True)
                    messagebox.showinfo(self._("Shell Output"), result.stdout[:1000] or self._("(No output)"))
                except Exception as e:
                    messagebox.showerror(self._("Shell Error"), str(e))
            elif ext in [".bat", ".cmd"]:
                import subprocess
                try:
                    result = subprocess.run(["cmd.exe", "/c", script] + args, capture_output=True, text=True)
                    messagebox.showinfo(self._("Shell Output"), result.stdout[:1000] or self._("(No output)"))
                except Exception as e:
                    messagebox.showerror(self._("Shell Error"), str(e))
            else:
                # Try to execute directly
                import subprocess
                try:
                    result = subprocess.run([script] + args, capture_output=True, text=True)
                    messagebox.showinfo(self._("Shell Output"), result.stdout[:1000] or self._("(No output)"))
                except Exception as e:
                    messagebox.showerror(self._("Shell Error"), str(e))
        elif t == "website":
            url = cfg.get("url")
            if not url:
                messagebox.showerror("No URL", self._("No website URL configured."))
                return
            import webbrowser
            webbrowser.open(url)
        elif t == "music":
            music = cfg.get("music")
            if not music or not os.path.isfile(music):
                messagebox.showerror("Music not found", self._("No music file configured or file missing."))
                return
            # Stop if same music is playing
            if self.current_music_path == music and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self._reset_music_button()
                return
            # Stop previous music if any
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self._reset_music_button()
            # Find the button widget for this music
            btn = None
            for b, c in zip(self.button_widgets, self.config_data.get("buttons", [])):
                if c is cfg:
                    btn = b
                    break
            self.current_music_btn = btn
            self.current_music_path = music
            if btn:
                self._start_music_glow(btn)
            threading.Thread(target=self._play_music_and_reset, args=(music, btn), daemon=True).start()
        elif t == "post":
            url = self.expand_wildcards(cfg.get("post_url", ""))
            headers = self.parse_headers(self.expand_wildcards(cfg.get("post_headers", "")))
            body = self.expand_wildcards(cfg.get("post_body", ""))
            try:
                resp = requests.post(url, headers=headers, data=body.encode("utf-8"))
                messagebox.showinfo(self._("POST Response"), f"{self._('Status')}: {resp.status_code}\n{resp.text[:1000]}")
            except Exception as e:
                messagebox.showerror(self._("POST Error"), str(e))
        elif t == "shell":
            cmd = cfg.get("shell_cmd", "")
            if not cmd:
                messagebox.showerror(self._("No Command"), self._("No shell command configured."))
                return
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                messagebox.showinfo(self._("Shell Output"), result.stdout[:1000] or self._("(No output)"))
            except Exception as e:
                messagebox.showerror(self._("Shell Error"), str(e))

    def expand_wildcards(self, text):
        from datetime import datetime
        now = datetime.now()
        text = text.replace("{date}", now.strftime("%Y-%m-%d"))
        text = text.replace("{time}", now.strftime("%H:%M:%S"))
        text = text.replace("{datetime}", now.strftime("%Y-%m-%d_%H-%M-%S"))
        return text

    def parse_headers(self, headers_str):
        headers = {}
        for line in headers_str.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip()] = v.strip()
        return headers

    def _start_music_glow(self, btn):
        self._stop_music_glow()
        self._music_glow_state = False
        def pulse():
            if not self.current_music_btn or not pygame.mixer.music.get_busy():
                self._stop_music_glow()
                return
            self._music_glow_state = not self._music_glow_state
            if self._music_glow_state:
                btn.config(highlightthickness=4, highlightbackground="#4a90e2")
            else:
                btn.config(highlightthickness=2, highlightbackground="#aee6ff")
            self._music_glow_job = self.after(200, pulse)
        pulse()

    def _stop_music_glow(self):
        if self._music_glow_job:
            self.after_cancel(self._music_glow_job)
            self._music_glow_job = None
        if self.current_music_btn:
            self.current_music_btn.config(highlightthickness=0)

    def _play_music_and_reset(self, path, btn):
        try:
            pygame.mixer.init()
            volume = self.config_data.get("volume", 100) / 100.0
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time; time.sleep(0.1)
        except Exception as e:
            messagebox.showerror("Music Error", f"Could not play music: {e}")
        finally:
            self.after(100, self._reset_music_button)

    def _reset_music_button(self):
        self._stop_music_glow()
        if self.current_music_btn:
            # Restore original color
            cfg = None
            for c in self.config_data.get("buttons", []):
                if c.get("music") == self.current_music_path:
                    cfg = c
                    break
            color = cfg.get("bg_color", self.theme["button_bg"]) if cfg else self.theme["button_bg"]
            self.current_music_btn.config(bg=color)
        self.current_music_btn = None
        self.current_music_path = None

    def expand_args(self, argstr):
        """Expand wildcards in arguments (e.g., {date}, {time}, {datetime})."""
        from datetime import datetime
        now = datetime.now()
        argstr = argstr.replace("{date}", now.strftime("%Y-%m-%d"))
        argstr = argstr.replace("{time}", now.strftime("%H:%M:%S"))
        argstr = argstr.replace("{datetime}", now.strftime("%Y-%m-%d_%H-%M-%S"))
        return argstr.split()

    def add_button(self):
        """Open the dialog to add a new button, only one at a time."""
        if self.button_settings_dialog is not None and self.button_settings_dialog.winfo_exists():
            self.button_settings_dialog.lift()
            return
        self.button_settings_dialog = ButtonSettingsDialog(self, self.theme, on_save=self._on_button_settings_save)
        self.button_settings_dialog.protocol("WM_DELETE_WINDOW", self._on_button_settings_close)

    def _on_button_settings_save(self, btn_cfg):
        self.save_new_button(btn_cfg)
        self._on_button_settings_close()

    def _on_button_settings_close(self):
        if self.button_settings_dialog is not None and self.button_settings_dialog.winfo_exists():
            self.button_settings_dialog.destroy()
        self.button_settings_dialog = None

    def save_new_button(self, btn_cfg):
        """Save a new button configuration and refresh the grid."""
        if not btn_cfg:
            return
        self.config_data.setdefault("buttons", []).append(btn_cfg)
        self.save_config()
        self.refresh_grid()

    def edit_button(self, btn_cfg):
        """Open the dialog to edit an existing button, only one at a time."""
        if self.button_settings_dialog is not None and self.button_settings_dialog.winfo_exists():
            self.button_settings_dialog.lift()
            return
        idx = self.config_data["buttons"].index(btn_cfg)
        self.button_settings_dialog = ButtonSettingsDialog(self, self.theme, btn_cfg, lambda new_cfg: self._on_edit_button_settings_save(idx, new_cfg), allow_delete=True)
        self.button_settings_dialog.protocol("WM_DELETE_WINDOW", self._on_button_settings_close)

    def _on_edit_button_settings_save(self, idx, new_cfg):
        self.save_edit_button(idx, new_cfg)
        self._on_button_settings_close()

    def save_edit_button(self, idx, new_cfg):
        """Save changes to an existing button or delete it."""
        if new_cfg is None:
            del self.config_data["buttons"][idx]
        else:
            self.config_data["buttons"][idx] = new_cfg
        self.save_config()
        self.refresh_grid()

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = THEMES[self.theme_name]
        self.config_data["theme"] = self.theme_name
        self.save_config()
        self.update_theme()
        self.refresh_grid()

    def update_theme(self):
        """Apply the current theme to the main window and widgets."""
        self.configure(bg=self.theme["bg"])
        self.topbar.config(bg=self.theme["topbar"])
        # Unified styling for all main menu buttons (icon only)
        for btn in [self.add_btn, self.theme_btn, self.settings_btn, self.about_btn, self.pin_btn]:
            btn.config(
                bg=self.theme["topbar"], fg=self.theme["button_fg"],
                activebackground=self.theme["button_hover"], activeforeground=self.theme["button_fg"]
            )
        self.theme_btn.config(text="☀" if self.theme_name=="light" else "🌙")
        self.pin_btn.config(text="📌" if self.always_on_top else "📍")
        Tooltip(self.pin_btn, self._("Keep on top") if self.always_on_top else self._("Do not keep on top"))
        self.grid_frame.config(bg=self.theme["bg"])
        self.grid_canvas.config(bg=self.theme["bg"])

    def load_config(self):
        """Load configuration from the config file, or return defaults if missing/corrupt."""
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"buttons": [], "theme": detect_system_theme()}

    def save_config(self):
        """Save the current configuration to the config file."""
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config_data, f, indent=2)

    def on_close(self):
        """Handle window close event: save config and exit."""
        self.save_config()
        self.destroy()

    def open_settings(self):
        """Open the settings dialog, only one at a time."""
        if self.settings_dialog is not None and self.settings_dialog.winfo_exists():
            self.settings_dialog.lift()
            return
        self.settings_dialog = SettingsDialog(self, self.theme, self.config_data, self.save_settings)
        self.settings_dialog.protocol("WM_DELETE_WINDOW", self._on_settings_close)

    def save_settings(self, new_settings):
        """Save settings from the settings dialog and apply them."""
        self.config_data["panel_size"] = new_settings["panel_size"]
        self.config_data["translucency"] = new_settings["translucency"]
        if "language" in new_settings:
            self.config_data["language"] = new_settings["language"]
        if "volume" in new_settings:
            self.config_data["volume"] = new_settings["volume"]
        self.save_config()
        self.apply_settings()
        self.update_theme()
        self.refresh_grid()

    def apply_settings(self):
        """Apply settings such as button size and translucency."""
        size = self.config_data.get("panel_size", MAX_BTN_SIZE)
        self.attributes("-alpha", self.config_data.get("translucency", 1.0))
        self.refresh_grid()

    def open_about(self):
        """Open the About dialog, only one at a time."""
        if self.about_dialog is not None and self.about_dialog.winfo_exists():
            self.about_dialog.lift()
            return
        self.about_dialog = AboutDialog(self, self.theme)
        self.about_dialog.protocol("WM_DELETE_WINDOW", self._on_about_close)

    def _on_about_close(self):
        self.about_dialog.destroy()
        self.about_dialog = None

    def _on_settings_close(self):
        if self.settings_dialog is not None and self.settings_dialog.winfo_exists():
            self.settings_dialog.destroy()
        self.settings_dialog = None

    def unregister_global_hotkeys(self):
        """Remove all registered global hotkeys."""
        if HAS_KEYBOARD:
            for hotkey in self.global_hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                except Exception:
                    pass
            self.global_hotkeys = []

QuickButtonsApp._ = _

class OutputOverlay(tk.Toplevel):
    """A floating window to show script output and handle input."""
    def __init__(self, master, script_path, args=None):
        super().__init__(master)
        self.title(self._("Script Output"))
        self.geometry("600x320+200+200")
        self.configure(bg=master.theme["bg"])
        self.attributes("-topmost", True)
        self.text = tk.Text(self, bg=master.theme["bg"], fg=master.theme["button_fg"], insertbackground=master.theme["button_fg"], font=("Consolas", 11))
        self.text.pack(fill=tk.BOTH, expand=True)
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(self, textvariable=self.input_var, bg=master.theme["bg"], fg=master.theme["button_fg"], insertbackground=master.theme["button_fg"], font=("Consolas", 11))
        self.input_entry.pack(fill=tk.X, side=tk.BOTTOM)
        self.input_entry.bind("<Return>", self.send_input)
        self.input_entry.pack_forget()
        self.proc = None
        self.waiting_for_input = False
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.run_script(script_path, args or [])

    def run_script(self, script_path, args):
        """Start the script as a subprocess and begin reading output."""
        self.text.delete(1.0, tk.END)
        try:
            self.proc = subprocess.Popen([sys.executable, script_path] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        except Exception as e:
            self.text.insert(tk.END, f"Error: {e}\n")
            return
        self.waiting_for_input = False
        threading.Thread(target=self.read_output, daemon=True).start()
        self.deiconify()
        self.lift()

    def read_output(self):
        """Read output from the script and display it. Show input box if needed."""
        for line in self.proc.stdout:
            self.text.insert(tk.END, line)
            self.text.see(tk.END)
            if line.strip().endswith((':', '?')):
                self.waiting_for_input = True
                self.input_entry.pack(fill=tk.X, side=tk.BOTTOM)
                self.input_entry.focus_set()
        self.proc.wait()
        self.input_entry.pack_forget()
        self.waiting_for_input = False
        self.after(500, self.close)

    def send_input(self, event=None):
        """Send user input to the script's stdin."""
        if self.proc and self.waiting_for_input:
            user_input = self.input_var.get() + '\n'
            try:
                self.proc.stdin.write(user_input)
                self.proc.stdin.flush()
            except Exception:
                pass
            self.input_var.set("")
            self.input_entry.pack_forget()
            self.waiting_for_input = False

    def close(self):
        """Close the overlay and terminate the script if running."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        self.withdraw()

class ButtonSettingsDialog(tk.Toplevel):
    """Dialog for adding/editing a button. Now scrollable and resizable."""
    def __init__(self, master, theme, btn_cfg=None, on_save=None, allow_delete=False):
        super().__init__(master)
        if btn_cfg is None:
            self.title(self.master._("Add New Button"))
        else:
            self.title(self.master._("Edit Button"))
        self.theme = theme
        self.on_save = on_save
        self.btn_cfg = btn_cfg.copy() if btn_cfg else {}
        self.geometry("370x500+300+300")
        self.configure(bg=theme["dialog_bg"])
        self.resizable(True, True)  # Allow resizing
        # --- Scrollable content setup ---
        self.canvas = tk.Canvas(self, bg=theme["dialog_bg"], highlightthickness=0, borderwidth=0)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.content_frame = tk.Frame(self.canvas, bg=theme["dialog_bg"])
        self.content_window = self.canvas.create_window((0,0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_frame.bind("<Configure>", lambda e: self._on_frame_configure())
        self.canvas.bind("<Configure>", lambda e: self._on_canvas_configure())
        self.bind("<Configure>", lambda e: self._on_dialog_resize())
        # --- Variables ---
        self.type_var = tk.StringVar(value=self.btn_cfg.get("type", "script"))
        self.type_var.trace_add("write", lambda *args: self.update_fields())
        self.label_var = tk.StringVar(value=self.btn_cfg.get("label", "Run Script"))
        self.shortcut_var = tk.StringVar(value=self.btn_cfg.get("shortcut", ""))
        self.args_var = tk.StringVar(value=self.btn_cfg.get("args", ""))
        self.script_var = tk.StringVar(value=self.btn_cfg.get("script", ""))
        self.url_var = tk.StringVar(value=self.btn_cfg.get("url", ""))
        self.music_var = tk.StringVar(value=self.btn_cfg.get("music", ""))
        self.icon_var = tk.StringVar(value=self.btn_cfg.get("icon", ""))
        self.bg_color = self.btn_cfg.get("bg_color", theme["button_bg"])
        self.fg_color = self.btn_cfg.get("fg_color", theme["button_fg"])
        self.insert_before_var = tk.StringVar()
        self._init_insert_before_options()
        self.build_ui(allow_delete)
        # Set POST fields if editing
        if btn_cfg:
            self.post_url_entry.delete(0, tk.END)
            self.post_url_entry.insert(0, btn_cfg.get("post_url", ""))
            self._load_headers_from_cfg(btn_cfg.get("post_headers", ""))
            self.post_body_text.delete("1.0", tk.END)
            self.post_body_text.insert("1.0", btn_cfg.get("post_body", ""))
        # Add syntax highlighting to POST body
        self._setup_post_body_highlighting()

    def _init_insert_before_options(self):
        # Build the list of options for the insert before dropdown
        btns = self.master.config_data.get("buttons", [])
        self.insert_before_options = []
        for idx, btn in enumerate(btns):
            label = btn.get("label", f"Button {idx+1}")
            self.insert_before_options.append(f"{idx+1}. {label}")
        self.insert_before_options.append(self.master._("At end"))
        # Default: at end for add, current position for edit
        if self.btn_cfg and self.btn_cfg in btns:
            idx = btns.index(self.btn_cfg)
            self.insert_before_var.set(self.insert_before_options[idx])
        else:
            self.insert_before_var.set(self.master._("At end"))

    def build_ui(self, allow_delete):
        f = self.content_frame
        # Button Label (text or emoji) - first
        tk.Label(f, text=self.master._("Button Label (text or emoji):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        label_frame = tk.Frame(f, bg=self.theme["dialog_bg"])
        label_frame.pack(padx=10, fill=tk.X)
        label_entry = tk.Entry(label_frame, textvariable=self.label_var)
        label_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if not self.label_var.get():
            label_entry.insert(0, "😀 Example or text")
        emoji_btn = tk.Button(label_frame, text="😊", width=2, command=lambda: self.open_emoji_picker(label_entry), bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        emoji_btn.pack(side=tk.LEFT, padx=(4,0))
        Tooltip(emoji_btn, self.master._("Pick emoji"))
        # Icon Path - second
        tk.Label(f, text=self.master._("Icon Path:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        icon_entry = tk.Entry(f, textvariable=self.icon_var)
        icon_entry.pack(padx=10, fill=tk.X)
        tk.Button(f, text="Browse...", command=self.browse_icon).pack(padx=10, pady=2, anchor="e")
        # Insert before dropdown
        tk.Label(f, text=self.master._("Insert before:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.insert_before_menu = tk.OptionMenu(f, self.insert_before_var, *self.insert_before_options)
        self.insert_before_menu.config(bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], highlightthickness=0)
        self.insert_before_menu.pack(padx=10, fill=tk.X)
        # Shortcut
        tk.Label(f, text=self.master._("Shortcut (e.g. Ctrl+1, Alt+Q, F5):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.shortcut_entry = tk.Entry(f, textvariable=self.shortcut_var, state="readonly")
        self.shortcut_entry.pack(padx=10, fill=tk.X)
        self.shortcut_entry.bind("<FocusIn>", self._on_shortcut_focus_in)
        self.shortcut_entry.bind("<FocusOut>", self._on_shortcut_focus_out)
        # Colors
        tk.Label(f, text=self.master._("Button Background Color:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.bg_btn = tk.Button(f, text=self.bg_color, bg=self.bg_color, fg=self.theme["button_fg"], command=self.pick_bg_color)
        self.bg_btn.pack(padx=10, pady=2, anchor="w")
        tk.Label(f, text=self.master._("Button Text Color:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.fg_btn = tk.Button(f, text=self.fg_color, bg=self.theme["dialog_bg"], fg=self.fg_color, command=self.pick_fg_color)
        self.fg_btn.pack(padx=10, pady=2, anchor="w")
        # --- Button Type and dynamic fields (moved to just above save/delete) ---
        # Container for type and dynamic fields
        self.type_and_dynamic_frame = tk.Frame(f, bg=self.theme["dialog_bg"])
        self.type_and_dynamic_frame.pack(fill=tk.X, padx=0, pady=0)
        # Type selector with translated display names
        tk.Label(self.type_and_dynamic_frame, text=self.master._("Button Type:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.type_code_to_disp = {
            "script": self.master._("Run Script"),
            "website": self.master._("Open Website"),
            "music": self.master._("Play Music"),
            "post": self.master._("POST Request"),
            "shell": self.master._("Run Shell Command")
        }
        self.type_disp_to_code = {v: k for k, v in self.type_code_to_disp.items()}
        self.type_display = tk.StringVar()
        # Set display value based on code
        self.type_display.set(self.type_code_to_disp.get(self.type_var.get(), self.master._("Run Script")))
        type_menu = tk.OptionMenu(self.type_and_dynamic_frame, self.type_display, *self.type_disp_to_code.keys())
        type_menu.config(bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], highlightthickness=0)
        type_menu.pack(padx=10, fill=tk.X)
        # When display value changes, update type_var
        def on_type_display_change(*args):
            code = self.type_disp_to_code.get(self.type_display.get(), "script")
            self.type_var.set(code)
        self.type_display.trace_add("write", on_type_display_change)
        # When type_var changes, update display value (for programmatic changes)
        def on_type_var_change(*args):
            disp = self.type_code_to_disp.get(self.type_var.get(), self.master._("Run Script"))
            if self.type_display.get() != disp:
                self.type_display.set(disp)
        self.type_var.trace_add("write", on_type_var_change)
        # --- Dynamic fields frame directly after type selector ---
        self.dynamic_frame = tk.Frame(self.type_and_dynamic_frame, bg=self.theme["dialog_bg"])
        self.dynamic_frame.pack(fill=tk.X, padx=0, pady=0)
        # Dynamic fields (do not pack yet)
        self.script_label = tk.Label(self.dynamic_frame, text=self.master._("Script Path:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        self.script_entry = tk.Entry(self.dynamic_frame, textvariable=self.script_var)
        self.script_browse = tk.Button(self.dynamic_frame, text="Browse...", command=self.browse_script)
        self.args_label = tk.Label(self.dynamic_frame, text=self.master._("Arguments (wildcards: {date}, {time}, {datetime}):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        self.args_entry = tk.Entry(self.dynamic_frame, textvariable=self.args_var)
        self.url_label = tk.Label(self.dynamic_frame, text=self.master._("Website URL:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        self.url_entry = tk.Entry(self.dynamic_frame, textvariable=self.url_var)
        self.music_label = tk.Label(self.dynamic_frame, text=self.master._("Music File:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        self.music_entry = tk.Entry(self.dynamic_frame, textvariable=self.music_var)
        self.music_browse = tk.Button(self.dynamic_frame, text="Browse...", command=self.browse_music)
        # Shell command field
        self.shell_label = tk.Label(self.dynamic_frame, text=self.master._("Shell Command:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        self.shell_var = tk.StringVar(value=self.btn_cfg.get("shell_cmd", ""))
        self.shell_entry = tk.Entry(self.dynamic_frame, textvariable=self.shell_var)
        # POST Request fields (now created here)
        self.post_url_label = tk.Label(self.dynamic_frame, text=self.master._("POST URL:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        self.post_url_entry = tk.Entry(self.dynamic_frame)
        self.post_headers_label = tk.Label(self.dynamic_frame, text=self.master._("Headers (key: value per line):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        # Dynamic header rows
        self.header_rows = []
        self.headers_frame = tk.Frame(self.dynamic_frame, bg=self.theme["dialog_bg"])
        self.add_header_btn = tk.Button(self.dynamic_frame, text="➕ " + self.master._("Add header"), command=self._add_header_row, bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        self.post_body_label = tk.Label(self.dynamic_frame, text=self.master._("Body (optional):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"])
        self.post_body_text = tk.Text(self.dynamic_frame, height=3, width=30)
        # --- End dynamic fields ---
        # Save/Delete buttons (already at the end)
        btn_frame = tk.Frame(f, bg=self.theme["dialog_bg"])
        btn_frame.pack(pady=12, padx=10, fill=tk.X)
        save_btn = tk.Button(btn_frame, text="💾", command=self.save, bg=self.theme["button_bg"], fg=self.theme["button_fg"], font=("Segoe UI", 12, "bold"), relief=tk.FLAT, height=1, width=2)
        save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipadx=0, ipady=2)
        Tooltip(save_btn, self.master._("Save"))
        if allow_delete:
            del_btn = tk.Button(btn_frame, text="🗑️", command=self.delete, bg="#a33", fg="white", font=("Segoe UI", 12, "bold"), relief=tk.FLAT, height=1, width=2)
            del_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipadx=0, ipady=2, padx=(8,0))
        self.update_fields()

    def _add_header_row(self, key='', value=''):
        row = tk.Frame(self.headers_frame, bg=self.theme["dialog_bg"])
        key_var = tk.StringVar(value=key)
        value_var = tk.StringVar(value=value)
        key_entry = tk.Entry(row, textvariable=key_var, width=12)
        value_entry = tk.Entry(row, textvariable=value_var, width=18)
        remove_btn = tk.Button(row, text="🗑️", command=lambda: self._remove_header_row(row), bg="#a33", fg="white", relief=tk.FLAT, width=2)
        key_entry.pack(side=tk.LEFT, padx=(0,4))
        value_entry.pack(side=tk.LEFT, padx=(0,4))
        remove_btn.pack(side=tk.LEFT)
        row.pack(fill=tk.X, padx=10, pady=2)
        self.header_rows.append((row, key_var, value_var))

    def _remove_header_row(self, row):
        for i, (r, _, _) in enumerate(self.header_rows):
            if r == row:
                r.destroy()
                self.header_rows.pop(i)
                break

    def _load_headers_from_cfg(self, headers_str):
        for r, _, _ in self.header_rows:
            r.destroy()
        self.header_rows.clear()
        for line in headers_str.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                self._add_header_row(k.strip(), v.strip())
        if not self.header_rows:
            self._add_header_row()

    def update_fields(self):
        """Show/hide fields based on button type. Always pack Entry widgets with fill=tk.X and expand=True. Dynamically resize window height to fit content."""
        t = self.type_var.get()
        # Remove all dynamic fields from dynamic_frame
        for w in [self.args_label, self.args_entry, self.script_label, self.script_entry, self.script_browse, self.url_label, self.url_entry, self.music_label, self.music_entry, self.music_browse,
                  self.post_url_label, self.post_url_entry, self.post_headers_label, self.headers_frame, self.add_header_btn, self.post_body_label, self.post_body_text, self.shell_label, self.shell_entry]:
            w.pack_forget()
        if t == "script":
            self.script_label.pack(anchor="w", padx=10, pady=(10,0))
            self.script_entry.pack(padx=10, fill=tk.X, expand=True)
            self.script_browse.pack(padx=10, pady=2, anchor="e")
            self.args_label.pack(anchor="w", padx=10, pady=(10,0))
            self.args_entry.pack(padx=10, fill=tk.X, expand=True)
        elif t == "website":
            self.url_label.pack(anchor="w", padx=10, pady=(10,0))
            self.url_entry.pack(padx=10, fill=tk.X, expand=True)
        elif t == "music":
            self.music_label.pack(anchor="w", padx=10, pady=(10,0))
            self.music_entry.pack(padx=10, fill=tk.X, expand=True)
            self.music_browse.pack(padx=10, pady=2, anchor="e")
        elif t == "post":
            self.post_url_label.pack(anchor="w", padx=10, pady=(10,0))
            self.post_url_entry.pack(padx=10, fill=tk.X, expand=True)
            self.post_headers_label.pack(anchor="w", padx=10, pady=(10,0))
            self.headers_frame.pack(fill=tk.X, padx=0, pady=0)
            self.add_header_btn.pack(padx=10, pady=(0,4), anchor="w")
            self.post_body_label.pack(anchor="w", padx=10, pady=(10,0))
            self.post_body_text.pack(padx=10, fill=tk.X, expand=True)
            if not self.header_rows:
                self._add_header_row()
        elif t == "shell":
            self.shell_label.pack(anchor="w", padx=10, pady=(10,0))
            self.shell_entry.pack(padx=10, fill=tk.X, expand=True)
        # Dynamically resize window height to fit content
        self.update_idletasks()
        w = self.winfo_width()
        h = self.content_frame.winfo_reqheight() + 20  # Add a little padding
        self.geometry(f"{w}x{h}")

    def _on_frame_configure(self):
        # Update scrollregion to fit content
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self):
        # Make the frame width match the canvas width
        self.canvas.itemconfig(self.content_window, width=self.canvas.winfo_width())

    def _on_dialog_resize(self):
        # When dialog is resized, update canvas/frame width
        self._on_canvas_configure()

    def _on_shortcut_focus_in(self, event):
        self.shortcut_entry.config(state="normal")
        self.shortcut_entry.delete(0, tk.END)
        self.shortcut_entry.insert(0, self.master._("Press shortcut..."))
        self.shortcut_entry.bind('<Key>', self._capture_shortcut)

    def _on_shortcut_focus_out(self, event):
        self.shortcut_entry.unbind('<Key>')
        # Restore previous value if not a valid shortcut
        val = self.shortcut_var.get()
        if not self._is_valid_shortcut(val):
            self.shortcut_entry.delete(0, tk.END)
            self.shortcut_entry.insert(0, val)
        self.shortcut_entry.config(state="readonly")

    def _capture_shortcut(self, event):
        mods = []
        if event.state & 0x4: mods.append('Ctrl')
        if event.state & 0x1: mods.append('Shift')
        if event.state & 0x20000: mods.append('Alt')
        key = event.keysym
        if key in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            return  # Ignore pure modifier
        if not mods:
            self.shortcut_entry.delete(0, tk.END)
            self.shortcut_entry.insert(0, self.master._("Shortcut must include Ctrl, Alt, or Shift"))
            return
        shortcut = '+'.join(mods + [key])
        self.shortcut_var.set(shortcut)
        self.shortcut_entry.delete(0, tk.END)
        self.shortcut_entry.insert(0, shortcut)
        self.shortcut_entry.unbind('<Key>')
        self.shortcut_entry.config(state="readonly")
        self.focus()  # Move focus away

    def _is_valid_shortcut(self, shortcut):
        # Must have at least one modifier and a key
        if not shortcut or shortcut == self.master._("Press shortcut..."):
            return True  # Allow empty (no shortcut)
        parts = shortcut.split('+')
        if len(parts) < 2:
            return False
        mods = {'Ctrl', 'Alt', 'Shift'}
        return any(m in mods for m in parts[:-1]) and parts[-1]

    def browse_script(self):
        """Open file dialog to select a Python script."""
        file_path = filedialog.askopenfilename(title="Select Python Script", filetypes=[("Python Files", "*.py")])
        if file_path:
            self.script_var.set(file_path)
    def browse_music(self):
        """Open file dialog to select a music file."""
        file_path = filedialog.askopenfilename(title="Select Music File", filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")])
        if file_path:
            self.music_var.set(file_path)
    def browse_icon(self):
        """Open file dialog to select an icon image."""
        file_path = filedialog.askopenfilename(title="Select Icon", filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")])
        if file_path:
            self.icon_var.set(file_path)
    def pick_bg_color(self):
        """Open color chooser for button background color."""
        color = colorchooser.askcolor(title="Choose background color", initialcolor=self.bg_color)[1]
        if color:
            self.bg_color = color
            self.bg_btn.config(bg=color, text=color)
    def pick_fg_color(self):
        """Open color chooser for button text color."""
        color = colorchooser.askcolor(title="Choose text color", initialcolor=self.fg_color)[1]
        if color:
            self.fg_color = color
            self.fg_btn.config(fg=color, text=color)
    def save(self):
        """Save the button configuration and close the dialog."""
        # Validate shortcut
        if not self._is_valid_shortcut(self.shortcut_var.get()):
            messagebox.showerror(self.master._("Invalid Shortcut"), self.master._("Shortcut must include Ctrl, Alt, or Shift and a key."))
            return
        # Collect headers from header_rows
        headers_str = ''
        if self.type_var.get() == "post":
            for _, key_var, value_var in self.header_rows:
                k = key_var.get().strip()
                v = value_var.get().strip()
                if k:
                    headers_str += f"{k}: {v}\n"
            headers_str = headers_str.strip()
        cfg = {
            "type": self.type_var.get(),
            "label": self.label_var.get(),
            "shortcut": self.shortcut_var.get(),
            "args": self.args_var.get(),
            "script": self.script_var.get(),
            "url": self.url_var.get(),
            "music": self.music_var.get(),
            "icon": self.icon_var.get(),
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "post_url": self.post_url_entry.get() if self.type_var.get() == "post" else "",
            "post_headers": headers_str if self.type_var.get() == "post" else "",
            "post_body": self.post_body_text.get("1.0", tk.END).strip() if self.type_var.get() == "post" else "",
            "shell_cmd": self.shell_var.get() if self.type_var.get() == "shell" else ""
        }
        # Determine insert position
        btns = self.master.config_data.get("buttons", [])
        insert_idx = len(btns)  # default: at end
        selected = self.insert_before_var.get()
        if selected != self.master._("At end"):
            for idx, opt in enumerate(self.insert_before_options):
                if opt == selected:
                    insert_idx = idx
                    break
        if self.btn_cfg and self.btn_cfg in btns:
            # Editing: move to new position if changed
            old_idx = btns.index(self.btn_cfg)
            if old_idx != insert_idx:
                btns.pop(old_idx)
                if insert_idx > old_idx:
                    insert_idx -= 1
            btns.insert(insert_idx, cfg)
            self.master.config_data["buttons"] = btns
            self.master.save_config()
            self.master.refresh_grid()
        else:
            # Adding: insert at position
            btns.insert(insert_idx, cfg)
            self.master.config_data["buttons"] = btns
            self.master.save_config()
            self.master.refresh_grid()
        if self.on_save:
            self.on_save(cfg)
        self.destroy()

    def delete(self):
        """Delete the button (send None to on_save) and close the dialog."""
        if self.on_save:
            self.on_save(None)
        self.destroy()

    def _setup_post_body_highlighting(self):
        # Only bind if the widget exists
        if hasattr(self, 'post_body_text'):
            self._highlight_json(self.post_body_text)
            self.post_body_text.bind('<KeyRelease>', lambda e: self._highlight_json(self.post_body_text))

    def _highlight_json(self, text_widget):
        # Remove previous tags
        for tag in text_widget.tag_names():
            text_widget.tag_remove(tag, "1.0", tk.END)
        # Define regex patterns
        patterns = [
            (r'"(\\.|[^"\\])*"\s*:', 'key'),      # JSON keys
            (r'"(\\.|[^"\\])*"', 'string'),        # JSON strings
            (r'\b\d+\b', 'number'),                    # Numbers
            (r'\btrue\b|\bfalse\b', 'boolean'),       # Booleans
            (r'\bnull\b', 'null'),                      # Null
            (r'[{}\[\],:]', 'punct'),                   # Punctuation
        ]
        content = text_widget.get("1.0", tk.END)
        for pattern, tag in patterns:
            for match in re.finditer(pattern, content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                text_widget.tag_add(tag, start, end)
        # Tag configurations (colors)
        text_widget.tag_config('key', foreground='#007acc')
        text_widget.tag_config('string', foreground='#a31515')
        text_widget.tag_config('number', foreground='#098658')
        text_widget.tag_config('boolean', foreground='#795e26')
        text_widget.tag_config('null', foreground='#795e26', font=('TkDefaultFont', 9, 'italic'))
        text_widget.tag_config('punct', foreground='#000000')

    def open_emoji_picker(self, entry_widget):
        # List of relevant emojis for this app
        emojis = [
            "🖥️", "🌐", "🎵", "📤", "⚡", "🔗", "📝", "🔊", "⭐", "❓", "✅", "❌", "🕒", "📅", "🔒", "🔓"
        ]
        picker = tk.Toplevel(self)
        picker.title(self.master._("Pick an emoji"))
        picker.transient(self)
        picker.resizable(False, False)
        picker.configure(bg=self.theme["dialog_bg"])
        # Place near the entry
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        picker.geometry(f"+{x}+{y}")
        # Emoji grid
        frame = tk.Frame(picker, bg=self.theme["dialog_bg"])
        frame.pack(padx=8, pady=8)
        cols = 5
        for i, emoji in enumerate(emojis):
            btn = tk.Button(frame, text=emoji, font=("Segoe UI Emoji", 16), width=2, height=1, relief=tk.FLAT, bg=self.theme["button_bg"], fg=self.theme["button_fg"], command=lambda e=emoji: self._insert_emoji(entry_widget, e, picker))
            btn.grid(row=i//cols, column=i%cols, padx=2, pady=2)
        # Close on focus out
        picker.bind("<FocusOut>", lambda e: picker.destroy())
        picker.grab_set()

    def _insert_emoji(self, entry_widget, emoji, picker):
        entry_widget.insert(entry_widget.index(tk.INSERT), emoji)
        picker.destroy()

class SettingsDialog(tk.Toplevel):
    """Dialog for application settings (button size, translucency, language, volume)."""
    def __init__(self, master, theme, config, on_save):
        super().__init__(master)
        self.title(master._("Settings"))
        self.theme = theme
        self.on_save = on_save
        self.geometry("340x320+350+350")
        self.configure(bg=theme["dialog_bg"])
        self.resizable(False, False)
        self.panel_size = tk.IntVar(value=config.get("panel_size", MAX_BTN_SIZE))
        self.translucency = tk.DoubleVar(value=config.get("translucency", 1.0))
        self.language = tk.StringVar(value=config.get("language", "en"))
        self.volume = tk.IntVar(value=config.get("volume", 100))
        tk.Label(self, text=master._("Button Size (px):"), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        tk.Scale(self, from_=MIN_BTN_SIZE, to=MAX_BTN_SIZE, orient=tk.HORIZONTAL, variable=self.panel_size, bg=theme["dialog_bg"], fg=theme["label_fg"], highlightthickness=0).pack(fill=tk.X, padx=10)
        tk.Label(self, text=master._("Translucency:"), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        tk.Scale(self, from_=0.5, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.translucency, bg=theme["dialog_bg"], fg=theme["label_fg"], highlightthickness=0).pack(fill=tk.X, padx=10)
        # Volume slider
        tk.Label(self, text=master._("Volume:"), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume, bg=theme["dialog_bg"], fg=theme["label_fg"], highlightthickness=0).pack(fill=tk.X, padx=10)
        # Language selector with proper names
        tk.Label(self, text=master._("Language:"), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.language_map = {
            master._("English"): "en",
            master._("Dutch"): "nl"
        }
        self.language_display = tk.StringVar()
        # Set display value based on code
        for disp, code in self.language_map.items():
            if code == self.language.get():
                self.language_display.set(disp)
                break
        lang_menu = tk.OptionMenu(self, self.language_display, *self.language_map.keys())
        lang_menu.config(bg=theme["dialog_bg"], fg=theme["label_fg"], highlightthickness=0)
        lang_menu.pack(padx=10, fill=tk.X)
        save_btn = tk.Button(self, text="💾", command=self.save, bg=theme["button_bg"], fg=theme["button_fg"], font=("Segoe UI", 12, "bold"), relief=tk.FLAT, height=2)
        save_btn.pack(pady=12, ipadx=0, ipady=4)
        Tooltip(save_btn, master._("Save"))

    def save(self):
        # Convert display value back to code
        lang_code = self.language_map.get(self.language_display.get(), "en")
        self.on_save({
            "panel_size": self.panel_size.get(),
            "translucency": self.translucency.get(),
            "language": lang_code,
            "volume": self.volume.get()
        })
        self.destroy()

class AboutDialog(tk.Toplevel):
    """About dialog with author and link."""
    def __init__(self, master, theme):
        super().__init__(master)
        self.title(self.master._("About QuickButtons"))
        self.geometry("340x240+350+350")
        self.configure(bg=theme["dialog_bg"])
        self.resizable(False, False)
        tk.Label(self, text="QuickButtons", font=("Segoe UI", 16, "bold"), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack(pady=(18,4))
        tk.Label(self, text=self.master._("Version: {version}").format(version=APP_VERSION), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack()
        tk.Label(self, text=self.master._("A modern floating button panel for scripts."), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack()
        tk.Label(self, text=self.master._("Made by Rik Heijmann"), bg=theme["dialog_bg"], fg=theme["label_fg"]).pack(pady=(10,0))
        link = tk.Label(self, text="https://Rik.blue", fg="#4a90e2", bg=theme["dialog_bg"], cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: self.open_link())
        close_btn = tk.Button(self, text="✖", command=self.destroy, bg=theme["button_bg"], fg=theme["button_fg"], relief=tk.FLAT)
        close_btn.pack(side=tk.BOTTOM, pady=16)
        Tooltip(close_btn, self.master._("Close"))

    def open_link(self):
        """Open the author's website in a browser."""
        import webbrowser
        webbrowser.open("https://Rik.blue")

class Tooltip:
    """A simple tooltip for Tkinter widgets."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 20
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#222", fg="white", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 10, "normal"))
        label.pack(ipadx=4, ipady=2)
    def hide(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def main():
    parser = argparse.ArgumentParser(description="QuickButtons - Floating button panel for scripts, websites, music, and POST requests.")
    parser.add_argument('-c', '--config', type=str, default="config.json", help="Path to configuration file (default: config.json)")
    args = parser.parse_args()
    global CONFIG_FILE
    CONFIG_FILE = args.config
    try:
        app = QuickButtonsApp()
        app.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Fatal Error", str(e))

if __name__ == "__main__":
    main() 