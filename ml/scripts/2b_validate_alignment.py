"""
Demuestra que la alineacion de fase es invariante al desplazamiento circular:
una misma onda, arrancada en puntos distintos del ciclo, vuelve a la misma forma
tras alinear el fundamental a fase 0. Usa la primera onda de AKWF (o una
sintetica si no hay dataset) y las funciones de 2_build_dataset.py.
"""

import os
import importlib.util
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# El script principal empieza por digito, asi que no se puede 'import 2_...'
# de forma normal: lo cargamos por ruta con importlib.
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "build_dataset_mod", os.path.join(HERE, "2_build_dataset.py"))
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)

N = bd.TARGET_LEN              # 1024
SHIFTS = [0, 200, 450, 800]   # puntos de arranque (desplazamientos circulares)


def cargar_onda_real(dataset_path):
    """Primera onda .wav del corpus, procesada SIN alinear la fase."""
    if os.path.isdir(dataset_path):
        for current_dir, dirs, files in os.walk(dataset_path):
            dirs.sort()
            for filename in sorted(files):
                if filename.lower().endswith(".wav"):
                    _, data = wavfile.read(os.path.join(current_dir, filename))
                    wave = bd.normalize_peak(bd.remove_dc(bd.resample(bd.to_float(data), N)))
                    return wave, f"{os.path.basename(current_dir)}/{filename}"
    return None, None


def onda_sintetica():
    """Onda rica en armonicos para la demo si no hay dataset disponible."""
    t = np.linspace(0, 2 * np.pi, N, endpoint=False)
    wave = (np.sin(t) + 0.5 * np.sin(2 * t + 1.0)
            + 0.3 * np.sin(3 * t + 2.0) + 0.15 * np.sin(5 * t))
    return bd.normalize_peak(bd.remove_dc(wave)), "sintetica (demo)"


def main():
    base, nombre = cargar_onda_real(bd.DATASET_PATH)
    if base is None:
        print(f"No se encontro AKWF en {bd.DATASET_PATH}; uso onda sintetica.")
        base, nombre = onda_sintetica()
    print(f"Onda de prueba: {nombre}")

    # Misma onda arrancada en puntos distintos del ciclo
    desplazadas = [np.roll(base, s) for s in SHIFTS]
    # Alinear cada copia (align_phase devuelve (onda, aligned); tomamos la onda)
    alineadas = [bd.normalize_peak(bd.align_phase(w)[0]) for w in desplazadas]

    # Cuantificar la coincidencia tras alinear
    ref = alineadas[0]
    err_max = max(float(np.max(np.abs(a - ref))) for a in alineadas)
    print(f"Error maximo entre las copias alineadas: {err_max:.2e}")
    print("=> practicamente identicas" if err_max < 1e-6
          else "=> NO coinciden (revisar)")

    # Figura
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for w, s in zip(desplazadas, SHIFTS):
        ax0.plot(w, linewidth=1, label=f"arranque +{s}")
    for a in alineadas:
        ax1.plot(a, linewidth=1.3, alpha=0.7)
    ax0.set_title("Misma onda, distintos puntos de arranque")
    ax1.set_title(f"Tras alinear: {len(SHIFTS)} curvas superpuestas (err {err_max:.0e})")
    for ax in (ax0, ax1):
        ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax.set_xlabel("Muestra")
        ax.grid(True, alpha=0.3)
    ax0.set_ylabel("Amplitud")
    ax0.legend(fontsize="small", loc="upper right")
    fig.suptitle(f"Invarianza de la alineacion al desplazamiento  -  {nombre}")
    fig.tight_layout()
    plt.savefig(os.path.join(HERE, "alignment_validation.png"), dpi=110)
    plt.show()


if __name__ == "__main__":
    main()
