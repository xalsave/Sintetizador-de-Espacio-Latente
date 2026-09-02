"""
8b_monitor_midi.py
Monitor de serie del Daisy: muestra en vivo las lineas de estado ("# NOTE_ON",
"# NOTE_OFF", "# SPI ok"...) y oculta el volcado NOTE_TABLE_* del auto-test.
  python 8b_monitor_midi.py --port COM7 [--raw]      (requiere pyserial)
"""

import argparse
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="puerto serie del Daisy (p.ej. COM7)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--raw", action="store_true",
                    help="imprime todas las lineas, incluida la tabla de auto-test")
    args = ap.parse_args()

    import serial  # pip install pyserial

    try:
        p = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        raise SystemExit(f"No se pudo abrir {args.port}: {e}\n"
                         "  - Cierra cualquier otro monitor/terminal que use ese COM.\n"
                         "  - Verifica el puerto del Daisy (Administrador de dispositivos).")

    print(f"Escuchando {args.port} @ {args.baud}. Pulsa teclas en el Keystep / toca la CYD.")
    print("(Ctrl+C para salir)\n")

    try:
        while True:
            line = p.readline().decode("ascii", errors="replace").strip()
            if not line:
                continue
            if args.raw:
                print(line)
                continue
            # Filtro: solo lineas de estado ("# ..."), fuera el volcado de tabla.
            if line.startswith("# "):
                print(line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nFin.")
    finally:
        p.close()


if __name__ == "__main__":
    main()
