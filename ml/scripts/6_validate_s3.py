"""
6_validate_s3.py
Valida la interpolacion bilineal del ESP32-S3 contra la referencia en PC.

Idea
----
El S3 imprime por serie la wavetable interpolada para una coordenada (x,y) en
0..65535 (bloque WAVE_BEGIN ... WAVE_END del main.cpp de la sesion 6). Este
script recalcula esa MISMA wavetable en numpy desde grid.npy con el mismo mapeo
(decision de S3: bilineal sobre grid 16x16), y compara muestra a muestra. Si el
error maximo es ~1 LSB de Q15, el firmware del S3 esta validado de forma
objetiva (no solo "se imprime algo").

Uso
---
  1) En el monitor serie del S3, manda una coordenada, p.ej.  "40000 12000"
  2) Copia TODO el bloque (incluidos WAVE_BEGIN y WAVE_END) a un .txt, o
     captura el serie a fichero. Ejemplo de captura con pyserial mas abajo.
  3) python 6_validate_s3.py --dump captura.txt --x 40000 --y 12000

Requiere ml/exports/grid.npy (lo genera 4_bake_grid.py).
"""

import os
import argparse
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRID_PATH  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "exports", "grid.npy"))


def reference_wave(grid, x, y):
    """Replica EXACTAMENTE la bilineal del firmware (interpolation.cpp).

    grid: (GRID, GRID, TABLE_LEN) float en [-1,1], indexado [fila=Y][col=X].
    x, y: enteros 0..65535. Devuelve la wavetable Q15 (int16) esperada.
    """
    G = grid.shape[0]
    scale = (G - 1) / 65535.0
    gx = x * scale          # eje X (columna)
    gy = y * scale          # eje Y (fila)

    ix0 = int(np.floor(gx)); ix0 = max(0, min(G - 1, ix0))
    iy0 = int(np.floor(gy)); iy0 = max(0, min(G - 1, iy0))
    ix1 = ix0 + 1 if ix0 < G - 1 else ix0
    iy1 = iy0 + 1 if iy0 < G - 1 else iy0
    fx = min(1.0, max(0.0, gx - ix0))
    fy = min(1.0, max(0.0, gy - iy0))

    # El firmware interpola sobre el grid YA en Q15. Replicamos ese orden:
    # primero a Q15, luego bilineal, luego redondeo (como lroundf en el S3).
    q = np.round(grid * 32767.0)
    q = np.clip(q, -32768, 32767)

    tl = q[iy0, ix0]; tr = q[iy0, ix1]
    bl = q[iy1, ix0]; br = q[iy1, ix1]
    top = tl + (tr - tl) * fx
    bot = bl + (br - bl) * fx
    val = top + (bot - top) * fy
    return np.round(val).astype(np.int16), (ix0, ix1, iy0, iy1, fx, fy)


def parse_dump(path):
    """Extrae las 1024 muestras del bloque WAVE_BEGIN ... WAVE_END."""
    vals, inside = [], False
    with open(path, "r", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if s == "WAVE_BEGIN":
                inside = True; vals = []; continue
            if s == "WAVE_END":
                break
            if inside and s and (s.lstrip("-").isdigit()):
                vals.append(int(s))
    return np.array(vals, dtype=np.int32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True, help="fichero con el bloque WAVE_*")
    ap.add_argument("--x", type=int, required=True)
    ap.add_argument("--y", type=int, required=True)
    args = ap.parse_args()

    if not os.path.isfile(GRID_PATH):
        raise SystemExit(f"No se encuentra {GRID_PATH}. Corre antes 4_bake_grid.py.")

    grid = np.load(GRID_PATH)                       # (G, G, TABLE_LEN) float32
    ref, loc = reference_wave(grid, args.x, args.y)
    got = parse_dump(args.dump)

    if got.size != ref.size:
        raise SystemExit(f"Tamano distinto: S3={got.size}, ref={ref.size}. "
                         "Revisa que copiaste el bloque WAVE_BEGIN..WAVE_END entero.")

    err = np.abs(got.astype(np.int32) - ref.astype(np.int32))
    ix0, ix1, iy0, iy1, fx, fy = loc
    print(f"coord=({args.x},{args.y})  X[{ix0}->{ix1}] fx={fx:.4f}  "
          f"Y[{iy0}->{iy1}] fy={fy:.4f}")
    print(f"error abs:  max={err.max()}  media={err.mean():.3f}  "
          f"muestras_con_error={(err > 0).sum()}/{err.size}")
    if err.max() <= 1:
        print("OK: coincide con la referencia dentro de 1 LSB (Q15). Bilineal validada.")
    else:
        print("ATENCION: error > 1 LSB. Revisa convencion de ejes o el mapeo de rango.")


if __name__ == "__main__":
    main()
