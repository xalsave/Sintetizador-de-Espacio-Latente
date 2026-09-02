"""
4_bake_grid.py
Hornea el grid 16x16 de wavetables con el VAE entrenado (ml/exports/vae.pt):
encodea el dataset, fija los limites del latente en los percentiles 2-98 de
cada eje (evita esquinas extrapoladas de zonas vacias), decodifica una tabla
por nodo y exporta grid.npy, grid_meta.npz, grid.h (Q15 int16: 512 KB en la
flash del S3 en vez de 1 MB en float) y grid_preview.png.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.nn.functional as F


# --------------------------------------------------------------------------- #
# Configuracion
# --------------------------------------------------------------------------- #
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "dataset"))
OUTPUT_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "exports"))

PROCESSED_PATH = os.path.join(DATASET_DIR, "akwf_processed.npy")
CKPT_PATH      = os.path.join(OUTPUT_DIR, "vae.pt")

GRID        = 16            # rejilla 16x16 = 256 wavetables
PCTL_LOW    = 2.0           # percentil inferior para los limites del latente
PCTL_HIGH   = 98.0          # percentil superior
SEED        = 42

torch.manual_seed(SEED)
np.random.seed(SEED)


# --------------------------------------------------------------------------- #
# Modelo (identico al de 3_train_vae.py; solo necesitamos el decoder en eval)
# --------------------------------------------------------------------------- #
class VAE(nn.Module):
    """Misma arquitectura FC que en 3_train_vae.py. Replicada aqui para poder
    cargar el state_dict sin importar el script de entrenamiento."""

    def __init__(self, input_dim, latent_dim, hidden):
        super().__init__()
        h1, h2 = hidden
        # Encoder
        self.enc_fc1 = nn.Linear(input_dim, h1)
        self.enc_fc2 = nn.Linear(h1, h2)
        self.fc_mu     = nn.Linear(h2, latent_dim)
        self.fc_logvar = nn.Linear(h2, latent_dim)
        # Decoder (espejo)
        self.dec_fc1 = nn.Linear(latent_dim, h2)
        self.dec_fc2 = nn.Linear(h2, h1)
        self.dec_out = nn.Linear(h1, input_dim)

    def encode(self, x):
        h = F.relu(self.enc_fc1(x))
        h = F.relu(self.enc_fc2(h))
        return self.fc_mu(h), self.fc_logvar(h)

    def decode(self, z):
        h = F.relu(self.dec_fc1(z))
        h = F.relu(self.dec_fc2(h))
        return torch.tanh(self.dec_out(h))      # [-1, 1]


# --------------------------------------------------------------------------- #
# Carga del modelo entrenado
# --------------------------------------------------------------------------- #
def load_model(device):
    if not os.path.isfile(CKPT_PATH):
        raise SystemExit(
            f"No se encuentra {CKPT_PATH}. Ejecuta antes 3_train_vae.py."
        )
    ckpt = torch.load(CKPT_PATH, map_location=device)
    model = VAE(
        input_dim=ckpt["input_dim"],
        latent_dim=ckpt["latent_dim"],
        hidden=tuple(ckpt["hidden"]),
    ).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    print(f"Modelo cargado: latent_dim={ckpt['latent_dim']}, "
          f"hidden={tuple(ckpt['hidden'])}, beta={ckpt.get('beta')}, "
          f"epochs={ckpt.get('epochs')}")
    if ckpt["latent_dim"] != 2:
        raise SystemExit("Este bake asume latente 2D (control tactil x,y).")
    return model


# --------------------------------------------------------------------------- #
# Limites del latente (percentiles de la zona poblada)
# --------------------------------------------------------------------------- #
def latent_bounds(model, device):
    """Encodea todo el dataset y devuelve (x_min, x_max, y_min, y_max) en los
    percentiles PCTL_LOW/PCTL_HIGH de cada eje. Usa mu (determinista)."""
    if not os.path.isfile(PROCESSED_PATH):
        raise SystemExit(
            f"No se encuentra {PROCESSED_PATH}. Ejecuta antes 2_build_dataset.py."
        )
    waves = np.load(PROCESSED_PATH).astype(np.float32)   # (N, 1024)
    x = torch.from_numpy(waves).to(device)
    with torch.no_grad():
        mu, _ = model.encode(x)
    mu = mu.cpu().numpy()                                 # (N, 2)

    x_min, x_max = np.percentile(mu[:, 0], [PCTL_LOW, PCTL_HIGH])
    y_min, y_max = np.percentile(mu[:, 1], [PCTL_LOW, PCTL_HIGH])
    print(f"Latente encodeado: {mu.shape[0]} ondas")
    print(f"Limites grid (pctl {PCTL_LOW:.0f}-{PCTL_HIGH:.0f}): "
          f"x[{x_min:.3f}, {x_max:.3f}]  y[{y_min:.3f}, {y_max:.3f}]")
    return float(x_min), float(x_max), float(y_min), float(y_max), mu


# --------------------------------------------------------------------------- #
# Bake del grid
# --------------------------------------------------------------------------- #
def bake(model, bounds, device):
    """Decodifica una wavetable en cada nodo de la rejilla GRID x GRID.

    Convencion de ejes (importante, debe casar con el firmware del S3):
      - eje X (columna j) recorre la dimension latente 0, de x_min a x_max
      - eje Y (fila i)    recorre la dimension latente 1, de y_min a y_max
      grid[i, j] = decode( (x[j], y[i]) )
    """
    x_min, x_max, y_min, y_max = bounds
    xs = np.linspace(x_min, x_max, GRID, dtype=np.float32)   # dim latente 0
    ys = np.linspace(y_min, y_max, GRID, dtype=np.float32)   # dim latente 1

    # Construye los 256 puntos latentes en orden fila-mayor (i sobre Y, j sobre X)
    coords = np.zeros((GRID * GRID, 2), dtype=np.float32)
    k = 0
    for i in range(GRID):          # fila -> eje Y
        for j in range(GRID):      # columna -> eje X
            coords[k, 0] = xs[j]   # latente dim 0
            coords[k, 1] = ys[i]   # latente dim 1
            k += 1

    z = torch.from_numpy(coords).to(device)
    with torch.no_grad():
        waves = model.decode(z).cpu().numpy()               # (256, 1024)

    grid = waves.reshape(GRID, GRID, -1).astype(np.float32) # (16, 16, 1024)
    print(f"Grid horneado: {grid.shape}  "
          f"min={grid.min():.3f} max={grid.max():.3f}")
    return grid, xs, ys


# --------------------------------------------------------------------------- #
# Exportacion
# --------------------------------------------------------------------------- #
def save_npy(grid, bounds):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    npy_path = os.path.join(OUTPUT_DIR, "grid.npy")
    np.save(npy_path, grid)
    print(f"Guardado: {npy_path}")

    x_min, x_max, y_min, y_max = bounds
    meta_path = os.path.join(OUTPUT_DIR, "grid_meta.npz")
    np.savez(meta_path,
             grid=np.int32(GRID),
             table_len=np.int32(grid.shape[-1]),
             x_min=np.float32(x_min), x_max=np.float32(x_max),
             y_min=np.float32(y_min), y_max=np.float32(y_max))
    print(f"Guardado: {meta_path}")


def to_q15(grid):
    """Convierte [-1, 1] float -> int16 Q15 con redondeo y clip de seguridad.
    1.0 -> 32767, -1.0 -> -32768. El tanh ya acota, el clip es por si acaso."""
    q = np.round(grid * 32767.0)
    q = np.clip(q, -32768, 32767)
    return q.astype(np.int16)


def save_header(grid, bounds):
    """Escribe ml/exports/grid.h: banco Q15 + dimensiones + limites del latente.

    Layout del array para el S3: GRID_TABLES[GRID][GRID][TABLE_LEN], fila-mayor,
    indexado [i][j] con i=fila(eje Y), j=columna(eje X), igual que en bake()."""
    x_min, x_max, y_min, y_max = bounds
    table_len = grid.shape[-1]
    q = to_q15(grid)                                        # (16,16,1024) int16

    h_path = os.path.join(OUTPUT_DIR, "grid.h")
    with open(h_path, "w") as f:
        f.write("// grid.h - GENERADO por 4_bake_grid.py. NO editar a mano.\n")
        f.write("// Banco de wavetables 16x16 decodificadas del VAE (Q15 int16).\n")
        f.write("// Indexado [fila i = eje Y][columna j = eje X][muestra].\n")
        f.write("// Limites del latente para mapear (x,y) tactil -> coordenada.\n\n")
        f.write("#ifndef GRID_H\n#define GRID_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write(f"#define GRID_SIZE   {GRID}\n")
        f.write(f"#define TABLE_LEN   {table_len}\n\n")
        # Limites del latente como float (el S3 los usa para el mapeo lineal).
        f.write(f"#define LATENT_X_MIN  {x_min:.6f}f\n")
        f.write(f"#define LATENT_X_MAX  {x_max:.6f}f\n")
        f.write(f"#define LATENT_Y_MIN  {y_min:.6f}f\n")
        f.write(f"#define LATENT_Y_MAX  {y_max:.6f}f\n\n")
        # El banco. 'const' para que el linker lo coloque en flash, no en RAM.
        f.write("const int16_t GRID_TABLES"
                f"[GRID_SIZE][GRID_SIZE][TABLE_LEN] = {{\n")
        for i in range(GRID):
            f.write("  { // fila i=%d (eje Y)\n" % i)
            for j in range(GRID):
                vals = ",".join(str(int(v)) for v in q[i, j])
                f.write("    {" + vals + "},\n")
            f.write("  },\n")
        f.write("};\n\n")
        f.write("#endif // GRID_H\n")

    size_kb = q.nbytes / 1024.0
    print(f"Guardado: {h_path}  ({size_kb:.0f} KB en flash, Q15)")


# --------------------------------------------------------------------------- #
# Vista previa (control de calidad visual)
# --------------------------------------------------------------------------- #
def save_preview(grid, path):
    """Mosaico GRID x GRID de las ondas. Permite ver de un vistazo que el
    morphing es continuo: ondas vecinas deben parecerse, sin saltos bruscos."""
    fig, axes = plt.subplots(GRID, GRID, figsize=(GRID, GRID))
    for i in range(GRID):
        for j in range(GRID):
            ax = axes[i, j]
            ax.plot(grid[i, j], linewidth=0.5)
            ax.set_ylim(-1.1, 1.1)
            ax.axis("off")
    fig.suptitle("Grid 16x16 de wavetables (eje Y=filas, eje X=columnas)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print(f"Guardado: {path}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo: {device}")

    model = load_model(device)

    x_min, x_max, y_min, y_max, _mu = latent_bounds(model, device)
    bounds = (x_min, x_max, y_min, y_max)

    grid, _xs, _ys = bake(model, bounds, device)

    save_npy(grid, bounds)
    save_header(grid, bounds)
    save_preview(grid, os.path.join(OUTPUT_DIR, "grid_preview.png"))

    print("\nSesion 3 (bake) completada: grid.npy, grid.h y preview generados.")
    print("Siguiente: demo de PC (raton -> interp bilineal -> sounddevice).")


if __name__ == "__main__":
    main()
