"""Lectura de una tabla de ondas mediante acumulador de fase.

Panel izquierdo: la tabla almacenada y la posicion fraccionaria del acumulador.
Panel derecho: detalle de la interpolacion lineal entre las dos muestras
vecinas, que es lo que describe la Ecuacion de interpolacion del capitulo 2.
"""

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, NARANJA, GRIS

aplicar_estilo()

N = 32
n = np.arange(N)
# Una onda con algo de contenido armonico, para que no sea un seno pelado
tabla = (np.sin(2 * np.pi * n / N)
         + 0.35 * np.sin(4 * np.pi * n / N)
         + 0.15 * np.sin(6 * np.pi * n / N))
tabla /= np.abs(tabla).max()

phi = 9.4                      # posicion actual del acumulador
i = int(np.floor(phi))
alpha = phi - i
valor = (1 - alpha) * tabla[i] + alpha * tabla[(i + 1) % N]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.0, 2.5),
                               gridspec_kw={"width_ratios": [2, 1]})

# --- Panel izquierdo: la tabla completa ---
ax1.stem(n, tabla, linefmt="-", markerfmt="o", basefmt=" ")
for artista in ax1.get_children():
    pass
lineas = ax1.get_lines()
ax1.cla()
ax1.vlines(n, 0, tabla, color="#BBBBCC", linewidth=0.9)
ax1.plot(n, tabla, "o", color=AZUL, markersize=3)
ax1.axhline(0, color=GRIS, linewidth=0.7)
ax1.plot([phi], [valor], "o", color=NARANJA, markersize=6, zorder=5)
ax1.vlines(phi, 0, valor, color=NARANJA, linewidth=1.4)
ax1.annotate(r"$\varphi$", xy=(phi, valor), xytext=(phi + 2.5, valor + 0.42),
             color=NARANJA, fontsize=10,
             arrowprops=dict(arrowstyle="->", color=NARANJA, linewidth=0.9))
ax1.set_xlim(-1, N)
ax1.set_ylim(-1.25, 1.35)
ax1.set_xlabel("Índice de la tabla")
ax1.set_ylabel("Amplitud")
ax1.set_title("Tabla de $N$ muestras", pad=6)
ax1.grid(False)
for lado in ("top", "right"):
    ax1.spines[lado].set_visible(False)

# --- Panel derecho: detalle de la interpolacion ---
xs = [i, i + 1]
ys = [tabla[i], tabla[(i + 1) % N]]
ax2.plot(xs, ys, "-", color="#BBBBCC", linewidth=1.2)
ax2.plot(xs, ys, "o", color=AZUL, markersize=5)
ax2.plot([phi], [valor], "o", color=NARANJA, markersize=7, zorder=5)
ax2.vlines(phi, min(ys) - 0.1, valor, color=NARANJA, linewidth=1.0,
           linestyle=":")

ax2.text(i, ys[0] - 0.10, "$T[i]$", ha="center", va="top", fontsize=8.5,
         color=AZUL)
ax2.text(i + 1, ys[1] + 0.09, "$T[i{+}1]$", ha="center", va="bottom",
         fontsize=8.5, color=AZUL)
ax2.text(phi + 0.04, valor + 0.06, "$s[n]$", fontsize=8.5, color=NARANJA)

# Marca de la parte fraccionaria
y_base = min(ys) - 0.22
ax2.annotate("", xy=(i, y_base), xytext=(phi, y_base),
             arrowprops=dict(arrowstyle="<->", color=GRIS, linewidth=0.8))
ax2.text((i + phi) / 2, y_base - 0.06, r"$\alpha$", ha="center", va="top",
         fontsize=9, color=GRIS)

ax2.set_xlim(i - 0.25, i + 1.25)
ax2.set_ylim(y_base - 0.25, max(ys) + 0.3)
ax2.set_xticks(xs)
ax2.set_xticklabels(["$i$", "$i{+}1$"])
ax2.set_yticks([])
ax2.set_title("Interpolación lineal", pad=6)
ax2.grid(False)
for lado in ("top", "right", "left"):
    ax2.spines[lado].set_visible(False)

fig.tight_layout(w_pad=2.0)
guardar(fig, "wavetable")
