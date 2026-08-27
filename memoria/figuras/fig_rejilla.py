"""Mosaico de la rejilla horneada desde el decodificador.

Se dibuja uno de cada tres nodos de la rejilla 16x16, es decir, las filas y
columnas 0, 3, 6, 9, 12 y 15, para que las ondas sean legibles. Aun con ese
submuestreo se aprecia que las celdas vecinas se parecen entre si y que el
recorrido del plano es continuo.

Los datos vienen de ml/exports/grid.npy, generado por 4_bake_grid.py.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS

aplicar_estilo()

RAIZ = Path(__file__).resolve().parent.parent.parent
rejilla = np.load(RAIZ / "ml" / "exports" / "grid.npy")

NODOS = [0, 3, 6, 9, 12, 15]
n = len(NODOS)

fig, axes = plt.subplots(n, n, figsize=(5.6, 5.6))

for fila, i in enumerate(NODOS):
    for col, j in enumerate(NODOS):
        ax = axes[n - 1 - fila, col]          # fila 0 (y minima) abajo
        ax.plot(rejilla[i, j], linewidth=0.6, color=AZUL)
        ax.set_ylim(-1.15, 1.15)
        ax.set_xticks([]); ax.set_yticks([])
        ax.grid(False)
        for lado in ax.spines.values():
            lado.set_color("#CCCCCC")
            lado.set_linewidth(0.5)
        if fila == 0:
            ax.set_xlabel(f"$j={j}$", fontsize=7, color=GRIS, labelpad=2)
        if col == 0:
            ax.set_ylabel(f"$i={i}$", fontsize=7, color=GRIS, labelpad=2)

fig.subplots_adjust(wspace=0.12, hspace=0.12)

guardar(fig, "rejilla")
