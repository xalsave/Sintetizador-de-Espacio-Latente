"""Las dos fases de operacion: preparacion fuera de linea y ejecucion en vivo.

Banda superior: lo que ocurre una sola vez en el ordenador, unica fase en la que
interviene la red. Banda inferior: lo que ocurre en el instrumento en cada
toque. La flecha discontinua marca el punto en el que la rejilla se embarca.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from estilo import aplicar_estilo, guardar, AZUL, GRIS, VERDE

aplicar_estilo()

RELLENO_OFF = "#EAEFF7"
RELLENO_VIVO = "#EAF2EC"

fig, ax = plt.subplots(figsize=(6.6, 2.95))
ax.set_xlim(0, 124)
ax.set_ylim(0, 55)
ax.set_aspect("equal")
ax.axis("off")

ANCHO = 21
SEPARACION = 3.75
X0 = [2 + i * (ANCHO + SEPARACION) for i in range(5)]

OFFLINE = [
    ("Dataset AKWF", "≈4000 ondas"),
    ("Preprocesado", "1024 muestras,\nfase alineada"),
    ("Entrenamiento", "del VAE"),
    ("Decodificación", "de la rejilla\n16×16"),
    ("Cabecera C", "en el ESP32-S3"),
]

VIVO = [
    ("Toque (x, y)", "en la CYD"),
    ("Interpolación", "bilineal en el S3"),
    ("Envío por SPI", "2054 B"),
    ("Transición", "de 20 ms"),
    ("Audio", "48 kHz"),
]


def fila(y0, y1, contenido, color, relleno):
    for x0, (titulo, detalle) in zip(X0, contenido):
        ax.add_patch(FancyBboxPatch(
            (x0, y0), ANCHO, y1 - y0,
            boxstyle="round,pad=0,rounding_size=1.2",
            linewidth=1.0, edgecolor=color, facecolor=relleno))
        cx = x0 + ANCHO / 2
        ax.text(cx, y1 - 3.4, titulo, ha="center", va="center",
                fontsize=7.6, fontweight="bold", color=color)
        ax.text(cx, y0 + (y1 - y0 - 6.8) / 2 + 1.2, detalle, ha="center",
                va="center", fontsize=6.9, color="#333333",
                linespacing=1.25)
    for x0 in X0[:-1]:
        ax.add_patch(FancyArrowPatch(
            (x0 + ANCHO, (y0 + y1) / 2), (x0 + ANCHO + SEPARACION, (y0 + y1) / 2),
            arrowstyle="-|>", mutation_scale=8, linewidth=1.0, color=color,
            shrinkA=0, shrinkB=0))


ax.text(123, 49, "Fase de preparación — una vez, en el ordenador",
        ha="right", va="center", fontsize=8, color=AZUL)
fila(32, 46, OFFLINE, AZUL, RELLENO_OFF)

ax.text(123, 21, "Fase de ejecución — en cada toque, en el instrumento",
        ha="right", va="center", fontsize=8, color=VERDE)
fila(4, 18, VIVO, VERDE, RELLENO_VIVO)

# La rejilla compilada baja al instrumento y alimenta la interpolacion
x_origen = X0[4] + ANCHO / 2
x_destino = X0[1] + ANCHO / 2
ax.plot([x_origen, x_origen, x_destino], [32, 26.5, 26.5],
        color=GRIS, linewidth=0.9, linestyle=(0, (3, 2)))
ax.add_patch(FancyArrowPatch(
    (x_destino, 26.5), (x_destino, 18), arrowstyle="-|>", mutation_scale=8,
    linewidth=0.9, color=GRIS, linestyle=(0, (3, 2)), shrinkA=0, shrinkB=0))
ax.text((x_origen + x_destino) / 2, 27.8, "la rejilla se embarca en el firmware",
        ha="center", va="bottom", fontsize=6.9, color=GRIS)

guardar(fig, "pipeline")
