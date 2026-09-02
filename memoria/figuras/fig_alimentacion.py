"""Esquema de la alimentacion: raíl unico de 5 V y sus cuatro cargas.

Es un esquema de principio, con designadores y valores. No lleva tensiones
medidas: esas estan en el capitulo de pruebas.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

RELLENO = "#EAEFF7"
Y_RAIL = 48.0
Y_GND = 6.0
Y_CAJA0, Y_CAJA1 = 16.0, 28.0

fig, ax = plt.subplots(figsize=(6.6, 1.95))
ax.set_xlim(-2, 232)
ax.set_ylim(0, 64)
ax.set_aspect("equal")
ax.axis("off")


def carga(x0, x1, titulo, detalle):
    """Bloque de carga. Devuelve su eje vertical."""
    ax.add_patch(FancyBboxPatch(
        (x0, Y_CAJA0), x1 - x0, Y_CAJA1 - Y_CAJA0,
        boxstyle="round,pad=0,rounding_size=1.2",
        linewidth=1.0, edgecolor=AZUL, facecolor=RELLENO))
    cx = (x0 + x1) / 2
    ax.text(cx, 24.2, titulo, ha="center", va="center",
            fontsize=7.5, fontweight="bold", color=AZUL)
    ax.text(cx, 19.4, detalle, ha="center", va="center",
            fontsize=7, color="#333333")
    ax.plot([cx, cx], [Y_GND, Y_CAJA0], color=GRIS, linewidth=1.0)
    return cx


def condensador(x, y_alto, designador, valor):
    """Condensador entre el nodo (x, y_alto) y el raíl de masa."""
    yp = 26.0
    ax.plot([x, x], [y_alto, yp], color=GRIS, linewidth=1.0)
    ax.plot([x - 3.2, x + 3.2], [yp, yp], color=GRIS, linewidth=1.6)
    ax.plot([x - 3.2, x + 3.2], [yp - 2.4, yp - 2.4], color=GRIS,
            linewidth=1.6)
    ax.plot([x, x], [yp - 2.4, Y_GND], color=GRIS, linewidth=1.0)
    ax.text(x, 20.4, designador, ha="center", va="center", fontsize=6.8,
            color="#333333")
    ax.text(x, 15.6, valor, ha="center", va="center", fontsize=6.8,
            color=GRIS)


def nodo(x, y):
    ax.scatter([x], [y], s=7, color=NARANJA, zorder=4)


# --- raíl de 5 V y raíl de masa ---------------------------------------
ax.plot([16, 58], [Y_RAIL, Y_RAIL], color=NARANJA, linewidth=1.8)
ax.plot([70, 160], [Y_RAIL, Y_RAIL], color=NARANJA, linewidth=1.8)
ax.text(115, Y_RAIL + 1.8, "+5 V", ha="center", va="bottom",
        fontsize=8, color=NARANJA, fontweight="bold")

ax.plot([16, 228], [Y_GND, Y_GND], color=GRIS, linewidth=1.8)
ax.text(228, Y_GND - 2.0, "GND", ha="right", va="top", fontsize=8,
        color=GRIS, fontweight="bold")

# --- entrada -----------------------------------------------------------
ax.add_patch(FancyBboxPatch(
    (-2, 26), 20, 24, boxstyle="round,pad=0,rounding_size=1.2",
    linewidth=1.0, edgecolor=AZUL, facecolor="white"))
ax.text(8, 44.0, "J1", ha="center", va="center", fontsize=7.5,
        fontweight="bold", color=AZUL)
ax.text(8, 34.5, "entrada\n5 V / 3 A", ha="center", va="center",
        fontsize=7, color="#333333", linespacing=1.35)
ax.plot([16, 16], [Y_RAIL, 46], color=NARANJA, linewidth=1.8)
ax.plot([16, 16], [Y_GND, 30], color=GRIS, linewidth=1.8)

# --- reserva del raíl, aguas arriba del interruptor --------------------
condensador(28, Y_RAIL, "C4", "470 µF")
condensador(46, Y_RAIL, "C8", "100 nF")
nodo(28, Y_RAIL)
nodo(46, Y_RAIL)

# --- interruptor de red ------------------------------------------------
ax.plot([58, 59.8], [Y_RAIL, Y_RAIL + 6.2], color=NARANJA, linewidth=1.5)
ax.plot([70, 70], [Y_RAIL, Y_RAIL + 6.2], color=NARANJA, linewidth=1.5)
ax.scatter([58, 70], [Y_RAIL + 6.2, Y_RAIL + 6.2], s=9, color=NARANJA,
           zorder=3)
ax.text(64, 57.5, "SW1", ha="center", va="bottom", fontsize=7.5,
        color=NARANJA, fontweight="bold")

# --- cargas directas del raíl ------------------------------------------
cx = carga(76, 96, "ESP32-S3", "control")
ax.plot([cx, cx], [Y_CAJA1, Y_RAIL], color=NARANJA, linewidth=1.0)
nodo(cx, Y_RAIL)

cx = carga(100, 126, "Shield MIDI", "6N138")
ax.plot([cx, cx], [Y_CAJA1, Y_RAIL], color=NARANJA, linewidth=1.0)
nodo(cx, Y_RAIL)

# --- rama de la CYD, tras el diodo de aislamiento -----------------------
cx = carga(130, 150, "CYD", "interfaz")
ax.plot([cx, cx], [Y_CAJA1, 36.0], color=NARANJA, linewidth=1.0)
ax.plot([cx, cx], [40.0, Y_RAIL], color=NARANJA, linewidth=1.0)
ax.plot([cx - 3.0, cx + 3.0, cx, cx - 3.0], [40.0, 40.0, 36.0, 40.0],
        color=NARANJA, linewidth=1.3)
ax.plot([cx - 3.0, cx + 3.0], [36.0, 36.0], color=NARANJA, linewidth=1.8)
ax.text(cx + 4.5, 40.0, "D1", ha="left", va="center", fontsize=6.8,
        color="#333333")
ax.text(cx + 4.5, 36.0, "1N5817", ha="left", va="center", fontsize=6.8,
        color=GRIS)
nodo(cx, Y_RAIL)

# --- rama del procesador de audio: la única con elemento en serie -------
cx = carga(168, 194, "Daisy Seed", "audio")
condensador(160, Y_RAIL, "C1", "100 µF")
nodo(160, Y_RAIL)

# resistencia serie, sobre la bajada
ax.plot([cx, cx], [Y_RAIL, 42.4], color=NARANJA, linewidth=1.0)
ax.add_patch(Rectangle((cx - 3.0, 36.4), 6.0, 6.0, linewidth=1.1,
                       edgecolor=NARANJA, facecolor="white"))
ax.plot([160, cx], [Y_RAIL, Y_RAIL], color=NARANJA, linewidth=1.0)
ax.text(cx + 4.5, 41.0, "R1", ha="left", va="center", fontsize=6.8,
        color="#333333")
ax.text(cx + 4.5, 37.0, "3,3 $\\Omega$", ha="left", va="center",
        fontsize=6.8, color=GRIS)

# nodo de salida del filtro, con sus dos desacoplos
ax.plot([cx, cx], [36.4, 32.0], color=NARANJA, linewidth=1.0)
ax.plot([cx, 222], [32.0, 32.0], color=NARANJA, linewidth=1.0)
ax.plot([cx, cx], [32.0, Y_CAJA1], color=NARANJA, linewidth=1.0)
nodo(cx, 32.0)
condensador(206, 32.0, "C2", "100 µF")
condensador(222, 32.0, "C3", "100 nF")
nodo(206, 32.0)
nodo(222, 32.0)

guardar(fig, "alimentacion")
