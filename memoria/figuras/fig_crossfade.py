"""El crossfade entre dos tablas vecinas, y por que se hace lineal.

Datos reales: los nodos (2,9) y (2,10) de ml/exports/grid.npy, que son las dos
celdas contiguas alcanzadas por la coordenada con la que se valido el enlace.

Panel izquierdo: las dos rampas de peso a lo largo de los 20 ms.
Panel central:   la senal a mitad de transicion, entre las dos tablas.
Panel derecho:   pico de la mezcla a lo largo de la transicion, comparando el
                 crossfade lineal con el de potencia constante. Como las dos
                 tablas estan alineadas en fase y se leen en la misma posicion
                 del acumulador, refuerzan en vez de cancelar, y es el de
                 potencia constante el que se pasa de nivel.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA, VERDE

aplicar_estilo()

RAIZ = Path(__file__).resolve().parent.parent.parent
grid = np.load(RAIZ / "ml" / "exports" / "grid.npy")

# Las dos celdas contiguas de la coordenada (40000, 12000) del capitulo 5.
tabla_a = grid[2, 9].astype(np.float64)
tabla_b = grid[2, 10].astype(np.float64)

XFADE_MS = 20.0
t = np.linspace(0.0, XFADE_MS, 400)     # eje temporal de la transicion
p = t / XFADE_MS                        # posicion del crossfade, 0..1

fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.15))

# --- izquierda: las dos rampas -------------------------------------------
ax = axes[0]
ax.plot(t, 1.0 - p, color=AZUL, linewidth=1.5, label="tabla activa")
ax.plot(t, p, color=NARANJA, linewidth=1.5, label="tabla nueva")
ax.set_xlabel("Tiempo (ms)")
ax.set_ylabel("Peso")
ax.set_xlim(0, XFADE_MS)
ax.set_ylim(-0.05, 1.28)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_title("Pesos del crossfade")
ax.legend(loc="upper center", handlelength=1.2)

# --- centro: la senal a mitad de transicion ------------------------------
ax = axes[1]
n = np.arange(1024)
ax.plot(n, tabla_a, color=AZUL, linewidth=0.8, alpha=0.55, label="activa")
ax.plot(n, tabla_b, color=NARANJA, linewidth=0.8, alpha=0.55, label="nueva")
ax.plot(n, 0.5 * tabla_a + 0.5 * tabla_b, color=VERDE, linewidth=1.3,
        label="mitad")
ax.set_xlabel("Muestra de la tabla")
ax.set_ylabel("Amplitud")
ax.set_xlim(0, 1023)
ax.set_xticks([0, 512, 1023])
ax.set_ylim(-1.15, 1.35)
ax.set_title("Punto medio de la mezcla")
ax.legend(loc="upper left", ncol=3, columnspacing=0.9, handlelength=1.2)

# --- derecha: pico a lo largo de la transicion ---------------------------
ax = axes[2]
lineal = np.array([np.abs(tabla_a * (1 - x) + tabla_b * x).max() for x in p])
potcte = np.array([np.abs(tabla_a * np.cos(x * np.pi / 2)
                          + tabla_b * np.sin(x * np.pi / 2)).max() for x in p])

ref = lineal[0]
ax.plot(t, 20 * np.log10(lineal / ref), color=AZUL, linewidth=1.5,
        label="lineal")
ax.plot(t, 20 * np.log10(potcte / ref), color=NARANJA, linewidth=1.5,
        linestyle="--", label="potencia cte.")
ax.axhline(0, color=GRIS, linewidth=0.6, linestyle=":")
ax.set_xlabel("Tiempo (ms)")
ax.set_ylabel("Pico (dB rel.)")
ax.set_xlim(0, XFADE_MS)
ax.set_ylim(-0.25, 4.4)
ax.set_yticks([0, 1, 2, 3])
ax.set_title("Nivel durante la transición")
ax.legend(loc="upper left", handlelength=1.4)

print("rizado lineal          : %.2f dB" % (20 * np.log10(lineal.max()
                                                          / lineal.min())))
print("rizado potencia const. : %.2f dB" % (20 * np.log10(potcte.max()
                                                          / potcte.min())))
print("correlación entre tablas: %.3f" % np.corrcoef(tabla_a, tabla_b)[0, 1])

fig.tight_layout()
guardar(fig, "crossfade")
