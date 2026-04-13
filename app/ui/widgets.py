from __future__ import annotations

import tkinter as tk


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tip_window: tk.Toplevel | None = None
        self.label: tk.Label | None = None
        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<Motion>", self._on_motion, add="+")

    def set_text(self, text: str) -> None:
        self.text = text
        if self.label is not None:
            self.label.config(text=text)

    def _on_enter(self, event=None) -> None:
        self._show(event)

    def _on_leave(self, _event=None) -> None:
        self._hide()

    def _on_motion(self, event=None) -> None:
        if self.tip_window is not None and event is not None:
            self.tip_window.geometry(f"+{event.x_root + 12}+{event.y_root + 12}")

    def _show(self, event=None) -> None:
        if self.tip_window is not None:
            return
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        x = (event.x_root + 12) if event is not None else (self.widget.winfo_rootx() + 12)
        y = (event.y_root + 12) if event is not None else (self.widget.winfo_rooty() + 12)
        self.tip_window.geometry(f"+{x}+{y}")
        self.label = tk.Label(
            self.tip_window,
            text=self.text,
            background="#111827",
            foreground="#F9FAFB",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=4,
            font=("Segoe UI", 9),
        )
        self.label.pack()

    def _hide(self) -> None:
        if self.tip_window is not None:
            self.tip_window.destroy()
            self.tip_window = None
            self.label = None
