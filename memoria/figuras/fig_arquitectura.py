"""Diagrama de bloques del sistema: las tres placas y sus enlaces.

Flechas continuas: enlaces digitales entre placas, rotulados con el medio y el
tamano de trama. Flechas discontinuas: perifericos del procesador de audio.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

RELLENO = "#EAEFF7"

fig, ax = plt.subplots(figsize=(6.6, 3.15))
ax.set_xlim(0, 126)
ax.set_ylim(0, 60)
ax.set_aspect("equal")
ax.axis("off")


def caja(x0, x1, y0, y1, titulo, lineas):
    """Bloque con titulo en negrita y un par de lineas de detalle debajo."""
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=0,rounding_size=1.2",
        linewidth=1.1, edgecolor=AZUL, facecolor=RELLENO))
    cx = (x0 + x1) / 2
    ax.text(cx, y1 - 3.6, titulo, ha="center", va="center",
            fontsize=8.5, fontweight="bold", color=AZUL)
    for i, linea in enumerate(lineas):
        ax.text(cx, y1 - 7.0 - 3.2 * i, linea, ha="center", va="center",
                fontsize=7.2, color="#333333")


def flecha(p0, p1, color=AZUL, estilo="-", ancho=1.1):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>", mutation_scale=9,
        linewidth=ancho, color=color, linestyle=estilo,
        shrinkA=0, shrinkB=0))


caja(1, 25, 28, 44, "CYD",
     ["ESP32 y táctil", "lectura del gesto", "y dibujo de la onda"])
caja(43, 67, 28, 44, "ESP32-S3",
     ["rejilla 16×16", "interpolación bilineal"])
caja(85, 109, 28, 44, "Daisy Seed",
     ["motor wavetable", "filtro y envolvente"])

# Enlace CYD -> S3 (coordenada) y su canal de vuelta (onda para dibujar)
flecha((25, 40), (43, 40))
ax.text(34, 42.0, "6 B  (x, y)", ha="center", va="bottom", fontsize=7,
        color=GRIS)
flecha((43, 32), (25, 32))
ax.text(34, 30.0, "260 B  (onda)", ha="center", va="top", fontsize=7,
        color=GRIS)
ax.text(34, 36.0, "UART\n460.800 bd", ha="center", va="center", fontsize=7,
        color=AZUL, linespacing=1.3)

# Enlace S3 -> Daisy (forma de onda completa)
flecha((67, 36), (85, 36))
ax.text(76, 38.2, "SPI 10 MHz", ha="center", va="bottom", fontsize=7,
        color=AZUL)
ax.text(76, 33.8, "2054 B  (tabla)", ha="center", va="top", fontsize=7,
        color=GRIS)

# Salida de audio
flecha((109, 36), (115, 36), color=NARANJA)
ax.text(117, 33.0, "salida\nde línea", ha="center", va="top", fontsize=7,
        color=NARANJA)

# Perifericos del procesador de audio
flecha((91, 21), (91, 28), color=GRIS, estilo=(0, (3, 2)), ancho=0.9)
ax.text(91, 19.5, "MIDI DIN\n(teclado externo)", ha="center", va="top",
        fontsize=7, color=GRIS)

flecha((103, 12), (103, 28), color=GRIS, estilo=(0, (3, 2)), ancho=0.9)
ax.text(104, 10.5, "6 potenciómetros\ny selector", ha="center", va="top",
        fontsize=7, color=GRIS)

flecha((97, 44), (97, 50), color=GRIS, estilo=(0, (3, 2)), ancho=0.9)
ax.text(97, 51.5, "OLED", ha="center", va="bottom", fontsize=7, color=GRIS)

guardar(fig, "arquitectura")
