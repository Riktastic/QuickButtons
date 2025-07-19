"""Settings dialog for QuickButtons application."""

import tkinter as tk
from tkinter import filedialog
import sys

from src.ui.components.tooltip import Tooltip
from src.ui.themes import apply_theme_recursive
from src.utils.logger import logger


class SettingsDialog(tk.Toplevel):
    """Dialog for editing global app settings."""
    
    def __init__(self, master, theme, config_data, on_save):
        super().__init__(master)
        self.title(master._("Settings"))
        self.theme = theme
        self.on_save = on_save
        self.config_data = config_data.copy()
        self.geometry("450x600+300+300")
        self.configure(bg=theme["dialog_bg"])
        self.resizable(True, True)
        
        # Set window icon
        try:
            from src.core.constants import ICON_ICO_PATH
            self.iconbitmap(ICON_ICO_PATH)
        except Exception as e:
            logger.warning(f"Could not set settings dialog icon: {e}")
        
        # --- Variables ---
        self.translucency_var = tk.DoubleVar(value=self.config_data.get("translucency", 1.0))
        self.language_var = tk.StringVar(value=self.config_data.get("language", "en"))
        self.volume_var = tk.DoubleVar(value=self.config_data.get("volume", 1.0))
        self.min_btn_width_var = tk.IntVar(value=self.config_data.get("min_btn_width", 80))
        self.max_btn_width_var = tk.IntVar(value=self.config_data.get("max_btn_width", 220))
        self.min_btn_height_var = tk.IntVar(value=self.config_data.get("min_btn_height", 40))
        self.max_btn_height_var = tk.IntVar(value=self.config_data.get("max_btn_height", 110))
        self.timer_sound_var = tk.StringVar(value=self.config_data.get("timer_sound", ""))
        self.minimal_mode_var = tk.BooleanVar(value=self.config_data.get("minimal_mode", False))
        self.log_level_var = tk.StringVar(value=self.config_data.get("log_level", "WARNING"))
        self.python_executable_var = tk.StringVar(value=self.config_data.get("python_executable", ""))
        
        # Animation settings
        self.animation_enabled_var = tk.BooleanVar(value=self.config_data.get("animation_enabled", True))
        # Initialize with the code, will be converted to display name in build_ui
        self.animation_type_var = tk.StringVar(value=self.config_data.get("default_animation_type", "ripple"))
        
        # --- Scrollable content setup ---
        # Create main container frame for layout
        main_container = tk.Frame(self, bg=theme["dialog_bg"])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable area
        scroll_container = tk.Frame(main_container, bg=theme["dialog_bg"])
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(scroll_container, bg=theme["dialog_bg"], highlightthickness=0, borderwidth=0)
        self.scrollbar = tk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=self.canvas.yview, width=16,
                                     relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        self.content_frame = tk.Frame(self.canvas, bg=theme["dialog_bg"])
        self.content_window = self.canvas.create_window((0,0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar - scrollbar is always visible
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Force scrollbar to be always visible
        self.scrollbar.pack_propagate(False)
        
        # Set initial scrollregion to ensure scrollbar is visible
        self.canvas.configure(scrollregion=(0, 0, 0, 1000))
        
        # Create fixed bottom frame for action buttons (outside scrollable area)
        self.bottom_frame = tk.Frame(main_container, bg=theme["dialog_bg"])
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Add separator line above bottom buttons
        separator = tk.Frame(self.bottom_frame, height=1, bg=theme.get("border_color", "#444444"))
        separator.pack(fill=tk.X, pady=(0, 8))
        
        self.content_frame.bind("<Configure>", lambda e: self._on_frame_configure())
        self.canvas.bind("<Configure>", lambda e: self._on_canvas_configure())
        self.bind("<Configure>", lambda e: self._on_dialog_resize())
        
        # Add mouse wheel scrolling support
        self._bind_mousewheel()
        
        # Force scrollbar to be visible
        self.after(100, self._ensure_scrollbar_visible)
        
        self.build_ui()
        
        self.grab_set()
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())
        self.apply_theme(theme)

    def _on_frame_configure(self):
        # Update scrollregion to fit content
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self):
        # Make the frame width match the canvas width
        self.canvas.itemconfig(self.content_window, width=self.canvas.winfo_width())

    def _on_dialog_resize(self):
        # When dialog is resized, update canvas/frame width
        self._on_canvas_configure()

    def _bind_mousewheel(self):
        """Bind mouse wheel events for scrolling."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        # Bind when mouse enters the canvas area
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)

    def _ensure_scrollbar_visible(self):
        """Ensure the scrollbar is always visible."""
        try:
            # Force the scrollbar to be visible by updating the scrollregion
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)
            
            # Make sure scrollbar is packed and visible
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.scrollbar.lift()  # Bring to front
            
        except Exception as e:
            logger.error(f"Error ensuring scrollbar visibility: {e}")

    def browse_timer_sound(self):
        """Open file dialog to select a timer sound file."""
        filename = filedialog.askopenfilename(
            title=self.master._("Select Timer Sound"),
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.ogg *.m4a"),
                ("MP3 files", "*.mp3"),
                ("WAV files", "*.wav"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.timer_sound_var.set(filename)

    def browse_python_executable(self):
        """Open file dialog to select a Python executable."""
        filename = filedialog.askopenfilename(
            title=self.master._("Select Python Executable"),
            filetypes=[
                ("Python executables", "python.exe python3.exe python"),
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.python_executable_var.set(filename)

    def auto_detect_python(self):
        """Auto-detect and set the Python executable."""
        try:
            from src.utils.system import detect_python_executable
            detected_python = detect_python_executable()
            if detected_python:
                self.python_executable_var.set(detected_python)
                logger.info(f"Auto-detected Python executable: {detected_python}")
            else:
                logger.warning("Could not auto-detect Python executable")
        except Exception as e:
            logger.error(f"Error auto-detecting Python executable: {e}")

    def build_ui(self):
        f = self.content_frame
        
        # --- Appearance Group ---
        appearance_group = tk.LabelFrame(f, text=self.master._("Appearance"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        appearance_group.pack(fill=tk.X, padx=8, pady=(10, 16))
        
        # Translucency
        tk.Label(appearance_group, text=self.master._("Translucency:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        translucency_scale = tk.Scale(appearance_group, from_=0.5, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, 
                                    variable=self.translucency_var, bg=self.theme["dialog_bg"], fg=self.theme["button_fg"], 
                                    highlightthickness=0, length=300)
        translucency_scale.pack(padx=10, fill=tk.X, pady=(0, 12))
        
        # Language
        tk.Label(appearance_group, text=self.master._("Language:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(0,0))
        lang_frame = tk.Frame(appearance_group, bg=self.theme["dialog_bg"])
        lang_frame.pack(padx=10, fill=tk.X, pady=(0, 12))
        
        # Create language options with translated names
        lang_options = [
            ("en", self.master._("English")),
            ("nl", self.master._("Dutch"))
        ]
        lang_menu = tk.OptionMenu(lang_frame, self.language_var, *[opt[1] for opt in lang_options])
        lang_menu.config(bg=self.theme["button_bg"], fg=self.theme["button_fg"], highlightthickness=0)
        lang_menu.pack(side=tk.LEFT)
        
        # Set the display value based on current language
        current_lang = self.language_var.get()
        for code, display in lang_options:
            if code == current_lang:
                self.language_var.set(display)
                break
        
        # Store mapping for save function
        self.lang_display_to_code = {display: code for code, display in lang_options}
        
        # --- Audio Group ---
        audio_group = tk.LabelFrame(f, text=self.master._("Audio"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        audio_group.pack(fill=tk.X, padx=8, pady=(0, 16))
        
        # Volume
        tk.Label(audio_group, text=self.master._("Volume:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        volume_scale = tk.Scale(audio_group, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, 
                              variable=self.volume_var, bg=self.theme["dialog_bg"], fg=self.theme["button_fg"], 
                              highlightthickness=0, length=300)
        volume_scale.pack(padx=10, fill=tk.X, pady=(0, 12))
        
        # Timer sound
        tk.Label(audio_group, text=self.master._("Timer Sound (optional):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(0,0))
        timer_sound_frame = tk.Frame(audio_group, bg=self.theme["dialog_bg"])
        timer_sound_frame.pack(padx=10, fill=tk.X, pady=(0, 12))
        timer_sound_entry = tk.Entry(timer_sound_frame, textvariable=self.timer_sound_var)
        timer_sound_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_sound_btn = tk.Button(timer_sound_frame, text=self.master._("Browse..."), command=self.browse_timer_sound, 
                                   bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        browse_sound_btn.pack(side=tk.LEFT, padx=(4,0))
        clear_sound_btn = tk.Button(timer_sound_frame, text="🗑️", command=lambda: self.timer_sound_var.set(""), 
                                  bg="#a33", fg="white", relief=tk.FLAT)
        clear_sound_btn.pack(side=tk.LEFT, padx=(4,0))
        Tooltip(browse_sound_btn, self.master._("Browse for timer sound file"))
        Tooltip(clear_sound_btn, self.master._("Clear timer sound"))
        
        # --- Button Sizing Group ---
        sizing_group = tk.LabelFrame(f, text=self.master._("Button Sizing"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        sizing_group.pack(fill=tk.X, padx=8, pady=(0, 16))
        
        # Width settings
        width_frame = tk.Frame(sizing_group, bg=self.theme["dialog_bg"])
        width_frame.pack(padx=10, fill=tk.X, pady=(10,0))
        
        tk.Label(width_frame, text=self.master._("Min Width:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(side=tk.LEFT)
        min_width_entry = tk.Entry(width_frame, textvariable=self.min_btn_width_var, width=8, 
                                 bg=self.theme["button_bg"], fg=self.theme["button_fg"])
        min_width_entry.pack(side=tk.LEFT, padx=(8, 16))
        
        tk.Label(width_frame, text=self.master._("Max Width:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(side=tk.LEFT)
        max_width_entry = tk.Entry(width_frame, textvariable=self.max_btn_width_var, width=8, 
                                 bg=self.theme["button_bg"], fg=self.theme["button_fg"])
        max_width_entry.pack(side=tk.LEFT, padx=(8, 0))
        
        # Height settings
        height_frame = tk.Frame(sizing_group, bg=self.theme["dialog_bg"])
        height_frame.pack(padx=10, fill=tk.X, pady=(8, 12))
        
        tk.Label(height_frame, text=self.master._("Min Height:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(side=tk.LEFT)
        min_height_entry = tk.Entry(height_frame, textvariable=self.min_btn_height_var, width=8, 
                                  bg=self.theme["button_bg"], fg=self.theme["button_fg"])
        min_height_entry.pack(side=tk.LEFT, padx=(8, 16))
        
        tk.Label(height_frame, text=self.master._("Max Height:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(side=tk.LEFT)
        max_height_entry = tk.Entry(height_frame, textvariable=self.max_btn_height_var, width=8, 
                                  bg=self.theme["button_bg"], fg=self.theme["button_fg"])
        max_height_entry.pack(side=tk.LEFT, padx=(8, 0))
        
        # --- Behavior Group ---
        behavior_group = tk.LabelFrame(f, text=self.master._("Behavior"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        behavior_group.pack(fill=tk.X, padx=8, pady=(0, 16))
        
        # Minimal mode checkbox
        minimal_cb = tk.Checkbutton(behavior_group, text=self.master._("Minimal mode (hide titlebar)"), 
                                  variable=self.minimal_mode_var, bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], 
                                  selectcolor=self.theme["dialog_bg"], activebackground=self.theme["dialog_bg"], 
                                  activeforeground=self.theme["label_fg"])
        minimal_cb.pack(anchor="w", padx=10, pady=(10, 8))
        
        # Logging level
        tk.Label(behavior_group, text=self.master._("Logging Level:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(8,0))
        log_level_frame = tk.Frame(behavior_group, bg=self.theme["dialog_bg"])
        log_level_frame.pack(padx=10, fill=tk.X, pady=(0, 12))
        log_level_menu = tk.OptionMenu(log_level_frame, self.log_level_var, "ERROR", "WARNING", "INFO", "DEBUG")
        log_level_menu.config(bg=self.theme["button_bg"], fg=self.theme["button_fg"], highlightthickness=0)
        log_level_menu.pack(side=tk.LEFT)
        Tooltip(log_level_menu, self.master._("Set the minimum logging level. ERROR=only errors, WARNING=errors and warnings, INFO=informational messages, DEBUG=detailed debugging info"))
        
        # Python executable
        tk.Label(behavior_group, text=self.master._("Python Executable (for script execution):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(8,0))
        python_frame = tk.Frame(behavior_group, bg=self.theme["dialog_bg"])
        python_frame.pack(padx=10, fill=tk.X, pady=(0, 12))
        python_entry = tk.Entry(python_frame, textvariable=self.python_executable_var)
        python_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        auto_detect_btn = tk.Button(python_frame, text=self.master._("Auto"), command=self.auto_detect_python, 
                                  bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        auto_detect_btn.pack(side=tk.LEFT, padx=(4,0))
        browse_python_btn = tk.Button(python_frame, text=self.master._("Browse..."), command=self.browse_python_executable, 
                                    bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        browse_python_btn.pack(side=tk.LEFT, padx=(4,0))
        clear_python_btn = tk.Button(python_frame, text="🗑️", command=lambda: self.python_executable_var.set(""), 
                                   bg="#a33", fg="white", relief=tk.FLAT)
        clear_python_btn.pack(side=tk.LEFT, padx=(4,0))
        Tooltip(auto_detect_btn, self.master._("Auto-detect Python executable"))
        Tooltip(browse_python_btn, self.master._("Browse for Python executable"))
        Tooltip(clear_python_btn, self.master._("Clear Python executable (use auto-detection)"))
        
        # --- Animations Group ---
        animations_group = tk.LabelFrame(f, text=self.master._("Button Animations"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        animations_group.pack(fill=tk.X, padx=8, pady=(0, 16))
        
        # Enable animations checkbox
        animation_enabled_cb = tk.Checkbutton(animations_group, text=self.master._("Enable button press animations"), 
                                            variable=self.animation_enabled_var, bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], 
                                            selectcolor=self.theme["dialog_bg"], activebackground=self.theme["dialog_bg"], 
                                            activeforeground=self.theme["label_fg"])
        animation_enabled_cb.pack(anchor="w", padx=10, pady=(10, 8))
        
        # Animation type selection
        tk.Label(animations_group, text=self.master._("Animation Type:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(8,0))
        animation_frame = tk.Frame(animations_group, bg=self.theme["dialog_bg"])
        animation_frame.pack(padx=10, fill=tk.X, pady=(0, 12))
        
        # Create animation options with translated names
        animation_options = [
            ("ripple", self.master._("Ripple Effect")),
            ("scale", self.master._("Scale Down")),
            ("glow", self.master._("Glow Effect")),
            ("bounce", self.master._("Bounce")),
            ("shake", self.master._("Shake")),
            ("flame", self.master._("Flame Burst")),
            ("confetti", self.master._("Confetti Burst")),
            ("sparkle", self.master._("Sparkle Effect")),
            ("explosion", self.master._("Explosion")),
            ("combined", self.master._("Combined (Scale + Glow)"))
        ]
        animation_menu = tk.OptionMenu(animation_frame, self.animation_type_var, *[opt[1] for opt in animation_options])
        animation_menu.config(bg=self.theme["button_bg"], fg=self.theme["button_fg"], highlightthickness=0)
        animation_menu.pack(side=tk.LEFT)
        
        # Store mapping for save function
        self.animation_display_to_code = {display: code for code, display in animation_options}
        
        # Set the display value based on current animation type
        current_animation = self.animation_type_var.get()
        logger.debug(f"Initial animation type: '{current_animation}'")
        logger.debug(f"Animation mappings: {self.animation_display_to_code}")
        
        # Find the display name for the current code
        for code, display in animation_options:
            if code == current_animation:
                self.animation_type_var.set(display)
                logger.debug(f"Set animation display to: '{display}'")
                break
        else:
            # If not found, use default
            logger.warning(f"Animation type '{current_animation}' not found in options, using default")
            self.animation_type_var.set(self.master._("Ripple Effect"))
        
        # Animation preview button
        def preview_clicked():
            logger.debug("Preview button clicked!")
            try:
                self.preview_animation()
                logger.debug("Preview animation function completed")
            except Exception as e:
                logger.error(f"Preview button error: {e}")
                import traceback
                traceback.print_exc()
        
        preview_btn = tk.Button(animation_frame, text=self.master._("Preview"), command=preview_clicked,
                              bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        preview_btn.pack(side=tk.LEFT, padx=(8, 0))
        Tooltip(preview_btn, self.master._("Preview the selected animation"))
        
        # Create the fixed bottom buttons after UI is built
        self._create_bottom_buttons()

    def preview_animation(self):
        """Preview the selected animation on a test button."""
        logger.debug("preview_animation function called")
        try:
            from src.utils.animations import animate_button_press
            logger.debug("Successfully imported animate_button_press")
            
            # Get animation type code and display name
            animation_display = self.animation_type_var.get()
            animation_code = self.animation_display_to_code.get(animation_display, "ripple")
            
            logger.debug(f"Preview animation called - display: '{animation_display}', code: '{animation_code}'")
            logger.debug(f"Available mappings: {self.animation_display_to_code}")
            
            # Create a preview window
            preview_window = tk.Toplevel(self)
            preview_window.title(animation_display)
            preview_window.geometry("280x200")
            preview_window.configure(bg=self.theme["bg"])
            preview_window.transient(self)
            preview_window.grab_set()
            preview_window.resizable(False, False)
            
            # Set window icon
            try:
                from src.core.constants import ICON_ICO_PATH
                preview_window.iconbitmap(ICON_ICO_PATH)
            except Exception as e:
                logger.warning(f"Could not set preview window icon: {e}")
            
            # Keep window border and ensure it's on top
            preview_window.attributes('-topmost', True)
            
            # Center the window
            preview_window.update_idletasks()
            x = (preview_window.winfo_screenwidth() // 2) - (280 // 2)
            y = (preview_window.winfo_screenheight() // 2) - (200 // 2)
            preview_window.geometry(f"280x200+{x}+{y}")
            
            # Create main container
            main_frame = tk.Frame(preview_window, bg=self.theme["bg"])
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Animation button with the animation name
            test_button = tk.Button(main_frame, text=animation_display, 
                                  bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                                  font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
                                  width=15, height=2)
            test_button.pack(expand=True)
            
            # Store original background for hover effects
            test_button.orig_bg = test_button.cget("bg")
            
            # Add hover effects
            def on_enter(event):
                test_button.config(bg=self.theme.get("button_hover", test_button.orig_bg))
            
            def on_leave(event):
                test_button.config(bg=test_button.orig_bg)
            
            test_button.bind("<Enter>", on_enter)
            test_button.bind("<Leave>", on_leave)
            
            # Button frame for restart and close
            button_frame = tk.Frame(main_frame, bg=self.theme["bg"])
            button_frame.pack(pady=(15, 0))
            
            def trigger_animation():
                """Trigger the animation."""
                # Use center of button for ripple effect
                center_x = test_button.winfo_width() // 2
                center_y = test_button.winfo_height() // 2
                animate_button_press(test_button, center_x, center_y, animation_type=animation_code)
            
            # Restart button
            restart_btn = tk.Button(button_frame, text="🔄", command=trigger_animation,
                                  bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                                  font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
                                  width=3, height=1)
            restart_btn.pack(side=tk.LEFT, padx=(0, 8))
            
            # Close button
            close_btn = tk.Button(button_frame, text="✕", command=preview_window.destroy,
                                bg=self.theme["button_bg"], fg=self.theme["button_fg"],
                                font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
                                width=3, height=1)
            close_btn.pack(side=tk.LEFT)
            
            # Trigger animation immediately
            preview_window.after(100, trigger_animation)
            
        except Exception as e:
            logger.warning(f"Animation preview failed: {e}")
            import traceback
            traceback.print_exc()

    def _create_bottom_buttons(self):
        """Create the fixed bottom action buttons (Save, Close)."""
        # --- Save/Close buttons ---
        btn_frame = tk.Frame(self.bottom_frame, bg=self.theme["dialog_bg"])
        btn_frame.pack(pady=(0, 5), padx=10, fill=tk.X)
        
        # Save button with disk icon
        save_btn = tk.Button(btn_frame, text="💾 Save", command=self.save, 
                           bg=self.theme["button_bg"], fg=self.theme["button_fg"], 
                           font=("Segoe UI", 10, "bold"), relief=tk.FLAT, height=1)
        save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipadx=5, ipady=3)
        Tooltip(save_btn, self.master._("Save settings and apply changes"))
        
        # Close button
        close_btn = tk.Button(btn_frame, text="❌ Close", command=self.destroy, 
                            bg=self.theme["button_bg"], fg=self.theme["button_fg"], 
                            font=("Segoe UI", 10, "bold"), relief=tk.FLAT, height=1)
        close_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipadx=5, ipady=3, padx=(8,0))
        Tooltip(close_btn, self.master._("Close without saving"))

    def save(self):
        # Convert language display name back to code
        language_display = self.language_var.get()
        language_code = self.lang_display_to_code.get(language_display, "en")
        
        # Convert animation display name back to code
        animation_display = self.animation_type_var.get()
        animation_code = self.animation_display_to_code.get(animation_display, "ripple")
        
        logger.debug(f"Settings save - animation display: '{animation_display}', code: '{animation_code}'")
        logger.debug(f"Animation mappings: {self.animation_display_to_code}")
        
        new_settings = {
            "translucency": self.translucency_var.get(),
            "language": language_code,
            "volume": self.volume_var.get(),
            "min_btn_width": self.min_btn_width_var.get(),
            "max_btn_width": self.max_btn_width_var.get(),
            "min_btn_height": self.min_btn_height_var.get(),
            "max_btn_height": self.max_btn_height_var.get(),
            "timer_sound": self.timer_sound_var.get(),
            "minimal_mode": self.minimal_mode_var.get(),
            "log_level": self.log_level_var.get(),
            "python_executable": self.python_executable_var.get(),
            "animation_enabled": self.animation_enabled_var.get(),
            "default_animation_type": animation_code,
        }
        
        logger.debug(f"Saving settings: {new_settings}")
        logger.info(f"Python executable being saved: '{new_settings.get('python_executable', '')}'")
        self.on_save(new_settings)
        self.destroy()

    def apply_theme(self, theme):
        apply_theme_recursive(self, theme)
        
        # Update scrollbar colors
        if hasattr(self, 'scrollbar') and self.scrollbar.winfo_exists():
            self.scrollbar.configure(
                bg=theme.get("scrollbar_bg", "#c0c0c0"),
                troughcolor=theme.get("scrollbar_trough", "#f0f0f0"),
                activebackground=theme.get("scrollbar_bg", "#c0c0c0"),
                relief=tk.FLAT, borderwidth=0
            ) 