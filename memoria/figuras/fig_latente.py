"""Espacio latente aprendido por el autoencoder variacional.

Cada punto es la media de la distribucion que el codificador asigna a una de
las 4358 ondas del conjunto de entrenamiento. Se colorean las doce familias
mas numerosas y el resto queda en gris. Encima se superpone el rectangulo de
percentiles 2-98 de cada eje, que delimita la zona poblada del plano.

Los datos vienen de datos/latent_mu.npy, precalculado con PyTorch a partir de
ml/exports/vae.pt; este script solo necesita numpy.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

RAIZ = Path(__file__).resolve().parent.parent.parent
mu = np.load(Path(__file__).resolve().parent / "datos" / "latent_mu.npy")
familias = np.load(RAIZ / "ml" / "dataset" / "akwf_families.npy", allow_pickle=True)

x_min, x_max = np.percentile(mu[:, 0], [2, 98])
y_min, y_max = np.percentile(mu[:, 1], [2, 98])

fig, ax = plt.subplots(figsize=(6.4, 4.3))

unicas, cuentas = np.unique(familias, return_counts=True)
top = unicas[np.argsort(cuentas)[::-1][:12]]

resto = ~np.isin(familias, top)
ax.scatter(mu[resto, 0], mu[resto, 1], s=4, c="#CCCCCC", alpha=0.5,
           linewidths=0, label="resto")

cmap = plt.colormaps["tab20"].resampled(len(top))
for i, fam in enumerate(top):
    m = familias == fam
    ax.scatter(mu[m, 0], mu[m, 1], s=6, color=cmap(i), alpha=0.85,
               linewidths=0, label=fam)

# Zona poblada del plano: percentiles 2-98 de cada eje
ax.add_patch(Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                       fill=False, edgecolor=NARANJA, linewidth=1.1,
                       linestyle="--"))

ax.set_xlabel("$z_1$")
ax.set_ylabel("$z_2$")
ax.axhline(0, color=GRIS, linewidth=0.5, linestyle=":")
ax.axvline(0, color=GRIS, linewidth=0.5, linestyle=":")
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=6.5,
          markerscale=2, labelspacing=0.35)

guardar(fig, "latente")
