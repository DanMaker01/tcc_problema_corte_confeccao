import re
import pandas as pd

# Regex para capturar cada parte - ajustadas para os caracteres especiais
re_seed = re.compile(r"seed_(\d+)_marques")
re_gen = re.compile(r"Gen\s+\d+:\s+Best\s*=\s*([\d.]+)")
re_seq = re.compile(r"Melhor sequ[^:]*:\s*\[(.*?)\]")  # Mais flexível para caracteres especiais
re_fit = re.compile(r"Fitness:\s*([\d.]+)")

resultados = []
current = None

with open("resultado.txt", "r", encoding="utf-8") as f:
    for linha in f:
        
        # Detecta início de um novo bloco (nova seed)
        m_seed = re_seed.search(linha)
        if m_seed:
            # Se já tinha um bloco anterior, salva
            if current:
                resultados.append(current)
            current = {
                "seed": int(m_seed.group(1)),
                "evolucao_geracoes": []
            }
        
        # Coleta o BEST de cada geração
        if current:
            m_gen = re_gen.search(linha)
            if m_gen:
                current["evolucao_geracoes"].append(float(m_gen.group(1)))

            # Sequência final
            m_seq = re_seq.search(linha)
            if m_seq:
                seq_str = m_seq.group(1)
                current["sequencia"] = seq_str

            # Fitness final = largura da faixa
            m_fit = re_fit.search(linha)
            if m_fit:
                current["largura"] = float(m_fit.group(1))

# Salva o último bloco
if current:
    resultados.append(current)

# DEBUG: Mostra o que foi coletado
print("=== DEBUG - DADOS COLETADOS ===")
for i, resultado in enumerate(resultados):
    print(f"Resultado {i}: {resultado}")

# Converte para DataFrame
if resultados:
    df = pd.DataFrame(resultados)
    
    print(f"\n=== TABELA DE RESULTADOS ===")
    print(f"Total de seeds: {len(df)}")
    
    # Reorganiza as colunas que existem
    colunas_finais = []
    for coluna in ['seed', 'largura', 'sequencia', 'evolucao_geracoes']:
        if coluna in df.columns:
            colunas_finais.append(coluna)
    
    if colunas_finais:
        df = df[colunas_finais]
        
        # Configura pandas para mostrar todas as colunas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        
        print(df)
        
        # Estatísticas resumidas
        print(f"\n=== ESTATÍSTICAS ===")
        if 'largura' in df.columns:
            print(f"Largura mínima: {df['largura'].min()}")
            print(f"Largura máxima: {df['largura'].max()}")
            print(f"Largura média: {df['largura'].mean():.2f}")
            
    else:
        print("Nenhuma coluna desejada foi encontrada!")
else:
    print("Nenhum resultado foi coletado!")