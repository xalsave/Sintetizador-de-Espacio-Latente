"""Las dos ventanas del tactil de la CYD sobre el plano de cuentas crudas.

Todos los numeros estan medidos en banco el 27 ago 2026 con la placa ya
montada en la carcasa:

  panel completo  148..3962 en X, 198..3902 en Y  (calibracion de S6 ya
                  espejada por el giro de 180 grados)
  visible         450..3730 en los dos ejes, lo que asoma por el hueco
  captura         600..3580 en los dos ejes, que toques se dan por buenos

y la pulsacion fantasma del labio impreso, en crudo (3714, 643).
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

COMPLETO = (148, 3962, 198, 3902)
VISIBLE = (450, 3730, 450, 3730)
CAPTURA = (600, 3580, 600, 3580)
FANTASMA = (3714, 643)

fig, ax = plt.subplots(figsize=(6.2, 3.4))


def rect(lim, color, ancho, estilo="-", relleno=None, z=2, etiqueta=None):
    x0, x1, y0, y1 = lim
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                           linewidth=ancho, edgecolor=color, linestyle=estilo,
                           facecolor="none" if relleno is None else relleno,
                           zorder=z, label=etiqueta))


rect(COMPLETO, GRIS, 0.9, estilo=(0, (4, 2)),
     etiqueta="cristal completo (148 – 3962)")
rect(VISIBLE, NARANJA, 1.2, etiqueta="ventana visible (450 – 3730)")
rect(CAPTURA, AZUL, 1.4, relleno="#EAEFF7", z=1,
     etiqueta="ventana de captura (600 – 3580)")

ax.plot(*FANTASMA, marker="x", markersize=7, markeredgewidth=1.6,
        color=NARANJA, zorder=5)
ax.annotate("pulsación fantasma\ncrudo (3714, 643)",
            xy=FANTASMA, xytext=(2300, 1300), fontsize=7.8, color=NARANJA,
            ha="center", va="center", linespacing=1.35,
            arrowprops=dict(arrowstyle="->", color=NARANJA, linewidth=0.9,
                            shrinkA=2, shrinkB=5))

ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), ncol=1,
          fontsize=8, handlelength=2.2, borderaxespad=0.0)

ax.set_xlim(0, 4095)
ax.set_ylim(4095, 0)          # el eje Y crece hacia abajo, como en pantalla
ax.set_aspect("equal")
ax.set_xlabel("cuentas crudas del eje X")
ax.set_ylabel("cuentas crudas del eje Y")
ax.set_xticks([0, 1024, 2048, 3072, 4095])
ax.set_yticks([0, 1024, 2048, 3072, 4095])

guardar(fig, "ventanas")
