"""Aparência da interface: paleta de cores, fontes e estilos dos widgets ttk."""

import tkinter.font as tkfont
from tkinter import ttk

# Paleta
BG = "#0f172a"
PAINEL = "#1e293b"
BORDA = "#334155"
TEXTO = "#e2e8f0"
APAGADO = "#64748b"
CINZA = "#94a3b8"
AZUL = "#60a5fa"
VERDE = "#4ade80"
VERMELHO = "#f87171"
AMARELO = "#facc15"
ROXO = "#c4b5fd"

CORES = {"alice": AZUL, "bob": VERDE, "meio": VERMELHO}
NOMES_COR = {"texto": TEXTO, "cinza": CINZA, "verde": VERDE, "vermelho": VERMELHO, "amarelo": AMARELO}


def criar_fontes():
    return {
        "normal": tkfont.Font(family="Helvetica", size=11),
        "negrito": tkfont.Font(family="Helvetica", size=11, weight="bold"),
        "titulo": tkfont.Font(family="Helvetica", size=15, weight="bold"),
        "no": tkfont.Font(family="Helvetica", size=13, weight="bold"),
        "status": tkfont.Font(family="Helvetica", size=14, weight="bold"),
        "mono": tkfont.Font(family="Courier", size=10),
        "msg": tkfont.Font(family="Helvetica", size=14, weight="bold"),
        "exp": tkfont.Font(family="Helvetica", size=13),
    }


def aplicar(f):
    """Configura os estilos ttk usados na interface (f: fontes de criar_fontes)."""
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("TCheckbutton", background=BG, foreground=TEXTO, font=f["negrito"],
                indicatorbackground=PAINEL, indicatorforeground=AMARELO)
    s.map("TCheckbutton", background=[("active", BG)],
          foreground=[("disabled", APAGADO)])
    s.configure("Painel.TCheckbutton", background=PAINEL, font=f["normal"])
    s.map("Painel.TCheckbutton", background=[("active", PAINEL)])
    s.configure("Acao.TButton", background="#2563eb", foreground="white",
                font=f["negrito"], borderwidth=0, padding=(16, 7))
    s.map("Acao.TButton", background=[("disabled", BORDA), ("active", "#1d4ed8")],
          foreground=[("disabled", APAGADO)])
    s.configure("Sec.TButton", background=BORDA, foreground=TEXTO,
                font=f["normal"], borderwidth=0, padding=(12, 7))
    s.map("Sec.TButton", background=[("disabled", PAINEL), ("active", "#475569")],
          foreground=[("disabled", APAGADO)])
    s.configure("Vertical.TScrollbar", background=BORDA, troughcolor=PAINEL,
                bordercolor=PAINEL, arrowcolor=CINZA, lightcolor=BORDA, darkcolor=BORDA)
    s.map("Vertical.TScrollbar", background=[("active", "#475569")])
    s.configure("TEntry", fieldbackground=BG, foreground=TEXTO, insertcolor=TEXTO,
                bordercolor=BORDA, lightcolor=BORDA, darkcolor=BORDA, padding=6)
    s.map("TEntry", fieldbackground=[("disabled", PAINEL)], foreground=[("disabled", APAGADO)])
