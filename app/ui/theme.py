from __future__ import annotations

from typing import Callable
from tkinter import ttk


class Theme:
    BG = "#F3F5F9"
    CARD = "#FFFFFF"
    TEXT = "#0F172A"
    SUB = "#64748B"
    ACCENT = "#2563EB"
    BORDER = "#CBD5E1"
    BADGE_BG = "#EEF2FF"


def setup_style(level_color_fn: Callable[[int], str]) -> None:
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Main.TFrame", background=Theme.BG)
    style.configure("Card.TFrame", background=Theme.CARD)
    style.configure("Card.TLabelframe", background=Theme.CARD,
                    bordercolor=Theme.BORDER, relief="solid")
    style.configure("Card.TLabelframe.Label", background=Theme.CARD,
                    foreground=Theme.TEXT, font=("Segoe UI", 10, "bold"))
    style.configure("Title.TLabel", background=Theme.BG,
                    foreground=Theme.TEXT, font=("Segoe UI", 17, "bold"))
    style.configure("Sub.TLabel", background=Theme.BG,
                    foreground=Theme.SUB, font=("Segoe UI", 9))
    style.configure("CardLabel.TLabel", background=Theme.CARD,
                    foreground=Theme.TEXT, font=("Segoe UI", 10))
    style.configure("Value.TLabel", background=Theme.CARD,
                    foreground=Theme.TEXT, font=("Segoe UI", 11))
    style.configure("ValueStrong.TLabel", background=Theme.CARD,
                    foreground=Theme.TEXT, font=("Segoe UI", 11, "bold"))
    style.configure("Badge.TLabel", background=Theme.BADGE_BG,
                    foreground="#1E3A8A", font=("Segoe UI", 10, "bold"))
    style.configure(
        "Metric.TLabel",
        background="#E9EEF5",
        foreground=Theme.TEXT,
        font=("Segoe UI", 10, "bold"),
        padding=(10, 4),
    )

    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=(14, 7),
        background="#5B7FA3",
        foreground="#FFFFFF",
        borderwidth=0,
        relief="flat",
        focusthickness=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#507395"), ("pressed", "#466787")],
        foreground=[("disabled", "#D1D5DB")],
    )

    style.configure(
        "Ghost.TButton",
        font=("Segoe UI", 10),
        padding=(12, 7),
        background="#E8ECF1",
        foreground=Theme.TEXT,
        borderwidth=0,
        relief="flat",
        focusthickness=0,
    )
    style.map(
        "Ghost.TButton",
        background=[("active", "#DCE3EA"), ("pressed", "#D1DAE3")],
        foreground=[("disabled", "#9CA3AF")],
    )

    style.configure("TEntry", fieldbackground="#FFFFFF", foreground=Theme.TEXT,
                    insertcolor=Theme.TEXT, bordercolor=Theme.BORDER)
    style.configure("TCombobox", fieldbackground="#FFFFFF",
                    foreground=Theme.TEXT, bordercolor=Theme.BORDER)
    style.configure(
        "Slim.Vertical.TScrollbar",
        background="#D6DEE8",
        troughcolor="#F3F6FA",
        bordercolor="#F3F6FA",
        darkcolor="#D6DEE8",
        lightcolor="#D6DEE8",
        arrowcolor="#94A3B8",
        relief="flat",
        gripcount=0,
        width=8,
    )
    style.map(
        "Slim.Vertical.TScrollbar",
        background=[("active", "#BFCBDA"), ("pressed", "#AEBCCD")],
    )

    for lvl in (1, 2, 3, 4, 5):
        level_style = f"Level{lvl}.Card.TLabelframe"
        style.configure(
            level_style,
            background=Theme.CARD,
            bordercolor=Theme.BORDER,
            relief="solid",
        )
        style.configure(
            f"Level{lvl}.Card.TLabelframe.Label",
            background=Theme.CARD,
            foreground=level_color_fn(lvl),
            font=("Segoe UI", 10, "bold"),
        )
