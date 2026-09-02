"""
2_build_dataset.py
Construye el dataset de entrenamiento del VAE a partir del corpus AKWF: cada
.wav se pasa a float, se remuestrea a 1024 muestras (FFT, preserva el cierre
del ciclo), se le quita el DC, se alinea el fundamental a fase 0 y se normaliza
por pico. Salida: akwf_processed.npy (N, 1024) y akwf_families.npy (N,).
"""

import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------- #
# Configuracion
# --------------------------------------------------------------------------- #
# Rutas relativas a este script: entrada ml/dataset/AKWF, salida ml/dataset/.
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "dataset"))
DATASET_PATH = os.path.join(DATASET_DIR, "AKWF")   # ml/dataset/AKWF
OUTPUT_DIR   = DATASET_DIR                          # ml/dataset

TARGET_LEN   = 1024          # muestras por ciclo tras el remuestreo
LIMITE       = None            # no maximo de ondas a procesar (None = todas)
VISUALIZAR   = True          # mostrar la comparacion antes/despues de alinear
N_VIS        = 6             # cuantas ondas dibujar en esa comparacion

# Si la magnitud del fundamental es despreciable frente al armonico mas fuerte
# (p.ej. en ruido), su fase es basura: en ese caso NO rotamos (fallback seguro).
PHASE_MIN_RATIO = 1e-3


# --------------------------------------------------------------------------- #
# Pasos del pipeline (funciones puras sobre un vector 1D)
# --------------------------------------------------------------------------- #
def to_float(data):
    """Convierte una onda entera (int16/int32) o float a float64 en [-1, 1]."""
    if data.ndim > 1:                       # si llega estereo, un solo canal
        data = data[:, 0]
    if np.issubdtype(data.dtype, np.integer):
        full_scale = np.iinfo(data.dtype).max + 1   # 32768 para int16
        return data.astype(np.float64) / full_scale
    return data.astype(np.float64)


def remove_dc(x):
    """Elimina el offset (componente continua) restando la media."""
    return x - np.mean(x)


def align_phase(x):
    """Rota circularmente el ciclo para dejar el fundamental a fase 0.

    Multiplicar el armonico k por exp(-j*k*phi) en el dominio de la frecuencia
    equivale a un desplazamiento circular fraccionario: alinea la fase sin
    romper el cierre del ciclo (no introduce clicks).

    Devuelve (onda, aligned). aligned es False si el fundamental era demasiado
    debil para fiarse de su fase y se dejo la onda sin rotar (fallback).
    """
    spectrum = np.fft.rfft(x)
    mag = np.abs(spectrum)
    if len(mag) < 2 or mag[1] < PHASE_MIN_RATIO * mag[1:].max():
        return x, False
    phi = np.angle(spectrum[1])
    k = np.arange(spectrum.shape[0])
    aligned_spectrum = spectrum * np.exp(-1j * k * phi)
    return np.fft.irfft(aligned_spectrum, n=len(x)), True


def normalize_peak(x):
    """Normaliza la amplitud dividiendo por el pico absoluto."""
    peak = np.max(np.abs(x))
    if peak < 1e-12:        # onda silenciosa: se deja como esta
        return x
    return x / peak


# --------------------------------------------------------------------------- #
# Carga y construccion del dataset
# --------------------------------------------------------------------------- #
def build_dataset(root, target_len=TARGET_LEN, limite=None, n_vis=0):
    """Recorre el corpus AKWF y procesa cada onda.

    Devuelve (waves, families, vis_pre, vis_post, n_fallback). vis_pre/vis_post
    contienen solo las primeras n_vis ondas (normalizadas) para comparar
    antes/despues de la alineacion. n_fallback cuenta cuantas ondas se dejaron
    sin alinear por tener el fundamental demasiado debil.
    """
    waves, families = [], []
    vis_pre, vis_post = [], []
    n_fallback = 0

    for current_dir, dirs, files in os.walk(root):
        dirs.sort()                         # recorrido determinista
        for filename in sorted(files):
            if not filename.lower().endswith(".wav"):
                continue

            path = os.path.join(current_dir, filename)
            try:
                _, data = wavfile.read(path)
            except Exception as err:
                print(f"  [aviso] no se pudo leer {path}: {err}")
                continue

            # Pipeline
            wave = to_float(data)
            wave = resample(wave, target_len)       # 600 -> 1024 (FFT)
            wave = remove_dc(wave)

            # Version pre-alineacion (ya normalizada) para la grafica
            if len(vis_pre) < n_vis:
                vis_pre.append(normalize_peak(wave.copy()))

            wave, aligned = align_phase(wave)
            if not aligned:
                n_fallback += 1
            wave = normalize_peak(wave)

            if len(vis_post) < n_vis:
                vis_post.append(wave.copy())

            waves.append(wave.astype(np.float32))
            families.append(os.path.basename(current_dir))

            if limite is not None and len(waves) >= limite:
                return (np.asarray(waves), np.asarray(families),
                        np.asarray(vis_pre), np.asarray(vis_post), n_fallback)

    return (np.asarray(waves), np.asarray(families),
            np.asarray(vis_pre), np.asarray(vis_post), n_fallback)


def plot_alignment(vis_pre, vis_post):
    """Dibuja unas pocas ondas antes y despues de alinear la fase."""
    fig, (ax_pre, ax_post) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for i in range(len(vis_pre)):
        ax_pre.plot(vis_pre[i], linewidth=1)
        ax_post.plot(vis_post[i], linewidth=1)
    ax_pre.set_title("Antes de alinear la fase")
    ax_post.set_title("Despues (fundamental a fase 0)")
    for ax in (ax_pre, ax_post):
        ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax.set_xlabel("Muestra")
        ax.grid(True, alpha=0.3)
    ax_pre.set_ylabel("Amplitud")
    fig.suptitle("Alineacion de fase del dataset AKWF")
    fig.tight_layout()
    plt.show()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    if not os.path.isdir(DATASET_PATH):
        raise SystemExit(f"No se encuentra la carpeta del dataset: {DATASET_PATH}")

    print(f"Construyendo dataset desde {DATASET_PATH} ...")
    waves, families, vis_pre, vis_post, n_fallback = build_dataset(
        DATASET_PATH, TARGET_LEN, LIMITE, N_VIS if VISUALIZAR else 0
    )

    if len(waves) == 0:
        raise SystemExit("No se proceso ninguna onda. Revisa la ruta y los .wav.")

    n = waves.shape[0]
    print(f"Ondas procesadas    : {n}")
    print(f"Forma del dataset   : {waves.shape}  dtype={waves.dtype}")
    print(f"Familias distintas  : {len(set(families.tolist()))}")
    print(f"Sin alinear (fallback fundamental debil): {n_fallback} "
          f"({100.0 * n_fallback / n:.1f}%)")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    waves_path    = os.path.join(OUTPUT_DIR, "akwf_processed.npy")
    families_path = os.path.join(OUTPUT_DIR, "akwf_families.npy")
    np.save(waves_path, waves)
    np.save(families_path, families)
    print(f"Guardado: {waves_path}")
    print(f"Guardado: {families_path}")

    if VISUALIZAR and len(vis_pre) > 0:
        plot_alignment(vis_pre, vis_post)


if __name__ == "__main__":
    main()
