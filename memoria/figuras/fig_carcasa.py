"""La carcasa: vista montada y despiece.

Las dos vistas se renderizan con OpenSCAD desde `hardware/cad/conjunto.scad`,
que es la fuente de las piezas impresas, y se dejan precalculadas en `datos/`
porque este guion solo puede depender de numpy y matplotlib. Para regenerarlas:

  openscad.com -o datos/carcasa_montado.png --imgsize=1600,1200 \
      --camera=93,92,20,62,0,32,520 --projection=perspective \
      --colorscheme=Cornfield -D 'vista="montado"' conjunto.scad

  openscad.com -o datos/carcasa_explosionado.png --imgsize=1600,1200 \
      --camera=93,92,55,64,0,32,640 --projection=perspective \
      --colorscheme=Cornfield -D 'vista="explosionado"' conjunto.scad
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, GRIS

aplicar_estilo()

DATOS = Path(__file__).resolve().parent / "datos"


def blanquear(img):
    """Sustituye el fondo crema de OpenSCAD por blanco."""
    img = img.copy()
    fondo = img[0, 0, :3]
    es_fondo = (abs(img[:, :, :3] - fondo).sum(axis=2) <= 0.05)
    img[es_fondo, :3] = 1.0
    return img


def recortar(img, margen=0.06):
    """Quita el fondo sobrante alrededor de la pieza."""
    fondo = img[0, 0, :3]
    mascara = (abs(img[:, :, :3] - fondo).sum(axis=2) > 0.05)
    filas = mascara.any(axis=1).nonzero()[0]
    cols = mascara.any(axis=0).nonzero()[0]
    if len(filas) == 0 or len(cols) == 0:
        return img
    dy = int((filas[-1] - filas[0]) * margen)
    dx = int((cols[-1] - cols[0]) * margen)
    y0 = max(filas[0] - dy, 0)
    y1 = min(filas[-1] + dy, img.shape[0] - 1)
    x0 = max(cols[0] - dx, 0)
    x1 = min(cols[-1] + dx, img.shape[1] - 1)
    return img[y0:y1, x0:x1]


fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7))

for ax, nombre, pie in [
    (axes[0], "carcasa_montado", "(a) conjunto montado"),
    (axes[1], "carcasa_explosionado", "(b) despiece"),
]:
    ax.imshow(blanquear(recortar(mpimg.imread(DATOS / f"{nombre}.png"))))
    ax.set_xticks([])
    ax.set_yticks([])
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.grid(False)
    ax.set_xlabel(pie, fontsize=8, color=GRIS, labelpad=4)

fig.subplots_adjust(wspace=0.04)
guardar(fig, "carcasa")
