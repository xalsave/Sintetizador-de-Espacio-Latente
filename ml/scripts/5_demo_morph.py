"""
5_demo_morph.py
Demo en PC del morphing latente: el raton navega el plano latente, se interpola
bilinealmente entre las wavetables vecinas del grid (como hara el S3) y se
reproduce en vivo con crossfade entre tablas (como hara el Daisy). El panel
derecho es un osciloscopio con la "diversidad" (RMS respecto a la onda media)
para distinguir un grid vivo de uno colapsado.
Teclas: 'a' arpegiador on/off, +/- octava. Requiere grid.npy y grid_meta.npz.
"""

import os
import sys
import threading
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    raise SystemExit("Falta sounddevice: pip install sounddevice")

import matplotlib.pyplot as plt


# --------------------------------------------------------------------------- #
# Configuracion
# --------------------------------------------------------------------------- #
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "exports"))
GRID_PATH   = os.path.join(OUTPUT_DIR, "grid.npy")
META_PATH   = os.path.join(OUTPUT_DIR, "grid_meta.npz")

SAMPLE_RATE = 48000        # Hz, igual que el codec del Daisy
BASE_NOTE   = 220.0        # tono base de demo (La3)
XFADE_MS    = 15.0         # crossfade entre tablas, ms
AMP         = 0.22         # volumen de salida [0..1], suave para los oidos
BLOCK       = 256          # muestras por bloque de audio

# Arpegiador: semitonos relativos a la nota base. Acorde mayor con septima + 8va.
ARP_STEPS   = [0, 4, 7, 11, 12, 11, 7, 4]
ARP_BPM     = 240          # velocidad del arpegio (notas por minuto efectivas)


def midi_ratio(semitones):
    """Factor de frecuencia para un desplazamiento en semitonos (12-TET)."""
    return 2.0 ** (semitones / 12.0)


# --------------------------------------------------------------------------- #
# Carga del grid
# --------------------------------------------------------------------------- #
def load_grid():
    if not (os.path.isfile(GRID_PATH) and os.path.isfile(META_PATH)):
        raise SystemExit(
            f"Faltan {GRID_PATH} o {META_PATH}. Ejecuta antes 4_bake_grid.py."
        )
    grid = np.load(GRID_PATH).astype(np.float32)            # (G, G, TABLE_LEN)
    meta = np.load(META_PATH)
    bounds = (float(meta["x_min"]), float(meta["x_max"]),
              float(meta["y_min"]), float(meta["y_max"]))
    print(f"Grid: {grid.shape}  limites x[{bounds[0]:.2f},{bounds[1]:.2f}] "
          f"y[{bounds[2]:.2f},{bounds[3]:.2f}]")
    return grid, bounds


def diagnose_grid(grid):
    """Sonda rapida: cuanto difieren las 4 esquinas y el rango global.
    Si las distancias son ~0, el grid esta colapsado (problema de modelo, no
    de percepcion) y conviene iterar el VAE antes de seguir."""
    G = grid.shape[0]
    corners = {
        "sup-izq": grid[0, 0],     "sup-der": grid[0, G - 1],
        "inf-izq": grid[G - 1, 0], "inf-der": grid[G - 1, G - 1],
    }
    keys = list(corners)
    print("\n--- Diagnostico del grid (RMS entre esquinas) ---")
    maxd = 0.0
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            d = float(np.sqrt(np.mean(
                (corners[keys[a]] - corners[keys[b]]) ** 2)))
            maxd = max(maxd, d)
            print(f"  {keys[a]:>8} vs {keys[b]:>8}: {d:.4f}")
    # Desviacion media tabla-a-tabla respecto a la media global del grid.
    mean_wave = grid.reshape(-1, grid.shape[-1]).mean(axis=0)
    spread = float(np.sqrt(np.mean(
        (grid.reshape(-1, grid.shape[-1]) - mean_wave) ** 2)))
    print(f"  dispersion global (RMS vs onda media): {spread:.4f}")
    if maxd < 0.02:
        print("  AVISO: esquinas casi identicas -> grid posiblemente COLAPSADO.")
        print("         El problema seria del VAE, no de la percepcion.")
    else:
        print("  OK: hay diferencia timbrica real entre zonas del latente.")
    print("-------------------------------------------------\n")
    return mean_wave


# --------------------------------------------------------------------------- #
# Interpolacion bilineal sobre el grid (lo que hara el S3)
# --------------------------------------------------------------------------- #
def bilinear_table(grid, gx, gy):
    """Devuelve la wavetable interpolada para coords de grid continuas
    (gx, gy) en [0, G-1]. gx -> columna(eje X), gy -> fila(eje Y)."""
    G = grid.shape[0]
    gx = min(max(gx, 0.0), G - 1.0)
    gy = min(max(gy, 0.0), G - 1.0)
    j0 = int(np.floor(gx)); j1 = min(j0 + 1, G - 1)
    i0 = int(np.floor(gy)); i1 = min(i0 + 1, G - 1)
    tx = gx - j0
    ty = gy - i0
    # grid[fila i = Y][columna j = X]
    w00 = (1 - tx) * (1 - ty)
    w10 = tx * (1 - ty)
    w01 = (1 - tx) * ty
    w11 = tx * ty
    return (w00 * grid[i0, j0] + w10 * grid[i0, j1] +
            w01 * grid[i1, j0] + w11 * grid[i1, j1]).astype(np.float32)


# --------------------------------------------------------------------------- #
# Motor de audio: acumulador de fase + crossfade entre tablas + arpegiador
# --------------------------------------------------------------------------- #
class MorphSynth:
    """Genera audio leyendo la tabla activa con un acumulador de fase. Cuando
    cambia la coordenada objetivo, hace crossfade de la tabla vieja a la nueva
    sin reiniciar la fase (anti-click, como el Daisy). Opcionalmente arpegia
    una secuencia de notas para destapar diferencias timbricas."""

    def __init__(self, grid, bounds):
        self.grid = grid
        self.bounds = bounds
        self.table_len = grid.shape[-1]
        self.lock = threading.Lock()

        center = (grid.shape[0] - 1) / 2.0
        t0 = bilinear_table(grid, center, center)
        self.cur_table = t0.copy()     # tabla que suena
        self.new_table = t0.copy()     # tabla objetivo tras un cambio
        self.xfade_n = max(1, int(SAMPLE_RATE * XFADE_MS / 1000.0))
        self.xfade_left = 0

        self.phase = 0.0               # 0..table_len, acumulador de fase
        self.base_note = BASE_NOTE
        self.octave = 0                # desplazamiento de octava (+/-)

        # Arpegiador
        self.arp_on = False
        self.arp_idx = 0
        self.arp_samples_per_step = int(SAMPLE_RATE * 60.0 / ARP_BPM)
        self.arp_counter = 0
        # Envolvente sencilla por nota (evita clicks al saltar de nota).
        self.note_env = 1.0
        self.env_attack = int(SAMPLE_RATE * 0.005)   # 5 ms
        self.env_pos = self.env_attack

        # Para el osciloscopio: copia de la tabla mezclada actual (segura de leer).
        self.scope_table = t0.copy()

    def _current_freq(self):
        f = self.base_note * (2.0 ** self.octave)
        if self.arp_on:
            f *= midi_ratio(ARP_STEPS[self.arp_idx])
        return f

    def set_target(self, gx, gy):
        """Fija una nueva tabla objetivo e inicia el crossfade."""
        tbl = bilinear_table(self.grid, gx, gy)
        with self.lock:
            self.new_table = tbl
            self.xfade_left = self.xfade_n
            self.scope_table = tbl     # el osciloscopio muestra el objetivo

    def toggle_arp(self):
        with self.lock:
            self.arp_on = not self.arp_on
            self.arp_idx = 0
            self.arp_counter = 0
        return self.arp_on

    def shift_octave(self, d):
        with self.lock:
            self.octave = max(-2, min(2, self.octave + d))
        return self.octave

    def callback(self, outdata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        with self.lock:
            cur = self.cur_table
            new = self.new_table
            xfade_left = self.xfade_left
            phase = self.phase
            arp_on = self.arp_on
            arp_idx = self.arp_idx
            arp_counter = self.arp_counter
            note_env = self.note_env
            env_pos = self.env_pos

        tlen = self.table_len
        xn = self.xfade_n
        buf = np.empty(frames, dtype=np.float32)
        phase_inc = self._current_freq() * tlen / SAMPLE_RATE

        for n in range(frames):
            # Avance del arpegiador: al cambiar de nota, reinicia envolvente.
            if arp_on:
                arp_counter += 1
                if arp_counter >= self.arp_samples_per_step:
                    arp_counter = 0
                    arp_idx = (arp_idx + 1) % len(ARP_STEPS)
                    env_pos = 0                      # re-ataque suave
                    phase_inc = (self.base_note * (2.0 ** self.octave) *
                                 midi_ratio(ARP_STEPS[arp_idx]) *
                                 tlen / SAMPLE_RATE)

            # Envolvente de ataque corta para no clickar al saltar de nota.
            if env_pos < self.env_attack:
                note_env = env_pos / self.env_attack
                env_pos += 1
            else:
                note_env = 1.0

            s_cur = self._read_sample_at(cur, phase, tlen)
            if xfade_left > 0:
                g = (xn - xfade_left) / xn
                s_new = self._read_sample_at(new, phase, tlen)
                s = s_cur * (1 - g) + s_new * g
                xfade_left -= 1
                if xfade_left == 0:
                    cur = new
            else:
                s = s_cur

            buf[n] = s * note_env
            phase += phase_inc
            if phase >= tlen:
                phase -= tlen

        with self.lock:
            self.cur_table = cur
            self.xfade_left = xfade_left
            self.phase = phase
            self.arp_idx = arp_idx
            self.arp_counter = arp_counter
            self.note_env = note_env
            self.env_pos = env_pos

        outdata[:, 0] = AMP * buf

    @staticmethod
    def _read_sample_at(table, phase, tlen):
        i0 = int(phase) % tlen
        i1 = (i0 + 1) % tlen
        frac = phase - np.floor(phase)
        return table[i0] * (1 - frac) + table[i1] * frac

    def get_scope(self):
        with self.lock:
            return self.scope_table.copy()


# --------------------------------------------------------------------------- #
# Interfaz: plano latente (raton) + osciloscopio (en vivo)
# --------------------------------------------------------------------------- #
def run():
    grid, bounds = load_grid()
    G = grid.shape[0]
    mean_wave = diagnose_grid(grid)
    synth = MorphSynth(grid, bounds)

    # El backend de matplotlib determina si la GUI se refresca sola. Si ves
    # 'agg' (no interactivo) la ventana no responderia: instala un backend GUI
    # (pip install pyqt5) o exporta MPLBACKEND=QtAgg / TkAgg antes de ejecutar.
    print(f"Backend matplotlib: {plt.get_backend()}")

    fig, (ax_lat, ax_scope) = plt.subplots(1, 2, figsize=(11, 5.5))

    # --- Panel izquierdo: plano latente ---
    ax_lat.set_title("Plano latente — mueve el raton aqui")
    ax_lat.set_xlim(0, G - 1); ax_lat.set_ylim(0, G - 1)
    ax_lat.set_xlabel("eje X (latente dim 0)")
    ax_lat.set_ylabel("eje Y (latente dim 1)")
    ax_lat.grid(alpha=0.3)
    gx_nodes, gy_nodes = np.meshgrid(range(G), range(G))
    ax_lat.scatter(gx_nodes, gy_nodes, s=8, c="lightgray")
    cursor, = ax_lat.plot([(G - 1) / 2], [(G - 1) / 2], "o",
                          color="crimson", ms=10)

    # --- Panel derecho: osciloscopio ---
    t0 = synth.get_scope()
    scope_line, = ax_scope.plot(np.arange(len(t0)), t0, lw=1.0, color="teal")
    ax_scope.set_ylim(-1.1, 1.1)
    ax_scope.set_xlim(0, len(t0) - 1)
    ax_scope.set_xlabel("muestra (1 ciclo)")
    ax_scope.set_title("Osciloscopio — onda interpolada")
    ax_scope.grid(alpha=0.3)
    ax_scope.axhline(0, color="black", lw=0.4, ls=":")

    state_txt = fig.text(0.5, 0.015,
                         "arp: OFF   |   octava: 0   |   tecla 'a' arpegio, +/- octava",
                         ha="center", fontsize=9)

    # Estado compartido de la posicion del raton. El callback SOLO escribe aqui;
    # el repintado (cursor + osciloscopio) ocurre todo en el lazo de animacion,
    # que es lo unico que el backend mantiene vivo de forma fiable. Repintar
    # dentro del callback del raton es justo lo que provocaba que solo se
    # actualizara al redimensionar la ventana.
    mouse = {"gx": (G - 1) / 2.0, "gy": (G - 1) / 2.0, "dirty": True}

    def on_move(event):
        if event.inaxes != ax_lat or event.xdata is None:
            return
        mouse["gx"], mouse["gy"] = event.xdata, event.ydata
        mouse["dirty"] = True
        synth.set_target(event.xdata, event.ydata)

    def on_key(event):
        if event.key == "a":
            on = synth.toggle_arp()
            print(f"Arpegiador: {'ON' if on else 'OFF'}")
        elif event.key in ("+", "="):
            o = synth.shift_octave(+1); print(f"Octava: {o:+d}")
        elif event.key in ("-", "_"):
            o = synth.shift_octave(-1); print(f"Octava: {o:+d}")

    fig.canvas.mpl_connect("motion_notify_event", on_move)
    fig.canvas.mpl_connect("key_press_event", on_key)

    # Lazo unico de refresco via FuncAnimation (~30 fps). Mas fiable que un
    # timer manual: actualiza cursor, osciloscopio, diversidad y estado.
    from matplotlib.animation import FuncAnimation

    def refresh(_frame):
        if mouse["dirty"]:
            cursor.set_data([mouse["gx"]], [mouse["gy"]])
            mouse["dirty"] = False
        wav = synth.get_scope()
        scope_line.set_ydata(wav)
        div = float(np.sqrt(np.mean((wav - mean_wave) ** 2)))   # vs onda media
        ax_scope.set_title(f"Osciloscopio — onda interpolada  "
                           f"(diversidad RMS vs media: {div:.3f})")
        state_txt.set_text(
            f"arp: {'ON ' if synth.arp_on else 'OFF'}   |   "
            f"octava: {synth.octave:+d}   |   tecla 'a' arpegio, +/- octava")
        return scope_line, cursor, state_txt

    stream = sd.OutputStream(
        samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK,
        callback=synth.callback,
    )
    with stream:
        print("Sonando. Mueve el raton; pulsa 'a' para arpegio, +/- octava.")
        print("Cierra la ventana para salir.")
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        # blit=False por compatibilidad entre backends (Qt/Tk/macosx).
        # Guardamos la referencia: si se recolecta, la animacion se detiene.
        anim = FuncAnimation(fig, refresh, interval=33,
                             blit=False, cache_frame_data=False)
        fig._morph_anim = anim   # evita que el GC se lleve la animacion
        plt.show()
    print("Demo terminada.")


if __name__ == "__main__":
    run()
