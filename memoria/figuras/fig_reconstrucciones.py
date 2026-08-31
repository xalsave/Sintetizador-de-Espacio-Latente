"""Fidelidad de la reconstruccion del autoencoder variacional.

Cuatro ondas del conjunto de entrenamiento comparadas con la salida del
decodificador, ordenadas de menor a mayor error. Se ve que las ondas suaves
se recuperan casi exactas mientras que los flancos verticales se pierden: es
el limite del cuello de botella de dos dimensiones.

Los datos vienen de datos/reconstrucciones.npz, precalculado con PyTorch a
partir de ml/exports/vae.pt; este script solo necesita numpy.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

datos = np.load(Path(__file__).resolve().parent / "datos" / "reconstrucciones.npz")
idx, orig, recon, mse = datos["idx"], datos["orig"], datos["recon"], datos["mse"]

orden = np.argsort(mse)

fig, axes = plt.subplots(2, 2, figsize=(6.6, 3.4), sharex=True, sharey=True)

for ax, k in zip(axes.ravel(), orden):
    ax.plot(orig[k], linewidth=1.0, color=AZUL, label="original")
    ax.plot(recon[k], linewidth=1.0, color=NARANJA, linestyle="--",
            label="reconstruida")
    ax.axhline(0, color=GRIS, linewidth=0.5, linestyle=":")
    ax.set_title(f"onda #{idx[k]}   MSE = {mse[k]:.4f}".replace(".", ","),
                 fontsize=8, color=AZUL)
    ax.set_xlim(0, orig.shape[1] - 1)
    ax.set_xticks([0, 512, 1024])

axes[0, 0].set_ylim(-1.15, 1.15)
for ax in axes[1]:
    ax.set_xlabel("Muestra")
for ax in axes[:, 0]:
    ax.set_ylabel("Amplitud")

fig.tight_layout()
fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center",
           ncol=2, fontsize=8, bbox_to_anchor=(0.5, -0.03))
guardar(fig, "reconstrucciones")
