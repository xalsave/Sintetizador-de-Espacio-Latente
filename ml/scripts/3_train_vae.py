"""
3_train_vae.py
Entrena el Variational Autoencoder (VAE) que aprende un espacio latente 2D de
wavetables a partir del dataset AKWF procesado en la sesion 1.

Idea
----
El encoder comprime cada onda de 1024 muestras a una coordenada (x, y) en un
espacio latente 2D. El decoder reconstruye la onda desde esa coordenada. Como es
un VAE, el latente queda regularizado (continuo y suave): puntos cercanos en
(x, y) producen ondas parecidas, que es justo lo que necesita el control tactil.

Arquitectura (segun el plan, parametros irrevocables del DISENO.md)
-------------------------------------------------------------------
  encoder:  1024 -> 512 -> 128 -> (mu_2d, logvar_2d)
  decoder:  2 -> 128 -> 512 -> 1024
  latente:  2D
  loss:     MSE(reconstruccion) + beta * KL,  beta-VAE con beta ~ 0.001

Salidas (en OUTPUT_DIR = ml/exports)
------------------------------------
  vae.pt                -> pesos del modelo entrenado (state_dict + meta)
  latent_scatter.png    -> scatter del latente coloreado por familia AKWF
  reconstructions.png   -> original vs reconstruida (varias ondas)
  loss_curve.png        -> curvas de perdida (total, recon, KL) por epoca

Uso
---
  python 3_train_vae.py
Ajusta los hiperparametros en la seccion "Configuracion". Si hay GPU disponible
(CUDA), se usa automaticamente; si no, corre en CPU (mas lento pero funciona).
Para Colab: sube akwf_processed.npy y akwf_families.npy y ajusta DATASET_DIR.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset, random_split


# --------------------------------------------------------------------------- #
# Configuracion
# --------------------------------------------------------------------------- #
# Rutas derivadas de la ubicacion del script (igual que en la sesion 1):
#   entrada: ml/dataset/akwf_processed.npy, akwf_families.npy
#   salida:  ml/exports/
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "dataset"))
OUTPUT_DIR  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "exports"))

PROCESSED_PATH = os.path.join(DATASET_DIR, "akwf_processed.npy")
FAMILIES_PATH  = os.path.join(DATASET_DIR, "akwf_families.npy")

# Hiperparametros del modelo (parametros irrevocables: NO cambiar dimensiones)
INPUT_DIM   = 1024          # muestras por onda
LATENT_DIM  = 2             # espacio latente 2D para control tactil
HIDDEN      = (512, 128)    # capas ocultas encoder; decoder es el espejo

# Hiperparametros de entrenamiento (estos SI se pueden tocar)
EPOCHS      = 300
BATCH_SIZE  = 64
LR          = 1e-3
BETA        = 1e-3          # peso de la KL (beta-VAE). Empezar bajo (0.001).
BETA_WARMUP = 50            # epocas de rampa lineal de beta (0 -> BETA). 0 = sin rampa.
VAL_FRACT   = 0.1           # fraccion del dataset para validacion
SEED        = 42

# Reproducibilidad
torch.manual_seed(SEED)
np.random.seed(SEED)


# --------------------------------------------------------------------------- #
# Modelo
# --------------------------------------------------------------------------- #
class VAE(nn.Module):
    """VAE totalmente conectado para wavetables de un ciclo.

    El encoder produce mu y logvar del latente 2D. El truco de
    reparametrizacion (mu + sigma * eps) permite retropropagar a traves del
    muestreo. El decoder reconstruye con tanh para acotar la salida en [-1, 1],
    coherente con la normalizacion por pico del dataset.
    """

    def __init__(self, input_dim=INPUT_DIM, latent_dim=LATENT_DIM, hidden=HIDDEN):
        super().__init__()
        h1, h2 = hidden

        # Encoder: input_dim -> h1 -> h2 -> (mu, logvar)
        self.enc_fc1 = nn.Linear(input_dim, h1)
        self.enc_fc2 = nn.Linear(h1, h2)
        self.fc_mu     = nn.Linear(h2, latent_dim)
        self.fc_logvar = nn.Linear(h2, latent_dim)

        # Decoder: latent_dim -> h2 -> h1 -> input_dim (simetrico)
        self.dec_fc1 = nn.Linear(latent_dim, h2)
        self.dec_fc2 = nn.Linear(h2, h1)
        self.dec_out = nn.Linear(h1, input_dim)

    def encode(self, x):
        h = F.relu(self.enc_fc1(x))
        h = F.relu(self.enc_fc2(h))
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        # En evaluacion devolvemos mu directamente (latente determinista).
        if not self.training:
            return mu
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        h = F.relu(self.dec_fc1(z))
        h = F.relu(self.dec_fc2(h))
        return torch.tanh(self.dec_out(h))      # salida en [-1, 1]

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar


def vae_loss(recon, x, mu, logvar, beta):
    """MSE de reconstruccion + beta * KL.

    - recon_loss: error cuadratico medio por muestra (promediado por lote).
    - kl: divergencia KL entre N(mu, sigma) y N(0, I), forma cerrada estandar.
    Devuelve (total, recon, kl) para poder graficar cada termino por separado.
    """
    recon_loss = F.mse_loss(recon, x, reduction="mean")
    # KL por elemento del lote, luego media. 0.5 * sum(1 + logvar - mu^2 - e^logvar)
    kl = -0.5 * torch.mean(torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=1))
    total = recon_loss + beta * kl
    return total, recon_loss, kl


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #
def load_data():
    """Carga el dataset procesado y las familias. Devuelve tensores y etiquetas."""
    if not os.path.isfile(PROCESSED_PATH):
        raise SystemExit(
            f"No se encuentra {PROCESSED_PATH}. Ejecuta antes 2_build_dataset.py."
        )
    waves = np.load(PROCESSED_PATH).astype(np.float32)   # (N, 1024)
    if os.path.isfile(FAMILIES_PATH):
        families = np.load(FAMILIES_PATH, allow_pickle=True)
    else:
        families = np.array(["?"] * len(waves))

    print(f"Dataset: {waves.shape}  dtype={waves.dtype}")
    print(f"Familias distintas: {len(set(families.tolist()))}")

    x = torch.from_numpy(waves)
    return x, families


# --------------------------------------------------------------------------- #
# Entrenamiento
# --------------------------------------------------------------------------- #
def train(model, train_loader, val_loader, device):
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    hist = {"total": [], "recon": [], "kl": [], "val_recon": []}

    for epoch in range(1, EPOCHS + 1):
        # Rampa lineal de beta para evitar colapso posterior (KL anneal).
        if BETA_WARMUP > 0:
            beta = BETA * min(1.0, epoch / BETA_WARMUP)
        else:
            beta = BETA

        model.train()
        ep_total = ep_recon = ep_kl = 0.0
        for (batch,) in train_loader:
            batch = batch.to(device)
            opt.zero_grad()
            recon, mu, logvar = model(batch)
            total, recon_loss, kl = vae_loss(recon, batch, mu, logvar, beta)
            total.backward()
            opt.step()
            ep_total += total.item() * batch.size(0)
            ep_recon += recon_loss.item() * batch.size(0)
            ep_kl    += kl.item() * batch.size(0)

        n_train = len(train_loader.dataset)
        ep_total /= n_train; ep_recon /= n_train; ep_kl /= n_train

        # Validacion: solo reconstruccion (mu determinista en eval).
        model.eval()
        val_recon = 0.0
        with torch.no_grad():
            for (batch,) in val_loader:
                batch = batch.to(device)
                recon, mu, logvar = model(batch)
                val_recon += F.mse_loss(recon, batch, reduction="mean").item() * batch.size(0)
        val_recon /= len(val_loader.dataset)

        hist["total"].append(ep_total)
        hist["recon"].append(ep_recon)
        hist["kl"].append(ep_kl)
        hist["val_recon"].append(val_recon)

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoca {epoch:3d}/{EPOCHS} | beta={beta:.4f} | "
                  f"total={ep_total:.6f} recon={ep_recon:.6f} kl={ep_kl:.4f} | "
                  f"val_recon={val_recon:.6f}")

    return hist


# --------------------------------------------------------------------------- #
# Visualizaciones
# --------------------------------------------------------------------------- #
def plot_loss(hist, path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(hist["recon"], label="recon (train)")
    ax1.plot(hist["val_recon"], label="recon (val)", linestyle="--")
    ax1.set_title("Perdida de reconstruccion (MSE)")
    ax1.set_xlabel("Epoca"); ax1.set_ylabel("MSE"); ax1.legend(); ax1.grid(alpha=0.3)
    ax2.plot(hist["kl"], color="tab:orange")
    ax2.set_title("Divergencia KL")
    ax2.set_xlabel("Epoca"); ax2.set_ylabel("KL"); ax2.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    print(f"Guardado: {path}")


def plot_latent_scatter(model, x, families, device, path, max_families=12):
    """Scatter del latente (mu) coloreado por familia AKWF.

    Solo se etiquetan las familias mas numerosas para que la leyenda sea legible;
    el resto se dibuja en gris claro de fondo.
    """
    model.eval()
    with torch.no_grad():
        mu, _ = model.encode(x.to(device))
    mu = mu.cpu().numpy()

    fams = np.asarray(families)
    uniq, counts = np.unique(fams, return_counts=True)
    top = uniq[np.argsort(counts)[::-1][:max_families]]

    fig, ax = plt.subplots(figsize=(8, 7))
    # Fondo: todo lo que no esta en top, gris claro.
    other = ~np.isin(fams, top)
    if other.any():
        ax.scatter(mu[other, 0], mu[other, 1], s=6, c="lightgray",
                   alpha=0.4, label="otras")
    cmap = plt.colormaps["tab20"].resampled(len(top))
    for i, fam in enumerate(top):
        m = fams == fam
        ax.scatter(mu[m, 0], mu[m, 1], s=10, color=cmap(i), alpha=0.8, label=fam)
    ax.set_title("Espacio latente 2D (mu) coloreado por familia AKWF")
    ax.set_xlabel("z[0]"); ax.set_ylabel("z[1]")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize="x-small")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=120, bbox_inches="tight"); plt.close(fig)
    print(f"Guardado: {path}")


def plot_reconstructions(model, x, device, path, n=6):
    """Compara n ondas originales con su reconstruccion."""
    model.eval()
    idx = np.random.choice(len(x), size=n, replace=False)
    sample = x[idx].to(device)
    with torch.no_grad():
        recon, _, _ = model(sample)
    sample = sample.cpu().numpy(); recon = recon.cpu().numpy()

    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 2.5 * rows))
    axes = np.atleast_1d(axes).ravel()
    for i in range(n):
        ax = axes[i]
        ax.plot(sample[i], label="original", linewidth=1.2)
        ax.plot(recon[i], label="reconstruida", linewidth=1.2, linestyle="--")
        ax.axhline(0, color="black", linewidth=0.4, linestyle=":")
        ax.set_title(f"onda #{idx[i]}", fontsize="small")
        ax.grid(alpha=0.3)
        if i == 0:
            ax.legend(fontsize="x-small")
    for j in range(n, len(axes)):
        axes[j].axis("off")
    fig.suptitle("Original vs reconstruida")
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    print(f"Guardado: {path}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo: {device}")

    x, families = load_data()

    # Split train/val. Guardamos los indices para poder colorear el scatter
    # con TODO el dataset al final (no solo el split de validacion).
    n = len(x)
    n_val = int(n * VAL_FRACT)
    n_train = n - n_val
    full_ds = TensorDataset(x)
    gen = torch.Generator().manual_seed(SEED)
    train_ds, val_ds = random_split(full_ds, [n_train, n_val], generator=gen)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
    print(f"Train: {n_train}  Val: {n_val}")

    model = VAE().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Parametros del modelo: {n_params:,}")

    hist = train(model, train_loader, val_loader, device)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Guardar pesos + metadatos (utiles para la sesion 3, bake del grid).
    ckpt_path = os.path.join(OUTPUT_DIR, "vae.pt")
    torch.save({
        "state_dict": model.state_dict(),
        "input_dim": INPUT_DIM,
        "latent_dim": LATENT_DIM,
        "hidden": HIDDEN,
        "beta": BETA,
        "epochs": EPOCHS,
    }, ckpt_path)
    print(f"Guardado: {ckpt_path}")

    # Visualizaciones de la sesion 2.
    plot_loss(hist, os.path.join(OUTPUT_DIR, "loss_curve.png"))
    plot_latent_scatter(model, x, families, device,
                        os.path.join(OUTPUT_DIR, "latent_scatter.png"))
    plot_reconstructions(model, x, device,
                         os.path.join(OUTPUT_DIR, "reconstructions.png"))

    print("\nSesion 2 completada: VAE entrenado y figuras generadas.")


if __name__ == "__main__":
    main()
