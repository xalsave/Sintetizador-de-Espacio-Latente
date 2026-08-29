"""La placa concentradora: reparto sobre las tiras y por que hay que cortarlas.

A la izquierda, el reparto de la placa: los dos raíles, las huellas de los dos
modulos con sus lineas de corte, y las tres zonas. Es un esquema del reparto,
no un plano acotado.

A la derecha, la razon de los cortes: un modulo de dos filas colocado
perpendicular a las tiras deja el pin p y el pin 41-p sobre la misma tira.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

ROJO = "#B03030"
RELLENO = "#EAEFF7"

fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.6, 3.0),
                             gridspec_kw={"width_ratios": [1.55, 1]})

# =======================================================================
#  Izquierda: el reparto de la placa
# =======================================================================
ax.set_xlim(-3, 66)
ax.set_ylim(0, 45)
ax.set_aspect("equal")
ax.axis("off")

# las 39 tiras de cobre
for t in range(1, 40):
    ax.plot([0, 63], [t, t], color="#D8D8D8", linewidth=0.45, zorder=1)

# los dos raíles
ax.plot([0, 63], [1, 1], color=GRIS, linewidth=1.8, zorder=2)
ax.plot([0, 57.5], [2, 2], color=NARANJA, linewidth=1.8, zorder=2)
ax.plot([58.5, 63], [2, 2], color=NARANJA, linewidth=1.8, zorder=2)
ax.text(-0.8, 1, "1", ha="right", va="center", fontsize=6.5, color=GRIS)
ax.text(-0.8, 2, "2", ha="right", va="center", fontsize=6.5, color=NARANJA)
ax.text(-0.8, 39, "39", ha="right", va="center", fontsize=6.5, color=GRIS)
ax.text(26, 0.2, "tira 1 · raíl de masa", ha="center", va="top",
        fontsize=6.5, color=GRIS)
ax.text(26, 3.0, "tira 2 · raíl +5 V", ha="center", va="bottom",
        fontsize=6.5, color=NARANJA)


def modulo(x0, x1, t0, t1, nombre, xcorte):
    """Huella de un modulo, con sus dos filas de pines y su linea de corte."""
    ax.add_patch(Rectangle((x0, t0), x1 - x0, t1 - t0, linewidth=1.0,
                           edgecolor=AZUL, facecolor=RELLENO, alpha=0.85,
                           zorder=3))
    for x in (x0, x1):
        ax.plot([x] * (t1 - t0 + 1), range(t0, t1 + 1), linestyle="none",
                marker="o", markersize=1.6, color=AZUL, zorder=4)
    ax.plot([xcorte, xcorte], [t0 - 0.4, t1 + 0.4], color=ROJO,
            linewidth=1.1, linestyle=(0, (2, 1.4)), zorder=5)
    ax.text((x0 + x1) / 2, t1 + 1.6, nombre, ha="center", va="bottom",
            fontsize=7.5, fontweight="bold", color=AZUL)


modulo(3, 13, 1, 22, "ESP32-S3", 8)
modulo(38, 48, 20, 39, "Daisy Seed", 43)

# corte de separacion entre los dos modulos
ax.plot([22, 22], [16.6, 22.4], color=ROJO, linewidth=1.1,
        linestyle=(0, (2, 1.4)), zorder=5)
ax.text(23.2, 19.5, "separación\nentre módulos", ha="left", va="center",
        fontsize=6.5, color=ROJO, linespacing=1.3)

# corte del raíl para el interruptor
ax.text(58, 6.6, "corte del raíl\npara el interruptor", ha="center",
        va="bottom", fontsize=6.5, color=ROJO, linespacing=1.3)
ax.annotate("", xy=(58, 2.4), xytext=(58, 6.4),
            arrowprops=dict(arrowstyle="-", color=ROJO, linewidth=0.7))

# etiquetas de las lineas de corte de los modulos
ax.text(15.0, 15.0, "22 cortes", ha="left", va="center", fontsize=6.5,
        color=ROJO)
ax.annotate("", xy=(8.4, 15.0), xytext=(14.6, 15.0),
            arrowprops=dict(arrowstyle="-", color=ROJO, linewidth=0.7))
ax.text(50.0, 31.0, "20 cortes", ha="left", va="center", fontsize=6.5,
        color=ROJO)
ax.annotate("", xy=(43.4, 31.0), xytext=(49.6, 31.0),
            arrowprops=dict(arrowstyle="-", color=ROJO, linewidth=0.7))

# zonas
ax.plot([2, 20], [43, 43], color=GRIS, linewidth=0.8)
ax.plot([26, 50], [43, 43], color=GRIS, linewidth=0.8)
ax.plot([52, 63], [43, 43], color=GRIS, linewidth=0.8)
ax.text(11, 43.6, "digital", ha="center", va="bottom", fontsize=6.8,
        color=GRIS)
ax.text(38, 43.6, "mixta", ha="center", va="bottom", fontsize=6.8,
        color=GRIS)
ax.text(57.5, 43.6, "analógica", ha="center", va="bottom", fontsize=6.8,
        color=GRIS)

# lo que aterriza en cada extremo
ax.text(17.5, 9.0, "enlaces\nde la CYD", ha="center", va="center",
        fontsize=6.5, color="#333333", linespacing=1.3)
ax.text(28.5, 33, "puentes\ndel SPI", ha="center", va="center",
        fontsize=6.5, color="#333333", linespacing=1.3)
ax.text(56, 26, "filtro y\nmazo del panel", ha="center", va="center",
        fontsize=6.5, color="#333333", linespacing=1.3)

# =======================================================================
#  Derecha: por que hay que cortar
# =======================================================================
bx.set_xlim(-1, 22)
bx.set_ylim(0, 21.5)
bx.axis("off")

criticos = {
    2:  ("2", "39 · VIN +5 V"),
    3:  ("3", "38 · 3V3D"),
    18: ("18 · AUDIO OUT L", "23 · pote Decay"),
    20: ("20 · AGND", "21 · 3V3A"),
}

for i in range(1, 21):
    y = 21 - i
    critico = i in criticos
    color = ROJO if critico else "#C8C8C8"
    ancho = 1.1 if critico else 0.5
    bx.plot([2, 12], [y, y], color=color, linewidth=ancho, zorder=1)
    bx.plot([2, 12], [y, y], linestyle="none", marker="o", markersize=2.4,
            color=ROJO if critico else AZUL, zorder=3)
    if critico:
        izq, der = criticos[i]
        bx.text(1.4, y, izq, ha="right", va="center", fontsize=6.4,
                color=ROJO)
        bx.text(12.6, y, der, ha="left", va="center", fontsize=6.4,
                color=ROJO)
    else:
        bx.text(1.4, y, str(i), ha="right", va="center", fontsize=6.0,
                color=GRIS)
        bx.text(12.6, y, str(41 - i), ha="left", va="center", fontsize=6.0,
                color=GRIS)

bx.plot([7, 7], [0.4, 20.6], color=ROJO, linewidth=1.1,
        linestyle=(0, (2, 1.4)), zorder=4)
bx.text(7, 21.0, "línea de corte", ha="center", va="bottom", fontsize=6.8,
        color=ROJO)
bx.text(2, -0.2, "fila 1–20", ha="center", va="top", fontsize=6.8,
        color=AZUL)
bx.text(12, -0.2, "fila 21–40", ha="center", va="top", fontsize=6.8,
        color=AZUL)

guardar(fig, "veroboard")
