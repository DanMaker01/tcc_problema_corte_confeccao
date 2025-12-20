import pandas as pd
import numpy as np
import re
from pathlib import Path

# =========================================================
# CONFIGURAÇÃO
# =========================================================
CSV_PATH = "evolucao_larga.csv"
SEP = ","
LIMIAR_CONVERGENCIA = 0.01
JANELA_ANALISE_CONVERGENCIA = 100  # Janela para análise de convergência

print("\n=== Análise 4: Estado de Convergência ===\n")

# =========================================================
# 1. LEITURA DO CSV
# =========================================================
print("[1] Lendo CSV...")
df = pd.read_csv(CSV_PATH, sep=SEP)
print(f"    Linhas iniciais: {len(df)} | Colunas: {len(df.columns)}")

# =========================================================
# 1.1 FILTRO: Q_16u e seeds 0 a 9
# =========================================================
print("[1.1] Filtrando apenas Q_16u e seeds 0–9...")

df["Arquivo"] = df["Arquivo"].astype(str)

# Filtrar Q = 16u
df = df[df["Arquivo"].str.contains(r"Q_16u")]

# Filtrar seeds 0 a 9 (evita seed_10, seed_11, ...)
df = df[df["Arquivo"].str.contains(r"seed_[0-9](?!\d)", regex=True)]

print(f"    Linhas após filtro: {len(df)}")

if df.empty:
    raise ValueError("Filtro resultou em DataFrame vazio. Verifique o padrão do nome dos arquivos.")

print("\n    Arquivos analisados:")
for a in sorted(df["Arquivo"].unique()):
    print("   ", a)

# =========================================================
# 2. DETECÇÃO DAS COLUNAS DE GERAÇÃO
# =========================================================
gen_cols = [c for c in df.columns if re.fullmatch(r"Gen_\d+", c)]
gen_cols.sort(key=lambda x: int(x.split("_")[1]))

if not gen_cols:
    raise ValueError("Nenhuma coluna Gen_X encontrada no CSV.")

print(f"\n[2] Gerações detectadas: {len(gen_cols)} "
      f"(Gen_0 … Gen_{len(gen_cols)-1})")

# =========================================================
# 3. CONVERSÃO PARA FORMATO LONGO
# =========================================================
print("\n[3] Convertendo para formato longo...")

df_long = df.melt(
    id_vars=[c for c in df.columns if c not in gen_cols],
    value_vars=gen_cols,
    var_name="Geracao",
    value_name="Bins_Geracao"
)

df_long["Geracao"] = (
    df_long["Geracao"]
    .str.replace("Gen_", "", regex=False)
    .astype(int)
)

n_seeds = df_long["Arquivo"].nunique()

print(f"    Seeds detectadas: {n_seeds}")

# =========================================================
# 4. ESTATÍSTICAS POR GERAÇÃO (APENAS O NECESSÁRIO)
# =========================================================
print("\n[4] Calculando estatísticas por geração...")

stats = (
    df_long
    .groupby("Geracao")["Bins_Geracao"]
    .agg(
        media="mean",
        minimo="min",
        maximo="max",
        dp="std",
        amplitude=lambda x: x.max() - x.min()
    )
    .reset_index()
)

# =========================================================
# 5. ANÁLISE DE CONVERGÊNCIA DETALHADA
# =========================================================
print("\n" + "="*60)
print("ANÁLISE 4: Estado de Convergência")
print("="*60)

# Calcular métricas de convergência
stats["velocidade"] = stats["media"].diff().abs()
stats["aceleracao"] = stats["velocidade"].diff()
stats["queda_absoluta"] = stats["media"].diff()
stats["queda_percentual"] = stats["queda_absoluta"] / stats["media"].shift() * 100

# =========================================================
# 5.1 MÉTRICAS DAS ÚLTIMAS GERAÇÕES
# =========================================================
print(f"\n[5.1] Métricas das últimas {JANELA_ANALISE_CONVERGENCIA} gerações:")

if len(stats) >= JANELA_ANALISE_CONVERGENCIA:
    ultimas_geracoes = stats.tail(JANELA_ANALISE_CONVERGENCIA)
    
    convergencia_metrica = {
        "media_inicial": ultimas_geracoes["media"].iloc[0],
        "media_final": ultimas_geracoes["media"].iloc[-1],
        "melhoria_absoluta": ultimas_geracoes["media"].iloc[0] - ultimas_geracoes["media"].iloc[-1],
        "melhoria_percentual": ((ultimas_geracoes["media"].iloc[0] - ultimas_geracoes["media"].iloc[-1]) / 
                               ultimas_geracoes["media"].iloc[0] * 100),
        "velocidade_media": ultimas_geracoes["velocidade"].mean(),
        "velocidade_maxima": ultimas_geracoes["velocidade"].max(),
        "velocidade_minima": ultimas_geracoes["velocidade"].min(),
        "dp_medio": ultimas_geracoes["dp"].mean(),
        "dp_final": ultimas_geracoes["dp"].iloc[-1],
        "amplitude_media": ultimas_geracoes["amplitude"].mean(),
        "amplitude_final": ultimas_geracoes["amplitude"].iloc[-1],
        "quedas_significativas": (ultimas_geracoes["queda_percentual"] < -0.5).sum(),
        "aumentos_significativos": (ultimas_geracoes["queda_percentual"] > 0.5).sum()
    }
    
    print(f"   • Média inicial: {convergencia_metrica['media_inicial']:.6f}")
    print(f"   • Média final: {convergencia_metrica['media_final']:.6f}")
    print(f"   • Melhoria: {convergencia_metrica['melhoria_absoluta']:.6f} "
          f"({convergencia_metrica['melhoria_percentual']:.4f}%)")
    print(f"   • Velocidade média: {convergencia_metrica['velocidade_media']:.8f}")
    print(f"   • Velocidade máxima: {convergencia_metrica['velocidade_maxima']:.8f}")
    print(f"   • DP médio: {convergencia_metrica['dp_medio']:.6f}")
    print(f"   • DP final: {convergencia_metrica['dp_final']:.6f}")
    print(f"   • Amplitude média: {convergencia_metrica['amplitude_media']:.6f}")
    print(f"   • Amplitude final: {convergencia_metrica['amplitude_final']:.6f}")
    print(f"   • Quedas >0.5%: {convergencia_metrica['quedas_significativas']}")
    print(f"   • Aumentos >0.5%: {convergencia_metrica['aumentos_significativos']}")
else:
    print(f"   AVISO: Menos de {JANELA_ANALISE_CONVERGENCIA} gerações disponíveis")

# =========================================================
# 5.2 ANÁLISE DA ÚLTIMA METADE DO PROCESSO
# =========================================================
print(f"\n[5.2] Análise da segunda metade do processo evolutivo:")

segunda_metade = len(stats) // 2
ultimo_quartil = 3 * len(stats) // 4

if len(stats) >= 4:  # Garantir que há dados suficientes
    segunda_metade_stats = stats.iloc[segunda_metade:]
    ultimo_quartil_stats = stats.iloc[ultimo_quartil:]
    
    print(f"   • Gerações da segunda metade: {segunda_metade} a {len(stats)-1}")
    print(f"   • Velocidade média (segunda metade): {segunda_metade_stats['velocidade'].mean():.8f}")
    print(f"   • DP médio (segunda metade): {segunda_metade_stats['dp'].mean():.6f}")
    
    if len(ultimo_quartil_stats) > 0:
        print(f"   • Velocidade média (último quartil): {ultimo_quartil_stats['velocidade'].mean():.8f}")
        print(f"   • DP médio (último quartil): {ultimo_quartil_stats['dp'].mean():.6f}")

# =========================================================
# 5.3 DETECÇÃO DE CONVERGÊNCIA
# =========================================================
print(f"\n[5.3] Detecção de convergência (limiar = {LIMIAR_CONVERGENCIA}):")

# Encontrar períodos de convergência
stats["convergido"] = stats["velocidade"] < LIMIAR_CONVERGENCIA

# Identificar blocos contínuos de convergência
blocos_convergencia = []
bloco_ativo = False
inicio_bloco = None

for idx, row in stats.iterrows():
    if row["convergido"] and not bloco_ativo:
        bloco_ativo = True
        inicio_bloco = int(row["Geracao"])
    elif not row["convergido"] and bloco_ativo:
        bloco_ativo = False
        fim_bloco = int(stats.iloc[idx-1]["Geracao"])
        duracao = fim_bloco - inicio_bloco + 1
        media_bloco = stats.iloc[idx-duracao:idx]["media"].mean()
        blocos_convergencia.append({
            "inicio": inicio_bloco,
            "fim": fim_bloco,
            "duracao": duracao,
            "media": media_bloco
        })

# Último bloco se ainda estiver ativo
if bloco_ativo and inicio_bloco is not None:
    fim_bloco = int(stats.iloc[-1]["Geracao"])
    duracao = fim_bloco - inicio_bloco + 1
    media_bloco = stats.iloc[-duracao:]["media"].mean()
    blocos_convergencia.append({
        "inicio": inicio_bloco,
        "fim": fim_bloco,
        "duracao": duracao,
        "media": media_bloco
    })

if blocos_convergencia:
    print(f"   • Total de períodos de convergência detectados: {len(blocos_convergencia)}")
    
    print(f"\n   Detalhes dos períodos de convergência:")
    for i, bloco in enumerate(blocos_convergencia, 1):
        print(f"   {i}. Gerações {bloco['inicio']}-{bloco['fim']} "
              f"(dura {bloco['duracao']} gerações, média = {bloco['media']:.6f})")
    
    # Análise do maior bloco
    maior_bloco = max(blocos_convergencia, key=lambda x: x["duracao"])
    print(f"\n   • Maior período de convergência:")
    print(f"     - Gerações: {maior_bloco['inicio']} a {maior_bloco['fim']}")
    print(f"     - Duração: {maior_bloco['duracao']} gerações")
    print(f"     - Média do período: {maior_bloco['media']:.6f}")
    
    # Verificar se está atualmente convergido
    if blocos_convergencia[-1]["fim"] == stats.iloc[-1]["Geracao"]:
        print(f"\n   • ESTADO ATUAL: CONVERGIDO (desde geração {blocos_convergencia[-1]['inicio']})")
    else:
        print(f"\n   • ESTADO ATUAL: NÃO CONVERGIDO")
else:
    print(f"   • Nenhum período de convergência detectado (velocidade sempre > {LIMIAR_CONVERGENCIA})")

# =========================================================
# 5.4 ANÁLISE DE TENDÊNCIA
# =========================================================
print(f"\n[5.4] Análise de tendência final:")

# Calcular tendência linear nas últimas 500 gerações (ou todas se menos)
janela_tendencia = min(500, len(stats))
if janela_tendencia >= 10:  # Mínimo para análise de tendência
    ultimas_para_tendencia = stats.tail(janela_tendencia)
    
    # Regressão linear simples
    x = np.arange(len(ultimas_para_tendencia))
    y = ultimas_para_tendencia["media"].values
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]  # Inclinação
    
    print(f"   • Análise de tendência nas últimas {janela_tendencia} gerações:")
    print(f"     - Inclinação (slope): {slope:.10f}")
    
    if abs(slope) < 1e-6:
        tendencia = "ESTÁVEL (sem tendência clara)"
    elif slope < 0:
        tendencia = f"MELHORANDO (decrescente, slope = {slope:.10f})"
    else:
        tendencia = f"PIORANDO (crescente, slope = {slope:.10f})"
    
    print(f"     - Tendência: {tendencia}")
    
    # Calcular R²
    y_pred = np.polyval(coeffs, x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    print(f"     - R² do ajuste: {r_squared:.4f}")
    
    if r_squared > 0.7:
        print(f"     - Tendência bem definida (R² > 0.7)")
    elif r_squared > 0.3:
        print(f"     - Tendência moderada (R² > 0.3)")
    else:
        print(f"     - Tendência fraca (R² ≤ 0.3)")

# =========================================================
# 5.5 DIAGNÓSTICO DO ESTADO ATUAL
# =========================================================
print(f"\n[5.5] Diagnóstico do estado atual:")

# Coletar métricas para diagnóstico
if len(stats) >= 10:
    ultimas_10 = stats.tail(10)
    diagnosticos = []
    
    # Critério 1: Velocidade baixa
    velocidade_media_10 = ultimas_10["velocidade"].mean()
    if velocidade_media_10 < LIMIAR_CONVERGENCIA:
        diagnosticos.append(f"✓ Velocidade baixa ({velocidade_media_10:.8f} < {LIMIAR_CONVERGENCIA})")
    else:
        diagnosticos.append(f"✗ Velocidade alta ({velocidade_media_10:.8f} ≥ {LIMIAR_CONVERGENCIA})")
    
    # Critério 2: DP baixo (população homogênea)
    dp_media_10 = ultimas_10["dp"].mean()
    dp_relativo = dp_media_10 / ultimas_10["media"].mean()
    if dp_relativo < 0.01:  # DP menor que 1% da média
        diagnosticos.append(f"✓ DP muito baixo ({dp_relativo:.4%} da média)")
    elif dp_relativo < 0.05:  # DP menor que 5% da média
        diagnosticos.append(f"✓ DP baixo ({dp_relativo:.4%} da média)")
    else:
        diagnosticos.append(f"✗ DP alto ({dp_relativo:.4%} da média)")
    
    # Critério 3: Sem melhorias significativas
    melhoria_10 = (ultimas_10["media"].iloc[0] - ultimas_10["media"].iloc[-1]) / ultimas_10["media"].iloc[0] * 100
    if abs(melhoria_10) < 0.1:  # Menos de 0.1% de melhoria
        diagnosticos.append(f"✓ Sem melhorias significativas ({melhoria_10:.4f}%)")
    elif melhoria_10 > 0:
        diagnosticos.append(f"✗ Melhoria ativa ({melhoria_10:.4f}%)")
    else:
        diagnosticos.append(f"⚠️  Piorando ({melhoria_10:.4f}%)")
    
    # Critério 4: Amplitude estável
    amplitude_var = ultimas_10["amplitude"].std() / ultimas_10["amplitude"].mean()
    if amplitude_var < 0.1:
        diagnosticos.append(f"✓ Amplitude estável (CV = {amplitude_var:.4f})")
    else:
        diagnosticos.append(f"✗ Amplitude variável (CV = {amplitude_var:.4f})")
    
    # Exibir diagnósticos
    print("   Critérios de convergência (últimas 10 gerações):")
    for diagnostico in diagnosticos:
        print(f"   {diagnostico}")
    
    # Diagnóstico final
    criterios_atendidos = sum(1 for d in diagnosticos if d.startswith("✓"))
    total_criterios = len(diagnosticos)
    
    if criterios_atendidos >= 3:
        estado_final = "CONVERGIDO"
    elif criterios_atendidos >= 2:
        estado_final = "PRÓXIMO DA CONVERGÊNCIA"
    else:
        estado_final = "EM EVOLUÇÃO ATIVA"
    
    print(f"\n   DIAGNÓSTICO FINAL: {estado_final} "
          f"({criterios_atendidos}/{total_criterios} critérios atendidos)")

# =========================================================
# 6. SALVAR RESULTADOS DA ANÁLISE DE CONVERGÊNCIA
# =========================================================
print("\n[6] Salvando resultados da análise de convergência...")

out_dir = Path("analise_convergencia_Q16u")
out_dir.mkdir(exist_ok=True)

# Salvar estatísticas com métricas de convergência
stats.to_csv(out_dir / "estatisticas_convergencia.csv", index=False)

# Salvar blocos de convergência
if blocos_convergencia:
    pd.DataFrame(blocos_convergencia).to_csv(out_dir / "blocos_convergencia.csv", index=False)

# Salvar relatório de diagnóstico
with open(out_dir / "diagnostico_convergencia.txt", "w") as f:
    f.write("DIAGNÓSTICO DE CONVERGÊNCIA\n")
    f.write("="*50 + "\n\n")
    f.write(f"Total de gerações analisadas: {len(stats)}\n")
    f.write(f"Limiar de convergência: {LIMIAR_CONVERGENCIA}\n")
    f.write(f"Janela de análise: {JANELA_ANALISE_CONVERGENCIA} gerações\n\n")
    
    f.write("ESTATÍSTICAS FINAIS:\n")
    f.write(f"  Média inicial: {stats['media'].iloc[0]:.6f}\n")
    f.write(f"  Média final: {stats['media'].iloc[-1]:.6f}\n")
    f.write(f"  Melhoria total: {stats['media'].iloc[0] - stats['media'].iloc[-1]:.6f}\n")
    f.write(f"  DP final: {stats['dp'].iloc[-1]:.6f}\n")
    f.write(f"  Velocidade final: {stats['velocidade'].iloc[-1]:.8f}\n\n")
    
    if 'convergencia_metrica' in locals():
        f.write(f"MÉTRICAS DAS ÚLTIMAS {JANELA_ANALISE_CONVERGENCIA} GERAÇÕES:\n")
        for key, value in convergencia_metrica.items():
            if isinstance(value, float):
                f.write(f"  {key}: {value:.6f}\n")
            else:
                f.write(f"  {key}: {value}\n")
    
    if blocos_convergencia:
        f.write(f"\nPERÍODOS DE CONVERGÊNCIA DETECTADOS: {len(blocos_convergencia)}\n")
        for bloco in blocos_convergencia:
            f.write(f"  • Gerações {bloco['inicio']}-{bloco['fim']} "
                   f"(dura {bloco['duracao']}, média = {bloco['media']:.6f})\n")
    
    if 'estado_final' in locals():
        f.write(f"\nDIAGNÓSTICO FINAL: {estado_final}\n")

print("    Arquivos salvos em:", out_dir.resolve())
print("\n=== Análise de convergência concluída ===\n")

# =========================================================
# 7. RESUMO EXECUTIVO
# =========================================================
print("\n" + "="*60)
print("RESUMO EXECUTIVO DA CONVERGÊNCIA")
print("="*60)

print(f"\n1. EVOLUÇÃO TOTAL:")
print(f"   • Início: {stats['media'].iloc[0]:.6f}")
print(f"   • Fim: {stats['media'].iloc[-1]:.6f}")
print(f"   • Melhoria: {stats['media'].iloc[0] - stats['media'].iloc[-1]:.6f} "
      f"({(stats['media'].iloc[0] - stats['media'].iloc[-1])/stats['media'].iloc[0]*100:.4f}%)")

print(f"\n2. ESTADO ATUAL:")
print(f"   • Média: {stats['media'].iloc[-1]:.6f}")
print(f"   • DP: {stats['dp'].iloc[-1]:.6f}")
print(f"   • Velocidade: {stats['velocidade'].iloc[-1]:.8f}")

print(f"\n3. CONVERGÊNCIA:")
if blocos_convergencia:
    if blocos_convergencia[-1]["fim"] == stats.iloc[-1]["Geracao"]:
        print(f"   • CONVERGIDO há {blocos_convergencia[-1]['duracao']} gerações")
        print(f"   • Desde geração: {blocos_convergencia[-1]['inicio']}")
    else:
        print(f"   • NÃO CONVERGIDO no momento")
        print(f"   • Último período: gerações {blocos_convergencia[-1]['inicio']}-{blocos_convergencia[-1]['fim']}")
else:
    print(f"   • NUNCA CONVERGIU (velocidade sempre > {LIMIAR_CONVERGENCIA})")

print(f"\n4. RECOMENDAÇÃO:")
if 'estado_final' in locals():
    if estado_final == "CONVERGIDO":
        print("   • PARAR execução - processo convergiu")
    elif estado_final == "PRÓXIMO DA CONVERGÊNCIA":
        print("   • CONTINUAR por mais algumas gerações para confirmar convergência")
    else:
        print("   • CONTINUAR - evolução ainda ativa")