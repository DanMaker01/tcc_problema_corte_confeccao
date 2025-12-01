import matplotlib.pyplot as plt
import numpy as np

# Dados
dados_seeds = [
    [50, 49, 49, 46, 46, 46, 46, 46, 46, 46],  # Seed 0
    [46, 43, 43, 43, 43, 43, 42, 42, 42, 42],  # Seed 1
    [50, 45, 45, 45, 45, 45, 45, 45, 45, 44],  # Seed 2
    [46, 46, 46, 46, 46, 46, 46, 43, 43, 43],  # Seed 3
    [46, 45, 45, 42, 42, 42, 42, 42, 42, 42],  # Seed 4
    [42, 42, 42, 42, 42, 42, 42, 42, 42, 42],  # Seed 5
    [46, 46, 46, 46, 46, 43, 43, 43, 43, 43],  # Seed 6
    [47, 46, 46, 46, 43, 43, 43, 43, 43, 43],  # Seed 7
    [43, 43, 43, 43, 43, 43, 43, 43, 43, 43],  # Seed 8
    [46, 46, 46, 46, 45, 45, 45, 45, 45, 45],  # Seed 9
    [45, 45, 43, 43, 43, 43, 43, 43, 43, 43],  # Seed 10
    [47, 47, 47, 47, 46, 46, 46, 45, 45, 45],  # Seed 11
    [46, 46, 45, 42, 42, 42, 42, 42, 42, 42],  # Seed 12
    [43, 43, 43, 43, 43, 43, 43, 43, 43, 43],  # Seed 13
    [46, 46, 46, 43, 43, 43, 43, 43, 43, 43],  # Seed 14
    [47, 46, 46, 45, 42, 42, 42, 42, 42, 42],  # Seed 15
    [49, 43, 43, 42, 42, 42, 42, 42, 42, 42],  # Seed 16
    [46, 46, 46, 46, 45, 45, 45, 44, 44, 44],  # Seed 17
    [45, 45, 45, 45, 45, 45, 42, 42, 42, 42],  # Seed 18
    [46, 46, 46, 46, 46, 46, 45, 45, 45, 43]   # Seed 19
]

# Calcular média, mínimo e máximo dos dados
dados_array = np.array(dados_seeds)
medias = np.mean(dados_array, axis=0).tolist()
minimos = np.min(dados_array, axis=0).tolist()
maximos = np.max(dados_array, axis=0).tolist()

# gerações
geracoes = list(range(10))

plt.figure(figsize=(14, 8))

# 1. Área transparente entre mínimo e máximo
plt.fill_between(geracoes, minimos, maximos, alpha=0.2, color='gray')

# 2. Linhas das seeds individuais - MAIS VISÍVEIS
cores = plt.cm.tab10(np.linspace(0, 1, 10))
for i, seed_data in enumerate(dados_seeds):
    plt.plot(geracoes, seed_data, 'o-', alpha=0.8, linewidth=1.5, markersize=4, 
             color=cores[i%len(cores)], label=f'Seed {i}', markeredgecolor='white', markeredgewidth=0.5)

# 3. Linha da média destacada
plt.plot(geracoes, medias, 's-', linewidth=3, markersize=10, color='red', 
         markerfacecolor='white', markeredgecolor='red', markeredgewidth=2, 
         label='Média', zorder=20)


# Configurações do gráfico
plt.xlabel('Geração', fontsize=12)
plt.ylabel('Fitness (Largura)', fontsize=12)
plt.title('Evolução do Fitness ao Longo das Gerações', fontsize=14)
plt.grid(True, alpha=0.3)
plt.ylim(40, 52)
plt.xticks(geracoes)
plt.yticks(range(40, 53, 2))

# Legenda completa com todas as seeds
plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1), frameon=True, fontsize=9)

plt.tight_layout()
plt.savefig('ispp_plotar_robustez.png', dpi=300, bbox_inches='tight')
plt.show()