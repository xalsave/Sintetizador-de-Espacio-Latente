"""Interpolacion bilineal: las cuatro celdas vecinas y la onda resultante.

Se usa la coordenada (40000, 12000), que es la misma con la que se valido el
enlace en la sesion 7. Con la escala 15/65535 cae en la celda X[9->10] con
fx = 0,1554 y Y[2->3] con fy = 0,7466.

Los datos vienen de ml/exports/grid.npy, generado por 4_bake_grid.py.
"""

import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

RAIZ = Path(__file__).resolve().parent.parent.parent
rejilla = np.load(RAIZ / "ml" / "exports" / "grid.npy")   # (16, 16, 1024)

X, Y = 40000, 12000
escala = (rejilla.shape[0] - 1) / 65535.0
gx, gy = X * escala, Y * escala
ix0, iy0 = math.floor(gx), math.floor(gy)
ix1, iy1 = ix0 + 1, iy0 + 1
fx, fy = gx - ix0, gy - iy0

# Convencion de indices de grid.h: [fila = eje Y][columna = eje X].
tl = rejilla[iy0, ix0]
tr = rejilla[iy0, ix1]
bl = rejilla[iy1, ix0]
br = rejilla[iy1, ix1]
arriba = tl + (tr - tl) * fx
abajo = bl + (br - bl) * fx
interpolada = arriba + (abajo - arriba) * fy

fig, (ax_celda, ax_onda) = plt.subplots(
    1, 2, figsize=(6.6, 2.5), gridspec_kw={"width_ratios": [1, 2.35]})

# --- Izquierda: la celda y el reparto de pesos --------------------------------
ax_celda.set_xlim(-0.78, 1.62)
ax_celda.set_ylim(1.90, -0.62)
ax_celda.set_aspect("equal")
ax_celda.axis("off")

for x0 in (0, 1):
    ax_celda.plot([x0, x0], [0, 1], color=GRIS, linewidth=0.8, zorder=1)
    ax_celda.plot([0, 1], [x0, x0], color=GRIS, linewidth=0.8, zorder=1)

# Peso de cada vecina y su indice en GRID_TABLES[fila][columna].
pesos = {(0, 0): (1 - fx) * (1 - fy), (1, 0): fx * (1 - fy),
         (0, 1): (1 - fx) * fy,       (1, 1): fx * fy}
etiquetas = {(0, 0): f"[{iy0}][{ix0}]", (1, 0): f"[{iy0}][{ix1}]",
             (0, 1): f"[{iy1}][{ix0}]", (1, 1): f"[{iy1}][{ix1}]"}

for (cx, cy), w in pesos.items():
    ax_celda.plot(cx, cy, marker="o", markersize=4, color=AZUL, zorder=3)
    # El eje Y esta invertido: cy = 0 queda arriba en pantalla.
    ax_celda.text(cx + (-0.07 if cx == 0 else 0.07),
                  cy + (-0.07 if cy == 0 else 0.07),
                  f"{etiquetas[(cx, cy)]}\n{w:.3f}".replace(".", ","),
                  ha="right" if cx == 0 else "left",
                  va="bottom" if cy == 0 else "top",
                  fontsize=6.8, color=AZUL, linespacing=1.3)

ax_celda.plot([fx, fx], [0, fy], color=NARANJA, linewidth=0.7,
              linestyle=(0, (2, 2)), zorder=2)
ax_celda.plot([0, fx], [fy, fy], color=NARANJA, linewidth=0.7,
              linestyle=(0, (2, 2)), zorder=2)
ax_celda.plot(fx, fy, marker="*", markersize=11, color=NARANJA, zorder=4)

ax_celda.text(0.5, 1.72,
              f"$f_x$ = {fx:.3f}".replace(".", ",") + "      "
              + f"$f_y$ = {fy:.3f}".replace(".", ","),
              ha="center", va="top", fontsize=7.5, color=NARANJA)
ax_celda.text(0.5, -0.50, "columna (eje X)  →", ha="center", va="bottom",
              fontsize=6.8, color=GRIS)
ax_celda.text(-0.62, 0.62, "fila (eje Y)  →", ha="center", va="bottom",
              fontsize=6.8, color=GRIS, rotation=-90)

# --- Derecha: las cuatro vecinas y la onda que sale ---------------------------
n = np.arange(rejilla.shape[2])
for onda in (tl, tr, bl, br):
    ax_onda.plot(n, onda, color=GRIS, linewidth=0.55, alpha=0.65, zorder=1)
ax_onda.plot(n, interpolada, color=AZUL, linewidth=1.3, zorder=3)

ax_onda.plot([], [], color=GRIS, linewidth=0.9, label="las cuatro vecinas")
ax_onda.plot([], [], color=AZUL, linewidth=1.3, label="onda interpolada")
ax_onda.legend(loc="lower right", ncol=2, fontsize=7)

ax_onda.set_xlim(0, rejilla.shape[2] - 1)
ax_onda.set_ylim(-1.15, 1.35)
ax_onda.set_xlabel("muestra del ciclo")
ax_onda.set_ylabel("amplitud")
ax_onda.set_xticks([0, 256, 512, 768, 1024])

guardar(fig, "bilineal")
