"""Estilo comun para todas las figuras de la memoria.

Cada script de figura importa `aplicar_estilo()` y `guardar()`. La salida va
en PDF vectorial a "plantilla latex/graficos/", que es donde LaTeX la busca.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Azul de los titulos de la memoria (preambulo.tex: rgb 0.1, 0.2, 0.4)
AZUL = "#1A3366"
GRIS = "#666666"
NARANJA = "#C1622B"
VERDE = "#3F7A4E"

DESTINO = Path(__file__).resolve().parent.parent / "plantilla latex" / "graficos"


def aplicar_estilo():
    """Fuente serif y rejilla discreta, para que la figura no desentone."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.edgecolor": GRIS,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": "#DDDDDD",
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "xtick.color": GRIS,
        "ytick.color": GRIS,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })


def guardar(fig, nombre):
    """Guarda en PDF (vectorial, para LaTeX) y PNG (para mirarlo rapido)."""
    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta_pdf = DESTINO / f"{nombre}.pdf"
    fig.savefig(ruta_pdf)
    fig.savefig(DESTINO / f"{nombre}.png", dpi=200)
    plt.close(fig)
    print(f"generado: {ruta_pdf.name}")
