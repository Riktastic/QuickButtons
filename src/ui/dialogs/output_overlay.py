"""Output overlay dialog for QuickButtons application."""

import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import sys
import os

from src.ui.themes import apply_theme_recursive
from src.utils.logger import logger
from src.utils.system import get_python_executable


class OutputOverlay(tk.Toplevel):
    """A floating window to show script output and handle input."""
    
    def __init__(self, master, script_path, args=None, btn_label=None, config=None):
        super().__init__(master)
        self.master = master
        self.config = config
        # Show label in title bar
        title = master._("Script Output")
        if btn_label:
            title = f"{title} - {btn_label}"
        self.title(title)
        self.geometry("600x220+200+200")
        self.configure(bg=master.theme["bg"])
        self.attributes("-topmost", True)
        
        # Set window icon
        try:
            from src.core.constants import ICON_ICO_PATH
            self.iconbitmap(ICON_ICO_PATH)
        except Exception as e:
            logger.warning(f"Could not set output overlay icon: {e}")
        
        main_frame = tk.Frame(self, bg=master.theme["bg"])
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        text_frame = tk.Frame(main_frame, bg=master.theme["bg"])
        text_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        self.text_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                         bg=master.theme.get("scrollbar_bg", "#c0c0c0"),
                                         troughcolor=master.theme.get("scrollbar_trough", "#f0f0f0"),
                                         activebackground=master.theme.get("scrollbar_bg", "#c0c0c0"),
                                         relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        self.text_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.text = tk.Text(text_frame, bg=master.theme["bg"], fg=master.theme["button_fg"], 
                           insertbackground=master.theme["button_fg"], font=("Consolas", 11), 
                           state="disabled", yscrollcommand=self.text_scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        self.text_scrollbar.config(command=self.text.yview)
        
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(main_frame, textvariable=self.input_var, bg=master.theme["bg"], 
                                   fg=master.theme["button_fg"], insertbackground=master.theme["button_fg"], 
                                   font=("Consolas", 11))
        self.input_entry.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        main_frame.grid_rowconfigure(1, weight=0)
        
        self.input_entry.bind("<Return>", self.send_input)
        
        self.input_placeholder = master._("Type your input here...")
        self._set_input_placeholder()
        self.input_entry.bind("<FocusIn>", self._clear_input_placeholder)
        self.input_entry.bind("<FocusOut>", self._set_input_placeholder)
        
        self.proc = None
        self.waiting_for_input = False
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._error_occurred = False
        self._user_closed = False
        
        self.run_script(script_path, args or [])

    def run_script(self, script_path, args):
        """Run the script and capture its output."""
        logger.info(f"OutputOverlay.run_script called with: script_path={script_path}, args={args}")
        
        self.text.config(state="normal")
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, "Running...\n")
        self.text.config(state="disabled")
        
        try:
            # Check if script file exists
            if not os.path.exists(script_path):
                error_msg = f"Script file not found: {script_path}"
                logger.error(error_msg)
                self.text.config(state="normal")
                self.text.insert(tk.END, f"{self.master._('Error:')} {error_msg}\n")
                self.text.config(state="disabled")
                self.input_entry.config(state="disabled")
                self._error_occurred = True
                self.title(self.title() + " - ERROR")
                messagebox.showerror(self.master._("Error"), error_msg)
                return
            
            # Determine if it's a Python script
            is_python = script_path.endswith('.py')
            
            if is_python:
                # For Python scripts, use the appropriate Python interpreter
                python_exe = get_python_executable(self.config)
                logger.info(f"Python executable from config: '{python_exe}'")
                if not python_exe:
                    error_msg = self.master._("No Python executable found. Please configure Python in settings.")
                    logger.error(error_msg)
                    self.text.config(state="normal")
                    self.text.insert(tk.END, f"{self.master._('Error:')} {error_msg}\n")
                    self.text.config(state="disabled")
                    self.input_entry.config(state="disabled")
                    self._error_occurred = True
                    self.title(self.title() + " - ERROR")
                    messagebox.showerror(self.master._("Error"), error_msg)
                    return
                
                # Check if Python executable exists
                if not os.path.exists(python_exe) and not python_exe in ['python', 'python3']:
                    error_msg = f"Python executable not found: {python_exe}"
                    logger.error(error_msg)
                    self.text.config(state="normal")
                    self.text.insert(tk.END, f"{self.master._('Error:')} {error_msg}\n")
                    self.text.config(state="disabled")
                    self.input_entry.config(state="disabled")
                    self._error_occurred = True
                    self.title(self.title() + " - ERROR")
                    messagebox.showerror(self.master._("Error"), error_msg)
                    return
                
                cmd = [python_exe, '-u', script_path] + args
                logger.info(f"Running Python script: {' '.join(cmd)}")
            else:
                # For other scripts, try to execute directly
                cmd = [script_path] + args
                logger.info(f"Running script: {' '.join(cmd)}")
            
            # Set up environment
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"  # Ensure Python output is not buffered
            
            logger.info(f"About to start subprocess with cmd: {cmd}")
            
            # Prepare subprocess creation flags
            creation_flags = 0
            if sys.platform.startswith("win"):
                # Hide console window on Windows
                import subprocess
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            # Create subprocess with proper settings
            self.proc = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True, 
                bufsize=1,  # Line buffered
                encoding="utf-8", 
                env=env,
                errors='replace',  # Handle encoding errors gracefully
                creationflags=creation_flags if sys.platform.startswith("win") else 0
            )
            
            logger.info(f"Script process started with PID: {self.proc.pid}")
            
        except Exception as e:
            error_msg = f"Failed to start script: {e}"
            logger.error(error_msg)
            self.text.config(state="normal")
            self.text.insert(tk.END, f"{self.master._('Error:')} {error_msg}\n")
            self.text.config(state="disabled")
            self.input_entry.config(state="disabled")
            self._error_occurred = True
            self.title(self.title() + " - ERROR")
            messagebox.showerror(self.master._("Error"), error_msg)
            return
        
        self.waiting_for_input = False
        logger.info("Starting output reading thread")
        threading.Thread(target=self.read_output, daemon=True).start()
        self.deiconify()
        self.lift()

    def read_output(self):
        """Read output from the script process."""
        logger.info("read_output thread started")
        error_occurred = False
        output_received = False
        
        try:
            # Read output line by line
            logger.info("Starting to read from stdout")
            for line in iter(self.proc.stdout.readline, ''):
                if line:  # Check if line is not empty
                    output_received = True
                    logger.info(f"Received output line: {line.strip()}")
                    # Ensure we're on the main thread when updating UI
                    self.after(0, self._append_output, line)
            
            # Wait for process to complete
            logger.info("Finished reading output, waiting for process to complete")
            exit_code = self.proc.wait()
            logger.info(f"Script completed with exit code: {exit_code}")
            
            if exit_code != 0:
                # Check if user manually closed the window
                if self._user_closed:
                    logger.info(f"Script terminated by user closing window (exit code: {exit_code})")
                    # Don't mark as error for user termination
                # Check if this was a user-initiated termination (common exit codes for termination)
                elif exit_code in [-1, 1, 2, 3, 15]:  # Common termination signals
                    logger.info(f"Script terminated by user (exit code: {exit_code})")
                    # Don't mark as error for user termination
                else:
                    error_occurred = True
                    logger.warning(f"Script failed with exit code: {exit_code}")
                    # Add more detailed error information
                    self.after(0, self._append_output, f"\n{self.master._('Script failed with exit code:')} {exit_code}\n")
                
        except Exception as e:
            error_msg = f"Error reading script output: {e}"
            logger.error(error_msg)
            self.after(0, self._append_output, f"\n{self.master._('Error:')} {error_msg}\n")
            self.input_entry.config(state="disabled")
            self._error_occurred = True
            self.title(self.title() + " - ERROR")
            messagebox.showerror(self.master._("Error"), error_msg)
            return
        
        # Finalize the output
        logger.info(f"Finalizing output: output_received={output_received}, error_occurred={error_occurred}")
        self.after(0, self._finalize_output, output_received, error_occurred)

    def _append_output(self, line):
        """Append a line of output to the text widget (called on main thread)."""
        try:
            self.text.config(state="normal")
            self.text.insert(tk.END, line)
            self.text.see(tk.END)
            self.text.config(state="disabled")
            self.text.yview_moveto(1.0)
        except Exception as e:
            logger.error(f"Error appending output: {e}")

    def _finalize_output(self, output_received, error_occurred):
        """Finalize the output display (called on main thread)."""
        try:
            self.input_entry.config(state="disabled")
            
            if not output_received:
                self.text.config(state="normal")
                self.text.insert(tk.END, self.master._("(No output generated)\n"))
                self.text.config(state="disabled")
                self.text.yview_moveto(1.0)
            
            # Update title based on result
            if error_occurred or self._error_occurred:
                if " - ERROR" not in self.title():
                    self.title(self.title() + " - ERROR")
            else:
                # Remove ERROR if present
                if " - ERROR" in self.title():
                    self.title(self.title().replace(" - ERROR", ""))
                # Auto-close after a delay if successful
                self.after(2000, self.close)
                
        except Exception as e:
            logger.error(f"Error finalizing output: {e}")

    def send_input(self, event=None):
        """Send user input to the script's stdin."""
        if self.proc and self.proc.poll() is None:
            user_input = self.input_var.get() + '\n'
            try:
                self.proc.stdin.write(user_input)
                self.proc.stdin.flush()
                logger.info(f"Sent input to script: {user_input.strip()}")
            except Exception as e:
                logger.error(f"Error sending input to script: {e}")
            self.input_var.set("")

    def close(self):
        """Close the overlay and terminate the script if running."""
        self._user_closed = True
        try:
            if self.proc and self.proc.poll() is None:
                logger.info("User closed window - terminating script process")
                self.proc.terminate()
                # Give it a moment to terminate gracefully
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    logger.warning("Script did not terminate gracefully, killing it")
                    self.proc.kill()
        except Exception as e:
            logger.error(f"Error closing script: {e}")
        finally:
            self.withdraw()

    def _set_input_placeholder(self, event=None):
        if not self.input_var.get():
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, self.input_placeholder)
            self.input_entry.config(fg="#888888")

    def _clear_input_placeholder(self, event=None):
        if self.input_entry.get() == self.input_placeholder:
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(fg=self.master.theme["button_fg"])

    def apply_theme(self, theme):
        apply_theme_recursive(self, theme)
        
        # Update scrollbar colors
        if hasattr(self, 'text_scrollbar') and self.text_scrollbar.winfo_exists():
            self.text_scrollbar.configure(
                bg=theme.get("scrollbar_bg", "#c0c0c0"),
                troughcolor=theme.get("scrollbar_trough", "#f0f0f0"),
                activebackground=theme.get("scrollbar_bg", "#c0c0c0"),
                relief=tk.FLAT, borderwidth=0
            ) 