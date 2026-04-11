import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import os

# =========================
# Configuração
# =========================
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

def plot_multiple_gens(df: pd.DataFrame, max_gens: list, out_dir: str):
    """Plota simultaneamente 4 gráficos para os diferentes limites de gerações."""
    n = len(max_gens)
    fig, axes = plt.subplots(1, n, figsize=(6*n, 5), sharey=True)

    if n == 1:
        axes = [axes]

    for ax, g in zip(axes, max_gens):
        gen_cols, gens = filter_generations(df, g)

        for Q, dfQ in df.groupby("Q"):
            data = dfQ[gen_cols].to_numpy()
            mean  = np.mean(data, axis=0)
            std   = np.std(data, axis=0)
            best  = np.min(data, axis=0)
            worst = np.max(data, axis=0)

            # Área melhor–pior
            ax.fill_between(gens, best, worst, alpha=0.1)
            # Área média ± DP
            ax.fill_between(gens, mean - std, mean + std, alpha=0.3, label="Média ± DP" if Q==df["Q"].unique()[0] else "")
            
            # Curvas individuais
            ax.plot(gens, mean, linewidth=2, label="Média" if Q==df["Q"].unique()[0] else "", color="blue")
            ax.plot(gens, best, linewidth=1.5, linestyle="--", label="Melhor seed" if Q==df["Q"].unique()[0] else "", color="green")
            ax.plot(gens, worst, linewidth=1.5, linestyle="--", label="Pior seed" if Q==df["Q"].unique()[0] else "", color="red")

        ax.set_title(f"Max Geração = {g}")
        ax.set_xlabel("Geração")
        ax.set_ylabel("Bins")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "evolucao_multiplas_gens.png"), dpi=300, bbox_inches="tight")
    plt.show()

# =========================
# Execução
# =========================
if __name__ == "__main__":
    df = load_data("evolucao_larga.csv")
    max_gens = [100, 1000, 10000, 100000]
    plot_multiple_gens(df, max_gens, OUT_DIR)
