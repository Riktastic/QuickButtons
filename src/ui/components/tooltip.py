"""Tooltip component for Tkinter widgets."""

import tkinter as tk

class Tooltip:
    """Tooltip class for Tkinter widgets."""
    
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self._text = text  # Set the _text attribute properly
        self.delay = delay  # milliseconds
        self._id = None
        self._tipwindow = None
        self._x = self._y = 0
        widget.bind('<Enter>', self._enter, add='+')
        widget.bind('<Leave>', self._leave, add='+')
        widget.bind('<ButtonPress>', self._leave, add='+')

    def _enter(self, event=None):
        self._schedule()

    def _leave(self, event=None):
        self._unschedule()
        self._hide_tip()

    def _schedule(self):
        self._unschedule()
        self._id = self.widget.after(self.delay, self._show_tip)

    def _unschedule(self):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None

    def _show_tip(self, event=None):
        if self._tipwindow or not self.text:
            return
        
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() + 20
        self._tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)  # Ensure tooltip appears above pinned application
        
        # Try to get theme colors from the widget's master
        try:
            if hasattr(self.widget, 'master') and hasattr(self.widget.master, 'theme'):
                theme = self.widget.master.theme
                bg_color = theme.get("tooltip_bg", "#ffffe0")
                fg_color = theme.get("tooltip_fg", "#000000")
            else:
                bg_color = "#ffffe0"
                fg_color = "#000000"
        except:
            bg_color = "#ffffe0"
            fg_color = "#000000"
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background=bg_color, foreground=fg_color,
                         relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=4, ipady=2)

    def _hide_tip(self):
        tw = self._tipwindow
        self._tipwindow = None
        if tw:
            tw.destroy()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        # If tooltip is visible, update it
        if hasattr(self, '_tipwindow') and self._tipwindow:
            for child in self._tipwindow.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(text=value) 