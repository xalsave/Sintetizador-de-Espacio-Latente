"""El suavizado de los mandos y el mapeo exponencial de la frecuencia de corte.

Izquierda: un giro rapido del potenciometro de corte, tal y como lo entrega el
ADC bloque a bloque, y el mismo giro tras el filtro de un polo del firmware
(coeficiente 0,03 por bloque a 1 kHz, unos 30 ms de constante de tiempo).

Derecha: el mismo recorrido llevado a hercios por el mapeo exponencial y por
uno lineal, para ver donde queda el rango util en cada caso.
"""

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

FS_CTRL = 1000.0        # una lectura por bloque de audio
CTRL_SMOOTH = 0.03      # coeficiente del polo, tal como esta en el firmware
CUTOFF_MIN = 30.0
CUTOFF_MAX = 12000.0

# Un giro rapido, de un cuarto de recorrido a tres cuartos en 40 ms. A esta
# velocidad el escalon por bloque se ve a escala completa, sin ampliaciones.
n = int(0.2 * FS_CTRL)
t = np.arange(n) / FS_CTRL * 1000.0     # ms
crudo = np.clip(0.25 + (np.arange(n) - 20) * 0.0125, 0.25, 0.75)

# El ADC entrega un valor por bloque: escalones, no una rampa continua.
suave = np.empty(n)
v = crudo[0]
for i in range(n):
    v += (crudo[i] - v) * CTRL_SMOOTH
    suave[i] = v

fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3))

# --- izquierda: crudo frente a suavizado ---------------------------------
ax = axes[0]
ax.step(t, crudo, where="post", color=NARANJA, linewidth=0.9,
        label="lectura del ADC")
ax.plot(t, suave, color=AZUL, linewidth=1.6, label="tras el polo de 30 ms")
ax.set_xlabel("Tiempo (ms)")
ax.set_ylabel("Posición del mando")
ax.set_xlim(0, t[-1])
ax.set_ylim(0.2, 0.8)
ax.set_title("Suavizado de los controles")
ax.legend(loc="lower right")

# --- derecha: mapeo exponencial frente a lineal --------------------------
ax = axes[1]
x = np.linspace(0.0, 1.0, 400)
exp = CUTOFF_MIN * (CUTOFF_MAX / CUTOFF_MIN) ** x
lin = CUTOFF_MIN + (CUTOFF_MAX - CUTOFF_MIN) * x

ax.plot(x, exp, color=AZUL, linewidth=1.6, label="exponencial")
ax.plot(x, lin, color=GRIS, linewidth=1.2, linestyle="--", label="lineal")
ax.set_yscale("log")
ax.set_xlabel("Posición del mando")
ax.set_ylabel("Frecuencia de corte (Hz)")
ax.set_xlim(0, 1)
ax.set_ylim(CUTOFF_MIN * 0.8, CUTOFF_MAX * 1.3)
ax.set_title("Mapeo de la frecuencia de corte")
ax.legend(loc="lower right")

fig.tight_layout()
guardar(fig, "suavizado")
