"""
8_validate_midi.py
Valida de forma objetiva la conversion nota MIDI -> frecuencia del Daisy (S8),
no solo de oido.

Idea
----
El Daisy usa una unica funcion note_to_hz() tanto para tocar en vivo (Note On ->
osc.SetFreq) como para volcar por serie la tabla de las 128 notas (MIDI_SELFTEST).
Asi que validar esa tabla valida directamente el camino de sonido real.

Con MIDI_SELFTEST=1 el Daisy imprime, al arrancar y cada 3 s, un bloque:

    NOTE_TABLE_BEGIN sr_milli=<int> len=1024
    <note> <hz_milli> <pinc_micro>
    ...   (128 lineas, notas 0..127)
    NOTE_TABLE_END

Este script lee ese bloque (de un fichero capturado o directo por --port) y para
cada nota comprueba dos cosas contra la referencia teorica:

  1. hz    == mtof(note) = 440 * 2^((note-69)/12)          -> conversion nota->Hz
  2. pinc  == hz * len / sr   (fase por muestra del oscilador)

usando la sample rate REAL que el propio Daisy reporto (sr_milli), no un 48000
asumido: asi la comprobacion de phase_inc es exacta aunque el codec no corra a
48000.000 clavados.

Uso
---
  A) Desde un fichero capturado del serie del Daisy:
       python 8_validate_midi.py --file daisy_midi.txt

  B) Directo por puerto serie (captura ~4 s, 1 bloque completo seguro):
       python 8_validate_midi.py --port COM7

Captura manual del serie a fichero (ejemplo, ajustar COM):
  python -c "import serial;p=serial.Serial('COM7',115200,timeout=5);\
open('daisy_midi.txt','wb').write(p.read(60000))"

Tolerancias: 1 milihercio en Hz y 2 micro-unidades en phase_inc (redondeo del
entero que imprime el Daisy). No requiere ningun fichero del repo: la referencia
es puramente la formula MIDI.
"""

import os
import argparse

# Tolerancias. Dimensionadas simulando el float32 del firmware contra la
# referencia en doble precision: el error real observado es <=2 milihercios en
# Hz y ~2e-7 relativo en phase_inc (ruido de float32 sobre valores ~1e8, no un
# error de formula). Se deja margen holgado, aun asi ordenes de magnitud por
# debajo de cualquier bug real (un semitono mal = miles de milihercios).
HZ_TOL_MILLI = 5      # +-5 milihercios (float32 da <=2; un bug real da miles)
PINC_REL_TOL = 1e-5   # 10 ppm en phase_inc (float32 da ~0.2 ppm)


def mtof(note: int) -> float:
    """Nota MIDI -> Hz. Misma formula que daisysp::mtof y note_to_hz() del Daisy."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def capture_serial(port: str, baud: int, seconds: float) -> str:
    """Lee el serie unos segundos y devuelve el texto (para no depender de un
    fichero previo). pyserial es opcional: solo hace falta con --port."""
    import time
    import serial  # pip install pyserial

    p = serial.Serial(port, baud, timeout=1)
    t0 = time.time()
    buf = bytearray()
    while time.time() - t0 < seconds:
        buf += p.read(4096)
    p.close()
    return buf.decode("ascii", errors="replace")


def parse_last_table(text: str):
    """Devuelve (sr_hz, {note: (hz_milli, pinc_micro)}) del ULTIMO bloque
    NOTE_TABLE_BEGIN..END completo del texto. Ignora cualquier otra linea
    (p.ej. '# SPI ok ...' si se toco la CYD durante la captura)."""
    sr_hz = None
    table = {}
    best_sr, best_table = None, None

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("NOTE_TABLE_BEGIN"):
            sr_hz, table = None, {}
            for tok in line.split():
                if tok.startswith("sr_milli="):
                    sr_hz = int(tok.split("=", 1)[1]) / 1000.0
        elif line.startswith("NOTE_TABLE_END"):
            if sr_hz is not None and len(table) == 128:
                best_sr, best_table = sr_hz, table  # nos quedamos con el ultimo completo
            sr_hz, table = None, {}
        else:
            parts = line.split()
            if len(parts) == 3 and sr_hz is not None:
                try:
                    n, hz_milli, pinc_micro = (int(parts[0]), int(parts[1]),
                                               int(parts[2]))
                except ValueError:
                    continue
                if 0 <= n <= 127:
                    table[n] = (hz_milli, pinc_micro)

    return best_sr, best_table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="fichero con la captura del serie del Daisy")
    ap.add_argument("--port", help="puerto serie del Daisy (p.ej. COM7)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--seconds", type=float, default=4.0,
                    help="segundos a capturar con --port (default 4, >1 bloque)")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", errors="replace") as f:
            text = f.read()
    elif args.port:
        print(f"Capturando {args.seconds:.0f}s de {args.port} @ {args.baud}...")
        text = capture_serial(args.port, args.baud, args.seconds)
    else:
        raise SystemExit("Indica --file <captura> o --port <COMx>.")

    sr_hz, table = parse_last_table(text)
    if table is None or sr_hz is None:
        raise SystemExit("No se encontro un bloque NOTE_TABLE_* completo (128 notas). "
                         "Revisa que el Daisy corre con MIDI_SELFTEST=1 y que la "
                         "captura duro lo suficiente.")

    print(f"Bloque leido: sr={sr_hz:.3f} Hz, {len(table)} notas.")

    len_table = 1024  # TABLE_LEN del firmware
    n_bad = 0
    worst_hz = 0        # milihercios
    worst_pinc_ppm = 0.0

    for n in range(128):
        hz_milli, pinc_micro = table[n]

        # Referencia en DOBLE precision (no desde el Hz ya redondeado): mtof y la
        # fase por muestra con la sr real que reporto el Daisy.
        ref_hz   = mtof(n)
        ref_pinc = ref_hz * len_table / sr_hz

        # 1) nota -> Hz contra mtof
        d_hz = abs(hz_milli - round(ref_hz * 1000.0))

        # 2) phase_inc contra hz*len/sr (error relativo, robusto en todo el rango)
        meas_pinc = pinc_micro / 1e6
        rel_pinc  = abs(meas_pinc - ref_pinc) / ref_pinc if ref_pinc > 0 else 0.0

        worst_hz = max(worst_hz, d_hz)
        worst_pinc_ppm = max(worst_pinc_ppm, rel_pinc * 1e6)

        if d_hz > HZ_TOL_MILLI or rel_pinc > PINC_REL_TOL:
            n_bad += 1
            if n_bad <= 8:  # no inundar
                print(f"  MISMATCH note={n:3d}  hz={hz_milli/1000:.3f} "
                      f"(ref {ref_hz:.3f}, d={d_hz}m)  "
                      f"pinc={meas_pinc:.6f} "
                      f"(ref {ref_pinc:.6f}, {rel_pinc*1e6:.2f}ppm)")

    # Puntos de referencia clasicos para el informe.
    for n, name in [(69, "A4=440"), (60, "C4"), (0, "min"), (127, "max")]:
        print(f"  nota {n:3d} ({name:7s}): {table[n][0]/1000:9.3f} Hz  "
              f"(mtof {mtof(n):9.3f})")

    print(f"[nota->Hz]     error max = {worst_hz} milihercios "
          f"(tol {HZ_TOL_MILLI})")
    print(f"[phase_inc]    error max = {worst_pinc_ppm:.2f} ppm "
          f"(tol {PINC_REL_TOL*1e6:.0f} ppm)")
    print(f"notas fuera de tolerancia: {n_bad}/128")
    print("RESULTADO:", "VALIDADO" if n_bad == 0 else "REVISAR")


if __name__ == "__main__":
    main()
