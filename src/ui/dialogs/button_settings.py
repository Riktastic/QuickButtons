"""Button settings dialog for QuickButtons application."""

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import re

from src.ui.components.tooltip import Tooltip
from src.ui.themes import apply_theme_recursive
from src.utils.logger import logger


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
        self.geometry("420x500+300+300")
        self.configure(bg=theme["dialog_bg"])
        self.resizable(True, True)  # Allow resizing
        
        # Set window icon
        try:
            from src.core.constants import ICON_ICO_PATH
            self.iconbitmap(ICON_ICO_PATH)
        except Exception as e:
            logger.warning(f"Could not set button settings dialog icon: {e}")
        
        # --- Variables ---
        self.type_var = tk.StringVar(value=self.btn_cfg.get("type", "python_script"))
        self.type_var.trace_add("write", lambda *args: self.update_fields())
        self.label_var = tk.StringVar(value=self.btn_cfg.get("label", "Run Python Script"))
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
        self.tooltip_var = tk.StringVar(value=self.btn_cfg.get("tooltip", ""))
        
        # Use default colors checkbox
        self.use_default_colors_var = tk.BooleanVar(value=self.btn_cfg.get("use_default_colors", False))
        
        # Animation settings
        self.use_default_animation_var = tk.BooleanVar(value=self.btn_cfg.get("use_default_animation", True))
        self.animation_type_var = tk.StringVar(value=self.btn_cfg.get("animation_type", "ripple"))
        self.disable_animation_var = tk.BooleanVar(value=self.btn_cfg.get("disable_animation", False))
        
        def on_default_colors_toggle():
            if self.use_default_colors_var.get():
                if hasattr(self, 'bg_btn'):
                    self.bg_btn.config(state="disabled")
                if hasattr(self, 'fg_btn'):
                    self.fg_btn.config(state="disabled")
            else:
                if hasattr(self, 'bg_btn'):
                    self.bg_btn.config(state="normal")
                if hasattr(self, 'fg_btn'):
                    self.fg_btn.config(state="normal")
        
        self.on_default_colors_toggle = on_default_colors_toggle
        
        def on_animation_settings_toggle():
            """Handle animation setting changes."""
            # Call the toggle function after UI is built
            self.after(100, self._update_animation_controls)
        
        self.on_animation_settings_toggle = on_animation_settings_toggle
        
        def preview_animation():
            """Preview the selected animation on a test button."""
            try:
                from src.utils.animations import animate_button_press
                
                # Get animation type code and display name
                animation_display = self.animation_type_var.get()
                animation_code = self.animation_display_to_code.get(animation_display, "ripple")
                
                logger.debug(f"Button settings preview animation called - display: '{animation_display}', code: '{animation_code}'")
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
        
        self.preview_animation = preview_animation
        
        def _update_animation_controls():
            """Update animation controls state based on checkboxes."""
            if hasattr(self, 'animation_menu') and hasattr(self, 'preview_btn'):
                # If animation is disabled for this button, disable all controls
                if self.disable_animation_var.get():
                    self.animation_menu.config(state="disabled")
                    self.preview_btn.config(state="disabled")
                # If using default animation, disable custom controls
                elif self.use_default_animation_var.get():
                    self.animation_menu.config(state="disabled")
                    self.preview_btn.config(state="disabled")
                # If using custom animation, enable controls
                else:
                    self.animation_menu.config(state="normal")
                    self.preview_btn.config(state="normal")
        
        self._update_animation_controls = _update_animation_controls
        
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
        
        # Initialize header_rows list
        self.header_rows = []
        
        self.build_ui(allow_delete)
        
        # Update animation controls state after UI is built
        self.after(100, self._update_animation_controls)
        
        # Force scrollbar to be visible after UI is built
        self.after(200, self._ensure_scrollbar_visible)
        
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
            else:
                # If no content, set a minimum scrollregion to force scrollbar visibility
                self.canvas.configure(scrollregion=(0, 0, 0, 1000))
            
            # Make sure scrollbar is packed and visible
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.scrollbar.lift()  # Bring to front
            
            # Force scrollbar to maintain its space
            self.scrollbar.pack_propagate(False)
            
            # Schedule another check to ensure it stays visible
            self.after(500, self._ensure_scrollbar_visible)
            
        except Exception as e:
            logger.error(f"Error ensuring scrollbar visibility: {e}")

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

    def browse_script(self):
        """Open file dialog to select a Python script."""
        file_path = filedialog.askopenfilename(title=self.master._("Select Python Script"), filetypes=[("Python Files", "*.py")])
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
    
    def browse_app(self):
        """Browse for an application file."""
        filename = filedialog.askopenfilename(
            title=self.master._("Select Application"),
            filetypes=[("Executable files", "*.exe *.bat *.cmd"), ("All files", "*.*")]
        )
        if filename:
            self.app_path_var.set(filename)
    

            
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

    def open_emoji_picker(self, entry_widget):
        # List of relevant emojis for this app
        emojis = [
            "🖥️", "🌐", "🎵", "📤", "⚡", "🔗", "📝", "🔊", "⭐", "❓", "✅", "❌", "🕒", "📅", "🔒", "🔓"
        ]
        picker = tk.Toplevel(self)
        picker.title(self.master._("Pick emoji"))
        picker.transient(self)
        picker.resizable(False, False)
        picker.configure(bg=self.theme["dialog_bg"])
        
        # Set window icon
        try:
            from src.core.constants import ICON_ICO_PATH
            picker.iconbitmap(ICON_ICO_PATH)
        except Exception as e:
            from src.utils.logger import logger
            logger.warning(f"Could not set emoji picker icon: {e}")
        # Place near the entry
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        picker.geometry(f"+{x}+{y}")
        # Emoji grid
        frame = tk.Frame(picker, bg=self.theme["dialog_bg"])
        frame.pack(padx=8, pady=8)
        cols = 5
        for i, emoji in enumerate(emojis):
            btn = tk.Button(frame, text=emoji, font=("Segoe UI Emoji", 16), width=2, height=1, relief=tk.FLAT, 
                           bg=self.theme["button_bg"], fg=self.theme["button_fg"], 
                           command=lambda e=emoji: self._insert_emoji(entry_widget, e, picker))
            btn.grid(row=i//cols, column=i%cols, padx=2, pady=2)
        # Close on focus out
        picker.bind("<FocusOut>", lambda e: picker.destroy())
        picker.grab_set()

    def _insert_emoji(self, entry_widget, emoji, picker):
        entry_widget.insert(entry_widget.index(tk.INSERT), emoji)
        picker.destroy()

    def _on_llm_provider_change(self, *args):
        """Handle LLM provider change to show/hide appropriate fields."""
        provider = self.llm_provider_var.get()
        
        # Show/hide endpoint field based on provider
        if provider == "azure":
            self.endpoint_entry.pack(padx=10, fill=tk.X, expand=True)
            # For Azure, show text entry for model
            if self.model_dropdown:
                self.model_dropdown.pack_forget()
            self.model_entry.pack(padx=10, fill=tk.X, expand=True)
        elif provider == "litellm":
            self.endpoint_entry.pack_forget()
            self.model_entry.pack_forget()
            if self.model_dropdown:
                self.model_dropdown.pack_forget()
            self._create_model_dropdown(provider)
        else:
            self.endpoint_entry.pack_forget()
            # For non-Azure, show dropdown with supported models
            self.model_entry.pack_forget()
            if self.model_dropdown:
                self.model_dropdown.pack_forget()
            self._create_model_dropdown(provider)
    
    def _create_model_dropdown(self, provider):
        """Create model dropdown for the specified provider."""
        # Define supported models for each provider
        models = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
            "gemini": ["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"],
            "litellm": ["gpt-3.5-turbo", "gpt-4", "claude-3-opus", "mixtral-8x7b"]
        }
        
        if provider in models:
            # Create dropdown
            self.model_dropdown = tk.OptionMenu(self.dynamic_frame, self.model_var, *models[provider])
            self.model_dropdown.config(bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], highlightthickness=0)
            self.model_dropdown.pack(padx=10, fill=tk.X, expand=True)
            
            # Set default model if current model is not in the list
            if self.model_var.get() not in models[provider]:
                self.model_var.set(models[provider][0])
    
    def _add_mcp_proxy_entry(self):
        """Add a new LLM proxy entry field."""
        # Create frame for this proxy entry
        proxy_frame = tk.Frame(self.mcp_frame, bg=self.theme["dialog_bg"])
        proxy_frame.pack(fill=tk.X, pady=2)
        
        # Create entry widget
        proxy_var = tk.StringVar()
        proxy_entry = tk.Entry(proxy_frame, textvariable=proxy_var)
        proxy_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Create delete button (only show if more than one entry)
        delete_btn = tk.Button(proxy_frame, text="🗑️", command=lambda: self._remove_mcp_proxy_entry(proxy_frame, proxy_var),
                              bg="#a33", fg="white", relief=tk.FLAT, width=3)
        delete_btn.pack(side=tk.RIGHT)
        
        # Store reference
        self.mcp_entries.append((proxy_frame, proxy_var, proxy_entry, delete_btn))
        
        # Show/hide delete buttons based on number of entries
        self._update_mcp_delete_buttons()
        
        # Set initial value if available
        if len(self.mcp_entries) <= len(self.mcp_proxies):
            proxy_var.set(self.mcp_proxies[len(self.mcp_entries) - 1])

    def _remove_mcp_proxy_entry(self, proxy_frame, proxy_var):
        """Remove an LLM proxy entry field."""
        # Remove from our list
        self.mcp_entries = [(frame, var, entry, btn) for frame, var, entry, btn in self.mcp_entries if frame != proxy_frame]
        
        # Destroy the frame
        proxy_frame.destroy()
        
        # Update delete buttons visibility
        self._update_mcp_delete_buttons()

    def _update_mcp_delete_buttons(self):
        """Update visibility of delete buttons based on number of entries."""
        for i, (frame, var, entry, delete_btn) in enumerate(self.mcp_entries):
            # Show delete button only if there's more than one entry
            if len(self.mcp_entries) > 1:
                delete_btn.pack(side=tk.RIGHT)
            else:
                delete_btn.pack_forget()

    def _collect_mcp_proxies(self):
        """Collect all LLM proxy values from the UI."""
        proxies = []
        for frame, var, entry, btn in self.mcp_entries:
            value = var.get().strip()
            if value:  # Only add non-empty values
                proxies.append(value)
        return proxies

    # Removed _resize_to_fit method - users should scroll instead of auto-resizing

    def _add_header_row(self, key='', value=''):
        if not hasattr(self, 'headers_frame') or not self.headers_frame.winfo_exists():
            return
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

    def _collect_headers(self):
        headers_str = ''
        for _, key_var, value_var in self.header_rows:
            k = key_var.get().strip()
            v = value_var.get().strip()
            if k:
                headers_str += f"{k}: {v}\n"
        return headers_str.strip()

    def build_ui(self, allow_delete):
        f = self.content_frame
        
        # --- General Settings Group ---
        general_group = tk.LabelFrame(f, text=self.master._("General"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        general_group.pack(fill=tk.X, padx=8, pady=(10, 16))
        
        tk.Label(general_group, text=self.master._("Button Label (text or emoji):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        label_frame = tk.Frame(general_group, bg=self.theme["dialog_bg"])
        label_frame.pack(padx=10, fill=tk.X)
        label_entry = tk.Entry(label_frame, textvariable=self.label_var)
        label_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if not self.label_var.get():
            label_entry.insert(0, "😀 Example or text")
        emoji_btn = tk.Button(label_frame, text="😊", width=2, command=lambda: self.open_emoji_picker(label_entry), 
                             bg=self.theme["dialog_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        emoji_btn.pack(side=tk.LEFT, padx=(4,0))
        Tooltip(emoji_btn, self.master._("Pick emoji"))
        
        tk.Label(general_group, text=self.master._("Tooltip (optional):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(6,0))
        tooltip_entry = tk.Entry(general_group, textvariable=self.tooltip_var)
        tooltip_entry.pack(padx=10, fill=tk.X, pady=(0,12))
        
        # --- Action Settings Group ---
        action_group = tk.LabelFrame(f, text=self.master._("Action"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        action_group.pack(fill=tk.BOTH, padx=8, pady=(0, 16), expand=True)
        
        # Type selector with translated display names
        tk.Label(action_group, text=self.master._("Button Type:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.type_code_to_disp = {
            # Core execution types
            "python_script": self.master._("Python Script"),
            "app_launcher": self.master._("Application Launcher"),
            "shell": self.master._("Run Shell Command"),
            
            # Web & communication
            "website": self.master._("Open Website"),
            "post": self.master._("POST Request"),
            "llm": self.master._("LLM Chat"),
            
            # Media & entertainment
            "music": self.master._("Play Music"),
            
            # Monitoring & testing
            "timer": self.master._("Timer"),
            "pomodoro": self.master._("Pomodoro Timer"),
            "ping": self.master._("Ping"),
            "network_speed": self.master._("Network Speed Test"),
            "http_test": self.master._("HTTP Test"),
            "color_picker": self.master._("Color Picker")
        }
        self.type_disp_to_code = {v: k for k, v in self.type_code_to_disp.items()}
        self.type_display = tk.StringVar()
        # Set display value based on code
        self.type_display.set(self.type_code_to_disp.get(self.type_var.get(), self.master._("Python Script")))
        type_menu = tk.OptionMenu(action_group, self.type_display, *self.type_disp_to_code.keys())
        type_menu.config(bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], highlightthickness=0)
        type_menu.pack(padx=10, fill=tk.X)
        
        # When display value changes, update type_var
        def on_type_display_change(*args):
            code = self.type_disp_to_code.get(self.type_display.get(), "python_script")
            self.type_var.set(code)
        self.type_display.trace_add("write", on_type_display_change)
        
        # When type_var changes, update display value (for programmatic changes)
        def on_type_var_change(*args):
            disp = self.type_code_to_disp.get(self.type_var.get(), self.master._("Python Script"))
            if self.type_display.get() != disp:
                self.type_display.set(disp)
        self.type_var.trace_add("write", on_type_var_change)
        
        # --- Dynamic fields frame ---
        self.dynamic_frame = tk.Frame(action_group, bg=self.theme["dialog_bg"])
        self.dynamic_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # Add a blank spacer at the bottom for extra padding
        self.action_group_spacer = tk.Frame(action_group, height=8, bg=self.theme["dialog_bg"])
        self.action_group_spacer.pack(fill=tk.X, padx=0, pady=(0,12))
        
        # --- Styling Group ---
        styling_group = tk.LabelFrame(f, text=self.master._("Styling"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], bd=1, relief=tk.GROOVE, labelanchor='nw')
        styling_group.pack(fill=tk.X, padx=8, pady=(0, 16))
        
        tk.Label(styling_group, text=self.master._("Icon Path:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        icon_row = tk.Frame(styling_group, bg=self.theme["dialog_bg"])
        icon_row.pack(padx=10, fill=tk.X)
        icon_entry = tk.Entry(icon_row, textvariable=self.icon_var)
        icon_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_icon_btn = tk.Button(icon_row, text=self.master._("Browse..."), command=self.browse_icon, 
                                   bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        browse_icon_btn.pack(side=tk.LEFT, padx=(4,0))
        del_icon_btn = tk.Button(icon_row, text="🗑️", command=lambda: self.icon_var.set(""), bg="#a33", fg="white", relief=tk.FLAT)
        del_icon_btn.pack(side=tk.LEFT, padx=(4,0))
        Tooltip(browse_icon_btn, self.master._("Browse for icon image"))
        Tooltip(del_icon_btn, self.master._("Clear icon path"))
        
        # Default color checkbox (placed just above color settings)
        default_colors_cb = tk.Checkbutton(styling_group, text=self.master._("Use default colors (auto swap in dark mode)"), 
                                          variable=self.use_default_colors_var, bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], 
                                          selectcolor=self.theme["dialog_bg"], activebackground=self.theme["dialog_bg"], 
                                          activeforeground=self.theme["label_fg"], command=self.on_default_colors_toggle)
        default_colors_cb.pack(anchor="w", padx=10, pady=(10,0))
        
        tk.Label(styling_group, text=self.master._("Button Background Color:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.bg_btn = tk.Button(styling_group, text=self.bg_color, bg=self.bg_color, fg=self.theme["button_fg"], command=self.pick_bg_color)
        self.bg_btn.pack(padx=10, pady=2, anchor="w")
        
        tk.Label(styling_group, text=self.master._("Button Text Color:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        self.fg_btn = tk.Button(styling_group, text=self.fg_color, bg=self.theme["dialog_bg"], fg=self.fg_color, command=self.pick_fg_color)
        self.fg_btn.pack(padx=10, pady=(2,12), anchor="w")
        
        self.on_default_colors_toggle()
        
        # --- Animation Settings ---
        # Disable animation checkbox (highest priority)
        disable_animation_cb = tk.Checkbutton(styling_group, text=self.master._("Disable animation for this button"), 
                                            variable=self.disable_animation_var, bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], 
                                            selectcolor=self.theme["dialog_bg"], activebackground=self.theme["dialog_bg"], 
                                            activeforeground=self.theme["label_fg"], command=self.on_animation_settings_toggle)
        disable_animation_cb.pack(anchor="w", padx=10, pady=(10,0))
        
        # Default animation checkbox
        default_animation_cb = tk.Checkbutton(styling_group, text=self.master._("Use default animation (from settings)"), 
                                            variable=self.use_default_animation_var, bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], 
                                            selectcolor=self.theme["dialog_bg"], activebackground=self.theme["dialog_bg"], 
                                            activeforeground=self.theme["label_fg"], command=self.on_animation_settings_toggle)
        default_animation_cb.pack(anchor="w", padx=10, pady=(5,0))
        
        # Animation type selection
        tk.Label(styling_group, text=self.master._("Animation Type:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
        animation_frame = tk.Frame(styling_group, bg=self.theme["dialog_bg"])
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
        self.animation_display_to_code = {display: code for code, display in animation_options}
        self.animation_code_to_display = {code: display for code, display in animation_options}
        
        # Set the display value based on current animation type
        current_animation = self.animation_type_var.get()
        current_display = self.animation_code_to_display.get(current_animation, self.master._("Ripple Effect"))
        self.animation_type_var.set(current_display)
        
        self.animation_menu = tk.OptionMenu(animation_frame, self.animation_type_var, *[opt[1] for opt in animation_options])
        self.animation_menu.config(bg=self.theme["button_bg"], fg=self.theme["button_fg"], highlightthickness=0)
        self.animation_menu.pack(side=tk.LEFT)
        
        # Animation preview button
        def preview_clicked():
            logger.debug("Button settings preview button clicked!")
            self.preview_animation()
        
        self.preview_btn = tk.Button(animation_frame, text=self.master._("Preview"), command=preview_clicked,
                                   bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
        self.preview_btn.pack(side=tk.LEFT, padx=(8, 0))
        Tooltip(self.preview_btn, self.master._("Preview the selected animation"))
        
        # Create the fixed bottom buttons after UI is built
        self._create_bottom_buttons(allow_delete)
        
        self.update_fields()

    def _create_bottom_buttons(self, allow_delete):
        """Create the fixed bottom action buttons (Save, Duplicate, Delete)."""
        # --- Save/Delete/Duplicate buttons ---
        btn_frame = tk.Frame(self.bottom_frame, bg=self.theme["dialog_bg"])
        btn_frame.pack(pady=(0, 5), padx=10, fill=tk.X)
        
        # Save button with disk icon
        save_btn = tk.Button(btn_frame, text="💾 Save", command=self.save, bg=self.theme["button_bg"], fg=self.theme["button_fg"], 
                           font=("Segoe UI", 10, "bold"), relief=tk.FLAT, height=1)
        save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipadx=5, ipady=3)
        Tooltip(save_btn, self.master._("Save button settings"))
        
        # Duplicate button
        dup_btn = tk.Button(btn_frame, text="📋 Duplicate", command=self.duplicate, bg=self.theme["button_bg"], fg=self.theme["button_fg"], 
                          font=("Segoe UI", 10, "bold"), relief=tk.FLAT, height=1)
        dup_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipadx=5, ipady=3, padx=(8,0))
        Tooltip(dup_btn, self.master._("Create a copy of this button"))
        
        if allow_delete:
            del_btn = tk.Button(btn_frame, text="🗑️ Delete", command=self.delete, bg="#a33", fg="white", 
                              font=("Segoe UI", 10, "bold"), relief=tk.FLAT, height=1)
            del_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, ipadx=5, ipady=3, padx=(8,0))
            Tooltip(del_btn, self.master._("Delete this button"))

    def update_fields(self):
        """Show/hide fields based on button type."""
        self._updating_fields = True
        try:
            t = self.type_var.get()
            # Remove all widgets from dynamic_frame to ensure a clean redraw
            for child in self.dynamic_frame.winfo_children():
                if child.winfo_exists():
                    child.destroy()
            
            # Now create and pack widgets for the selected type
            if t == "python_script":
                tk.Label(self.dynamic_frame, text=self.master._("Python Script Path:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                script_entry = tk.Entry(self.dynamic_frame, textvariable=self.script_var)
                script_entry.pack(padx=10, fill=tk.X, expand=True)
                script_browse = tk.Button(self.dynamic_frame, text="Browse...", command=self.browse_script)
                script_browse.pack(padx=10, pady=2, anchor="e")
                
                tk.Label(self.dynamic_frame, text=self.master._("Arguments (wildcards: {date}, {time}, {datetime}):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                args_entry = tk.Entry(self.dynamic_frame, textvariable=self.args_var)
                args_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Add background option
                self.background_var = tk.BooleanVar(value=self.btn_cfg.get("background", False))
                background_check = tk.Checkbutton(self.dynamic_frame, text=self.master._("Run in background (minimized)"), 
                                                variable=self.background_var, bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], 
                                                selectcolor=self.theme["dialog_bg"], activebackground=self.theme["dialog_bg"], 
                                                activeforeground=self.theme["label_fg"])
                background_check.pack(anchor="w", padx=10, pady=(2,8))
                
            elif t == "website":
                tk.Label(self.dynamic_frame, text=self.master._("Website URL:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                url_entry = tk.Entry(self.dynamic_frame, textvariable=self.url_var)
                url_entry.pack(padx=10, fill=tk.X, expand=True)
                
            elif t == "music":
                tk.Label(self.dynamic_frame, text=self.master._("Music File:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                music_entry = tk.Entry(self.dynamic_frame, textvariable=self.music_var)
                music_entry.pack(padx=10, fill=tk.X, expand=True)
                music_browse = tk.Button(self.dynamic_frame, text="Browse...", command=self.browse_music)
                music_browse.pack(padx=10, pady=2, anchor="e")
                
            elif t == "post":
                tk.Label(self.dynamic_frame, text=self.master._("POST URL:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.post_url_entry = tk.Entry(self.dynamic_frame)
                self.post_url_entry.pack(padx=10, fill=tk.X, expand=True)
                
                tk.Label(self.dynamic_frame, text=self.master._("Headers (key: value per line):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.headers_frame = tk.Frame(self.dynamic_frame, bg=self.theme["dialog_bg"])
                self.headers_frame.pack(fill=tk.X, padx=0, pady=0)
                
                add_header_btn = tk.Button(self.dynamic_frame, text="➕ " + self.master._("Add header"), command=self._add_header_row, 
                                         bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
                add_header_btn.pack(padx=10, pady=(0,4), anchor="w")
                
                tk.Label(self.dynamic_frame, text=self.master._("Body (optional):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.post_body_text = tk.Text(self.dynamic_frame, height=3, width=30)
                self.post_body_text.pack(padx=10, fill=tk.X, expand=True)
                
                if not self.header_rows:
                    self._add_header_row()
                    
            elif t == "shell":
                tk.Label(self.dynamic_frame, text=self.master._("Shell Command:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.shell_var = tk.StringVar(value=self.btn_cfg.get("shell_cmd", ""))
                shell_entry = tk.Entry(self.dynamic_frame, textvariable=self.shell_var)
                shell_entry.pack(padx=10, fill=tk.X, expand=True)
                
            elif t == "timer":
                tk.Label(self.dynamic_frame, text=self.master._("Timer Duration (h:mm:ss):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.timer_duration_var = tk.StringVar(value=self.btn_cfg.get("timer_duration", "0:01:00"))
                timer_duration_entry = tk.Entry(self.dynamic_frame, textvariable=self.timer_duration_var)
                timer_duration_entry.pack(padx=10, fill=tk.X, expand=True)
                
            elif t == "llm":
                # Add LLM specific fields
                tk.Label(self.dynamic_frame, text=self.master._("LLM Provider:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.llm_provider_var = tk.StringVar(value=self.btn_cfg.get("llm_provider", "openai"))
                provider_options = ["openai", "azure", "gemini", "litellm"]
                provider_menu = tk.OptionMenu(self.dynamic_frame, self.llm_provider_var, *provider_options, command=self._on_llm_provider_change)
                provider_menu.config(bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], highlightthickness=0)
                provider_menu.pack(padx=10, fill=tk.X, pady=(0,6))
                
                # Endpoint URL field (for Azure)
                tk.Label(self.dynamic_frame, text=self.master._("Endpoint URL:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(6,0))
                self.endpoint_var = tk.StringVar(value=self.btn_cfg.get("llm_endpoint", ""))
                self.endpoint_entry = tk.Entry(self.dynamic_frame, textvariable=self.endpoint_var)
                self.endpoint_entry.pack(padx=10, fill=tk.X, expand=True)
                
                tk.Label(self.dynamic_frame, text=self.master._("API Key:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(6,0))
                self.api_key_var = tk.StringVar(value=self.btn_cfg.get("llm_api_key", ""))
                api_key_entry = tk.Entry(self.dynamic_frame, textvariable=self.api_key_var, show="*")
                api_key_entry.pack(padx=10, fill=tk.X, expand=True)
                

                
                # Model field - textbox for Azure, dropdown for others
                tk.Label(self.dynamic_frame, text=self.master._("Model:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(6,0))
                self.model_var = tk.StringVar(value=self.btn_cfg.get("llm_model", "gpt-3.5-turbo"))
                self.model_entry = tk.Entry(self.dynamic_frame, textvariable=self.model_var)
                self.model_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Model dropdown for non-Azure providers
                self.model_dropdown = None
                
                tk.Label(self.dynamic_frame, text=self.master._("Context (system prompt):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(6,0))
                self.context_text = tk.Text(self.dynamic_frame, height=3, width=30)
                self.context_text.insert("1.0", self.btn_cfg.get("llm_context", ""))
                self.context_text.pack(padx=10, fill=tk.X, expand=True)
                
                # MCP/Proxy settings
                tk.Label(self.dynamic_frame, text=self.master._("MCP/Proxy Settings:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10,0))
                
                # MCP proxies frame
                self.mcp_frame = tk.Frame(self.dynamic_frame, bg=self.theme["dialog_bg"])
                self.mcp_frame.pack(fill=tk.X, padx=10, pady=(5,0))
                
                # Initialize MCP proxies list
                self.mcp_proxies = self.btn_cfg.get("llm_proxies", [""])
                self.mcp_entries = []
                
                # Add initial proxy entry
                self._add_mcp_proxy_entry()
                
                # Add new proxy button
                add_proxy_btn = tk.Button(self.dynamic_frame, text="➕ " + self.master._("Add New Proxy"), 
                                        command=self._add_mcp_proxy_entry,
                                        bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
                add_proxy_btn.pack(padx=10, pady=(5,0), anchor="w")
                
                # Initialize provider-specific UI
                self._on_llm_provider_change()
                
            elif t == "app_launcher":
                tk.Label(self.dynamic_frame, text=self.master._("Application Path:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                app_path_frame = tk.Frame(self.dynamic_frame, bg=self.theme["dialog_bg"])
                app_path_frame.pack(padx=10, fill=tk.X, expand=True)
                self.app_path_var = tk.StringVar(value=self.btn_cfg.get("app_path", ""))
                app_path_entry = tk.Entry(app_path_frame, textvariable=self.app_path_var)
                app_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                browse_app_btn = tk.Button(app_path_frame, text=self.master._("Browse..."), command=self.browse_app, 
                                         bg=self.theme["button_bg"], fg=self.theme["button_fg"], relief=tk.FLAT)
                browse_app_btn.pack(side=tk.LEFT, padx=(4,0))
                
                tk.Label(self.dynamic_frame, text=self.master._("Arguments (optional):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.app_args_var = tk.StringVar(value=self.btn_cfg.get("args", ""))
                app_args_entry = tk.Entry(self.dynamic_frame, textvariable=self.app_args_var)
                app_args_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Background option
                self.app_background_var = tk.BooleanVar(value=self.btn_cfg.get("background", False))
                app_background_check = tk.Checkbutton(self.dynamic_frame, text=self.master._("Run in background"), 
                                                    variable=self.app_background_var, bg=self.theme["dialog_bg"], 
                                                    fg=self.theme["label_fg"], selectcolor=self.theme["dialog_bg"])
                app_background_check.pack(anchor="w", padx=10, pady=(5,0))
                
            elif t == "network_speed":
                # Network speed test configuration
                info_label = tk.Label(self.dynamic_frame, text=self.master._("Click the button to run a network speed test. Results will be displayed on the button."), 
                                    bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left")
                info_label.pack(anchor="w", padx=10, pady=(10,0))
                
            elif t == "ping":
                # Ping configuration
                info_label = tk.Label(self.dynamic_frame, text=self.master._("Click the button to ping a host. Results will be displayed on the button."), 
                                    bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left")
                info_label.pack(anchor="w", padx=10, pady=(10,0))
                
                # Host configuration
                tk.Label(self.dynamic_frame, text=self.master._("Host to ping:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.ping_host_var = tk.StringVar(value=self.btn_cfg.get("ping_host", "8.8.8.8"))
                ping_host_entry = tk.Entry(self.dynamic_frame, textvariable=self.ping_host_var)
                ping_host_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Ping count configuration
                tk.Label(self.dynamic_frame, text=self.master._("Number of pings:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.ping_count_var = tk.StringVar(value=str(self.btn_cfg.get("ping_count", 3)))
                ping_count_entry = tk.Entry(self.dynamic_frame, textvariable=self.ping_count_var)
                ping_count_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Help text
                help_label = tk.Label(self.dynamic_frame, text=self.master._("Enter hostname or IP address (e.g., google.com, 8.8.8.8)"), 
                                    bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left", font=("Segoe UI", 8))
                help_label.pack(anchor="w", padx=10, pady=(5,0))
                
            elif t == "pomodoro":
                # Pomodoro configuration
                info_label = tk.Label(self.dynamic_frame, text=self.master._("Click to start Pomodoro timer. Click: start/pause, Right-click: skip, Double-click: reset"), 
                                    bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left")
                info_label.pack(anchor="w", padx=10, pady=(10,0))
                
                # Work duration
                tk.Label(self.dynamic_frame, text=self.master._("Work Duration (minutes):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.work_duration_var = tk.StringVar(value=str(self.btn_cfg.get("work_duration", 25)))
                work_duration_entry = tk.Entry(self.dynamic_frame, textvariable=self.work_duration_var)
                work_duration_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Short break duration
                tk.Label(self.dynamic_frame, text=self.master._("Short Break (minutes):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.short_break_var = tk.StringVar(value=str(self.btn_cfg.get("short_break_duration", 5)))
                short_break_entry = tk.Entry(self.dynamic_frame, textvariable=self.short_break_var)
                short_break_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Long break duration
                tk.Label(self.dynamic_frame, text=self.master._("Long Break (minutes):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.long_break_var = tk.StringVar(value=str(self.btn_cfg.get("long_break_duration", 15)))
                long_break_entry = tk.Entry(self.dynamic_frame, textvariable=self.long_break_var)
                long_break_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Sessions before long break
                tk.Label(self.dynamic_frame, text=self.master._("Sessions before Long Break:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.sessions_var = tk.StringVar(value=str(self.btn_cfg.get("sessions_before_long_break", 4)))
                sessions_entry = tk.Entry(self.dynamic_frame, textvariable=self.sessions_var)
                sessions_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Auto-advance option
                self.auto_advance_var = tk.BooleanVar(value=self.btn_cfg.get("auto_advance", True))
                auto_advance_check = tk.Checkbutton(self.dynamic_frame, text=self.master._("Auto-advance between phases"), 
                                                  variable=self.auto_advance_var, bg=self.theme["dialog_bg"], 
                                                  fg=self.theme["label_fg"], selectcolor=self.theme["dialog_bg"])
                auto_advance_check.pack(anchor="w", padx=10, pady=(5,0))
                
            elif t == "http_test":
                # HTTP test configuration
                info_label = tk.Label(self.dynamic_frame, text=self.master._("Click to test HTTP/HTTPS connectivity. Shows lock status and response time."), 
                                    bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left")
                info_label.pack(anchor="w", padx=10, pady=(10,0))
                
                # Test URL
                tk.Label(self.dynamic_frame, text=self.master._("Test URL:"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.test_url_var = tk.StringVar(value=self.btn_cfg.get("test_url", "https://google.com"))
                test_url_entry = tk.Entry(self.dynamic_frame, textvariable=self.test_url_var)
                test_url_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Timeout
                tk.Label(self.dynamic_frame, text=self.master._("Timeout (seconds):"), bg=self.theme["dialog_bg"], fg=self.theme["label_fg"]).pack(anchor="w", padx=10, pady=(10,0))
                self.timeout_var = tk.StringVar(value=str(self.btn_cfg.get("timeout", 10)))
                timeout_entry = tk.Entry(self.dynamic_frame, textvariable=self.timeout_var)
                timeout_entry.pack(padx=10, fill=tk.X, expand=True)
                
                # Help text
                help_label = tk.Label(self.dynamic_frame, text=self.master._("🔒 = HTTPS with valid certificate, 🔓 = HTTPS with invalid certificate, 🌐 = HTTP only"), 
                                    bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left", font=("Segoe UI", 8))
                help_label.pack(anchor="w", padx=10, pady=(5,0))
                
            elif t == "color_picker":
                # Color picker configuration
                info_label = tk.Label(self.dynamic_frame, text=self.master._("Click to pick a color from anywhere on your screen. The hex color code will be copied to clipboard."), 
                                    bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left")
                info_label.pack(anchor="w", padx=10, pady=(10,0))
                
                # Instructions
                instructions_label = tk.Label(self.dynamic_frame, text=self.master._("Workflow: Click button → Click on screen → Color copied to clipboard"), 
                                            bg=self.theme["dialog_bg"], fg=self.theme["label_fg"], wraplength=300, justify="left", font=("Segoe UI", 8))
                instructions_label.pack(anchor="w", padx=10, pady=(5,0))
            
            # Let users scroll instead of auto-resizing
        finally:
            self._updating_fields = False
            
        # Ensure scrollbar is visible after fields are updated
        self.after(50, self._ensure_scrollbar_visible)

    def save(self):
        """Save the button configuration and close the dialog."""
        # Check if this is a Python script button and Python executable is not configured
        if self.type_var.get() == "python_script":
            python_executable = self.master.config_data.get("python_executable", "")
            if not python_executable:
                # Prompt user to configure Python executable
                result = messagebox.askyesno(
                    self.master._("Python Executable Required"),
                    self.master._("No Python executable is configured. Would you like to configure it now?")
                )
                if result:
                    # Open settings dialog to configure Python executable
                    from src.ui.dialogs.settings import SettingsDialog
                    settings_dialog = SettingsDialog(
                        self.master, 
                        self.theme, 
                        self.master.config_data, 
                        lambda new_settings: self._on_settings_save(new_settings)
                    )
                    return  # Don't save yet, wait for settings to be saved
                else:
                    # User cancelled, don't save the button
                    return
        
        cfg = {
            "type": self.type_var.get(),
            "label": self.label_var.get(),
            "tooltip": self.tooltip_var.get(),
            "shortcut": self.shortcut_var.get(),
            "args": self.args_var.get(),
            "script": self.script_var.get(),
            "url": self.url_var.get(),
            "music": self.music_var.get(),
            "icon": self.icon_var.get(),
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "use_default_colors": self.use_default_colors_var.get(),
            "use_default_animation": self.use_default_animation_var.get(),
            "animation_type": self.animation_display_to_code.get(self.animation_type_var.get(), "ripple"),
            "disable_animation": self.disable_animation_var.get(),
        }
        
        # Add type-specific fields
        if self.type_var.get() == "python_script" and hasattr(self, 'background_var'):
            cfg["background"] = self.background_var.get()
        elif self.type_var.get() == "post":
            cfg["post_url"] = self.post_url_entry.get() if hasattr(self, "post_url_entry") else ""
            cfg["post_headers"] = self._collect_headers()
            cfg["post_body"] = self.post_body_text.get("1.0", tk.END).strip() if hasattr(self, "post_body_text") else ""
        elif self.type_var.get() == "shell" and hasattr(self, 'shell_var'):
            cfg["shell_cmd"] = self.shell_var.get()
        elif self.type_var.get() == "timer" and hasattr(self, 'timer_duration_var'):
            cfg["timer_duration"] = self.timer_duration_var.get()
        elif self.type_var.get() == "llm":
            cfg["llm_provider"] = self.llm_provider_var.get() if hasattr(self, 'llm_provider_var') else ""
            cfg["llm_endpoint"] = self.endpoint_var.get() if hasattr(self, 'endpoint_var') else ""
            cfg["llm_api_key"] = self.api_key_var.get() if hasattr(self, 'api_key_var') else ""
            cfg["llm_model"] = self.model_var.get() if hasattr(self, 'model_var') else ""
            cfg["llm_context"] = self.context_text.get("1.0", tk.END).strip() if hasattr(self, 'context_text') else ""
            cfg["llm_proxies"] = self._collect_mcp_proxies() if hasattr(self, 'mcp_entries') else []
        elif self.type_var.get() == "app_launcher":
            cfg["app_path"] = self.app_path_var.get() if hasattr(self, 'app_path_var') else ""
            cfg["args"] = self.app_args_var.get() if hasattr(self, 'app_args_var') else ""
            cfg["background"] = self.app_background_var.get() if hasattr(self, 'app_background_var') else False

        elif self.type_var.get() == "ping":
            cfg["ping_host"] = self.ping_host_var.get() if hasattr(self, 'ping_host_var') else "8.8.8.8"
            try:
                cfg["ping_count"] = int(self.ping_count_var.get()) if hasattr(self, 'ping_count_var') else 3
            except ValueError:
                cfg["ping_count"] = 3
        elif self.type_var.get() == "pomodoro":
            try:
                cfg["work_duration"] = int(self.work_duration_var.get()) if hasattr(self, 'work_duration_var') else 25
            except ValueError:
                cfg["work_duration"] = 25
            try:
                cfg["short_break_duration"] = int(self.short_break_var.get()) if hasattr(self, 'short_break_var') else 5
            except ValueError:
                cfg["short_break_duration"] = 5
            try:
                cfg["long_break_duration"] = int(self.long_break_var.get()) if hasattr(self, 'long_break_var') else 15
            except ValueError:
                cfg["long_break_duration"] = 15
            try:
                cfg["sessions_before_long_break"] = int(self.sessions_var.get()) if hasattr(self, 'sessions_var') else 4
            except ValueError:
                cfg["sessions_before_long_break"] = 4
            cfg["auto_advance"] = self.auto_advance_var.get() if hasattr(self, 'auto_advance_var') else True
        elif self.type_var.get() == "http_test":
            cfg["test_url"] = self.test_url_var.get() if hasattr(self, 'test_url_var') else "https://google.com"
            try:
                cfg["timeout"] = int(self.timeout_var.get()) if hasattr(self, 'timeout_var') else 10
            except ValueError:
                cfg["timeout"] = 10
        
        if self.on_save:
            self.on_save(cfg)
        self.destroy()

    def _on_settings_save(self, new_settings):
        """Handle settings save and then save the button."""
        # Update the master's config data
        self.master.config_data.update(new_settings)
        self.master.save_config()
        
        # Now save the button
        self.save()

    def delete(self):
        """Delete the button (send None to on_save) and close the dialog."""
        if self.on_save:
            self.on_save(None)
        self.destroy()

    def duplicate(self):
        """Duplicate this button and add it as a new button."""
        cfg = {
            "type": self.type_var.get(),
            "label": self.label_var.get() + " (Copy)",
            "tooltip": self.tooltip_var.get(),
            "shortcut": "",  # Clear shortcut for duplicate
            "args": self.args_var.get(),
            "script": self.script_var.get(),
            "url": self.url_var.get(),
            "music": self.music_var.get(),
            "icon": self.icon_var.get(),
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "use_default_colors": self.use_default_colors_var.get(),
            "use_default_animation": self.use_default_animation_var.get(),
            "animation_type": self.animation_display_to_code.get(self.animation_type_var.get(), "ripple"),
            "disable_animation": self.disable_animation_var.get(),
        }
        
        # Add type-specific fields
        if self.type_var.get() == "python_script" and hasattr(self, 'background_var'):
            cfg["background"] = self.background_var.get()
        elif self.type_var.get() == "post":
            cfg["post_url"] = self.post_url_entry.get() if hasattr(self, "post_url_entry") else ""
            cfg["post_headers"] = self._collect_headers()
            cfg["post_body"] = self.post_body_text.get("1.0", tk.END).strip() if hasattr(self, "post_body_text") else ""
        elif self.type_var.get() == "shell" and hasattr(self, 'shell_var'):
            cfg["shell_cmd"] = self.shell_var.get()
        elif self.type_var.get() == "timer" and hasattr(self, 'timer_duration_var'):
            cfg["timer_duration"] = self.timer_duration_var.get()
        elif self.type_var.get() == "llm":
            cfg["llm_provider"] = self.llm_provider_var.get() if hasattr(self, 'llm_provider_var') else ""
            cfg["llm_endpoint"] = self.endpoint_var.get() if hasattr(self, 'endpoint_var') else ""
            cfg["llm_api_key"] = self.api_key_var.get() if hasattr(self, 'api_key_var') else ""
            cfg["llm_model"] = self.model_var.get() if hasattr(self, 'model_var') else ""
            cfg["llm_context"] = self.context_text.get("1.0", tk.END).strip() if hasattr(self, 'context_text') else ""
            cfg["llm_proxies"] = self._collect_mcp_proxies() if hasattr(self, 'mcp_entries') else []
        
        self.master.config_data.setdefault("buttons", []).append(cfg)
        self.master.save_config()
        self.master.refresh_grid()
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
        
        if hasattr(self, '_updating_fields') and not self._updating_fields:
            self.update_fields()  # To redraw dynamic fields with new theme 