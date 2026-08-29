"""Reparto de la alimentacion: un solo rail de 5 V y sus cuatro ramas.

El bulk queda aguas arriba del corte del rail y el interruptor aguas abajo, de
modo que al cerrar las placas ven un flanco rapido. La rama del Daisy es la
unica con elemento serie. Las tensiones rotuladas son las medidas en banco.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

RELLENO = "#EAEFF7"
Y_RAIL = 46.0
Y_GND = 8.0
Y_CAJA0, Y_CAJA1 = 14.0, 26.0

fig, ax = plt.subplots(figsize=(6.6, 2.45))
ax.set_xlim(0, 172)
ax.set_ylim(0, 60)
ax.set_aspect("equal")
ax.axis("off")


def carga(x0, x1, titulo, detalle):
    """Bloque de carga, colgando del rail. Devuelve su eje."""
    ax.add_patch(FancyBboxPatch(
        (x0, Y_CAJA0), x1 - x0, Y_CAJA1 - Y_CAJA0,
        boxstyle="round,pad=0,rounding_size=1.2",
        linewidth=1.0, edgecolor=AZUL, facecolor=RELLENO))
    cx = (x0 + x1) / 2
    ax.text(cx, 22.2, titulo, ha="center", va="center",
            fontsize=8, fontweight="bold", color=AZUL)
    ax.text(cx, 17.4, detalle, ha="center", va="center",
            fontsize=7, color="#333333")
    ax.plot([cx, cx], [Y_GND, Y_CAJA0], color=GRIS, linewidth=1.0)
    return cx


def condensador(x, y, etiqueta):
    """Condensador entre el punto (x, y) y el rail de masa."""
    yp = (y + Y_GND) / 2 + 1.0
    ax.plot([x, x], [y, yp], color=GRIS, linewidth=1.0)
    ax.plot([x - 3, x + 3], [yp, yp], color=GRIS, linewidth=1.5)
    ax.plot([x - 3, x + 3], [yp - 2, yp - 2], color=GRIS, linewidth=1.5)
    ax.plot([x, x], [yp - 2, Y_GND], color=GRIS, linewidth=1.0)
    ax.text(x, yp - 4.0, etiqueta, ha="center", va="top", fontsize=6.8,
            color=GRIS)


def tension(x, valor):
    ax.text(x + 1.8, 31.0, valor, ha="left", va="center", fontsize=7,
            color=NARANJA, fontweight="bold")


# --- rail de 5 V, partido por el corte del interruptor ------------------
ax.plot([19, 44], [Y_RAIL, Y_RAIL], color=NARANJA, linewidth=1.8)
ax.plot([52, 152], [Y_RAIL, Y_RAIL], color=NARANJA, linewidth=1.8)
ax.text(80, Y_RAIL + 1.6, "+5 V", ha="center", va="bottom",
        fontsize=7.5, color=NARANJA, fontweight="bold")

ax.plot([44, 44], [Y_RAIL - 2.0, Y_RAIL + 2.0], color=GRIS, linewidth=0.9)
ax.plot([52, 52], [Y_RAIL - 2.0, Y_RAIL + 2.0], color=GRIS, linewidth=0.9)
ax.plot([44, 45.6], [Y_RAIL, Y_RAIL + 6.0], color=NARANJA, linewidth=1.4)
ax.plot([52, 52], [Y_RAIL, Y_RAIL + 6.0], color=NARANJA, linewidth=1.4)
ax.scatter([44, 52], [Y_RAIL + 6.0, Y_RAIL + 6.0], s=9, color=NARANJA,
           zorder=3)
ax.text(48, 54.5, "interruptor", ha="center", va="bottom",
        fontsize=7, color=NARANJA)
ax.text(48, Y_RAIL - 3.0, "corte", ha="center", va="top",
        fontsize=6.8, color=GRIS)

# --- rail de masa, continuo -------------------------------------------
ax.plot([19, 168], [Y_GND, Y_GND], color=GRIS, linewidth=1.8)
ax.text(168, Y_GND - 2.2, "masa, sin cortar en ningún punto",
        ha="right", va="top", fontsize=7, color=GRIS)

# --- entrada ----------------------------------------------------------
ax.add_patch(FancyBboxPatch(
    (1, 24), 18, 24, boxstyle="round,pad=0,rounding_size=1.2",
    linewidth=1.0, edgecolor=AZUL, facecolor="white"))
ax.text(10, 42.6, "entrada", ha="center", va="center", fontsize=8,
        fontweight="bold", color=AZUL)
ax.text(10, 33.6, "alimentador\nexterno\n5 V / 3 A", ha="center",
        va="center", fontsize=7, color="#333333", linespacing=1.35)
ax.plot([19, 19], [Y_RAIL, 44], color=NARANJA, linewidth=1.8)
ax.plot([19, 19], [Y_GND, 28], color=GRIS, linewidth=1.8)

# --- bulk, aguas arriba del corte -------------------------------------
condensador(28, Y_RAIL, "470 µF")
condensador(38, Y_RAIL, "100 nF")

# --- rama del ESP32-S3, directa del rail ------------------------------
cx = carga(58, 76, "ESP32-S3", "control")
ax.plot([cx, cx], [Y_CAJA1, Y_RAIL], color=NARANJA, linewidth=1.0)

# --- rama del shield MIDI: es la que fija el minimo del rail ----------
cx = carga(82, 102, "shield MIDI", "6N138")
ax.plot([cx, cx], [Y_CAJA1, Y_RAIL], color=NARANJA, linewidth=1.0)
tension(cx, "4,91 V")
ax.text(cx, 11.4, "mínimo 4,5 V", ha="center", va="center", fontsize=6.8,
        color=GRIS)

# --- rama de la CYD, tras el diodo-OR ---------------------------------
cx = carga(108, 126, "CYD", "interfaz")
ax.plot([cx, cx], [Y_CAJA1, 36.8], color=NARANJA, linewidth=1.0)
ax.plot([cx, cx], [40.6, Y_RAIL], color=NARANJA, linewidth=1.0)
ax.plot([cx - 2.8, cx + 2.8, cx, cx - 2.8], [40.6, 40.6, 36.8, 40.6],
        color=NARANJA, linewidth=1.3)
ax.plot([cx - 2.8, cx + 2.8], [36.8, 36.8], color=NARANJA, linewidth=1.6)
ax.text(cx + 3.6, 38.7, "D1", ha="left", va="center", fontsize=6.8,
        color=GRIS)
tension(cx, "4,7 V")

# --- rama del Daisy, la unica con elemento serie ----------------------
cx = carga(140, 158, "Daisy Seed", "audio")
ax.plot([cx, cx], [Y_CAJA1, 34.0], color=NARANJA, linewidth=1.0)
ax.plot([cx, cx], [39.6, Y_RAIL], color=NARANJA, linewidth=1.0)
ax.add_patch(Rectangle((cx - 2.6, 34.0), 5.2, 5.6, linewidth=1.1,
                       edgecolor=NARANJA, facecolor="white"))
ax.text(cx + 4.0, 36.8, "3R3 · 1 W", ha="left", va="center", fontsize=6.8,
        color=GRIS)
tension(cx, "3,4 V")

# los dos 100 uF, uno a cada lado de la resistencia
ax.plot([134, cx], [Y_RAIL, Y_RAIL], color=NARANJA, linewidth=1.0)
condensador(134, Y_RAIL, "100 µF")
ax.plot([cx, 164], [34.0, 34.0], color=NARANJA, linewidth=1.0)
condensador(164, 34.0, "100 µF")

guardar(fig, "alimentacion")
