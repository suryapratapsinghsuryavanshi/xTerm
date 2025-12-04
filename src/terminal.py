"""
Custom Tkinter Widget for Terminal Emulation.
"""
import tkinter as tk
from tkinter import font
import os
import pyte

class TerminalWidget(tk.Text):
    """
    A Tkinter Text widget that acts as a VT100/xterm emulator using Pyte.
    """
    def __init__(self, master, rows=24, cols=80, **kwargs):
        super().__init__(master, **kwargs)
        self.rows = rows
        self.cols = cols
        
        # Pyte Emulation
        self.screen = pyte.HistoryScreen(self.cols, self.rows, history=1000, ratio=0.5)
        self.stream = pyte.Stream(self.screen)
        
        # State
        self.screen_dirty = False
        self.cursor_visible = True
        self.resize_timer = None
        self.on_input_callback = None  # Function to call when user types

        self._configure_appearance()
        self.bind_events()

    def _configure_appearance(self):
        """Sets up fonts and colors."""
        font_family = "Consolas" if "nt" in os.name else "Monospace"
        self.term_font = font.Font(family=font_family, size=11)
        self.char_width = self.term_font.measure("M")
        self.char_height = self.term_font.metrics("linespace")

        self.configure(
            bg="#1e1e1e", fg="#cccccc", font=self.term_font,
            state=tk.DISABLED, wrap=tk.NONE, insertbackground="white",
            padx=5, pady=5
        )

        # ANSI Colors
        colors = {
            "red": "#ff5555", "green": "#50fa7b", "blue": "#bd93f9",
            "cyan": "#8be9fd", "magenta": "#ff79c6", "yellow": "#f1fa8c",
            "white": "#ffffff", "black": "#000000"
        }
        self.tag_configure("cursor", background="#cccccc", foreground="black")
        self.tag_configure("default", foreground="#cccccc")
        for name, code in colors.items():
            self.tag_configure(name, foreground=code)

    def bind_events(self):
        """Binds keyboard and resize events."""
        self.bind("<Key>", self._on_key_press)
        self.bind("<Configure>", self._on_resize)

    def feed(self, data):
        """Feeds data from SSH into the emulator."""
        self.stream.feed(data)
        self.screen_dirty = True

    def redraw(self):
        """Draws the screen buffer to the Text widget."""
        if not self.screen_dirty:
            return

        self.config(state=tk.NORMAL)
        self.delete("1.0", tk.END)

        for r in range(self.screen.lines):
            line_data = self.screen.buffer.get(r, {})
            current_col = 0
            while current_col < self.cols:
                if current_col in line_data:
                    char = line_data[current_col]
                    fg = char.fg
                    if fg == "brown": fg = "yellow"
                    if fg not in ["red", "green", "blue", "cyan", "magenta", "yellow", "white", "black"]:
                        fg = "default"
                    self.insert(tk.END, char.data, fg)
                else:
                    self.insert(tk.END, " ")
                current_col += 1
            self.insert(tk.END, "\n")
        
        self._update_cursor()
        self.config(state=tk.DISABLED)
        self.see(tk.END)
        self.screen_dirty = False

    def _update_cursor(self):
        self.tag_remove("cursor", "1.0", tk.END)
        if self.cursor_visible:
            cy, cx = self.screen.cursor.y, self.screen.cursor.x
            if cy < self.rows and cx < self.cols:
                self.tag_add("cursor", f"{cy + 1}.{cx}")

    def toggle_cursor(self):
        """Blinks the cursor."""
        self.cursor_visible = not self.cursor_visible
        if not self.screen_dirty:
            self._update_cursor()

    def _on_key_press(self, event):
        """Handles keyboard input and sends it to the callback."""
        if not self.on_input_callback:
            return "break"

        mapping = {
            "Return": "\r", "BackSpace": "\x08", "Tab": "\t",
            "Up": "\x1b[A", "Down": "\x1b[B", "Left": "\x1b[D", "Right": "\x1b[C",
            "Escape": "\x1b"
        }
        
        out = mapping.get(event.keysym)
        if not out and len(event.char) == 1 and ord(event.char) >= 32:
            out = event.char
            
        if out:
            self.on_input_callback(out)
            self.cursor_visible = True
            self._update_cursor()
        
        return "break"

    def _on_resize(self, event):
        """Debounces resize events."""
        if self.resize_timer:
            self.after_cancel(self.resize_timer)
        self.resize_timer = self.after(200, self._calculate_dimensions)

    def _calculate_dimensions(self):
        w = self.winfo_width()
        h = self.winfo_height()
        new_cols = int(w / self.char_width) - 2
        new_rows = int(h / self.char_height)
        
        if new_cols < 10 or new_rows < 5:
            return

        if new_cols != self.cols or new_rows != self.rows:
            self.cols = new_cols
            self.rows = new_rows
            self.screen.resize(self.rows, self.cols)
            self.screen_dirty = True
            # Return new dimensions to be handled by controller if needed
            return self.cols, self.rows