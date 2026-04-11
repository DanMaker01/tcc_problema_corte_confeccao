import pandas as pd
import numpy as np
import re
from pathlib import Path

# =========================================================
# CONFIGURAÇÃO
# =========================================================
CSV_PATH = "evolucao_larga.csv"
SEP = ","
print("\n=== Análise: Gerações em que a Média Passa por Inteiros ===\n")

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
# 4. ESTATÍSTICAS POR GERAÇÃO
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
# 5. ANÁLISE DE PASSAGEM POR NÚMEROS INTEIROS
# =========================================================
print("\n" + "="*60)
print("ANÁLISE: Gerações em que a Média Passa por Inteiros")
print("="*60)

def analisar_passagem_inteiros(series_media, series_geracao):
    """Analisa quando a média passa por valores inteiros."""
    
    passagens = []
    direcoes = []
    gerações = []
    valores_inteiros = []
    
    # Para cada par de gerações consecutivas
    for i in range(len(series_media) - 1):
        media_atual = series_media.iloc[i]
        media_proxima = series_media.iloc[i + 1]
        geracao_atual = series_geracao.iloc[i]
        
        # Encontrar todos os inteiros entre as duas médias
        menor = min(media_atual, media_proxima)
        maior = max(media_atual, media_proxima)
        
        # Encontrar inteiros no intervalo
        inteiro_inicio = int(np.floor(menor))
        inteiro_fim = int(np.ceil(maior))
        
        for inteiro in range(inteiro_inicio, inteiro_fim + 1):
            # Verificar se o inteiro está entre as duas médias
            if menor < inteiro < maior or (inteiro == menor and inteiro < media_proxima) or (inteiro == maior and inteiro > media_atual):
                # Determinar direção
                if media_proxima > media_atual:
                    direcao = "CRESCENTE"
                elif media_proxima < media_atual:
                    direcao = "DECRESCENTE"
                else:
                    direcao = "ESTÁVEL"
                
                passagens.append(inteiro)
                direcoes.append(direcao)
                gerações.append(geracao_atual)
                valores_inteiros.append(inteiro)
    
    return pd.DataFrame({
        'Geracao': gerações,
        'Inteiro': valores_inteiros,
        'Direcao': direcoes,
        'Media_Anterior': series_media.iloc[gerações].values if gerações else [],
        'Media_Seguinte': series_media.iloc[np.array(gerações) + 1].values if gerações else []
    })

# Executar análise
df_passagens = analisar_passagem_inteiros(stats['media'], stats['Geracao'])

# =========================================================
# 5.1 DETECÇÃO DE PASSAGENS EXATAS POR INTEIROS
# =========================================================
print("\n[5.1] Detecção de passagens exatas por inteiros:")

# Limite para considerar "próximo de um inteiro"
LIMITE_PROXIMIDADE = 0.001

# Encontrar gerações onde a média está muito próxima de um inteiro
proximidades_inteiros = []
for idx, row in stats.iterrows():
    media = row['media']
    inteiro_proximo = round(media)
    distancia = abs(media - inteiro_proximo)
    
    if distancia < LIMITE_PROXIMIDADE:
        proximidades_inteiros.append({
            'Geracao': int(row['Geracao']),
            'Media': media,
            'Inteiro_Proximo': inteiro_proximo,
            'Distancia': distancia,
            'Status': 'MUITO PRÓXIMO'
        })
    elif distancia < 0.01:
        proximidades_inteiros.append({
            'Geracao': int(row['Geracao']),
            'Media': media,
            'Inteiro_Proximo': inteiro_proximo,
            'Distancia': distancia,
            'Status': 'PRÓXIMO'
        })

df_proximidades = pd.DataFrame(proximidades_inteiros)

# =========================================================
# 5.2 ANÁLISE DETALHADA
# =========================================================
if not df_passagens.empty:
    print(f"\n[5.2] Foram detectadas {len(df_passagens)} passagens por inteiros:")
    
    # Agrupar por inteiro
    inteiros_unicos = df_passagens['Inteiro'].unique()
    inteiros_unicos.sort()
    
    for inteiro in inteiros_unicos:
        passagens_inteiro = df_passagens[df_passagens['Inteiro'] == inteiro]
        primeira_passagem = passagens_inteiro['Geracao'].min()
        ultima_passagem = passagens_inteiro['Geracao'].max()
        total_passagens = len(passagens_inteiro)
        
        # Contar direções
        crescentes = (passagens_inteiro['Direcao'] == 'CRESCENTE').sum()
        decrescentes = (passagens_inteiro['Direcao'] == 'DECRESCENTE').sum()
        
        print(f"\n   Inteiro {inteiro}:")
        print(f"     • Total de passagens: {total_passagens}")
        print(f"     • Primeira passagem: geração {primeira_passagem}")
        print(f"     • Última passagem: geração {ultima_passagem}")
        print(f"     • Passagens crescentes: {crescentes}")
        print(f"     • Passagens decrescentes: {decrescentes}")
        
        # Mostrar primeiras passagens
        primeiras_3 = passagens_inteiro.head(3)
        for _, passagem in primeiras_3.iterrows():
            print(f"     - Geração {passagem['Geracao']}: {passagem['Direcao']} "
                  f"({passagem['Media_Anterior']:.3f} → {passagem['Media_Seguinte']:.3f})")
        
        if total_passagens > 3:
            print(f"     ... e mais {total_passagens - 3} passagens")
else:
    print("\n[5.2] Nenhuma passagem por inteiros detectada.")

# =========================================================
# 5.3 ANÁLISE DE PROXIMIDADE
# =========================================================
if not df_proximidades.empty:
    print(f"\n[5.3] Análise de proximidade com inteiros:")
    
    # Separar por status
    muito_proximos = df_proximidades[df_proximidades['Status'] == 'MUITO PRÓXIMO']
    proximos = df_proximidades[df_proximidades['Status'] == 'PRÓXIMO']
    
    if not muito_proximos.empty:
        print(f"\n   Gerações MUITO PRÓXIMAS de inteiros (distância < {LIMITE_PROXIMIDADE}):")
        for _, row in muito_proximos.iterrows():
            print(f"     • Geração {row['Geracao']}: média = {row['Media']:.6f}, "
                  f"inteiro = {row['Inteiro_Proximo']}, distância = {row['Distancia']:.6f}")
    
    if not proximos.empty:
        print(f"\n   Gerações PRÓXIMAS de inteiros (distância < 0.01):")
        for _, row in proximos.head(5).iterrows():  # Mostrar apenas as 5 primeiras
            print(f"     • Geração {row['Geracao']}: média = {row['Media']:.6f}, "
                  f"inteiro = {row['Inteiro_Proximo']}, distância = {row['Distancia']:.6f}")
        
        if len(proximos) > 5:
            print(f"     ... e mais {len(proximos) - 5} gerações")
else:
    print(f"\n[5.3] Nenhuma geração próxima de inteiros detectada (limite = {LIMITE_PROXIMIDADE}).")

# =========================================================
# 5.4 ANÁLISE DE TRAJETÓRIA ENTRE INTEIROS
# =========================================================
print(f"\n[5.4] Análise de trajetória entre inteiros:")

# Encontrar mínimo e máximo de inteiros
if not df_passagens.empty:
    inteiro_min = df_passagens['Inteiro'].min()
    inteiro_max = df_passagens['Inteiro'].max()
    
    print(f"   • Faixa de inteiros atravessada: {inteiro_min} a {inteiro_max}")
    
    # Analisar tempo entre passagens por inteiros consecutivos
    tempos_entre_inteiros = []
    
    for inteiro in range(inteiro_min, inteiro_max):
        passagens_inteiro = df_passagens[df_passagens['Inteiro'] == inteiro]
        passagens_proximo = df_passagens[df_passagens['Inteiro'] == inteiro + 1]
        
        if not passagens_inteiro.empty and not passagens_proximo.empty:
            primeira_passagem_atual = passagens_inteiro['Geracao'].min()
            primeira_passagem_proximo = passagens_proximo['Geracao'].min()
            
            if primeira_passagem_proximo > primeira_passagem_atual:
                tempo = primeira_passagem_proximo - primeira_passagem_atual
                tempos_entre_inteiros.append({
                    'De': inteiro,
                    'Para': inteiro + 1,
                    'Tempo_Geracoes': tempo,
                    'Geracao_Inicio': primeira_passagem_atual,
                    'Geracao_Fim': primeira_passagem_proximo
                })
    
    if tempos_entre_inteiros:
        print(f"\n   Tempo entre passagens por inteiros consecutivos:")
        for tempo in tempos_entre_inteiros:
            print(f"     • {tempo['De']} → {tempo['Para']}: {tempo['Tempo_Geracoes']} gerações "
                  f"(gerações {tempo['Geracao_Inicio']} a {tempo['Geracao_Fim']})")
        
        # Estatísticas
        tempos_array = [t['Tempo_Geracoes'] for t in tempos_entre_inteiros]
        print(f"\n   Estatísticas dos tempos:")
        print(f"     • Média: {np.mean(tempos_array):.1f} gerações")
        print(f"     • Mediana: {np.median(tempos_array):.1f} gerações")
        print(f"     • Mínimo: {np.min(tempos_array)} gerações")
        print(f"     • Máximo: {np.max(tempos_array)} gerações")
        print(f"     • Desvio padrão: {np.std(tempos_array):.1f} gerações")

# =========================================================
# 6. SALVAR RESULTADOS
# =========================================================
print("\n[6] Salvando resultados da análise de passagem por inteiros...")

out_dir = Path("analise_inteiros_Q16u")
out_dir.mkdir(exist_ok=True)

# Salvar dados completos
stats.to_csv(out_dir / "estatisticas_completas.csv", index=False)

if not df_passagens.empty:
    df_passagens.to_csv(out_dir / "passagens_por_inteiros.csv", index=False)

if not df_proximidades.empty:
    df_proximidades.to_csv(out_dir / "proximidades_inteiros.csv", index=False)

# Salvar relatório resumido
with open(out_dir / "relatorio_inteiros.txt", "w") as f:
    f.write("RELATÓRIO DE PASSAGEM POR NÚMEROS INTEIROS\n")
    f.write("="*50 + "\n\n")
    
    f.write(f"Total de gerações analisadas: {len(stats)}\n")
    f.write(f"Faixa de gerações: {stats['Geracao'].min()} a {stats['Geracao'].max()}\n")
    f.write(f"Média inicial: {stats['media'].iloc[0]:.6f}\n")
    f.write(f"Média final: {stats['media'].iloc[-1]:.6f}\n\n")
    
    if not df_passagens.empty:
        f.write(f"PASSAGENS POR INTEIROS: {len(df_passagens)}\n")
        inteiros_unicos = df_passagens['Inteiro'].unique()
        inteiros_unicos.sort()
        
        for inteiro in inteiros_unicos:
            passagens_inteiro = df_passagens[df_passagens['Inteiro'] == inteiro]
            f.write(f"\nInteiro {inteiro}:\n")
            f.write(f"  • Total de passagens: {len(passagens_inteiro)}\n")
            f.write(f"  • Primeira passagem: geração {passagens_inteiro['Geracao'].min()}\n")
            f.write(f"  • Última passagem: geração {passagens_inteiro['Geracao'].max()}\n")
            
            # Exemplo de passagens
            for _, row in passagens_inteiro.head(2).iterrows():
                f.write(f"  • Geração {row['Geracao']}: {row['Direcao']} "
                       f"({row['Media_Anterior']:.3f} → {row['Media_Seguinte']:.3f})\n")
    else:
        f.write("Nenhuma passagem por inteiros detectada.\n")
    
    if not df_proximidades.empty:
        f.write(f"\nPROXIMIDADES COM INTEIROS: {len(df_proximidades)}\n")
        f.write(f"  • Muito próximos (<{LIMITE_PROXIMIDADE}): {len(df_proximidades[df_proximidades['Status']=='MUITO PRÓXIMO'])}\n")
        f.write(f"  • Próximos (<0.01): {len(df_proximidades[df_proximidades['Status']=='PRÓXIMO'])}\n")
    
    f.write(f"\nINTEIROS ENCONTRADOS NA TRAJETÓRIA:\n")
    media_inicial = stats['media'].iloc[0]
    media_final = stats['media'].iloc[-1]
    inteiro_inicial = int(np.floor(min(media_inicial, media_final)))
    inteiro_final = int(np.ceil(max(media_inicial, media_final)))
    
    for inteiro in range(inteiro_inicial, inteiro_final + 1):
        if inteiro == round(media_inicial):
            status_inicial = " (PRÓXIMO DO INÍCIO)"
        elif inteiro == round(media_final):
            status_final = " (PRÓXIMO DO FIM)"
        else:
            status_final = ""
        
        f.write(f"  • {inteiro}{status_final if 'status_final' in locals() else ''}\n")

print("    Arquivos salvos em:", out_dir.resolve())

# =========================================================
# 7. RESUMO EXECUTIVO
# =========================================================
print("\n" + "="*60)
print("RESUMO EXECUTIVO - PASSAGEM POR INTEIROS")
print("="*60)

print(f"\n1. TRAJETÓRIA DA MÉDIA:")
print(f"   • Início: {stats['media'].iloc[0]:.6f}")
print(f"   • Fim: {stats['media'].iloc[-1]:.6f}")
print(f"   • Inteiro mais próximo do início: {round(stats['media'].iloc[0])}")
print(f"   • Inteiro mais próximo do fim: {round(stats['media'].iloc[-1])}")

print(f"\n2. PASSAGENS DETECTADAS:")
if not df_passagens.empty:
    print(f"   • Total de passagens: {len(df_passagens)}")
    print(f"   • Inteiros atravessados: {len(df_passagens['Inteiro'].unique())}")
    print(f"   • Faixa de inteiros: {df_passagens['Inteiro'].min()} a {df_passagens['Inteiro'].max()}")
else:
    print(f"   • Nenhuma passagem completa por inteiros detectada")

print(f"\n3. PROXIMIDADES:")
if not df_proximidades.empty:
    muito_prox = len(df_proximidades[df_proximidades['Status'] == 'MUITO PRÓXIMO'])
    prox = len(df_proximidades[df_proximidades['Status'] == 'PRÓXIMO'])
    print(f"   • Muito próximas de inteiros: {muito_prox} gerações")
    print(f"   • Próximas de inteiros: {prox} gerações")
    
    if muito_prox > 0:
        ultima_prox = df_proximidades[df_proximidades['Status'] == 'MUITO PRÓXIMO'].iloc[-1]
        print(f"   • Última proximidade: geração {ultima_prox['Geracao']} "
              f"(média = {ultima_prox['Media']:.6f}, inteiro = {ultima_prox['Inteiro_Proximo']})")
else:
    print(f"   • Nenhuma proximidade significativa detectada")

print(f"\n4. ANÁLISE COMPORTAMENTAL:")
if not df_passagens.empty:
    # Contar mudanças de direção
    mudancas_direcao = 0
    for i in range(1, len(df_passagens)):
        if df_passagens.iloc[i]['Direcao'] != df_passagens.iloc[i-1]['Direcao']:
            mudancas_direcao += 1
    
    print(f"   • Mudanças de direção: {mudancas_direcao}")
    print(f"   • Oscilações entre inteiros: {mudancas_direcao // 2 if mudancas_direcao > 1 else 0}")

print("\n=== Análise de passagem por inteiros concluída ===\n")

# =========================================================
# 8. VISUALIZAÇÃO (OPCIONAL - para análise mais detalhada)
# =========================================================
print("[8] Gerando visualização da trajetória em relação aos inteiros...")

try:
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(12, 6))
    
    # Plotar média
    plt.plot(stats['Geracao'], stats['media'], 'b-', linewidth=2, label='Média', alpha=0.7)
    
    # Plotar bandas de inteiros
    y_min, y_max = stats['media'].min(), stats['media'].max()
    inteiro_min_plot = int(np.floor(y_min))
    inteiro_max_plot = int(np.ceil(y_max))
    
    for inteiro in range(inteiro_min_plot, inteiro_max_plot + 1):
        plt.axhline(y=inteiro, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
        plt.text(stats['Geracao'].max() + 1, inteiro, f'{inteiro}', 
                verticalalignment='center', color='gray', alpha=0.7)
    
    # Destacar passagens por inteiros
    if not df_passagens.empty:
        for _, row in df_passagens.iterrows():
            plt.axvline(x=row['Geracao'], color='red', linestyle=':', alpha=0.5, linewidth=0.5)
    
    # Destacar proximidades
    if not df_proximidades.empty:
        for _, row in df_proximidades[df_proximidades['Status'] == 'MUITO PRÓXIMO'].iterrows():
            plt.plot(row['Geracao'], row['Media'], 'ro', markersize=4, alpha=0.7)
    
    plt.xlabel('Geração')
    plt.ylabel('Média')
    plt.title('Trajetória da Média em Relação aos Números Inteiros')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Salvar figura
    plt.savefig(out_dir / "trajetoria_inteiros.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    print("    Gráfico salvo como: trajetoria_inteiros.png")
    
except ImportError:
    print("    AVISO: matplotlib não instalado. Pule esta seção ou instale com: pip install matplotlib")
except Exception as e:
    print(f"    AVISO: Erro ao gerar gráfico: {e}")