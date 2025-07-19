"""LLM Chat overlay dialog for QuickButtons application."""

import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
import re
import textwrap

from src.ui.components.tooltip import Tooltip
from src.ui.themes import apply_theme_recursive
from src.utils.logger import logger

# Optional imports for LLM functionality
try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class LLMChatOverlay(tk.Toplevel):
    """A floating window for LLM chat (OpenAI, Azure, Gemini, etc)."""
    
    def __init__(self, master, cfg, btn_label=None):
        super().__init__(master)
        self.master = master
        self.cfg = cfg
        self.btn_label = btn_label or "Chat"
        
        self.title(master._("LLM Chat") + (f" - {btn_label}" if btn_label else ""))
        self.geometry("500x400+220+220")
        self.configure(bg=master.theme["bg"])
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.close)
        
        # Set window icon
        try:
            from src.core.constants import ICON_ICO_PATH
            self.iconbitmap(ICON_ICO_PATH)
        except Exception as e:
            logger.warning(f"Could not set LLM overlay icon: {e}")
        
        # Chat data
        self.conversation = []
        self.first_message_time = None
        
        # Colors for chat bubbles (will be set by theme)
        self.user_bubble_color = None
        self.assistant_bubble_color = None
        self.user_text_color = None
        self.assistant_text_color = None
        self.time_color = None
        self.name_color = None
        
        # Create UI
        self.create_topbar()
        self.create_chat_area()
        self.create_input_area()
        
        # Apply theme immediately using the exact same theme object as main app
        self.apply_theme(master.theme)
        
        # Force theme reapplication after a short delay
        self.after(50, lambda: self.apply_theme(master.theme))
        
        # Initialize chat width after window is fully created
        # self.after(100, self._update_chat_width)  # Disabled to prevent width shrinking
        
        # Apply theme after window is fully created
        self.after(100, lambda: self.apply_theme(master.theme))
        
        # Set initial canvas width to prevent messages from being too wide
        self.after(300, self._set_initial_width)
        
        # Ensure send button is always visible
        self.after(200, self._ensure_send_button_visible)
        
        # Force topbar color to match main app exactly
        self.after(250, lambda: self._force_topbar_color(master.theme["topbar_bg"]))

    def _ensure_send_button_visible(self):
        """Ensure the send button is always visible and properly positioned."""
        try:
            if hasattr(self, 'send_btn') and self.send_btn.winfo_exists():
                # Force the send button to be visible
                self.send_btn.pack_propagate(False)
                self.send_btn.update_idletasks()
                
                # Schedule this to run periodically
                self.after(1000, self._ensure_send_button_visible)
        except Exception as e:
            logger.error(f"Error ensuring send button visibility: {e}")

    def create_topbar(self):
        """Create a topbar similar to the main app."""
        self.topbar = tk.Frame(self, bg=self.master.theme["topbar_bg"], height=18)
        self.topbar.pack(fill=tk.X, side=tk.TOP)
        self.topbar.pack_propagate(False)
        
        # Export button
        export_btn = tk.Button(self.topbar, text="📁", command=self.export_chat, 
                             bg=self.master.theme["topbar_bg"], fg=self.master.theme["button_fg"], 
                             relief=tk.FLAT, font=("Segoe UI", 9))
        export_btn.pack(side=tk.LEFT, padx=(2,0), pady=1)
        Tooltip(export_btn, self.master._("Export chat to file"))

    def create_chat_area(self):
        """Create the scrollable chat area with canvas."""
        # Main chat container with no side padding for maximum width
        self.chat_container = tk.Frame(self, bg=self.master.theme.get("chat_bg", "#FFFFFF"))
        self.chat_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=2)
        
        # Canvas and scrollbar for chat
        self.chat_canvas = tk.Canvas(self.chat_container, bg=self.master.theme.get("chat_bg", "#FFFFFF"), 
                                   highlightthickness=0, borderwidth=0)
        self.chat_scrollbar = tk.Scrollbar(self.chat_container, orient=tk.VERTICAL, 
                                         command=self.chat_canvas.yview, width=20,
                                         bg=self.master.theme.get("scrollbar_bg", "#c0c0c0"),
                                         troughcolor=self.master.theme.get("scrollbar_trough", "#f0f0f0"),
                                         activebackground=self.master.theme.get("scrollbar_bg", "#c0c0c0"),
                                         highlightthickness=0, relief=tk.FLAT, borderwidth=0)
        self.chat_frame = tk.Frame(self.chat_canvas, bg=self.master.theme.get("chat_bg", "#FFFFFF"))
        
        # Configure canvas
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        
        # Pack canvas and scrollbar - ensure scrollbar is always visible
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Force scrollbar to be always visible
        self.chat_scrollbar.pack_propagate(False)
        
        # Bind events
        self.chat_frame.bind("<Configure>", self._on_chat_frame_configure)
        self.chat_canvas.bind("<Configure>", self._on_chat_canvas_configure)
        self.chat_canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Bind window resize events for better width adjustment
        self.bind("<Configure>", self._on_window_resize)

    def create_input_area(self):
        """Create the input area with auto-resizing text widget."""
        self.input_container = tk.Frame(self, bg=self.master.theme.get("chat_input_bg", "#F8F9FA"))
        self.input_container.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=4)
        
        # Input frame with modern styling (no heavy borders)
        self.input_frame = tk.Frame(self.input_container, bg="#F0F0F0", relief=tk.FLAT, borderwidth=0)
        self.input_frame.pack(fill=tk.X)
        
        # Send button with modern styling - pack first to reserve space
        self.send_btn = tk.Button(self.input_frame, text="➤", command=self.send_message,
                                bg=self.master.theme.get("chat_send_button", "#2196F3"), 
                                fg="white", relief=tk.FLAT,
                                font=("Segoe UI", 12, "bold"), width=3, height=1,
                                activebackground=self.master.theme.get("chat_send_button_hover", "#1976D2"), 
                                activeforeground="white")
        self.send_btn.pack(side=tk.RIGHT, padx=2, pady=1)
        
        # Text widget for input (auto-resizing) - pack after send button
        self.input_text = tk.Text(self.input_frame, height=1, wrap=tk.WORD, 
                                 bg="white", fg="black", font=("Segoe UI", 10),
                                 relief=tk.FLAT, padx=12, pady=8, borderwidth=0,
                                 insertbackground="black")
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1, pady=1)
        
        # Add placeholder text
        self.placeholder_text = self.master._("Type your message here...")
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(fg="gray")
        
        # Bind events
        self.input_text.bind("<KeyPress>", self._on_input_keypress)
        self.input_text.bind("<KeyRelease>", self._on_input_keyrelease)
        self.input_text.bind("<Return>", self._on_return_press)
        self.input_text.bind("<Shift-Return>", self._on_shift_return_press)
        self.input_text.bind("<FocusIn>", self._on_input_focus_in)
        self.input_text.bind("<FocusOut>", self._on_input_focus_out)
        
        # Focus on input
        self.input_text.focus_set()

    def _on_chat_frame_configure(self, event=None):
        """Update canvas scrollregion when frame size changes."""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def _on_chat_canvas_configure(self, event=None):
        """Update frame width when canvas is resized."""
        try:
            # Get the canvas width
            canvas_width = self.chat_canvas.winfo_width()
            
            # Ensure minimum width
            if canvas_width < 200:
                canvas_width = 200
            
            # Account for scrollbar width and padding
            scrollbar_width = self.chat_scrollbar.winfo_width() if self.chat_scrollbar.winfo_exists() else 20
            padding = 8  # Extra padding to prevent overlap
            
            # Calculate available width for chat content
            available_width = canvas_width - scrollbar_width - padding
            
            # Ensure minimum available width
            if available_width < 150:
                available_width = 150
            
            # Update the chat frame width to use the available space
            self.chat_canvas.itemconfig(self.chat_window, width=available_width)
            
        except Exception as e:
            logger.error(f"Error in canvas configure: {e}")

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_window_resize(self, event=None):
        """Handle window resize events to adjust chat area width."""
        # Handle window resize events - disabled automatic width updates to prevent shrinking
        pass



    def _redraw_messages(self):
        """Redraw existing messages to adjust to new width."""
        try:
            # Get the current theme background color
            chat_bg = self.master.theme.get("chat_bg", "#FFFFFF")
            
            # Force existing text widgets to recalculate their wrapping and remove borders
            for widget in self.chat_frame.winfo_children():
                if isinstance(widget, tk.Frame):  # Message container
                    # Remove any borders from message container and ensure correct background
                    widget.configure(relief=tk.FLAT, borderwidth=0, highlightthickness=0, bg=chat_bg)
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Frame):  # Message frame or bubble frame
                            # Remove any borders from frame and ensure correct background
                            child.configure(relief=tk.FLAT, borderwidth=0, 
                                          highlightthickness=0, highlightbackground=child.cget("bg"),
                                          highlightcolor=child.cget("bg"), bg=chat_bg)
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, tk.Text):
                                    # Temporarily enable to recalculate
                                    grandchild.config(state=tk.NORMAL)
                                    content = grandchild.get("1.0", tk.END + "-1c")
                                    grandchild.delete("1.0", tk.END)
                                    grandchild.insert("1.0", content)
                                    self._resize_text_widget(grandchild)
                                    # Remove any borders from text widget and update selection colors
                                    grandchild.config(state=tk.NORMAL, relief=tk.FLAT, borderwidth=0,
                                                     highlightthickness=0, 
                                                     selectbackground=self.master.theme.get("chat_text_select_bg", "#005a9e"),
                                                     selectforeground=self.master.theme.get("chat_text_select_fg", "#ffffff"), 
                                                     insertwidth=0)
                                elif isinstance(grandchild, tk.Label):  # Name or time labels
                                    # Remove any borders from labels and ensure correct background
                                    grandchild.configure(relief=tk.FLAT, borderwidth=0, highlightthickness=0, bg=chat_bg)
                        elif isinstance(child, tk.Label):  # Name or time labels
                            # Remove any borders from labels and ensure correct background
                            child.configure(relief=tk.FLAT, borderwidth=0, highlightthickness=0, bg=chat_bg)
        except Exception as e:
            logger.error(f"Error redrawing messages: {e}")

    def _on_input_keypress(self, event):
        """Handle input keypress for auto-resize."""
        # Schedule resize check
        self.after(10, self._resize_input)

    def _on_input_keyrelease(self, event):
        """Handle input keyrelease for auto-resize."""
        # Schedule resize check
        self.after(10, self._resize_input)

    def _on_return_press(self, event):
        """Handle Enter key press."""
        if not event.state & 0x1:  # No Shift
            self.send_message()
            return "break"  # Prevent default behavior

    def _on_shift_return_press(self, event):
        """Handle Shift+Enter for new line."""
        # Allow default behavior (new line)
        pass

    def _on_input_focus_in(self, event):
        """Handle input focus in - clear placeholder if present."""
        current_text = self.input_text.get("1.0", tk.END + "-1c")
        if current_text == self.placeholder_text:
            self.input_text.delete("1.0", tk.END)
            self.input_text.config(fg="black")

    def _on_input_focus_out(self, event):
        """Handle input focus out - show placeholder if empty."""
        current_text = self.input_text.get("1.0", tk.END + "-1c")
        if not current_text.strip():
            self.input_text.insert("1.0", self.placeholder_text)
            self.input_text.config(fg="gray")

    def _resize_input(self):
        """Resize input text widget based on content."""
        content = self.input_text.get("1.0", tk.END + "-1c")
        if not content.strip():
            # Reset to minimum height
            self.input_text.configure(height=1)
            return
        
        # Calculate required height
        lines = content.count('\n') + 1
        # Limit height to reasonable bounds
        max_height = 5
        new_height = min(max(1, lines), max_height)
        
        current_height = int(self.input_text.cget("height"))
        if new_height != current_height:
            self.input_text.configure(height=new_height)

    def send_message(self, event=None):
        """Send a message."""
        user_msg = self.input_text.get("1.0", tk.END + "-1c").strip()
        if not user_msg or user_msg == self.placeholder_text:
            return
        
        # Clear input
        self.input_text.delete("1.0", tk.END)
        self._resize_input()
        
        # Add message to conversation
        timestamp = datetime.datetime.now()
        if not self.first_message_time:
            self.first_message_time = timestamp
        
        self.conversation.append({
            "sender": self.master._("You"),
            "message": user_msg,
            "timestamp": timestamp
        })
        
        # Display message
        self.append_message(self.master._("You"), user_msg, timestamp)
        
        # Get AI response
        self.after(100, lambda: self.get_llm_response(user_msg))

    def append_message(self, sender, message, timestamp=None):
        """Add a message bubble to the chat."""
        if timestamp is None:
            timestamp = datetime.datetime.now()
        
        # Create message container with no side padding for maximum width
        msg_container = tk.Frame(self.chat_frame, bg=self.master.theme.get("chat_bg", "#FFFFFF"), 
                               relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        msg_container.pack(fill=tk.X, padx=0, pady=0, expand=True)
        
        # Ensure the message container background matches the theme
        msg_container.configure(bg=self.master.theme.get("chat_bg", "#FFFFFF"))
        
        # Configure grid columns for proper expansion
        msg_container.grid_columnconfigure(0, weight=1)
        
        # Determine alignment and colors
        is_user = sender == self.master._("You")
        if is_user:
            bubble_color = self.user_bubble_color
            text_color = self.user_text_color
        else:
            bubble_color = self.assistant_bubble_color
            text_color = self.assistant_text_color
        
        # Create a frame to hold all message elements vertically aligned
        message_frame = tk.Frame(msg_container, bg=self.master.theme.get("chat_bg", "#FFFFFF"),
                               relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        # All messages span the full width, alignment is handled by the message content
        if is_user:
            message_frame.grid(row=0, column=0, sticky="ew", padx=(40, 8))
        else:
            message_frame.grid(row=0, column=0, sticky="ew", padx=(8, 40))
        
        # Ensure the message frame background matches the theme
        message_frame.configure(bg=self.master.theme.get("chat_bg", "#FFFFFF"))
        
        # Author name (top)
        name_label = tk.Label(message_frame, text=sender, bg=self.master.theme.get("chat_bg", "#FFFFFF"), 
                            fg=self.name_color, font=("Segoe UI", 9, "bold"),
                            relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        name_label.pack(anchor=tk.W if not is_user else tk.E, pady=(0, 0))
        
        # Create bubble frame with modern styling (no borders at all)
        bubble_frame = tk.Frame(message_frame, bg=bubble_color, relief=tk.FLAT, borderwidth=0, 
                               highlightthickness=0, highlightbackground=bubble_color,
                               highlightcolor=bubble_color)
        # Align bubble to left for assistant, right for user
        if is_user:
            bubble_frame.pack(anchor=tk.E, fill=tk.NONE, expand=False)
        else:
            bubble_frame.pack(anchor=tk.W, fill=tk.NONE, expand=False)
        
        # Message text (with markdown support)
        formatted_message = self._format_markdown(message)
        msg_text = tk.Text(bubble_frame, wrap=tk.WORD, bg=bubble_color, fg=text_color,
                         font=("Segoe UI", 10), relief=tk.FLAT, padx=8, pady=4,
                         height=1, cursor="ibeam", borderwidth=0,
                         highlightthickness=0,                          selectbackground=self.master.theme.get("chat_text_select_bg", "#005a9e"),
                         selectforeground=self.master.theme.get("chat_text_select_fg", "#ffffff"), insertwidth=0)
        msg_text.pack(fill=tk.X, expand=True)
        
        # Insert formatted text
        msg_text.insert("1.0", formatted_message)
        
        # Auto-resize text widget to content
        self._resize_text_widget(msg_text)
        
        # Make text selectable but not editable by binding events
        def prevent_edit(event):
            return "break"
        
        # Bind events to prevent editing while allowing selection
        msg_text.bind("<Key>", prevent_edit)
        msg_text.bind("<Button-1>", lambda e: msg_text.focus_set())
        
        # Configure text widget to be read-only but selectable
        msg_text.config(state=tk.NORMAL)
        msg_text.bind("<KeyPress>", prevent_edit)
        msg_text.bind("<KeyRelease>", prevent_edit)
        
        # Add right-click context menu for copy functionality
        def show_context_menu(event):
            try:
                # Create context menu
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label=self.master._("Copy"), 
                                       command=lambda: copy_selected_text())
                context_menu.add_command(label=self.master._("Copy All"), 
                                       command=lambda: copy_all_text())
                context_menu.tk_popup(event.x_root, event.y_root)
            except Exception as e:
                logger.error(f"Error showing context menu: {e}")
        
        def copy_selected_text():
            try:
                selected_text = msg_text.get("sel.first", "sel.last")
                if selected_text:
                    self.clipboard_clear()
                    self.clipboard_append(selected_text)
            except tk.TclError:
                # No text selected
                pass
        
        def copy_all_text():
            try:
                all_text = msg_text.get("1.0", tk.END + "-1c")
                if all_text:
                    self.clipboard_clear()
                    self.clipboard_append(all_text)
            except Exception as e:
                logger.error(f"Error copying all text: {e}")
        
        # Bind right-click to show context menu
        msg_text.bind("<Button-3>", show_context_menu)
        
        # Add keyboard shortcuts for copying
        def copy_on_ctrl_c(event):
            try:
                selected_text = msg_text.get("sel.first", "sel.last")
                if selected_text:
                    self.clipboard_clear()
                    self.clipboard_append(selected_text)
                return "break"  # Prevent default behavior
            except tk.TclError:
                # No text selected, copy all
                all_text = msg_text.get("1.0", tk.END + "-1c")
                if all_text:
                    self.clipboard_clear()
                    self.clipboard_append(all_text)
                return "break"
        
        # Bind Ctrl+C to copy
        msg_text.bind("<Control-c>", copy_on_ctrl_c)
        msg_text.bind("<Control-C>", copy_on_ctrl_c)
        
        # Time label (bottom)
        time_str = timestamp.strftime("%H:%M")
        time_label = tk.Label(message_frame, text=time_str, bg=self.master.theme.get("chat_bg", "#FFFFFF"), 
                            fg=self.time_color, font=("Segoe UI", 8),
                            relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        time_label.pack(anchor=tk.W if not is_user else tk.E, pady=(0, 0))
        
        # Scroll to bottom
        self.chat_canvas.after(10, self._scroll_to_bottom)

    def _format_markdown(self, text):
        """Format markdown text for display."""
        # Convert emojis
        text = self._convert_emojis(text)
        
        # Basic markdown formatting
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'**\1**', text)
        text = re.sub(r'__(.*?)__', r'**\1**', text)
        
        # Italic: *text* or _text_
        text = re.sub(r'\*(.*?)\*', r'*\1*', text)
        text = re.sub(r'_(.*?)_', r'*\1*', text)
        
        # Code: `text`
        text = re.sub(r'`(.*?)`', r'`\1`', text)
        
        # Line breaks
        text = text.replace('\n', '\n')
        
        return text

    def _convert_emojis(self, text):
        """Convert emoji codes to actual emojis."""
        emoji_map = {
            ':smile:': '😊', ':sad:': '😢', ':laugh:': '😄', ':wink:': '😉',
            ':heart:': '❤️', ':thumbsup:': '👍', ':thumbsdown:': '👎',
            ':ok:': '👌', ':pray:': '🙏', ':clap:': '👏', ':fire:': '🔥',
            ':star:': '⭐', ':check:': '✅', ':x:': '❌', ':warning:': '⚠️',
            ':info:': 'ℹ️', ':question:': '❓', ':exclamation:': '❗',
            ':rocket:': '🚀', ':bulb:': '💡', ':gear:': '⚙️', ':link:': '🔗'
        }
        
        for code, emoji in emoji_map.items():
            text = text.replace(code, emoji)
        
        return text

    def _resize_text_widget(self, text_widget):
        """Resize text widget to fit content."""
        try:
            content = text_widget.get("1.0", tk.END + "-1c")
            if not content.strip():
                return
            
            # Calculate required height
            lines = content.count('\n') + 1
            # Get widget width to calculate wrapping
            widget_width = text_widget.winfo_width()
            if widget_width <= 1:  # Widget not yet rendered
                widget_width = 400  # Default width for better initial sizing
            
            # Estimate wrapped lines with better character width calculation
            # Account for padding (24px total) and use more accurate character width
            available_width = widget_width - 24  # 12px padding on each side
            avg_chars_per_line = max(1, available_width // 8)  # More accurate for Segoe UI
            if avg_chars_per_line > 0:
                wrapped_lines = len(textwrap.wrap(content, avg_chars_per_line))
                lines = max(lines, wrapped_lines)
            
            # Set height (minimum 1, maximum 15 for better readability)
            new_height = min(max(1, lines), 15)
            text_widget.configure(height=new_height)
            
        except Exception as e:
            logger.error(f"Error resizing text widget: {e}")

    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        self.chat_canvas.yview_moveto(1.0)

    def get_llm_response(self, user_msg):
        """Get response from LLM using the button configuration."""
        try:
            # Get configuration from button settings
            api_type = self.cfg.get("llm_provider", "openai")
            api_key = self.cfg.get("llm_api_key", "")
            model = self.cfg.get("llm_model", "gpt-3.5-turbo")
            context = self.cfg.get("llm_context", "")
            
            # Validate required fields
            if not api_key:
                error_msg = "API key is required. Please set up your API key in the button settings."
                self._add_error_response(error_msg)
                return
            
            if not model:
                error_msg = "Model is required. Please select a model in the button settings."
                self._add_error_response(error_msg)
                return
            
            # Validate Azure-specific requirements
            if api_type == "azure":
                endpoint = self.cfg.get("llm_endpoint", "")
                if not endpoint:
                    error_msg = "Endpoint URL is required for Azure. Please configure the endpoint URL in the button settings."
                    self._add_error_response(error_msg)
                    return
            
            # Prepare the request
            if api_type == "openai":
                response = self._call_openai_api(user_msg, api_key, model, context)
            elif api_type == "azure":
                response = self._call_azure_api(user_msg, api_key, model, context)
            elif api_type == "gemini":
                response = self._call_gemini_api(user_msg, api_key, model, context)
            else:
                error_msg = f"Unsupported API type: {api_type}"
                self._add_error_response(error_msg)
                return
            
            if response:
                # Add to conversation
                timestamp = datetime.datetime.now()
                self.conversation.append({
                    "sender": self.master._("Assistant"),
                    "message": response,
                    "timestamp": timestamp
                })
                
                # Display response
                self.append_message(self.master._("Assistant"), response, timestamp)
            else:
                self._add_error_response("No response received from the API.")
                
        except Exception as e:
            error_msg = f"Error calling LLM API: {str(e)}"
            self._add_error_response(error_msg)

    def _add_error_response(self, error_msg):
        """Add an error message to the conversation."""
        timestamp = datetime.datetime.now()
        self.conversation.append({
            "sender": self.master._("Assistant"),
            "message": f"❌ {self.master._('Error:')} {error_msg}",
            "timestamp": timestamp
        })
        self.append_message(self.master._("Assistant"), f"❌ {self.master._('Error:')} {error_msg}", timestamp)

    def _call_openai_api(self, user_msg, api_key, model, context):
        """Call OpenAI API."""
        if openai is None:
            raise Exception("OpenAI library not installed. Install with: pip install openai")
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            # Prepare messages
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": user_msg})
            
            # Make request
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _call_azure_api(self, user_msg, api_key, model, context):
        """Call Azure OpenAI API using REST API."""
        try:
            import requests
            
            # Azure configuration
            endpoint = self.cfg.get("llm_endpoint", "")
            api_version = "2024-02-15-preview"  # Fixed API version for Azure OpenAI
            
            if not endpoint:
                raise Exception("Azure endpoint URL not configured")
            
            # Clean up endpoint URL
            endpoint = endpoint.rstrip("/")
            
            # Construct the full URL for Azure OpenAI
            url = f"{endpoint}/openai/deployments/{model}/chat/completions?api-version={api_version}"
            
            # Prepare headers
            headers = {
                "api-key": api_key,
                "Content-Type": "application/json"
            }
            
            # Prepare messages
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": user_msg})
            
            # Prepare request data
            data = {
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Make request
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Azure API returned status {response.status_code}: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except ImportError:
            raise Exception("Requests library not installed. Install with: pip install requests")
        except Exception as e:
            raise Exception(f"Azure API error: {str(e)}")

    def _call_gemini_api(self, user_msg, api_key, model, context):
        """Call Google Gemini API."""
        if genai is None:
            raise Exception("Google Generative AI library not installed. Install with: pip install google-generativeai")
        
        try:
            # Configure API
            genai.configure(api_key=api_key)
            
            # Get model
            if not model or model == "default":
                model = "gemini-pro"
            
            model_instance = genai.GenerativeModel(model)
            
            # Prepare prompt
            prompt = user_msg
            if context:
                prompt = f"{context}\n\nUser: {user_msg}"
            
            # Generate response
            response = model_instance.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def export_chat(self):
        """Export chat to text file."""
        if not self.conversation:
            messagebox.showinfo(self.master._("Export"), self.master._("No messages to export."))
            return
        
        # Generate filename
        timestamp_str = self.first_message_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Export_{self.btn_label}_{timestamp_str}.txt"
        
        # Get save location
        filepath = filedialog.asksaveasfilename(
            title=self.master._("Export Chat"),
            defaultextension=".txt",
            initialfile=filename,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    for msg in self.conversation:
                        timestamp_str = msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"{timestamp_str} - {msg['sender']}: {msg['message']}\n")
                
                messagebox.showinfo(self.master._("Export"), 
                                  self.master._("Chat exported successfully!"))
            except Exception as e:
                messagebox.showerror(self.master._("Export Error"), 
                                   f"{self.master._('Failed to export chat:')} {e}")

    def close(self):
        """Close the chat window."""
        self.destroy()

    def apply_theme(self, theme):
        """Apply theme to the chat window."""
        # Ensure we're using the exact same theme as the main app
        if hasattr(self.master, 'theme'):
            theme = self.master.theme
        
        self.configure(bg=theme["bg"])
        
        # Update topbar colors - force the exact same color as main app
        if hasattr(self, 'topbar'):
            self.topbar.configure(bg=theme["topbar_bg"])
            # Force update all topbar buttons to use the same colors
            for child in self.topbar.winfo_children():
                if isinstance(child, tk.Button):
                    child.configure(bg=theme["topbar_bg"], fg=theme["button_fg"])
        
        # Update chat area colors from theme
        chat_bg = theme.get("chat_bg", "#FFFFFF")
        chat_input_bg = theme.get("chat_input_bg", "#F8F9FA")
        
        # Force update all chat area backgrounds with multiple attempts
        if hasattr(self, 'chat_frame'):
            self.chat_frame.configure(bg=chat_bg)
        if hasattr(self, 'chat_canvas'):
            self.chat_canvas.configure(bg=chat_bg)
            # Force canvas to redraw its background
            self.chat_canvas.update_idletasks()
        if hasattr(self, 'chat_container'):
            self.chat_container.configure(bg=chat_bg)
        if hasattr(self, 'input_container'):
            self.input_container.configure(bg=chat_input_bg)
        
        # Force update the main window background
        self.configure(bg=chat_bg)
        
        # Update input frame and text colors
        if hasattr(self, 'input_frame'):
            # Check if we're in dark mode by looking at the background color
            if theme.get("bg") == "#181c20":  # Dark theme background
                self.input_frame.configure(bg="#404040")
                if hasattr(self, 'input_text'):
                    self.input_text.configure(bg="#404040", fg="white", insertbackground="white")
            else:
                self.input_frame.configure(bg="#F0F0F0")
                if hasattr(self, 'input_text'):
                    self.input_text.configure(bg="white", fg="black", insertbackground="black")
        
        # Update send button colors
        if hasattr(self, 'send_btn'):
            self.send_btn.configure(
                bg=theme.get("chat_send_button", "#2196F3"),
                activebackground=theme.get("chat_send_button_hover", "#1976D2")
            )
        
        # Update scrollbar colors
        if hasattr(self, 'chat_scrollbar') and self.chat_scrollbar.winfo_exists():
            self.chat_scrollbar.configure(
                bg=theme.get("scrollbar_bg", "#c0c0c0"),
                troughcolor=theme.get("scrollbar_trough", "#f0f0f0"),
                activebackground=theme.get("scrollbar_bg", "#c0c0c0"),
                relief=tk.FLAT, borderwidth=0
            )
        
        # Update bubble and text colors from theme
        self.user_bubble_color = theme.get("chat_user_bubble", "#E3F2FD")
        self.assistant_bubble_color = theme.get("chat_assistant_bubble", "#F5F5F5")
        self.user_text_color = theme.get("chat_user_text", "#000000")
        self.assistant_text_color = theme.get("chat_assistant_text", "#000000")
        self.time_color = theme.get("chat_time_color", "#999999")
        self.name_color = theme.get("chat_name_color", "#666666")
        
        # Update selection colors
        self.text_select_bg = theme.get("chat_text_select_bg", "#005a9e")
        self.text_select_fg = theme.get("chat_text_select_fg", "#ffffff")
        
        # Force a redraw of existing messages to apply new theme colors
        self.after(50, self._redraw_messages)
        
        # Force another theme application after a delay to ensure canvas background is set
        self.after(100, lambda: self._force_canvas_background(chat_bg))
        
        # Force topbar color update again after a delay
        self.after(150, lambda: self._force_topbar_color(theme["topbar_bg"]))
        
        apply_theme_recursive(self, theme)
    
    def _set_initial_width(self):
        """Set the initial canvas width to prevent messages from being too wide."""
        try:
            if hasattr(self, 'chat_canvas') and self.chat_canvas.winfo_exists():
                # Get the current window width
                window_width = self.winfo_width()
                if window_width <= 1:  # Window not yet fully rendered
                    # Try again after a short delay
                    self.after(100, self._set_initial_width)
                    return
                
                # Calculate proper width accounting for scrollbar
                scrollbar_width = self.chat_scrollbar.winfo_width() if self.chat_scrollbar.winfo_exists() else 20
                padding = 12  # Extra padding to prevent overlap
                
                # Calculate available width for chat content
                available_width = window_width - scrollbar_width - padding
                
                # Ensure minimum available width
                if available_width < 150:
                    available_width = 150
                
                # Update the chat frame width
                if hasattr(self, 'chat_window'):
                    self.chat_canvas.itemconfig(self.chat_window, width=available_width)
                    
                # Force a redraw to ensure the width is applied
                self.chat_canvas.update_idletasks()
                
        except Exception as e:
            logger.error(f"Error setting initial width: {e}")
            # Try again after a short delay if there was an error
            self.after(100, self._set_initial_width)

    def _force_canvas_background(self, bg_color):
        """Force the canvas background to be set properly."""
        try:
            if hasattr(self, 'chat_canvas') and self.chat_canvas.winfo_exists():
                self.chat_canvas.configure(bg=bg_color)
                # Force a complete redraw
                self.chat_canvas.delete("all")
                # Recreate the window
                if hasattr(self, 'chat_window'):
                    self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
                # Force update
                self.chat_canvas.update_idletasks()
        except Exception as e:
            logger.error(f"Error forcing canvas background: {e}")

    def _force_topbar_color(self, topbar_bg):
        """Force the topbar to use the exact same color as the main app."""
        try:
            if hasattr(self, 'topbar') and self.topbar.winfo_exists():
                self.topbar.configure(bg=topbar_bg)
                # Force update all topbar children
                for child in self.topbar.winfo_children():
                    if isinstance(child, tk.Button):
                        child.configure(bg=topbar_bg)
                    elif isinstance(child, tk.Frame):
                        child.configure(bg=topbar_bg)
                # Force update
                self.topbar.update_idletasks()
        except Exception as e:
            logger.error(f"Error forcing topbar color: {e}") 