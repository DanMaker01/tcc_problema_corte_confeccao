# ---------------------------------------------------------------------------------
import numpy as np
import random
from typing import List, Tuple, Callable
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


        for chrom in self.population:
            sequence_indexes = self.decode(chrom)
            sequence = [demanda_sequenciada[i] for i in sequence_indexes]
            fitness = self.fitness_func(sequence)
            
            # Penaliza fitness inválidos em vez de reinicializar tudo
            if not np.isfinite(fitness):
                fitness = 1e9
            
            evaluated.append((fitness, chrom))
        
        return sorted(evaluated, key=lambda x: x[0])

    def crossover(self, elite: np.ndarray, non_elite: np.ndarray) -> np.ndarray:
        """Crossover uniforme entre elite e não-elite."""
        mask = np.random.random(self.n) < self.inheritance_prob
        return np.where(mask, elite, non_elite)

    def _create_new_population(self, evaluated: List[Tuple[float, np.ndarray]]):
        """Cria nova população com base na avaliação atual."""
        new_pop = []

        # Grupo elite
        elite_chroms = [chrom for _, chrom in evaluated[:self.elite_size]]
        new_pop.extend(elite_chroms)

        # Grupo não-elite
        non_elite_pool = [chrom for _, chrom in evaluated[self.elite_size:]]

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

    def evolve(self, demanda_q, generations: int = 100, verbose=True) -> Tuple[List[int], float]:
        """Executa o processo evolutivo do BRKGA."""
        log_interval = 1 if verbose is True else (verbose if isinstance(verbose, int) else None)
        
        for gen in range(generations):
            evaluated = self.evaluate_population(demanda_q)
            current_best_fitness, current_best_chrom = evaluated[0]

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

        return self.best_sequence, self.best_fitness

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

class BRKGA_bin:            ######## BRGKA bin, implementar com itens_types genéricos
    def __init__(self,n, pop_size=100, elite_frac = 0.2, mutant_frac = 0.3,prob_heranca=0.7,seed=None ):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        self.n = n
        self.pop_size = pop_size
        self.prob_heranca = prob_heranca

        self.elite_size = int(pop_size*elite_frac)
        self.mutant_size = int(pop_size*mutant_frac)
        self.offspring_size = pop_size - self.elite_size - self.mutant_size
        self.population = np.random.random((pop_size, n)).astype(float)

        pass
    def random_individual(self, demanda_dict:dict):
        tamanho = sum(demanda_dict.values())
        return [random.random() for _ in range(tamanho)]
    def decode(self,individual):
        pass
    def fitness(self,individual):           ## fitness aqui? ou recebe uma função externa?
        pass
    def biased_crossover(self):
        pass
    def evolve(self, num_geracoes=100):     ##### implementar
        melhor_indiv = None
        melhor_fitness = float("inf")

        for gen in range(num_geracoes):
            #avaliar popula
            pop_fitness = [self.fitness(indiv) for indiv in self.population]
            pop_fitness.sort(key=lambda x: x[0])

            #comparar e achar melhor fitness
            desperdicio_atual, melhor_atual = pop_fitness[0]
            if melhor_atual < melhor_fitness:
                melhor_indiv = melhor_atual
             
            #nova popula ########## implementar
            # nova_pop = [ind for ]
            # self.population = nova_pop

        bins, desperdicio_final = self.decode(melhor_indiv)########## implementar
        num_bins = len(bins)
        sequencia_de_corte = [ [tipo for _, tipo, _ in bin] for bin in bins]

        return num_bins, desperdicio_final, sequencia_de_corte

# ---------------------------------------------------------------------------------
