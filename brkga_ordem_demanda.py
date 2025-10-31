import numpy as np
import random
from typing import List, Tuple, Callable
import copy
from bottom_left import Bottom_Left

class BRKGA:
    def __init__(self, demanda: List[int], fitness_func: Callable, 
                 pop_size: int = 100, elite_frac: float = 0.2,
                 mutant_frac: float = 0.2, inheritance_prob: float = 0.7):
        """
        Inicializa o BRKGA
        
        Args:
            demanda: Lista de demandas [0,0,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,6,6,7,7]
            fitness_func: Função que recebe uma sequência e retorna o valor a ser minimizado
            pop_size: Tamanho da população
            elite_frac: Fração da população que é elite
            mutant_frac: Fração da população que é mutante
            inheritance_prob: Probabilidade de herdar do pai elite no crossover
        """
        self.demanda = demanda
        self.fitness_func = fitness_func
        self.pop_size = pop_size
        self.elite_frac = elite_frac
        self.mutant_frac = mutant_frac
        self.inheritance_prob = inheritance_prob
        
        self.n = len(demanda)
        self.elite_size = int(pop_size * elite_frac)
        self.mutant_size = int(pop_size * mutant_frac)
        self.normal_size = pop_size - self.elite_size - self.mutant_size
        
        # Inicializa população
        self.population = self._initialize_population() 
        
    def _initialize_population(self) -> np.ndarray:
        """Inicializa a população com chaves aleatórias"""
        return np.random.random((self.pop_size, self.n))
    
    def decode(self, chromosome: np.ndarray) -> List[int]:
        """
        Decodifica um cromossomo (vetor de chaves) para uma sequência de demanda
        Usa argsort para converter chaves em permutação
        """
        # Obtém a ordem baseada nas chaves
        order = np.argsort(chromosome)
        # Aplica a ordem à demanda original
        return [self.demanda[i] for i in order]
    
    def evaluate_population(self) -> List[Tuple[float, np.ndarray]]:
        """Avalia toda a população e retorna lista (fitness, chromosome) ordenada"""
        evaluated = []
        for i, chrom in enumerate(self.population):
            sequence = self.decode(chrom)
            fitness = self.fitness_func(sequence)
            
            # Ignora valores inválidos
            if not np.isfinite(fitness):
                print(f"Indivíduo {i+1}/{self.pop_size}: Fitness inválido ignorado ({fitness})")
                continue
                
            evaluated.append((fitness, chrom))
            print(f"{i+1}/{self.pop_size}\n")
        
        # Se todos os fitness forem inválidos, cria uma população nova
        if len(evaluated) == 0:
            print("ATENÇÃO: Todos os fitness são inválidos! Reinicializando população...")
            self.population = self._initialize_population()
            return self.evaluate_population()
        
        # Ordena por fitness (menor é melhor)
        return sorted(evaluated, key=lambda x: x[0])
    
    def crossover(self, elite_parent: np.ndarray, non_elite_parent: np.ndarray) -> np.ndarray:
        """Realiza crossover entre um pai elite e um não-elite"""
        child = np.zeros(self.n)
        for i in range(self.n):
            if random.random() < self.inheritance_prob:
                child[i] = elite_parent[i]
            else:
                child[i] = non_elite_parent[i]
        return child
    
    def evolve(self, generations: int = 100, verbose: bool = True) -> Tuple[List[int], float]:
        """
        Executa a evolução do BRKGA
        """
        best_sequence = None
        best_fitness = float('inf')
        
        for gen in range(generations):
            # Avalia população
            evaluated_pop = self.evaluate_population()
            
            # Verifica se temos indivíduos válidos
            if len(evaluated_pop) == 0:
                print(f"Geração {gen}: Nenhum indivíduo válido, pulando...")
                continue
                
            current_best_fitness, current_best_chrom = evaluated_pop[0]
            
            # Atualiza melhor global apenas se for válido
            if current_best_fitness < best_fitness and np.isfinite(current_best_fitness):
                best_fitness = current_best_fitness
                best_sequence = self.decode(current_best_chrom)
            
            if verbose and gen % 1 == 0:
                valid_count = len(evaluated_pop)
                print(f"Geração {gen}: Melhor Fitness = {current_best_fitness:.4f} ({valid_count}/{self.pop_size} válidos\n)")
            
            # Cria nova população apenas se temos elite suficiente
            if len(evaluated_pop) >= self.elite_size:
                new_population = []
                
                # Mantém elite
                elite_chromosomes = [chrom for _, chrom in evaluated_pop[:self.elite_size]]
                new_population.extend(elite_chromosomes)
                
                # Cria filhos por crossover
                for _ in range(self.normal_size):
                    elite_parent = random.choice(elite_chromosomes)
                    # Pega não-elite apenas se houver indivíduos suficientes
                    non_elite_pool = [chrom for _, chrom in evaluated_pop[self.elite_size:]]
                    if non_elite_pool:
                        non_elite_parent = random.choice(non_elite_pool)
                        child = self.crossover(elite_parent, non_elite_parent)
                        new_population.append(child)
                    else:
                        # Se não há não-elite, cria um mutante
                        new_population.append(np.random.random(self.n))
                
                # Adiciona mutantes 
                for _ in range(self.mutant_size):
                    mutant = np.random.random(self.n)
                    new_population.append(mutant)
                
                self.population = np.array(new_population)
            else:
                # Se não temos elite suficiente, reinicializa a população
                print(f"Geração {gen}: População insuficiente, reinicializando...")
                self.population = self._initialize_population()
        
        if verbose:
            if best_sequence is not None:
                print(f"\nMelhor solução encontrada:")
                print(f"Sequência: {best_sequence}")
                print(f"Fitness: {best_fitness}")
            else:
                print("\nNenhuma solução válida encontrada!")
        
        return best_sequence, best_fitness

# Função para criar uma solução inicial inteligente
def create_initial_solution(demanda: List[int]) -> np.ndarray:
    """
    Cria uma solução inicial que distribui os itens de forma mais equilibrada
    """
    n = len(demanda)
    # Conta a frequência de cada item
    from collections import Counter
    counts = Counter(demanda)
    
    # Cria uma sequência que intercala os itens
    sequence = []
    remaining = counts.copy()
    
    while sum(remaining.values()) > 0:
        for item in sorted(remaining.keys()):
            if remaining[item] > 0:
                sequence.append(item)
                remaining[item] -= 1
    
    # Converte para chromosome (encontrando a permutação que gera esta sequência)
    # Como é complexo mapear diretamente, vamos criar chaves que aproximem esta ordem
    chrom = np.random.random(n)
    positions = {}
    current_pos = 0
    for item in sorted(set(demanda)):
        item_indices = [i for i, x in enumerate(demanda) if x == item]
        for idx in item_indices:
            if item not in positions:
                positions[item] = []
            positions[item].append(current_pos)
            current_pos += 1
    
    # Atribui chaves baseadas na posição desejada
    for i, item in enumerate(sequence):
        available_indices = [j for j in range(n) if demanda[j] == item and chrom[j] == chrom[j]]
        if available_indices:
            chrom[available_indices[0]] = i / n
    
    return chrom
