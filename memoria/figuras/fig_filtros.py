"""Respuesta en magnitud de un paso bajo, un paso alto y un paso banda.

Se emplean biquads de segundo orden con la formulacion de Audio EQ Cookbook,
que es la misma familia de filtros que usa el motor de audio del instrumento.
"""

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, NARANJA, VERDE, GRIS

aplicar_estilo()

FS = 48000.0
FC = 1000.0
Q = 0.707


def biquad(tipo, fc, q, fs):
    w0 = 2 * np.pi * fc / fs
    alpha = np.sin(w0) / (2 * q)
    cw = np.cos(w0)
    if tipo == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
    elif tipo == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
    else:
        b = [alpha, 0.0, -alpha]
    a = [1 + alpha, -2 * cw, 1 - alpha]
    return np.array(b) / a[0], np.array(a) / a[0]


def respuesta(b, a, f, fs):
    w = 2 * np.pi * f / fs
    z = np.exp(-1j * w)
    num = b[0] + b[1] * z + b[2] * z**2
    den = a[0] + a[1] * z + a[2] * z**2
    return 20 * np.log10(np.abs(num / den) + 1e-12)


f = np.logspace(np.log10(20), np.log10(20000), 800)

fig, ax = plt.subplots(figsize=(5.6, 2.4))

for tipo, color, etiqueta in [("lp", AZUL, "Paso bajo"),
                              ("hp", NARANJA, "Paso alto"),
                              ("bp", VERDE, "Paso banda")]:
    b, a = biquad(tipo, FC, Q, FS)
    ax.semilogx(f, respuesta(b, a, f, FS), color=color, linewidth=1.5,
                label=etiqueta)

ax.axvline(FC, color=GRIS, linewidth=0.7, linestyle=":")
ax.text(FC * 1.1, -38, "$f_c$", fontsize=9, color=GRIS)
ax.axhline(-3, color=GRIS, linewidth=0.6, linestyle=":")
ax.text(22, -2.4, "−3 dB", fontsize=7.5, color=GRIS)

ax.set_xlim(20, 20000)
ax.set_ylim(-42, 6)
ax.set_xlabel("Frecuencia (Hz)")
ax.set_ylabel("Magnitud (dB)")
ax.set_xticks([20, 100, 1000, 10000, 20000])
ax.set_xticklabels(["20", "100", "1k", "10k", "20k"])
ax.legend(loc="lower left", ncol=1, bbox_to_anchor=(0.015, 0.02))
for lado in ("top", "right"):
    ax.spines[lado].set_visible(False)

guardar(fig, "filtros")
