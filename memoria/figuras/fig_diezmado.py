"""Por que el diezmado hacia la pantalla promedia en vez de quedarse una de
cada cuatro muestras.

Se reproduce exactamente lo que hace wave_sender.cpp: media de cada grupo de
cuatro muestras Q15, truncamiento y desplazamiento de ocho bits para pasar a
Q7, y recorte a [-128, 127]. Enfrente, el mismo diezmado tomando una muestra
de cada cuatro sin promediar.

Se dibuja el nodo (0, 7) de la rejilla, que es donde mas se separan los dos
metodos: 68 cuentas Q7 de diferencia en el peor punto, sobre una amplitud
maxima de 122.

Los datos vienen de ml/exports/grid.npy, generado por 4_bake_grid.py.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

RAIZ = Path(__file__).resolve().parent.parent.parent
rejilla = np.load(RAIZ / "ml" / "exports" / "grid.npy")

FILA, COLUMNA = 0, 7
PASO = 4
PUNTOS = 256

q15 = np.clip(np.round(rejilla[FILA, COLUMNA] * 32767.0), -32768, 32767)


def a_q7(valores):
    """Q15 -> Q7 tal como lo hace el firmware: truncar y desplazar 8 bits."""
    q = np.trunc(valores)                       # division entera de C
    return np.clip(np.floor(q / 256.0), -128, 127)   # desplazamiento aritmetico


promediada = a_q7(q15.reshape(PUNTOS, PASO).mean(axis=1))
directa = a_q7(q15[::PASO])

x = np.arange(PUNTOS) * PASO

fig, (ax_ciclo, ax_zoom) = plt.subplots(
    1, 2, figsize=(6.6, 2.35), gridspec_kw={"width_ratios": [1.55, 1]})

ZOOM = (216, 344)

for ax, recorte in ((ax_ciclo, None), (ax_zoom, ZOOM)):
    ax.plot(np.arange(1024), q15 / 256.0, color=GRIS, linewidth=0.5,
            alpha=0.55, zorder=1)
    ax.plot(x, directa, color=NARANJA, linewidth=0.9,
            linestyle=(0, (3, 1.6)), zorder=2)
    ax.plot(x, promediada, color=AZUL, linewidth=1.1, zorder=3)
    ax.set_xlabel("muestra del ciclo")
    if recorte is None:
        ax.set_xlim(0, 1023)
        ax.set_xticks([0, 256, 512, 768, 1024])
        ax.set_ylabel("amplitud (Q7)")
    else:
        ax.set_xlim(*recorte)
        ax.set_ylim(-135, 135)

ax_ciclo.set_ylim(-135, 168)
ax_ciclo.plot([], [], color=GRIS, linewidth=0.9, label="1024 muestras")
ax_ciclo.plot([], [], color=NARANJA, linewidth=0.9, linestyle=(0, (3, 1.6)),
              label="256 sin promediar")
ax_ciclo.plot([], [], color=AZUL, linewidth=1.1, label="256 promediando")
ax_ciclo.legend(loc="upper center", ncol=3, fontsize=6.8,
                columnspacing=1.1, handlelength=1.8)

ax_ciclo.axvspan(*ZOOM, color=AZUL, alpha=0.07, zorder=0)
ax_zoom.set_title("ampliación del tramo sombreado", fontsize=7.5, color=GRIS)

guardar(fig, "diezmado")
