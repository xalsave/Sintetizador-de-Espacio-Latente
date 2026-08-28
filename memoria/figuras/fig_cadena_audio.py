"""Estructura del firmware de audio y las tres tasas a las que trabaja.

La banda superior es lo que ocurre una vez por muestra (48 kHz), la del medio
una vez por bloque de 48 muestras (1 kHz) y la inferior en el bucle principal,
sin cadencia fija. Las flechas discontinuas son las que cruzan de un ritmo a
otro, que son justamente las que hay que resolver con cuidado.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA, VERDE

aplicar_estilo()

RELLENO = "#EAEFF7"
BANDA = "#F2F5FA"

fig, ax = plt.subplots(figsize=(6.6, 3.3))
ax.set_xlim(0, 142)
ax.set_ylim(0, 72)
ax.set_aspect("equal")
ax.axis("off")


def banda(y0, y1, titulo, detalle):
    """Franja de fondo con su rotulo en la columna izquierda."""
    ax.add_patch(Rectangle((0, y0), 142, y1 - y0, linewidth=0,
                           facecolor=BANDA, zorder=0))
    cy = (y0 + y1) / 2
    ax.text(2, cy + 2.4, titulo, ha="left", va="center", fontsize=7.4,
            fontweight="bold", color=GRIS, zorder=1)
    ax.text(2, cy - 2.6, detalle, ha="left", va="center", fontsize=6.5,
            color=GRIS, zorder=1)


def caja(x0, x1, titulo, sub, y0=None, y1=None, color=AZUL):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=0,rounding_size=1.2",
        linewidth=1.1, edgecolor=color, facecolor=RELLENO, zorder=2))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ax.text(cx, cy + 2.4, titulo, ha="center", va="center", fontsize=7.5,
            fontweight="bold", color=color, zorder=3)
    ax.text(cx, cy - 2.6, sub, ha="center", va="center", fontsize=6.5,
            color="#333333", zorder=3)


def flecha(p0, p1, color=AZUL, estilo="-", ancho=1.1):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>", mutation_scale=8,
        linewidth=ancho, color=color, linestyle=estilo,
        shrinkA=0, shrinkB=0, zorder=4))


CRUCE = dict(color=VERDE, estilo=(0, (3, 2)), ancho=0.9)

banda(50, 72, "Por muestra", "48 kHz")
banda(24, 48, "Por bloque", "1 kHz")
banda(0, 22, "Bucle principal", "sin cadencia fija")

# --- cadena de audio, muestra a muestra ----------------------------------
caja(32, 58, "Acumulador", "tabla Q15 y crossfade", y0=54, y1=68)
caja(64, 84, "Svf", "LP / BP / HP", y0=54, y1=68)
caja(88, 108, "ADSR", "envolvente", y0=54, y1=68)
caja(114, 136, "Ganancia", "velocity y salida", y0=54, y1=68)

for x0, x1 in [(58, 64), (84, 88), (108, 114)]:
    flecha((x0, 61), (x1, 61))

flecha((136, 61), (140, 61), color=NARANJA)
ax.text(141, 61, "códec", ha="left", va="center", fontsize=6.8, color=NARANJA)

# --- lo que se refresca una vez por bloque -------------------------------
caja(62, 96, "Lectura del ADC", "7 canales y suavizado", y0=28, y1=44)
caja(102, 136, "Reataque diferido", "petición del hilo MIDI", y0=28, y1=44)

# El corte y la Q van al filtro; los cuatro tiempos, a la envolvente.
flecha((70, 44), (70, 54), **CRUCE)
flecha((90, 44), (90, 54), **CRUCE)
flecha((105, 44), (105, 54), **CRUCE)

# --- lo que atiende el bucle principal -----------------------------------
caja(32, 58, "Trama SPI", "cabecera y CRC", y0=4, y1=18)
caja(62, 136, "MIDI", "nota, puerta y dinámica", y0=4, y1=18)

flecha((46, 18), (46, 54), **CRUCE)
ax.text(44, 24, "tabla nueva", ha="right", va="center", fontsize=6.4,
        color=VERDE)

# La nota fija la frecuencia del acumulador. Se rodea por el hueco que queda
# entre el acumulador y el filtro, para no cruzar la lectura del ADC.
ax.plot([62, 60, 60], [11, 11, 57], color=VERDE, linewidth=0.9,
        linestyle=(0, (3, 2)), zorder=4)
flecha((60, 57), (58, 57), **CRUCE)
ax.text(62, 23, "frecuencia", ha="left", va="center", fontsize=6.4,
        color=VERDE)

# La puerta y la dinamica cruzan por el hueco entre las dos cajas de bloque.
flecha((99, 18), (99, 54), **CRUCE)
ax.text(97.5, 23, "puerta y dinámica", ha="right", va="center", fontsize=6.4,
        color=VERDE)

guardar(fig, "cadena_audio")
