# ------------------------------------------------
# Externos
from shapely.geometry import Point, Polygon
from shapely.prepared import prep
from typing import List, Tuple
import numpy as np
# Internos
import ifp_generator
import nfp_generator
from bl import Bottom_Left
import json
import os

# -------------------------------------
# Cache ISPP
def _cache_filename(modelo, W, L, R, C, seed, gens):
    """nome_modelo_W_L_R_C_seed_gens.json"""
    L_str = f"{L:.2f}".replace('.', '_')
    return f"cache/{modelo}_W{W}_L{L_str}_R{R}_C{C}_seed{seed}_gens{gens}.json"

def _load_cache(modelo, W, L, R, C, seed, gens):
    fname = _cache_filename(modelo, W, L, R, C, seed, gens)
    if not os.path.exists(fname):
        return None
    with open(fname) as f:
        data = json.load(f)
    return data['seq'], data['fitness'], [(t, tuple(p)) for t, p in data['pecas']]

def _save_cache(modelo, W, L, R, C, seed, gens, seq, fitness, pecas):
    os.makedirs("cache", exist_ok=True)
    data = {
        'seq': seq,
        'fitness': fitness,
        'pecas': [(t, list(p)) for t, p in pecas]
    }
    with open(_cache_filename(modelo, W, L, R, C, seed, gens), 'w') as f:
        json.dump(data, f)

# -------------------------------------
# Cache PCME
def _cache_pcme_filename(Q, capacidade_bin, seed, gens):
    """nome_Q1_valor_nome2_Q2_valor_..._sSEED_gGENS.json"""
    partes = []
    for modelo, qtd in sorted(Q.items()):  # sorted para garantir ordem consistente
        partes.append(f"{modelo}_Q{qtd}")
    nome_base = "_".join(partes)
    return f"cache_pcme/{nome_base}_cap{capacidade_bin}_s{seed}_g{gens}.json"

def _load_cache_pcme(Q, capacidade_bin, seed, gens):
    fname = _cache_pcme_filename(Q, capacidade_bin, seed, gens)
    if not os.path.exists(fname):
        return None
    with open(fname) as f:
        data = json.load(f)
    return data['num_bins'], data['desperdicio'], data['seq_corte'], data['hist']

def _save_cache_pcme(Q, capacidade_bin, seed, gens, num_bins, desperdicio, seq_corte, hist):
    os.makedirs("cache_pcme", exist_ok=True)
    data = {
        'num_bins': num_bins,
        'desperdicio': desperdicio,
        'seq_corte': seq_corte,
        'hist': hist
    }
    with open(_cache_pcme_filename(Q, capacidade_bin, seed, gens), 'w') as f:
        json.dump(data, f)
# -------------------------------------
# ------------------------------------------------
DEBUG = True
# --------------------------------------
# BRKGAs
def brkga_ordem(T,q,W,L,R,C,NFP,IFP_D,pop=10,gens=10,her=0.7,mut=0.2,eli=0.2,seed=42):
    
    def _medir_largura_faixa_BL(T,pecas_posicionadas: List[Tuple[int, Tuple[float, float]]]) -> float:
        '''
        Calcula o comprimento L necessário para conter todas as peças posicionadas.
        
        Args:
            pecas_posicionadas: [(t,(x,y)), (t,(x,y)), ...] - lista de tuplas (tipo, posição)
            
        Returns:
            float: Maior coordenada x encontrada (comprimento necessário)
            se não cabe, retorna 9e9
        '''
        try:
            if not pecas_posicionadas or pecas_posicionadas == [] :
                return 999999.0
            
            max_x = 0.0
            
            for tipo, posicao in pecas_posicionadas:
                x_pos, y_pos = posicao
                
                # Verifica se o tipo é válido
                if 0 <= tipo < len(T):
                    # Obtém o polígono do tipo
                    poligono = T[tipo]
                    
                    # Encontra o vértice mais à direita do polígono
                    max_x_poligono = max(x for x, y in poligono)
                    
                    # Calcula a posição mais à direita deste polígono posicionado
                    x_max_atual = x_pos + max_x_poligono
                    
                    # Atualiza o máximo global
                    if x_max_atual > max_x:
                        max_x = x_max_atual
            
            return round(max_x,10) 
            
        except Exception as e:
            print(f"Erro ao medir largura da faixa BL: {e}")
            return 999999


    def _rodar_BL(T,sequencias_resolvidas,seq,W,L,R,C,NFP,IFP_D) -> float:   
        resolvida = sequencias_resolvidas.get(tuple(seq))   #se já foi resolvido antes, adianta tempo
        if resolvida != None:
            largura_ja_existente, pecas_posicionadas = resolvida
            if largura_ja_existente != None:                                   
                return largura_ja_existente,pecas_posicionadas ####### salvar entre sessões?? acho q não.
        else:                
            bl = Bottom_Left(W,L,R,C,seq,NFP,IFP_D,T,debug=False)
            pecas_posicionadas = bl.rodar()           # retorna lista com itens (t,(x,y))
            # visualizar_posicionamento(T,pecas_posicionadas,W,L,str(seq))
            if not pecas_posicionadas:
                print(f"BL retornou lista vazia p/ seq {seq}. Aumente L ou refine a malha.")
            largura_resultado_bl = _medir_largura_faixa_BL(T,pecas_posicionadas)   
            sequencias_resolvidas[tuple(seq)] = (largura_resultado_bl,pecas_posicionadas)    #
            return largura_resultado_bl, pecas_posicionadas


    def _decode(chromosome: np.ndarray) -> List[int]:
        """Decodifica cromossomo em sequência (ordenação pelos alelos)."""
        return np.argsort(chromosome).tolist()

    def _avaliar_pop(T,q,populacao,seq_resolvidas,W,L,R,C,NFP,IFP_D) -> List[Tuple[float, np.ndarray]]:
        """Avalia a população e retorna uma lista ordenada por fitness."""
        evaluated = []
        demanda_sequenciada = []
        for i in range(len(list(q))):
            for _ in range(q[i]):
                demanda_sequenciada.append(i)

        for i,chrom in enumerate(populacao):               # para toda a população
            sequence_indexes = _decode(chrom)
            sequence = [demanda_sequenciada[i] for i in sequence_indexes]
            fitness,pecas_posicionadas = _rodar_BL(T,seq_resolvidas,sequence,W,L,R,C,NFP,IFP_D)   #roda o BL em si
            # print("\tindiv:",i,"sequencia",sequence,"fitness:",fitness)
            # Penaliza fitness inválidos em vez de reinicializar tudo
            if not np.isfinite(fitness):
                fitness = 1e9
            
            evaluated.append((fitness, chrom, pecas_posicionadas))
        
        return sorted(evaluated, key=lambda x: x[0])
    
    def _crossover(n,inheritance_prob, elite: np.ndarray, non_elite: np.ndarray) -> np.ndarray:
        """Crossover uniforme entre elite e não-elite."""
        mask = np.random.random(n) < inheritance_prob
        return np.where(mask, elite, non_elite)

    def _criar_proxima_populacao(pop,eli,her,mut,n,evaluated: List[Tuple[float, np.ndarray]]):
        """Cria nova população com base na avaliação atual."""
        new_pop = []
        
        elite_size =int(pop*eli)
        mutant_size =int(pop*mut)
        offspring_size = pop-elite_size-mutant_size

        # Grupo elite
        elite_chroms = [chrom for _, chrom,pecas_posicionadas in evaluated[:elite_size]]
        new_pop.extend(elite_chroms)

        # Grupo não-elite
        non_elite_pool = [chrom for _, chrom,pecas_posicionadas in evaluated[elite_size:]]

        elite_indices = np.random.randint(0, len(elite_chroms), offspring_size)
        non_elite_indices = np.random.randint(0, len(non_elite_pool), offspring_size)

        # Crossover
        for e_idx, ne_idx in zip(elite_indices, non_elite_indices):
            elite_parent = elite_chroms[e_idx]
            non_elite_parent = non_elite_pool[ne_idx]
            new_pop.append(_crossover(n, her, elite_parent, non_elite_parent))

        # Mutantes aleatórios
        new_pop.extend(np.random.random((mutant_size, n)))

        return np.array(new_pop, dtype=float)

    # ---------------
    ##implementar -- definir o seed no random
    if seed is not None:
        np.random.seed(seed)

    sequencias_resolvidas = {}

    #gera pop inicial
    n = sum(q)
    populacao = np.random.random((pop,n)).astype(float)

    # registro do mais adaptado
    melhor_seq = None
    melhor_fitness = float('inf')
    melhor_pecas_pos = []

    # evolui as gerações
    for gen in range(gens): 
        avaliados = _avaliar_pop(T,q,populacao,sequencias_resolvidas,W,L,R,C,NFP,IFP_D)
        gen_melhor_fitness, gen_melhor_seq, gen_melhor_pecas_pos = avaliados[0]
        if gen_melhor_fitness < melhor_fitness:
            melhor_fitness = gen_melhor_fitness
            melhor_seq = gen_melhor_seq
            melhor_pecas_pos = gen_melhor_pecas_pos
        if DEBUG:
            print(f"gen: {gen} \tmelhor_fitness:{melhor_fitness}")
        populacao = _criar_proxima_populacao(pop,eli,her,mut,n,avaliados)
    
    # return melhor_seq,melhor_fitness,melhor_pecas_pos
    # --------------------
    
    # --------------------

    # ao invés de mostrar a sequencia de alelos (alelo \in [0,1]^n),
    # mostra a sequencia de índices das peças
    demanda_sequenciada = []
    for i in range(len(list(q))):
        for _ in range(q[i]):
            demanda_sequenciada.append(i)

    melhor_seq_indices = [demanda_sequenciada[i] for i in _decode(melhor_seq)]

    return melhor_seq_indices, melhor_fitness, melhor_pecas_pos
    # --------------------

def brkga_bins(l,Q,largura_bin,pop_size=100,elite_frac=0.3,mutant_frac=0.4,prob_her=0.6,seed=42,gens=100000):
    
    def plotar_resultado_bins(l, capacidade_bin, sequencia_de_corte, num_bins, desperdicio_total, historico_fitness=None, nome_arquivo=None,mostrar_visualizacao=True):
        """
        Plota o resultado do BRKGA_bins usando matplotlib
        
        Args:
            l: dicionário {nome_modelo: largura}
            capacidade_bin: largura máxima do bin
            sequencia_de_corte: lista de bins, onde cada bin é uma lista de nomes de modelos
            num_bins: número total de bins usados
            desperdicio_total: desperdício total
            historico_fitness: histórico do fitness (opcional)
            nome_arquivo: nome do arquivo para salvar a imagem (opcional)
        """
        # Configurações de cores
        cores = plt.cm.Set3(np.linspace(0, 1, len(l)))
        # Criar dicionário de cores usando os nomes dos modelos como chave
        cor_map = {modelo_nome: cor for modelo_nome, cor in zip(l.keys(), cores)}
        
        # Criar figura com subplots
        if historico_fitness is not None:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            fig.suptitle(f'BRKGA Bin Packing - {num_bins} Bins - Desperdício Total: {desperdicio_total:.2f}', 
                        fontsize=16, fontweight='bold')
        else:
            fig, ax1 = plt.subplots(1, 1, figsize=(14, 8))
            fig.suptitle(f'BRKGA Bin Packing - {num_bins} Bins - Desperdício Total: {desperdicio_total:.2f}', 
                        fontsize=16, fontweight='bold')
            ax2 = None
        
        # Plotar bins
        bin_height = 0.8
        y_pos = 0
        max_bins_per_column = 10
        
        # Converter sequencia_de_corte para o formato correto se necessário
        # sequencia_de_corte pode vir como [['marques_m', 'marques_m'], ...]
        # ou já como [[largura1, largura2], ...]
        bins_para_plotar = []
        for bin_itens in sequencia_de_corte:
            if isinstance(bin_itens[0], str):
                # Converte nomes para larguras
                bin_larguras = [l[item] for item in bin_itens]
                bins_para_plotar.append(bin_larguras)
            else:
                # Já são larguras
                bins_para_plotar.append(bin_itens)

        for i, bin_larguras in enumerate(bins_para_plotar):
            coluna = i // max_bins_per_column
            linha = i % max_bins_per_column
            
            x_start = coluna * (capacidade_bin * 1.1)
            y_start = (max_bins_per_column - linha - 1) * (bin_height + 0.2)
            
            # Desenhar bin (capacidade total)
            ax1.add_patch(patches.Rectangle(
                (x_start, y_start), capacidade_bin, bin_height,
                fill=False, edgecolor='black', linewidth=2
            ))
            
            # Desenhar itens
            x_current = x_start
            soma_bin = sum(bin_larguras)
            
            # Para cada item no bin, precisamos saber seu nome original para a cor
            # Se temos apenas larguras, usamos um índice
            for j, largura in enumerate(bin_larguras):
                # Encontrar o nome do modelo para esta largura
                modelo_nome = None
                for nome, larg in l.items():
                    if abs(larg - largura) < 0.01:  # Tolerância para floats
                        modelo_nome = nome
                        break
                
                # Se não encontrou, usa a largura como identificador
                if modelo_nome is None:
                    modelo_nome = f"{largura:.2f}"
                    # Cria uma cor para este caso
                    if modelo_nome not in cor_map:
                        cor_map[modelo_nome] = plt.cm.Set3(hash(modelo_nome) % 12 / 12)
                
                ax1.add_patch(patches.Rectangle(
                    (x_current, y_start), largura, bin_height,
                    facecolor=cor_map[modelo_nome], edgecolor='black', alpha=0.7
                ))
                
                # Adicionar texto do tamanho se houver espaço
                if largura > capacidade_bin * 0.1:
                    ax1.text(x_current + largura/2, y_start + bin_height/2, 
                            f'{largura:.2f}', ha='center', va='center', 
                            fontsize=8, fontweight='bold')
                
                x_current += largura
            
            # Barra de utilização
            utilizacao = soma_bin / capacidade_bin
            ax1.add_patch(patches.Rectangle(
                (x_start, y_start + bin_height), capacidade_bin * utilizacao, 0.1,
                facecolor='green' if utilizacao > 0.8 else 'orange' if utilizacao > 0.6 else 'red',
                alpha=0.7
            ))
            
            # Adicionar texto com o nome do bin
            ax1.text(x_start + capacidade_bin/2, y_start + bin_height/2, 
                    f'Bin {i+1}', ha='center', va='center', 
                    fontsize=10, fontweight='bold', alpha=0.3)
        
        # Configurar eixo dos bins
        num_colunas = (len(bins_para_plotar) - 1) // max_bins_per_column + 1
        ax1.set_xlim(0, num_colunas * (capacidade_bin * 1.1))
        ax1.set_ylim(-0.5, max_bins_per_column * (bin_height + 0.2))
        ax1.set_xlabel('Capacidade dos Bins')
        ax1.set_ylabel('Bins')
        ax1.set_title('Alocação nos Bins')
        ax1.grid(True, alpha=0.3)
        
        # Adicionar legenda
        legend_handles = []
        for modelo_nome, cor in cor_map.items():
            if isinstance(modelo_nome, str) and modelo_nome in l:
                legend_handles.append(patches.Patch(color=cor, label=f'{modelo_nome} (largura: {l[modelo_nome]:.2f})'))
            elif isinstance(modelo_nome, str) and modelo_nome not in l:
                # É um nome genérico
                legend_handles.append(patches.Patch(color=cor, label=f'Item: {modelo_nome}'))
        
        ax1.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1, 1), 
                fontsize=8, title="Produtos")
        
        # Plotar evolução do fitness se disponível
        if ax2 is not None and historico_fitness is not None:
            ax2.plot(historico_fitness, linewidth=2, color='blue', alpha=0.7)
            ax2.set_xlabel('Geração')
            ax2.set_ylabel('Número de Bins')
            ax2.set_title('Evolução do Fitness (Número de Bins)')
            ax2.grid(True, alpha=0.3)
            
            # Destacar melhor fitness
            melhor_fitness = min(historico_fitness)
            ax2.axhline(y=melhor_fitness, color='red', linestyle='--', alpha=0.8, 
                    label=f'Melhor: {melhor_fitness} bins')
            ax2.legend()
        
        plt.tight_layout()
        
        # Salvar a imagem se um nome de arquivo foi fornecido
        if nome_arquivo:
            plt.savefig(nome_arquivo, dpi=300, bbox_inches='tight')
            print(f"Imagem salva como: {nome_arquivo}")
        
        if mostrar_visualizacao:
            plt.show()

    def _decode( individual): #!
        """Decodifica um indivíduo em uma solução de bin packing"""
        # Monta uma lista fixa com a demanda usando os tamanhos reais
        itens_ordenados = []
        for modelo_nome, qtd in Q.items():
            # Repete cada tamanho pela quantidade demandada
            itens_ordenados.extend([modelo_nome] * qtd)

        # Ordena índices pelo gene float (menor para maior)
        indices = range(len(individual))
        indices_ordenados = sorted(indices, key=lambda i: individual[i])

        # Sequência de itens na ordem dos genes ordenados
        sequencia_ordenada = [itens_ordenados[i] for i in indices_ordenados]

        # Divide a sequência em bins -------------------------
        bins = []
        bin_atual = []
        soma_atual = 0.0
        
        for i, modelo_nome in enumerate(sequencia_ordenada):
            largura_tamanho_tipo = l[modelo_nome]
            if soma_atual + largura_tamanho_tipo <= largura_bin:
                bin_atual.append((i, modelo_nome))
                soma_atual += largura_tamanho_tipo
            else:
                bins.append(bin_atual)
                bin_atual = [(i, modelo_nome)]
                soma_atual = largura_tamanho_tipo
        if bin_atual:
            bins.append(bin_atual)
        return bins
    
    def _fitness( individual):
        """Calcula o fitness (número de bins) de um indivíduo"""
        bins = _decode(individual)
        return len(bins)    

    def _random_indiv(n):
        return [np.random.random() for _ in range(n)]

    def _biased_crossover(prob_her, elite, non_elite):
        """Crossover biased: herda genes do elite com probabilidade prob_heranca"""
        child = []
        for e_gene, n_gene in zip(elite, non_elite):
            if np.random.random() < prob_her:
                child.append(e_gene)
            else:
                child.append(n_gene)
        return child
    # --------------------------------------------

    # --------------------------------------------
    if seed is not None:
            np.random.seed(seed)
    
    # cria populacao
    n = sum(Q.values())
    elite_size=int(pop_size*elite_frac)
    mutant_size=int(pop_size*mutant_frac)
    offspring_size= pop_size-elite_size-mutant_size
    
    populacao = [_random_indiv(n) for _ in range(pop_size)]

    #evolve
    melhor_indiv = None
    melhor_fitness=float('inf')
    historico_fitness = []

    for g in range(gens):
        pop_fitness = [(_fitness(indiv), indiv) for indiv in populacao]
        pop_fitness.sort(key=lambda x: x[0])

        num_bins_atual, melhor_atual_indiv = pop_fitness[0]
        if num_bins_atual < melhor_fitness:
            melhor_fitness = num_bins_atual
            melhor_indiv = melhor_atual_indiv

        historico_fitness.append(melhor_fitness)

        new_pop = [indiv for _, indiv in pop_fitness[:elite_size]]

        for _ in range(mutant_size):
            new_pop.append(_random_indiv(n))
        
        import random

        while len(new_pop)<pop_size:
            elite = random.choice(new_pop[:elite_size])
            non_elite=random.choice(populacao[elite_size:])
            filho = _biased_crossover(prob_her,elite,non_elite)
            new_pop.append(filho)
        populacao = new_pop
        if DEBUG:
            if g%(int(gens/10))==0:
                print(f"gen={g}\t\tmelhor_fitness={melhor_fitness}")
        

    bins = _decode(melhor_indiv)
    num_bins = len(bins)

    desperdicio_total = 0.0
    for bin in bins:
        soma_bin = sum(l[modelo_nome] for _, modelo_nome in bin)
        desperdicio_total+= largura_bin - soma_bin

    sequencia_corte = [[modelo_nome for _, modelo_nome in bin] for bin in bins]
    nome_arquivo = ""  
    
    nome_arquivo = "_".join(f"{modelo_nome}_{Q[modelo_nome]}" for modelo_nome in Q.keys())
    nome_arquivo = nome_arquivo+"_seed"+str(seed)+"_gens"+str(gens)+".png"
    plotar_resultado_bins(l,
                          largura_bin,
                          sequencia_corte,
                          num_bins,
                          desperdicio_total,
                          historico_fitness,
                          nome_arquivo=nome_arquivo,
                          mostrar_visualizacao=False)

    return num_bins, desperdicio_total, sequencia_corte, historico_fitness
# -------------------------------------

# -------------------------------------
# visualização
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MplPolygon

        
def visualizar_posicionamento(T, pecas_posicionadas, W, L, titulo="Posicionamento das Peças", nome_arquivo=None, modelo_nome=None, mostrar_visualizacao=False):
    """
    Visualiza as peças posicionadas na faixa.
    
    Args:
        T: Lista de polígonos das peças
        pecas_posicionadas: Lista de tuplas (tipo, (x, y)) 
        W: Altura da faixa
        L: Comprimento da faixa
        titulo: Título do gráfico
        nome_arquivo: Nome do arquivo para salvar (se None, não salva)
        modelo_nome: Nome do modelo (usado para gerar nome automático)
    """
    if not pecas_posicionadas:
        print("Nenhuma peça para visualizar!")
        return
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Desenha o contorno da faixa
    faixa = patches.Rectangle((0, 0), L, W, linewidth=2, 
                              edgecolor='black', facecolor='none', 
                              linestyle='--')
    ax.add_patch(faixa)
    
    # Cores para diferentes tipos
    cores = ['lightblue', 'lightgreen', 'lightsalmon', 'lightyellow', 
             'plum', 'lightcyan', 'lightpink', 'lightgray', 
             '#FFB6C1', '#B0E0E6', '#98FB98', '#FFD700']
    
    # Desenha cada peça
    for tipo, (x_pos, y_pos) in pecas_posicionadas:
        poligono = T[tipo]
        # Translada o polígono
        poligono_transladado = [(x + x_pos, y + y_pos) for x, y in poligono]
        
        # Cria e adiciona o polígono
        mpl_poly = MplPolygon(poligono_transladado, closed=True, 
                              facecolor=cores[tipo % len(cores)], 
                              edgecolor='black', linewidth=1.5, 
                              alpha=0.7)
        ax.add_patch(mpl_poly)
        
        # Adiciona rótulo com o tipo
        centro_x = sum(p[0] for p in poligono_transladado) / len(poligono_transladado)
        centro_y = sum(p[1] for p in poligono_transladado) / len(poligono_transladado)
        ax.text(centro_x, centro_y, f'T{tipo}', 
               ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Configura o gráfico
    ax.set_xlim(-5, L + 5)
    ax.set_ylim(-5, W + 5)
    ax.set_xlabel('Comprimento (L)', fontsize=12)
    ax.set_ylabel('Altura (W)', fontsize=12)
    ax.set_title(titulo, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal')
    
    # Informações
    n_pecas = len(pecas_posicionadas)
    comprimento_usado = max([max(p[0] + x for p in T[tipo]) for tipo, (x, _) in pecas_posicionadas])
    eficiencia = (comprimento_usado / L) * 100 if L > 0 else 0
    
    # info_text = f'Peças: {n_pecas}\nComprimento usado: {comprimento_usado:.1f} / {L:.1f}'
    # ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
    #        fontsize=10, verticalalignment='top',
    #        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Salvar a imagem se nome_arquivo foi fornecido
    if nome_arquivo is not None:
        plt.savefig(nome_arquivo, dpi=300, bbox_inches='tight')
        print(f"Imagem salva como: {nome_arquivo}")
    elif modelo_nome is not None:
        # Gera nome automático no formato: modelo_nome_W_R_C_L.png
        nome_auto = f"{modelo_nome}_W{W}_R{int(W*100)}_{L:.2f}.png"
        plt.savefig(nome_auto, dpi=300, bbox_inches='tight')
        print(f"Imagem salva como: {nome_auto}")

    if mostrar_visualizacao:
        plt.show()
# -------------------------------------


# -------------------------------------
# métodos aux
def escala(poligono, fator_escala=1.0, arredondamento=7):
    T, q = poligono
    
    T_escalado = [
        [(round(fator_escala*x, arredondamento),
          round(fator_escala*y, arredondamento)) for (x, y) in pol]
        for pol in T
    ]
    
    return T_escalado, q

def marques():
    T = [
        [(0, 0), (21, 0), (21, 22), (14, 28), (7, 28), (0, 22)],

        [(0, 5), (2, 0), (11, 2), (19, 0), (21, 5), (17, 4), (11, 6), (4, 4), (0, 5)],

        [(0, 0), (33, 0), (33, 14), (30, 14), (26, 17), (13, 15), (0, 17)],

        [(0, 0), (4, 0), (4, 39), (0, 39)],

        [(0, 0), (10, 0), (10, 11), (0, 11)],

        [(2, 20), (0, 18), (2, 10), (0, 2), (2, 0), (4, 10), (2, 20)],

        [(0, 0), (29, 0), (27, 12), (29, 22), (25, 26), (25, 33),
        (18, 37), (16, 35), (14, 35), (12, 37), (4, 34), (4, 26),
        (0, 22), (2, 12)],

        [(0, 0), (33, 0), (37, 6), (35, 13), (28, 13),
        (25, 15), (14, 13), (0, 15)]
    ]

    q = [2,2,1,1,2,2,1,1]
    return T, q 

def gerar_pontos_malha(W,L,R,C):
    pontos = {}
    gx = L/(C-1)
    gy = W/(R-1)
    for i in range(C):
        for j in range(R):
            n = i*R+j
            pontos[n] = (i*gx, j*gy)
    return pontos   

def discretizar_poligono(W, L, R, C, pontos_a_verificar: dict, poligono_t: Polygon, 
                         somente_interior=False, epsilon=1e-7):
    """
    Retorna lista de coordenadas (x, y) dos pontos contidos no polígono.
    """
    gx = L/(C-1)
    gy = W/(R-1)
    epsilon_adapt = max(epsilon, min(gx, gy)*0.001)
    
    if somente_interior:
        poligono_robusto = poligono_t.buffer(-epsilon_adapt) if poligono_t.area > epsilon_adapt else poligono_t
    else:
        poligono_robusto = poligono_t.buffer(epsilon_adapt)
    
    poligono_prep = prep(poligono_robusto)
    minx, miny, maxx, maxy = poligono_t.bounds
    minx -= epsilon_adapt
    miny -= epsilon_adapt
    maxx += epsilon_adapt
    maxy += epsilon_adapt
    
    pontos_contidos = []
    for ponto_num, ponto_coords in pontos_a_verificar.items():
        x, y = ponto_coords
        if not (minx <= x <= maxx and miny <= y <= maxy):
            continue
        
        if poligono_prep.contains(Point(ponto_coords)):
            pontos_contidos.append(ponto_coords)  # ← SÓ AS COORDENADAS
        elif not somente_interior:
            if poligono_t.boundary.distance(Point(ponto_coords)) <= epsilon_adapt:
                pontos_contidos.append(ponto_coords)  # ← SÓ AS COORDENADAS
    
    return pontos_contidos  # Lista de [(x1,y1), (x2,y2), ...]


# --------------------------------------


# -------------------------------------
def main():

    geral_gens = 10
    geral_seed = 5
    modelos_list = {
        "marques_pp":   {"T-q":escala(marques(),0.85), "W":104, "L":75, "R":105, "C":76, "seed":geral_seed, "gens":geral_gens},
        "marques_p":    {"T-q":escala(marques(),0.90), "W":104, "L":75, "R":105, "C":76, "seed":geral_seed, "gens":geral_gens},
        "marques_m" :   {"T-q":escala(marques(),1.00), "W":104, "L":75, "R":105, "C":76, "seed":geral_seed, "gens":geral_gens},
        "marques_g":    {"T-q":escala(marques(),1.06), "W":104, "L":75, "R":105, "C":76, "seed":geral_seed, "gens":geral_gens},
        "marques_gg":    {"T-q":escala(marques(),1.13), "W":104, "L":75, "R":105, "C":76, "seed":geral_seed, "gens":geral_gens},
        # "marques_m_refinado":   {"T-q":escala(marques(),1.00), "W":104, "L":75, "R":209,"C":151, "seed":geral_seed, "gens":geral_gens},
    }
    
    print("modelos:")
    print()

    # 1. Pré-processamento

    # primeiro passar olhando cada modelo e agrupa-los por malhas (W,L,R,C) únicas. 
    malhas = {}
    for modelo_nome, modelo_params in modelos_list.items():
        W, L, R, C = modelo_params["W"], modelo_params["L"], modelo_params["R"], modelo_params["C"]
        if (W, L, R, C) not in malhas:
            malhas[(W, L, R, C)] = []        
        malhas[(W, L, R, C)].append(modelo_nome)

    print("malhas:")
    print(malhas)
    print()

    # calcular todos IFP_Ds
    print("IFP_Ds:")
    # No main(), onde você calcula IFP_Ds:
    IFP_Ds = {}
    for malha_atributos, modelos_nesta_malha in malhas.items():
        W, L, R, C = malha_atributos
        pontos_malha = gerar_pontos_malha(W, L, R, C)
        
        for modelo_nome in modelos_nesta_malha:
            modelo = modelos_list[modelo_nome]
            T, q = modelo["T-q"]
            ifp_por_peca = {}   # Dicionário para armazenar IFP de cada peça
            for idx, poligono_t in enumerate(T):
                retangulo_malha = [(0,0), (L,0), (L,W), (0,W)]
                ifp = ifp_generator.calculate_ifp(retangulo_malha, poligono_t)
                ifp_d = discretizar_poligono(W, L, R, C, pontos_malha, ifp)
                ifp_por_peca[idx] = ifp_d
                if DEBUG:
                    print(f"  Peça {idx}: {len(ifp_d)} pontos no IFP")
            
            IFP_Ds[modelo_nome] = ifp_por_peca
            print(f"modelo: {modelo_nome} - ok")
    print()

    # calcular todos NFPs
    NFPs = {}
    for modelo_nome, modelo_params in modelos_list.items():
        T,q = modelo_params["T-q"]
        NFPs_modelo = {}    #calcular o NFP de t e u, para cada par de peças (t,u)
        for u_indice, u in enumerate(T):
            for t_indice, t in enumerate(T):
                NFPs_modelo[u_indice,t_indice] = nfp_generator.calculate_nfp(u,t) 
                # print()
        NFPs[modelo_nome] = NFPs_modelo

    print("NFPs calculados!")
    print()


    # 2. ISPP (menor faixa)
    l = {}
    print("ISPP:")
    for i, v in enumerate(malhas.items()):
        malha_key, malha_val = v
        W,L,R,C = malha_key
        modelos_names = malha_val
        print("malha:",W,L,R,C,":")

        for modelo_nome in modelos_names:
            # print("resolvendo modelo:",modelo_nome)
            # resolver brkga com BL
            modelo_params = modelos_list[modelo_nome]
            T,q = modelo_params["T-q"]
            IFP_D = IFP_Ds[modelo_nome]
            NFP = NFPs[modelo_nome]
            seed = modelo_params["seed"]
            gens = modelo_params["gens"]
            
            pop_size = 100    ###### arbitrário
            print(f"Executando BRKGA para: {modelo_nome} | pop={pop_size}, gens={gens}, seed={seed} |")
            cache = _load_cache(modelo_nome, W, L, R, C, seed, gens)
            if cache:
                seq_melhor, fitness_melhor, pecas_pos_melhor = cache
                print(f"Modelo já resolvido (json encontrado): {modelo_nome}, fitness: {fitness_melhor:.2f}")
            else:
                seq_melhor, fitness_melhor, pecas_pos_melhor = brkga_ordem(T,q,W,L,R,C,NFP,IFP_D,
                                                                        pop=pop_size,gens=gens,seed=seed)
                _save_cache(modelo_nome, W, L, R, C, seed, gens, seq_melhor, fitness_melhor, pecas_pos_melhor)

            l[modelo_nome] = fitness_melhor # registrar largura l da faixa
            
            print(f"RESULTADO PARA {modelo_nome}:")
            print(f"Melhor fitness (comprimento): {fitness_melhor:.2f}")
            print(f"Melhor sequência: {seq_melhor}...")
            # print(f"Número de peças posicionadas: {len(pecas_pos_melhor)}")
            
            # Visualiza o resultado
            # No main(), onde você chama visualizar_posicionamento:
            if pecas_pos_melhor:
                # Gera o nome do arquivo no formato desejado
                nome_imagem = f"{modelo_nome}_W{W}_R{R}_C{C}_L{fitness_melhor:.2f}_g{gens}_s{seed}.png"
                
                visualizar_posicionamento(
                    T, 
                    pecas_pos_melhor, 
                    W, 
                    fitness_melhor,
                    titulo=f"{modelo_nome} - Comprimento: {fitness_melhor:.2f}",
                    nome_arquivo=nome_imagem,  # ou pode usar modelo_nome=modelo_nome para gerar automaticamente
                    mostrar_visualizacao=False
                )
                print()
            else:
                print(f"AVISO: Nenhuma peça foi posicionada para {modelo_nome}")
            
            # print("\n" + "-"*60 + "\n")
    print("ISPP acabou.")
    print()

    # 3. PCME (mínimo de bins)
    # Dados
    Q = {
        "marques_pp":           16,
        "marques_p":            32,
        "marques_m":            32,
        "marques_g":            32,
        "marques_gg":           16,
        # "marques_m_refinado":   16
    }
    
    capacidade_bin = 110 # 

    print("PCME:")
    WW = -1     # verificação se todos tem faixas de mesma dimensão vertical (W)
    for modelo_nome, modelo_params in modelos_list.items():
        W_modelo = modelo_params["W"] 
        if WW <=0:
            WW = W_modelo
        if W_modelo != WW:
            print(f"erro, os modelos de roupa têm alturas DIFERENTES: {WW} e {W_modelo}")
            return 
    # se passou por aqui, faz o PCME
    brkga_bins_gens=10000
    brkga_bins_seed=42
    pop_size=100
    elite_frac=0.3
    mutant_frac=0.4
    prob_her=0.6
    print(f"brkga_bins para:Q={Q}, l={l}, seed={brkga_bins_seed},pop={pop_size},gens={brkga_bins_gens}")

    cache_pcme = _load_cache_pcme(Q, capacidade_bin, brkga_bins_seed, brkga_bins_gens)
    if cache_pcme:
        num_bins, desperdicio, seq_corte, hist = cache_pcme
        print(f"Cache PCME hit: {num_bins} bins, desperdício: {desperdicio:.2f}")
    else:
        num_bins, desperdicio, seq_corte, hist = brkga_bins(l, Q, capacidade_bin,
                                                            pop_size, elite_frac, mutant_frac, prob_her,
                                                            brkga_bins_seed, brkga_bins_gens)
        _save_cache_pcme(Q, capacidade_bin, brkga_bins_seed, brkga_bins_gens, 
                        num_bins, desperdicio, seq_corte, hist)

    
    print("num_bins:",num_bins)
    print("desperdicio:",desperdicio)
    print("seq_corte:",seq_corte)
        
if __name__ == "__main__":
    main()
