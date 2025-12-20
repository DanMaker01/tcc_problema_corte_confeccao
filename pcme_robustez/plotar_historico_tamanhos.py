# =============================================================================================================
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import os
from matplotlib.lines import Line2D

# =========================
# Configuração
# =========================
MAX_GENS = [100, 1000, 10000, 100000]
OUT_DIR = "figuras_evolucao"
os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# Funções
# =========================
def extract_q(name: str) -> int:
    m = re.search(r"Q_(\d+)", name)
    return int(m.group(1)) if m else None

def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df["Q"] = df["Arquivo"].apply(extract_q)
    return df

def filter_generations(df: pd.DataFrame, max_gen: int):
    gen_cols = [c for c in df.columns if c.startswith("Gen_")]
    gens = np.array([int(c.split("_")[1]) for c in gen_cols])
    mask = gens <= max_gen
    gen_cols = np.array(gen_cols)[mask].tolist()
    gens = gens[mask]
    return gen_cols, gens

def plot_Q_multiple_generations(df: pd.DataFrame, Q: int, max_gens: list, out_dir: str):
    dfQ = df[df["Q"] == Q]
    n = len(max_gens)
    fig, axes = plt.subplots(1, n, figsize=(6*n,5), sharey=True)

    if n == 1:
        axes = [axes]

    for ax, g in zip(axes, max_gens):
        gen_cols, gens = filter_generations(dfQ, g)
        data = dfQ[gen_cols].to_numpy()

        mean  = np.mean(data, axis=0)
        std   = np.std(data, axis=0)
        best  = np.min(data, axis=0)
        worst = np.max(data, axis=0)

        # Área melhor–pior
        ax.fill_between(gens, best, worst, alpha=0.1)
        # Área média ± DP
        ax.fill_between(gens, mean - std, mean + std, alpha=0.3, color="orange")
        # Curvas individuais
        ax.plot(gens, mean, linewidth=2, color="blue")
        ax.plot(gens, best, linewidth=1.5, linestyle="--", color="green")
        ax.plot(gens, worst, linewidth=1.5, linestyle="--", color="red")

        ax.set_title(f"{g} Gerações")
        ax.set_xlabel("Geração")
        ax.set_ylabel("Bins")

    # Legenda única incluindo a faixa Média ± DP
    custom_lines = [
        Line2D([0], [0], color='blue', lw=2, label='Média'),
        Line2D([0], [0], color='orange', lw=10, alpha=0.3, label='Média ± DP'),
        Line2D([0], [0], color='green', lw=1.5, linestyle='--', label='Melhor seed'),
        Line2D([0], [0], color='red', lw=1.5, linestyle='--', label='Pior seed')
    ]
    fig.legend(handles=custom_lines, loc='center left', bbox_to_anchor=(0.90, 0.5), frameon=False)

    # Ajuste de layout para título e espaçamento
    # plt.suptitle(f"Evolução para Q = {Q}", fontsize=16, y=1.03)
    plt.subplots_adjust(wspace=0.3, right=0.88, top=0.85)  # Ajuste fino para legenda e título

    filename = f"evolucao_Q_{Q}_comparativo.png"
    plt.savefig(os.path.join(out_dir, filename), dpi=300, bbox_inches="tight")
    # plt.show()
    plt.close()

# =========================
# Execução
# =========================
if __name__ == "__main__":
    df = load_data("evolucao_larga_1kk.csv")
    for Q in sorted(df["Q"].unique()):
        plot_Q_multiple_generations(df, Q, MAX_GENS, OUT_DIR)

# =============================================================================================================