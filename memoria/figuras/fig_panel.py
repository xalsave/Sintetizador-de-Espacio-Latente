"""Alzado del panel frontal, a escala, con las cotas que lo gobiernan.

Los valores salen de `hardware/cad/panel.scad`, que es la fuente de la pieza
impresa: 186 x 116 x 3,4 mm, seis potenciometros a paso de 24 mm y las dos
ventanas. El trazo discontinuo es lo que queda POR DETRAS del panel (el
contorno de las dos placas); el continuo, lo que se ve desde fuera.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from estilo import aplicar_estilo, guardar, AZUL, GRIS, NARANJA

aplicar_estilo()

# --- cotas de panel.scad ----------------------------------------------
PANEL_W, PANEL_H, CORNER_R = 186.0, 116.0, 4.0
POT_N, POT_PITCH, POT_X0, POT_Y = 6, 24.0, 22.0, 24.0
POT_D, POT_CLEAR = 7.0, 0.3
AR_W, AR_H, AR_R = 2.8, 1.2, 7.8          # pletina antigiro, a 180 grados
SW_X, SW_Y, SW_D = 166.0, 24.0, 6.0
OLED_CX, OLED_CY = 135.0, 90.0
OLED_PCB = 26.0
OLED_WIN_W, OLED_WIN_H, OLED_WIN_DY = 22.2, 11.3, 1.52
CYD_X0, CYD_Y0, CYD_W, CYD_H = 11.0, 56.0, 86.0, 50.0
CYD_WIN = (16.75, 2.25, 56.0, 45.5)       # dx, dy, ancho, alto
MOUNT = [(7, 7), (179, 7), (7, 109), (179, 109)]
CYD_SCREWS = [(4, 4), (82, 4), (4, 46), (82, 46)]
NOMBRES = ["ATTACK", "DECAY", "SUSTAIN", "RELEASE", "CUTOFF", "Q"]
LABEL_DY = -11.0

fig, ax = plt.subplots(figsize=(6.0, 4.0))
ax.set_xlim(-14, 200)
ax.set_ylim(-16, 126)
ax.set_aspect("equal")
ax.axis("off")

# --- plancha ----------------------------------------------------------
ax.add_patch(FancyBboxPatch(
    (CORNER_R, CORNER_R), PANEL_W - 2 * CORNER_R, PANEL_H - 2 * CORNER_R,
    boxstyle=f"round,pad={CORNER_R}", linewidth=1.2, edgecolor=AZUL,
    facecolor="#F6F7FA"))

# --- ventana de la CYD -----------------------------------------------
ax.add_patch(Rectangle((CYD_X0, CYD_Y0), CYD_W, CYD_H, linewidth=0.7,
                       edgecolor=GRIS, facecolor="none",
                       linestyle=(0, (3, 2))))
dx, dy, w, h = CYD_WIN
ax.add_patch(Rectangle((CYD_X0 + dx, CYD_Y0 + dy), w, h, linewidth=1.1,
                       edgecolor=AZUL, facecolor="white"))
ax.text(CYD_X0 + dx + w / 2, CYD_Y0 + dy + h / 2, "pantalla táctil",
        ha="center", va="center", fontsize=9, color=GRIS)
for sx, sy in CYD_SCREWS:
    ax.add_patch(Circle((CYD_X0 + sx, CYD_Y0 + sy), 1.8, linewidth=0.7,
                        edgecolor=GRIS, facecolor="white"))

# --- ventana del OLED -------------------------------------------------
ax.add_patch(Rectangle((OLED_CX - OLED_PCB / 2, OLED_CY - OLED_PCB / 2),
                       OLED_PCB, OLED_PCB, linewidth=0.7, edgecolor=GRIS,
                       facecolor="none", linestyle=(0, (3, 2))))
ax.add_patch(Rectangle(
    (OLED_CX - OLED_WIN_W / 2, OLED_CY + OLED_WIN_DY - OLED_WIN_H / 2),
    OLED_WIN_W, OLED_WIN_H, linewidth=1.1, edgecolor=AZUL,
    facecolor="white"))
ax.text(OLED_CX, OLED_CY - 17, "OLED", ha="center", va="center",
        fontsize=9, color=GRIS)


def antigiro(cx, cy, ancho, alto, radio, ang):
    """Ranura de la espiga antigiro, tangente a la circunferencia del eje."""
    if ang == 180:
        ax.add_patch(Rectangle((cx - radio - alto / 2, cy - ancho / 2),
                               alto, ancho, linewidth=0.9, edgecolor=AZUL,
                               facecolor="white"))
    else:
        ax.add_patch(Rectangle((cx - ancho / 2, cy + radio - alto / 2),
                               ancho, alto, linewidth=0.9, edgecolor=AZUL,
                               facecolor="white"))


# --- seis potenciometros ----------------------------------------------
for i, nombre in enumerate(NOMBRES):
    x = POT_X0 + i * POT_PITCH
    ax.add_patch(Circle((x, POT_Y), (POT_D + POT_CLEAR) / 2, linewidth=1.1,
                        edgecolor=AZUL, facecolor="white"))
    antigiro(x, POT_Y, AR_W, AR_H, AR_R, 180)
    ax.text(x, POT_Y + LABEL_DY, nombre, ha="center", va="center",
            fontsize=8, color="#333333")

# --- selector de tipo de filtro ---------------------------------------
ax.add_patch(Circle((SW_X, SW_Y), (SW_D + 0.3) / 2, linewidth=1.1,
                    edgecolor=AZUL, facecolor="white"))
antigiro(SW_X, SW_Y, 2.8, 2.8, 6.4, 90)
for texto, pos in [("FILTER", (SW_X, SW_Y + 20)), ("HPF", (SW_X, SW_Y + 12)),
                   ("BPF", (SW_X + 11, SW_Y)), ("LPF", (SW_X, SW_Y - 11))]:
    ax.text(pos[0], pos[1], texto, ha="center", va="center", fontsize=8,
            color="#333333")

# --- taladros de sujecion del panel -----------------------------------
for mx, my in MOUNT:
    ax.add_patch(Circle((mx, my), 1.6, linewidth=0.8, edgecolor=NARANJA,
                        facecolor="white"))


# --- cotas ------------------------------------------------------------
def cota(x0, x1, y, texto, vertical=False):
    if vertical:
        ax.annotate("", xy=(y, x0), xytext=(y, x1),
                    arrowprops=dict(arrowstyle="<->", color=GRIS,
                                    linewidth=0.7, shrinkA=0, shrinkB=0))
        ax.text(y - 2.5, (x0 + x1) / 2, texto, ha="right", va="center",
                fontsize=8.5, color=GRIS, rotation=90)
    else:
        ax.annotate("", xy=(x0, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="<->", color=GRIS,
                                    linewidth=0.7, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y + 1.5, texto, ha="center", va="bottom",
                fontsize=8.5, color=GRIS)


cota(0, PANEL_W, -9, "186")
cota(0, PANEL_H, -6, "116", vertical=True)
cota(POT_X0, POT_X0 + POT_PITCH, 33, "24")
ax.text(PANEL_W + 5, PANEL_H - 6, "3,4 mm\nde espesor", ha="left",
        va="center", fontsize=8.5, color=GRIS, linespacing=1.35)

guardar(fig, "panel")
