"""Envolvente ADSR con sus cuatro tramos marcados."""

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

# Duraciones relativas de cada tramo y nivel de sostenimiento
t_a, t_d, t_s, t_r = 1.1, 1.4, 2.8, 2.1
nivel_sustain = 0.6

t_ataque = np.linspace(0, t_a, 50)
v_ataque = t_ataque / t_a

t_decay = np.linspace(0, t_d, 50)
v_decay = 1 - (1 - nivel_sustain) * (t_decay / t_d)

t_sustain = np.linspace(0, t_s, 20)
v_sustain = np.full_like(t_sustain, nivel_sustain)

t_release = np.linspace(0, t_r, 50)
v_release = nivel_sustain * (1 - t_release / t_r)

t = np.concatenate([t_ataque, t_a + t_decay, t_a + t_d + t_sustain,
                    t_a + t_d + t_s + t_release])
v = np.concatenate([v_ataque, v_decay, v_sustain, v_release])

fig, ax = plt.subplots(figsize=(6.2, 2.5))
ax.plot(t, v, color=AZUL, linewidth=1.8)
ax.fill_between(t, v, color=AZUL, alpha=0.07)

fronteras = [0, t_a, t_a + t_d, t_a + t_d + t_s, t_a + t_d + t_s + t_r]
for x in fronteras[1:-1]:
    ax.axvline(x, color=GRIS, linewidth=0.6, linestyle=":")

# Momento en que se suelta la tecla
x_off = t_a + t_d + t_s
ax.axvline(x_off, color=NARANJA, linewidth=1.0, linestyle="--")
ax.text(x_off - 0.12, 1.07, "se suelta la tecla", ha="right", va="center",
        fontsize=8, color=NARANJA)

# Etiquetas de cada tramo, dentro de la figura
etiquetas = ["Ataque", "Decaimiento", "Sostenimiento", "Liberación"]
for nombre, x0, x1 in zip(etiquetas, fronteras[:-1], fronteras[1:]):
    ax.text((x0 + x1) / 2, -0.075, nombre, ha="center", va="top", fontsize=8.5)

ax.axhline(nivel_sustain, color=GRIS, linewidth=0.6, linestyle=":")

# El eje se extiende mas alla del final de la envolvente para que la flecha
# de tiempo no se solape con el tramo de liberacion
margen_derecho = 1.4

ax.set_xlim(-0.05, fronteras[-1] + margen_derecho)
ax.set_ylim(-0.24, 1.16)
ax.set_ylabel("Amplitud")
ax.set_xticks([])
ax.set_yticks([0, nivel_sustain, 1])
ax.set_yticklabels(["0", "$S$", "1"])
ax.grid(False)
for lado in ("top", "right", "bottom"):
    ax.spines[lado].set_visible(False)

# Eje de tiempo como flecha, para no chocar con las etiquetas de los tramos
ax.annotate("", xy=(fronteras[-1] + margen_derecho - 0.45, 0), xytext=(-0.05, 0),
            arrowprops=dict(arrowstyle="->", color=GRIS, linewidth=0.8))
ax.text(fronteras[-1] + margen_derecho - 0.38, 0, "tiempo", ha="left",
        va="center", fontsize=8, color=GRIS)

guardar(fig, "adsr")
