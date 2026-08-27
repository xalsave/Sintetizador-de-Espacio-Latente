"""Invarianza de la alineacion de fase al desplazamiento circular.

Una misma onda del conjunto de datos se arranca en cuatro puntos distintos del
ciclo. A la izquierda son cuatro curvas separadas; a la derecha, tras rotar
cada una para dejar su armonico fundamental a fase 0, las cuatro colapsan en
una sola. Es la propiedad que permite promediar wavetables sin cancelaciones
entre armonicos.

Solo necesita numpy: la rotacion es la misma operacion en el dominio de la
frecuencia que aplica ml/scripts/2_build_dataset.py.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS

aplicar_estilo()

RAIZ = Path(__file__).resolve().parent.parent.parent
ondas = np.load(RAIZ / "ml" / "dataset" / "akwf_processed.npy")

DESPLAZAMIENTOS = [0, 137, 411, 700]
base = ondas[100].astype(np.float64)


def alinear(x):
    """Deja el armonico fundamental a fase 0 rotando el ciclo."""
    espectro = np.fft.rfft(x)
    fase = np.angle(espectro[1])
    k = np.arange(espectro.shape[0])
    y = np.fft.irfft(espectro * np.exp(-1j * k * fase), n=len(x))
    return y / np.max(np.abs(y))


desplazadas = [np.roll(base, d) for d in DESPLAZAMIENTOS]
alineadas = [alinear(w) for w in desplazadas]
error = max(np.max(np.abs(alineadas[0] - w)) for w in alineadas[1:])

fig, (ax_pre, ax_post) = plt.subplots(1, 2, figsize=(6.6, 2.5), sharey=True)

for w, d in zip(desplazadas, DESPLAZAMIENTOS):
    ax_pre.plot(w, linewidth=1.0, alpha=0.9, label=f"$+{d}$")
for w in alineadas:
    ax_post.plot(w, linewidth=1.0, alpha=0.9)

ax_pre.set_title("Cuatro arranques distintos del mismo ciclo", color=AZUL)
exp = int(np.floor(np.log10(error)))
ax_post.set_title(f"Tras alinear (error máx. $10^{{{exp}}}$)", color=AZUL)
ax_pre.legend(loc="lower right", ncol=4, fontsize=6.5, columnspacing=0.9,
              handlelength=1.2)

for ax in (ax_pre, ax_post):
    ax.axhline(0, color=GRIS, linewidth=0.6, linestyle="--")
    ax.set_xlabel("Muestra")
    ax.set_xlim(0, ondas.shape[1] - 1)
    ax.set_xticks([0, 256, 512, 768, 1024])

ax_pre.set_ylabel("Amplitud")
ax_pre.set_ylim(-1.25, 1.25)

guardar(fig, "alineacion")
