"""
7_validate_spi.py
Valida el enlace SPI S3 -> Daisy de forma objetiva (sesion 7), no solo de oido.

Idea
----
En S6 ya se valido que el S3 interpola bien (6_validate_s3.py: S3 vs numpy, error
<= 1 LSB Q15). En S7 lo que hay que probar es el TRANSPORTE: que la wavetable que
el Daisy REPRODUCE es exactamente la que el S3 calculo y envio por SPI.

Para una coordenada (x,y) fija se cruzan hasta tres cosas:
  1. ref  : la wavetable que numpy calcula desde grid.npy (verdad de referencia,
            misma bilineal que el firmware). Reutiliza reference_wave() de
            6_validate_s3.py -> una sola fuente de verdad para el mapeo.
  2. daisy : las 1024 muestras que el Daisy imprime por USB al recibir la trama
            (bloque WAVE_BEGIN..WAVE_END, SPI_DEBUG_DUMP=1 en su .cpp).
  3. s3    : (opcional) el volcado WAVE_* del propio S3 para esa coord.

Criterios:
  - daisy == s3    -> exactamente igual (0 errores): el SPI no corrompe nada.
  - daisy vs ref   -> <= 1 LSB Q15: la cadena entera es correcta (mismo margen de
                     redondeo Q15 ya caracterizado en S6).

Uso
---
  1) Flashea el Daisy con SPI_DEBUG_DUMP 1.
  2) Manda UNA coordenada fija al S3 (texto "x y" por su USB, o un toque en la
     CYD). El S3 interpola y la envia por SPI; el Daisy vuelca el bloque WAVE_*.
  3) Captura el serie del DAISY a un fichero (ver captura con pyserial abajo) y:
       python 7_validate_spi.py --daisy daisy_dump.txt --x 40000 --y 12000
     Opcional, cruzar tambien contra el volcado del S3:
       python 7_validate_spi.py --daisy daisy_dump.txt --s3 s3_dump.txt \
                                --x 40000 --y 12000

Captura del serie del Daisy (ejemplo, ajustar COM):
  python -c "import serial;p=serial.Serial('COM7',115200,timeout=2);\
open('daisy_dump.txt','wb').write(p.read(200000))"

Requiere ml/exports/grid.npy (lo genera 4_bake_grid.py).
"""

import os
import argparse
import importlib.util
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRID_PATH  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "exports", "grid.npy"))
REF_SCRIPT = os.path.join(SCRIPT_DIR, "6_validate_s3.py")


def load_ref_module():
    """Carga 6_validate_s3.py como modulo para reutilizar reference_wave() y
    parse_dump() (el nombre empieza por digito, no vale un import normal)."""
    spec = importlib.util.spec_from_file_location("validate_s3", REF_SCRIPT)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT-FALSE. Mismo algoritmo que spi_sender.cpp (S3) y el .cpp del
    Daisy. Se usa para confirmar que el CRC que veriamos en la trama coincide con
    el de las muestras de referencia."""
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daisy", required=True,
                    help="captura del serie del Daisy con el bloque WAVE_*")
    ap.add_argument("--s3", default=None,
                    help="(opcional) volcado WAVE_* del S3 para la misma coord")
    ap.add_argument("--x", type=int, required=True)
    ap.add_argument("--y", type=int, required=True)
    args = ap.parse_args()

    if not os.path.isfile(GRID_PATH):
        raise SystemExit(f"No se encuentra {GRID_PATH}. Corre antes 4_bake_grid.py.")
    if not os.path.isfile(REF_SCRIPT):
        raise SystemExit(f"No se encuentra {REF_SCRIPT} (se reutiliza su bilineal).")

    ref_mod = load_ref_module()
    grid    = np.load(GRID_PATH)
    ref, loc = ref_mod.reference_wave(grid, args.x, args.y)
    daisy    = ref_mod.parse_dump(args.daisy)

    ix0, ix1, iy0, iy1, fx, fy = loc
    print(f"coord=({args.x},{args.y})  X[{ix0}->{ix1}] fx={fx:.4f}  "
          f"Y[{iy0}->{iy1}] fy={fy:.4f}")

    if daisy.size != ref.size:
        raise SystemExit(f"Tamano distinto: Daisy={daisy.size}, ref={ref.size}. "
                         "Revisa que capturaste el bloque WAVE_BEGIN..WAVE_END entero.")

    ok = True

    # --- 1) Daisy (reproducido) vs referencia numpy -------------------------
    err = np.abs(daisy.astype(np.int32) - ref.astype(np.int32))
    print(f"[Daisy vs ref]  max={err.max()}  media={err.mean():.3f}  "
          f"muestras_con_error={(err > 0).sum()}/{err.size}")
    if err.max() <= 1:
        print("  OK: la wavetable reproducida coincide con la referencia (<=1 LSB Q15).")
    else:
        print("  ATENCION: error > 1 LSB. Revisa el mapeo o la integridad SPI.")
        ok = False

    # --- 2) Daisy vs volcado del S3 (integridad pura del transporte) --------
    if args.s3:
        s3 = ref_mod.parse_dump(args.s3)
        if s3.size != daisy.size:
            print(f"[Daisy vs S3]   tamanos distintos (S3={s3.size}, Daisy={daisy.size}).")
            ok = False
        else:
            d = np.abs(daisy.astype(np.int32) - s3.astype(np.int32))
            print(f"[Daisy vs S3]   max={d.max()}  muestras_con_error={(d > 0).sum()}/{d.size}")
            if d.max() == 0:
                print("  OK: el SPI transporta la tabla EXACTA (0 errores). Enlace integro.")
            else:
                print("  ATENCION: el Daisy recibe algo distinto de lo que el S3 volco.")
                ok = False

    # --- CRC de referencia (informativo): el que deberia viajar en la trama --
    payload = ref.astype("<i2").tobytes()
    print(f"[info] CRC16 de referencia (payload) = 0x{crc16_ccitt(payload):04X}")

    print("RESULTADO:", "VALIDADO" if ok else "REVISAR")


if __name__ == "__main__":
    main()
