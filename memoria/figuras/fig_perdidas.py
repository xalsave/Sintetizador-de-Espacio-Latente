"""Curvas de entrenamiento del autoencoder variacional.

Izquierda, el error cuadratico medio de reconstruccion en entrenamiento y en
validacion; derecha, la divergencia de Kullback-Leibler. Se aprecia que el
error de validacion deja de bajar hacia la epoca 40 mientras el de
entrenamiento sigue cayendo, y que la divergencia se estabiliza en torno a 7
una vez terminada la rampa de beta.

Procedencia de los datos
------------------------
3_train_vae.py no guarda el historico de perdidas en disco, solo la figura
loss_curve.png que genera al terminar. Volver a obtenerlo exigiria reentrenar,
lo que daria un modelo distinto y obligaria a rehornear la rejilla ya
embarcada en el firmware. Las series de datos/perdidas.npz se recuperaron por
tanto de esa imagen, midiendo la posicion de cada curva pixel a pixel y
convirtiendola a coordenadas de dato con la calibracion de los ejes. Los
valores finales asi recuperados (0,0431, 0,0687 y 7,10) coinciden con los que
imprimio el entrenamiento (0,043, 0,068 y 7), pero la reconstruccion es
aproximada y la figura vale por su forma, no por su precision punto a punto.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

datos = np.load(Path(__file__).resolve().parent / "datos" / "perdidas.npz")
train, val, kl = datos["train"], datos["val"], datos["kl"]
epocas = np.arange(len(train))

fig, (ax_mse, ax_kl) = plt.subplots(1, 2, figsize=(6.6, 2.5))

ax_mse.plot(epocas, train, color=AZUL, linewidth=1.0, label="entrenamiento")
ax_mse.plot(epocas, val, color=NARANJA, linewidth=1.0, linestyle="--",
            label="validación")
ax_mse.axvline(40, color=GRIS, linewidth=0.7, linestyle=":")
ax_mse.annotate("la validación\ndeja de bajar", xy=(40, 0.064), xytext=(95, 0.088),
                fontsize=6.5, color=GRIS, ha="left",
                arrowprops=dict(arrowstyle="->", color=GRIS, linewidth=0.6))
ax_mse.set_ylabel("MSE de reconstrucción")
ax_mse.set_ylim(0.038, 0.105)
ax_mse.legend(loc="upper right")

ax_kl.plot(epocas, kl, color=NARANJA, linewidth=1.0)
ax_kl.axvline(50, color=GRIS, linewidth=0.7, linestyle=":")
ax_kl.annotate("fin de la rampa\nde " + r"$\beta$", xy=(50, 9.5), xytext=(105, 13.0),
               fontsize=6.5, color=GRIS, ha="left",
               arrowprops=dict(arrowstyle="->", color=GRIS, linewidth=0.6))
ax_kl.set_ylabel("Divergencia KL")
ax_kl.set_ylim(5.8, 17.5)

for ax in (ax_mse, ax_kl):
    ax.set_xlabel("Época")
    ax.set_xlim(0, len(train) - 1)
    ax.set_xticks([0, 50, 100, 150, 200, 250, 300])

fig.tight_layout()
guardar(fig, "perdidas")
