# ---------------------------------------------------------------------------------
import numpy as np
import random
from typing import List, Tuple, Callable
import matplotlib.pyplot as plt
import matplotlib.patches as patches
# ---------------------------------------------------------------------------------

class BRKGA_ordem:
    def __init__(self, n: int, fitness_func: Callable, pop_size: int = 100, 
                 elite_frac: float = 0.2, mutant_frac: float = 0.2, 
                 inheritance_prob: float = 0.7, seed: int = None):
        
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.n = n
        self.fitness_func = fitness_func
        self.pop_size = pop_size
        self.inheritance_prob = inheritance_prob
        
        # Tamanhos dos grupos
        self.elite_size = int(pop_size * elite_frac)
        self.mutant_size = int(pop_size * mutant_frac)
        self.offspring_size = pop_size - self.elite_size - self.mutant_size
        
        # População inicial
        self.population = np.random.random((pop_size, n)).astype(float)
        
        # Melhor solução global
        self.best_sequence = None
        self.best_fitness = float('inf')
        self.best_pecas_posicionadas = []

    def decode(self, chromosome: np.ndarray) -> List[int]:
        """Decodifica cromossomo em sequência (ordenação pelos alelos)."""
        return np.argsort(chromosome).tolist()

    def evaluate_population(self,demanda_q) -> List[Tuple[float, np.ndarray]]:
        """Avalia a população e retorna uma lista ordenada por fitness."""
        evaluated = []
        demanda_sequenciada = []
        for i in range(len(list(demanda_q))):
            for _ in range(demanda_q[i]):
                demanda_sequenciada.append(i)

        # ii=1
        total=len(self.population)
        for i,chrom in enumerate(self.population):               # para toda a população
            sequence_indexes = self.decode(chrom)
            sequence = [demanda_sequenciada[i] for i in sequence_indexes]
            fitness,pecas_posicionadas = self.fitness_func(sequence)   #roda o BL em si
            if i % 10 == 0:
                print(f"{i+1}/{total} fit:{fitness} seq:{sequence} pecas_pos:{str(pecas_posicionadas)}")
            # if ii in [2,4,8,16,32,64,100]:
            #     print(f"{ii}/{total}\tseq:{sequence}\tlargura:{fitness}")

            # ii+=1
            # Penaliza fitness inválidos em vez de reinicializar tudo
            if not np.isfinite(fitness):
                fitness = 1e9
            
            evaluated.append((fitness, chrom, pecas_posicionadas))
        
        return sorted(evaluated, key=lambda x: x[0])

    def crossover(self, elite: np.ndarray, non_elite: np.ndarray) -> np.ndarray:
        """Crossover uniforme entre elite e não-elite."""
        mask = np.random.random(self.n) < self.inheritance_prob
        return np.where(mask, elite, non_elite)

    def _create_new_population(self, evaluated: List[Tuple[float, np.ndarray]]):
        """Cria nova população com base na avaliação atual."""
        new_pop = []

        # Grupo elite
        elite_chroms = [chrom for _, chrom,pecas_posicionadas in evaluated[:self.elite_size]]
        new_pop.extend(elite_chroms)

        # Grupo não-elite
        non_elite_pool = [chrom for _, chrom,pecas_posicionadas in evaluated[self.elite_size:]]

        elite_indices = np.random.randint(0, len(elite_chroms), self.offspring_size)
        non_elite_indices = np.random.randint(0, len(non_elite_pool), self.offspring_size)

        # Crossover
        for e_idx, ne_idx in zip(elite_indices, non_elite_indices):
            elite_parent = elite_chroms[e_idx]
            non_elite_parent = non_elite_pool[ne_idx]
            new_pop.append(self.crossover(elite_parent, non_elite_parent))

        # Mutantes aleatórios
        new_pop.extend(np.random.random((self.mutant_size, self.n)))

        self.population = np.array(new_pop, dtype=float)

    def evolve(self, demanda_q, gens: int = 100, verbose=True) -> Tuple[List[int], float]:
        """Executa o processo evolutivo do BRKGA."""
        log_interval = 1 if verbose is True else (verbose if isinstance(verbose, int) else None)
        
        for gen in range(gens):
            evaluated = self.evaluate_population(demanda_q)
            current_best_fitness, current_best_chrom, current_best_pecas_posicionadas = evaluated[0]

            # Atualiza melhor global
            if current_best_fitness < self.best_fitness:
                self.best_fitness = current_best_fitness
                sequence_indexes = self.decode(current_best_chrom)
                demanda_sequenciada = []
                for i in range(len(list(demanda_q))):
                    for _ in range(demanda_q[i]):
                        demanda_sequenciada.append(i)
                sequence = [demanda_sequenciada[i] for i in sequence_indexes]
                self.best_sequence = sequence
                self.best_pecas_posicionadas = current_best_pecas_posicionadas
            # Log de progresso
            if log_interval and gen % log_interval == 0:
                print(f"Gen {gen:03d}: Best = {current_best_fitness:.4f} | Valid = {len(evaluated)}")

            # Nova população
            self._create_new_population(evaluated)

        # Resultado final
        if verbose:
            print("\n=== Resultado Final ===")
            print(f"Melhor sequência: {self.best_sequence}")
            print(f"Fitness: {self.best_fitness:.6f}")
            # print(f"Peças posicionadas: {str(self.best_pecas_posicionadas)}")

        return self.best_sequence, self.best_fitness, self.best_pecas_posicionadas

    def create_initial_solution(self, method: str = "random") -> Tuple[List[int], float]:
        """Gera uma solução inicial (útil para comparar com o BRKGA)."""
        if method == "sorted":
            sequence = list(range(self.n))
        elif method == "greedy":
            # Placeholder: aqui pode entrar um heurístico real
            sequence = random.sample(range(self.n), self.n)
        else:
            sequence = random.sample(range(self.n), self.n)

        fitness = self.fitness_func(sequence)
        return sequence, fitness

# ---------------------------------------------------------------------------------
class BRKGA_bins:
    def __init__(self, tamanhos_itens, demanda, capacidade_bin, pop_size=100, elite_frac=0.2, 
                 mutant_frac=0.4, prob_heranca=0.6, seed=None):
        """
        Args:
            tamanhos_itens: dicionário {tamanho: quantidade, ...} 
                Ex: {0.94: 51.2, 1.00: 55.865, ...}
            demanda: dicionário {tamanho: quantidade_inteira, ...}
                Ex: {0.94: 10, 1.00: 15, ...}
            capacidade_bin: capacidade máxima de cada bin
        """
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        self.tamanhos_itens = tamanhos_itens
        self.demanda = demanda
        self.capacidade_bin = capacidade_bin
        
        # Calcular tamanho do indivíduo (total de itens)
        self.n = sum(demanda.values())
        
        self.pop_size = pop_size
        self.prob_heranca = prob_heranca
        self.elite_size = int(pop_size * elite_frac)
        self.mutant_size = int(pop_size * mutant_frac)
        self.offspring_size = pop_size - self.elite_size - self.mutant_size
        
        # Inicializar população
        self.population = [self.random_individual() for _ in range(pop_size)]
    
    def random_individual(self):
        """Gera um vetor de R^n onde cada componente pertence à [0,1]"""
        return [random.random() for _ in range(self.n)]
    
    def decode(self, individual):
        """Decodifica um indivíduo em uma solução de bin packing"""
        # Monta uma lista fixa com a demanda usando os tamanhos reais
        itens_ordenados = []
        for tamanho_tipo, qtd in self.demanda.items():
            # Repete cada tamanho pela quantidade demandada
            itens_ordenados.extend([tamanho_tipo] * qtd)

        # Ordena índices pelo gene float (menor para maior)
        indices = range(len(individual))
        indices_ordenados = sorted(indices, key=lambda i: individual[i])

        # Sequência de itens na ordem dos genes ordenados
        sequencia_ordenada = [itens_ordenados[i] for i in indices_ordenados]

        # Divide a sequência em bins
        bins = []
        bin_atual = []
        soma_atual = 0.0

        for i, tamanho_tipo in enumerate(sequencia_ordenada):
            largura_tamanho_tipo = self.tamanhos_itens[tamanho_tipo]
            if soma_atual + largura_tamanho_tipo <= self.capacidade_bin:
                bin_atual.append((i, tamanho_tipo))
                soma_atual += largura_tamanho_tipo
            else:
                bins.append(bin_atual)
                bin_atual = [(i, tamanho_tipo)]
                soma_atual = largura_tamanho_tipo

        if bin_atual:
            bins.append(bin_atual)

        return bins
    
    def fitness(self, individual):
        """Calcula o fitness (número de bins) de um indivíduo"""
        bins = self.decode(individual)
        return len(bins)
    
    def biased_crossover(self, elite, non_elite):
        """Crossover biased: herda genes do elite com probabilidade prob_heranca"""
        child = []
        for e_gene, n_gene in zip(elite, non_elite):
            if random.random() < self.prob_heranca:
                child.append(e_gene)
            else:
                child.append(n_gene)
        return child
    
    def evolve(self, num_geracoes=10000):
        """Executa o algoritmo evolutivo"""
        melhor_indiv = None
        melhor_fitness = float("inf")
        historico_fitness = []

        for gen in range(num_geracoes):
            # Avaliar população
            pop_fitness = [(self.fitness(indiv), indiv) for indiv in self.population]
            pop_fitness.sort(key=lambda x: x[0])

            # Comparar e achar melhor fitness
            num_bins_atual, melhor_atual_indiv = pop_fitness[0]
            if num_bins_atual < melhor_fitness:
                melhor_fitness = num_bins_atual
                melhor_indiv = melhor_atual_indiv
            
            historico_fitness.append(melhor_fitness)

            # Nova população
            new_pop = [indiv for _, indiv in pop_fitness[:self.elite_size]]
            
            # Adicionar mutantes
            for _ in range(self.mutant_size):
                new_pop.append(self.random_individual())
            
            # Adicionar offspring (crossover entre elite e não-elite)
            while len(new_pop) < self.pop_size:
                elite = random.choice(new_pop[:self.elite_size])
                non_elite = random.choice(self.population[self.elite_size:])
                filho = self.biased_crossover(elite, non_elite)
                new_pop.append(filho)

            self.population = new_pop

        # Decodificar melhor solução encontrada
        bins = self.decode(melhor_indiv)
        num_bins = len(bins)
        
        # Calcular desperdício para informação adicional
        desperdicio_total = 0.0
        for bin in bins:
            soma_bin = sum(self.tamanhos_itens[tamanho] for _, tamanho in bin)
            desperdicio_total += self.capacidade_bin - soma_bin
        
        # Formatar sequência de corte (apenas os tamanhos)
        sequencia_de_corte = [[tamanho for _, tamanho in bin] for bin in bins]

        return num_bins, desperdicio_total, sequencia_de_corte, historico_fitness
    
    # implementar ####testar
    def plotar_resultado_bins(self, sequencia_de_corte, num_bins, desperdicio_total, historico_fitness=None, nome_arquivo=None):
        """
        Plota o resultado do BRKGA_bins usando matplotlib
        
        Args:
            sequencia_de_corte: lista de bins com itens alocados
            num_bins: número total de bins usados
            desperdicio_total: desperdício total
            historico_fitness: histórico do fitness (opcional)
            nome_arquivo: nome do arquivo para salvar a imagem (opcional)
        """
        # Configurações de cores
        cores = plt.cm.Set3(np.linspace(0, 1, len(self.tamanhos_itens)))
        cor_map = {tamanho: cor for tamanho, cor in zip(self.tamanhos_itens.keys(), cores)}
        
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
        
        for i, bin_itens in enumerate(sequencia_de_corte):
            coluna = i // max_bins_per_column
            linha = i % max_bins_per_column
            
            x_start = coluna * (self.capacidade_bin * 1.1)
            y_start = (max_bins_per_column - linha - 1) * (bin_height + 0.2)
            
            # Desenhar bin (capacidade total)
            ax1.add_patch(patches.Rectangle(
                (x_start, y_start), self.capacidade_bin, bin_height,
                fill=False, edgecolor='black', linewidth=2
            ))
            
            # Desenhar itens
            x_current = x_start
            soma_bin = sum(bin_itens)
            
            for tamanho in bin_itens:
                largura_tamanho_tipo = self.tamanhos_itens[tamanho]
                ax1.add_patch(patches.Rectangle(
                    (x_current, y_start), largura_tamanho_tipo, bin_height,
                    facecolor=cor_map[tamanho], edgecolor='black', alpha=0.7
                ))
                
                # Adicionar texto do tamanho se houver espaço
                if self.tamanhos_itens[tamanho] > self.capacidade_bin * 0.1:
                    ax1.text(x_current + self.tamanhos_itens[tamanho]/2, y_start + bin_height/2, 
                            f'{largura_tamanho_tipo:.2f}', ha='center', va='center', 
                            fontsize=8, fontweight='bold')
                
                x_current += self.tamanhos_itens[tamanho]
            
            # Barra de utilização
            utilizacao = soma_bin / self.capacidade_bin
            ax1.add_patch(patches.Rectangle(
                (x_start, y_start + bin_height), self.capacidade_bin * utilizacao, 0.1,
                facecolor='green' if utilizacao > 0.8 else 'orange' if utilizacao > 0.6 else 'red',
                alpha=0.7
            ))
        
        # Configurar eixo dos bins
        num_colunas = (len(sequencia_de_corte) - 1) // max_bins_per_column + 1
        ax1.set_xlim(0, num_colunas * (self.capacidade_bin * 1.1))
        ax1.set_ylim(-0.5, max_bins_per_column * (bin_height + 0.2))
        ax1.set_xlabel('Capacidade dos Bins')
        ax1.set_ylabel('Bins')
        ax1.set_title('Alocação nos Bins')
        ax1.grid(True, alpha=0.3)
        
        # Adicionar legenda
        legend_handles = []
        for tamanho, cor in cor_map.items():
            legend_handles.append(patches.Patch(color=cor, label=f'tamanho: x{tamanho:.2f} (qtd: {self.demanda[tamanho]})'))
        
        ax1.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1, 1), 
                fontsize=8, title="Tipos de Produtos finais (escalados)")
        
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
        
        plt.show()
# ---------------------------------------------------------------------------------
