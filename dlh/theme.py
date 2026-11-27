"""Tema escuro verde/dourado para Tkinter/ttk."""
import tkinter as tk
from tkinter import ttk

PALETTE = {
    "bg": "#081B1B",
    "card": "#203B37",
    "line": "#2f524c",
    "text": "#EEE8B2",
    "muted": "#96CDB0",
    "gold": "#C18D52",
    "gold_hover": "#d6a873",
    "on_gold": "#081B1B",
    "error": "#ef8a74",
}

FONT = "Segoe UI"
FONT_BOLD = "Segoe UI Semibold"


def apply(root: tk.Tk) -> ttk.Style:
    p = PALETTE
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=p["bg"])
    base = (FONT, 10)

    style.configure(".", background=p["bg"], foreground=p["text"], font=base,
                    bordercolor=p["line"], lightcolor=p["line"],
                    darkcolor=p["line"], troughcolor=p["card"],
                    focuscolor=p["gold"], insertcolor=p["text"])
    style.map(".", foreground=[("disabled", p["muted"])])

    style.configure("TFrame", background=p["bg"])
    style.configure("Card.TFrame", background=p["card"])
    style.configure("TLabel", background=p["bg"], foreground=p["text"])
    style.configure("Title.TLabel", font=(FONT_BOLD, 20), foreground=p["gold"])
    style.configure("Sub.TLabel", foreground=p["muted"])
    style.configure("Step.TLabel", font=(FONT_BOLD, 11), foreground=p["gold"])
    style.configure("Muted.TLabel", foreground=p["muted"])

    style.configure("TLabelframe", background=p["bg"], bordercolor=p["line"])
    style.configure("TLabelframe.Label", background=p["bg"],
                    foreground=p["gold"], font=(FONT_BOLD, 10))
    style.configure("Card.TLabelframe", background=p["card"],
                    bordercolor=p["line"])
    style.configure("Card.TLabelframe.Label", background=p["card"],
                    foreground=p["gold"], font=(FONT_BOLD, 10))

    style.configure("TButton", background=p["card"], foreground=p["text"],
                    bordercolor=p["line"], padding=(10, 5))
    style.map("TButton",
              background=[("disabled", p["bg"]), ("pressed", p["line"]),
                          ("active", p["line"])],
              foreground=[("disabled", p["line"])])
    style.configure("Gold.TButton", background=p["gold"],
                    foreground=p["on_gold"], bordercolor=p["gold"],
                    font=(FONT_BOLD, 10), padding=(12, 6))
    style.map("Gold.TButton",
              background=[("disabled", p["line"]),
                          ("pressed", p["gold_hover"]),
                          ("active", p["gold_hover"])],
              foreground=[("disabled", p["muted"])],
              bordercolor=[("disabled", p["line"])])

    field = dict(fieldbackground=p["card"], foreground=p["text"],
                 background=p["card"], insertcolor=p["text"],
                 bordercolor=p["line"])
    style.configure("TEntry", **field)
    style.configure("TSpinbox", arrowcolor=p["text"], **field)
    style.configure("TCombobox", arrowcolor=p["text"],
                    selectbackground=p["card"], selectforeground=p["text"],
                    **field)
    for name in ("TEntry", "TSpinbox", "TCombobox"):
        style.map(name,
                  fieldbackground=[("disabled", p["bg"]),
                                   ("readonly", p["card"])],
                  foreground=[("disabled", p["muted"])],
                  bordercolor=[("focus", p["gold"])])

    style.configure("TNotebook", background=p["bg"], bordercolor=p["line"])
    style.configure("TNotebook.Tab", background=p["card"],
                    foreground=p["muted"], padding=(14, 6))
    style.map("TNotebook.Tab",
              background=[("selected", p["bg"])],
              foreground=[("selected", p["gold"])])

    style.configure("Treeview", background=p["card"], fieldbackground=p["card"],
                    foreground=p["text"], bordercolor=p["line"], rowheight=24)
    style.map("Treeview",
              background=[("selected", p["gold"])],
              foreground=[("selected", p["on_gold"])])
    style.configure("Treeview.Heading", background=p["bg"],
                    foreground=p["gold"], font=(FONT_BOLD, 10),
                    bordercolor=p["line"])
    style.map("Treeview.Heading", background=[("active", p["card"])])

    style.configure("TScrollbar", background=p["line"], troughcolor=p["card"],
                    bordercolor=p["card"], arrowcolor=p["text"])
    style.map("TScrollbar", background=[("active", p["gold"])])
    style.configure("TProgressbar", background=p["gold"],
                    troughcolor=p["card"], bordercolor=p["line"])
    style.configure("TSeparator", background=p["line"])

    # Popup da Combobox e Listbox/Text classicos (nao sao ttk).
    root.option_add("*TCombobox*Listbox.background", p["card"])
    root.option_add("*TCombobox*Listbox.foreground", p["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", p["gold"])
    root.option_add("*TCombobox*Listbox.selectForeground", p["on_gold"])
    root.option_add("*TCombobox*Listbox.font", base)
    return style


def dark_titlebar(root: tk.Tk) -> None:
    """Pede barra de titulo escura ao Windows 10/11; ignora se indisponivel."""
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass
