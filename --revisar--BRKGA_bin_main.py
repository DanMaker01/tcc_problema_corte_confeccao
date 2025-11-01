import random
import pygame
import csv
import os
from datetime import datetime
import traceback

import matplotlib.pyplot as plt

# ========= PARAMETROS DO PROBLEMA =========
ITEM_TYPES = {"PP":3000.0,"P": 5006.04, "M": 5720, "G": 6493.98, "GG": 7550}
n=10
CAMISA_COUNTS = {"PP":n*4,"P": n*2, "M": n*3, "G": n*2, "GG": n*1}
BIN_CAPACITY = 24000.0

# PARAMETROS DO ALG. GENÉTICO
POP_SIZE = 100
ELITE_FRAC = 0.2
MUTANT_FRAC = 0.4
INHERIT_PROB = 0.6

# PARAMETROS DE INTERFACE GRÁFICA
CORES = {"PP": (100, 255, 255),"P": (255, 100, 100), "M": (100, 255, 100), "G": (100, 100, 255), "GG": (240, 240, 50)}
LARGURA_TELA, ALTURA_TELA = 1200, 700
BG = (30, 30, 30)
BRANCO = (255, 255, 255)
AMARELO = (255, 255, 0)

# ========= FUNÇÕES DO ALG. GENÉTICO  =========

def random_individual():
    # Gera um vetor de R^n onde cada componente pertece à [0,1]
    tamanho = sum(CAMISA_COUNTS.values())
    return [random.random() for _ in range(tamanho)]

def decode(individual):
    # Monta uma lista fixa com a demanda. Ex.: [P,P,M,M,M,G,G,G,G,GG]
    tipos_ordenados = []
    for tipo, qtd in CAMISA_COUNTS.items():
        tipos_ordenados.extend([tipo] * qtd)

    # Ordena índices pelo gene float (menor para maior)
    indices = range(len(individual))
    indices_ordenados = sorted( indices, key=lambda i: individual[i])

    # Sequência de camisas na ordem dos genes ordenados
    individuo_ordenado = [tipos_ordenados[i] for i in indices_ordenados]

    # Divide a sequencia, tentando ocupar todo o bin, na medida do possível
    bins = []
    current_bin = []
    current_sum = 0.0
    sobra_total = 0.0

    for i, tipo in enumerate(individuo_ordenado):
        size = ITEM_TYPES[tipo]
        if current_sum + size <= BIN_CAPACITY:
            current_bin.append((i, tipo, size))
            current_sum += size
        else:
            bins.append(current_bin)
            sobra_total += BIN_CAPACITY - current_sum
            current_bin = [(i, tipo, size)]
            current_sum = size

    if current_bin:
        bins.append(current_bin)
        sobra_total += BIN_CAPACITY - current_sum

    return bins, sobra_total

def fitness(individual):
    bins_usados, sobra = decode(individual)
    return sobra

def biased_crossover(elite, non_elite, inherit_prob=INHERIT_PROB):
    # Crossover clássico gene a gene
    child = []
    for e_gene, n_gene in zip(elite, non_elite):
        if random.random() < inherit_prob:
            child.append(e_gene)
        else:
            child.append(n_gene)
    return child

# ========= FUNÇÕES DE VISUALIZAÇÃO =========

def desenhar_grafico(historico, x, y, largura, altura, max_valor):
    if len(historico) < 2:
        return
    max_valor = max_valor if max_valor > 0 else 1
    pontos = len(historico)
    escala_y = altura / max_valor
    escala_x = largura / (pontos - 1)

    for i in range(pontos - 1):
        x1 = x + i * escala_x
        y1 = y + altura - historico[i] * escala_y
        x2 = x + (i + 1) * escala_x
        y2 = y + altura - historico[i + 1] * escala_y
        pygame.draw.line(screen, AMARELO, (x1, y1), (x2, y2), 2)

    pygame.draw.line(screen, BRANCO, (x, y), (x, y + altura), 2)
    pygame.draw.line(screen, BRANCO, (x, y + altura), (x + largura, y + altura), 2)

    texto_max = font.render(f"{max_valor:.2f}", True, BRANCO)
    screen.blit(texto_max, (x - texto_max.get_width() - 5, y))
import math
def desenhar_bins_e_grafico(bins, geracao, desperdicio, historico, max_desperdicio,
                            destaque=False, melhoria_valor=None, melhoria_bins=None):
    screen.fill(BG)
    bin_altura = 20  # Aumentei a altura para melhor visualização
    altura_disponivel = ALTURA_TELA - 100
    bins_por_coluna = altura_disponivel // bin_altura
    total_bins = len(bins)
    num_colunas = max(1, math.ceil(total_bins / bins_por_coluna))

    area_grafico = 250
    largura_coluna = (LARGURA_TELA - area_grafico) // num_colunas

    # CORREÇÃO PRINCIPAL: Aumentar significativamente a escala
    escala = largura_coluna / BIN_CAPACITY * 0.9  # Usar 90% da largura disponível
    
    # Garantir largura mínima para cada item
    largura_minima = 5

    for i, bin in enumerate(bins[:bins_por_coluna * num_colunas]):
        coluna = i // bins_por_coluna
        linha = i % bins_por_coluna
        x_inicial = 10 + coluna * (largura_coluna + 10)
        y = 10 + linha * bin_altura

        x_atual = x_inicial
        for _, tipo, tamanho in bin:
            largura = max(largura_minima, round(tamanho * escala))
            pygame.draw.rect(screen, CORES[tipo], (x_atual, y, largura, bin_altura - 4))
            
            if destaque:
                pygame.draw.rect(screen, BRANCO, (x_atual, y, largura, bin_altura - 4), 1)

            # Desenha a letra apenas se houver espaço suficiente
            if largura >= 15:  # Só desenha texto se tiver espaço
                letra = tipo
                letra_surface = font.render(letra, True, BRANCO)
                letra_rect = letra_surface.get_rect(center=(x_atual + largura // 2, y + (bin_altura - 4) // 2))
                screen.blit(letra_surface, letra_rect)

            x_atual += largura + 1

    # Resto do código permanece igual...
    # Info lateral à direita
    base_x = num_colunas * (largura_coluna + 10) + 10
    screen.blit(font.render(f"Geração: {geracao + 1}", True, BRANCO), (base_x, 20))
    screen.blit(font.render(f"Sobra: {desperdicio:.2f}m", True, BRANCO), (base_x, 50))
    screen.blit(font.render(f"Bins usados: {len(bins)}", True, BRANCO), (base_x, 80))

    if melhoria_valor is not None:
        screen.blit(font.render(f"-{melhoria_valor:.2f}", True, AMARELO), (base_x + 140, 50))
    if melhoria_bins is not None:
        screen.blit(font.render(f"-{melhoria_bins}", True, AMARELO), (base_x + 140, 80))

    desenhar_grafico(historico, base_x, 110, 180, 580, max_desperdicio)
    pygame.display.flip()

# ========= ALGORITMO PRINCIPAL =========
def brkga_visual(pop_size, elite_frac, mutant_frac, inherit_prob):
    population = [random_individual() for _ in range(pop_size)]
    elite_size = int(elite_frac * pop_size)
    mutant_size = int(mutant_frac * pop_size)
    melhor_desperdicio = float("inf")
    melhor_num_bins = float("inf")
    efeito_frames = 0
    melhoria_valor = None
    melhoria_bins = None
    historico_desperdicio = []

    geracao = 0
    rodando = True

    while rodando:
        # Eventos (permite fechar janela e sair com ESC)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                rodando = False

        # Avaliar população
        pop_fitness = [(fitness(ind), ind) for ind in population]
        pop_fitness.sort(key=lambda x: x[0])

        melhor = pop_fitness[0][1]
        desperdicio = pop_fitness[0][0]
        bins, _ = decode(melhor)
        num_bins = len(bins)

        historico_desperdicio.append(desperdicio)
        max_desperdicio = max(historico_desperdicio)

        if desperdicio < melhor_desperdicio:
            melhoria_valor = melhor_desperdicio - desperdicio
            melhoria_bins = melhor_num_bins - num_bins if num_bins < melhor_num_bins else None
            melhor_desperdicio = desperdicio
            melhor_num_bins = num_bins
            efeito_frames = 20

        if geracao % 50 == 0:
            desenhar_bins_e_grafico(
                bins, geracao, desperdicio, historico_desperdicio, max_desperdicio,
                destaque=efeito_frames > 0,
                melhoria_valor=melhoria_valor if efeito_frames > 0 else None,
                melhoria_bins=melhoria_bins if efeito_frames > 0 else None,
            )
            if efeito_frames > 0:
                efeito_frames -= 1

        # Nova população
        new_pop = [ind for _, ind in pop_fitness[:elite_size]]
        for _ in range(mutant_size):
            new_pop.append(random_individual())
        while len(new_pop) < pop_size:
            elite = random.choice(new_pop[:elite_size])
            non_elite = random.choice(population[elite_size:])
            filho = biased_crossover(elite, non_elite, inherit_prob)
            new_pop.append(filho)

        population = new_pop
        geracao += 1
        clock.tick(60)  # taxa de atualização

import time

def brgka_simples(num_geracoes, pop_size, elite_frac, mutant_frac, inherit_prob):
    
    population = [random_individual() for _ in range(pop_size)]
    elite_size = int(elite_frac * pop_size)
    mutant_size = int(mutant_frac * pop_size)

    melhor_individuo = None
    melhor_desperdicio = float("inf")

    for geracao in range(num_geracoes):
        # Avaliar população
        pop_fitness = [ (fitness(ind) , ind) for ind in population]
        pop_fitness.sort(key=lambda x: x[0])

        desperdicio_atual = pop_fitness[0][0]
        melhor_atual = pop_fitness[0][1]

        if desperdicio_atual < melhor_desperdicio:
            melhor_desperdicio = desperdicio_atual
            melhor_individuo = melhor_atual

        # Nova população
        new_pop = [ind for _, ind in pop_fitness[:elite_size]]
        for _ in range(mutant_size):
            new_pop.append(random_individual())
        while len(new_pop) < pop_size:
            elite = random.choice(new_pop[:elite_size])
            non_elite = random.choice(population[elite_size:])
            filho = biased_crossover(elite, non_elite, inherit_prob)
            new_pop.append(filho)

        population = new_pop

    # Decode final
    bins, desperdicio_final = decode(melhor_individuo)
    num_bins = len(bins)
    sequencia_de_corte = [ [tipo for _, tipo, _ in bin] for bin in bins]

    return num_bins, desperdicio_final, sequencia_de_corte

# ==================================================================
# ===================== EXECUÇÃO PRINCIPAL =========================
# ==================================================================

# ========= INTERFACE VISUAL =========
pygame.init()
screen = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("BRKGA - Bin Packing")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
brkga_visual(POP_SIZE, ELITE_FRAC, MUTANT_FRAC, INHERIT_PROB)
pygame.quit()
