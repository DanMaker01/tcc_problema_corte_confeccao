import matplotlib.pyplot as plt
import numpy as np

# Dados
dados_seeds = [
    [50,49,49,46,46,46,46,46,46,46, 46,43,43,43,43,43,43,43,43,43],  # 0
    [46,43,43,43,43,43,42,42,42,42, 42,42,42,42,42,42,42,42,42,42],  # 1
    [50,45,45,45,45,45,45,45,45,44, 43,43,43,43,43,43,43,43,43,42],  # 2
    [46,46,46,46,46,46,46,43,43,43, 43,43,43,43,43,43,43,43,43,43],  # 3
    [46,45,45,42,42,42,42,42,42,42, 42,42,42,42,42,42,42,42,42,42],  # 4
    [42,42,42,42,42,42,42,42,42,42, 42,42,42,42,42,42,42,42,42,42],  # 5
    [46,46,46,46,46,43,43,43,43,43, 43,43,43,43,43,43,43,43,43,43],  # 6
    [47,46,46,46,43,43,43,43,43,43, 43,43,43,43,43,43,43,43,43,43],  # 7
    [43,43,43,43,43,43,43,43,43,43, 42,42,42,42,42,42,42,42,42,42],  # 8
    [46,46,46,46,45,45,45,45,45,45, 43,43,43,43,43,43,43,43,43,43],  # 9
    [45,45,43,43,43,43,43,43,43,43, 43,42,42,42,42,42,42,42,42,42],  # 10
    [47,47,47,47,46,46,46,45,45,45, 45,45,45,45,45,43,43,43,43,43],  # 11
    [46,46,45,42,42,42,42,42,42,42, 42,42,42,42,42,42,42,42,42,42],  # 12
    [43,43,43,43,43,43,43,43,43,43, 43,43,43,43,42,42,42,42,42,42],  # 13
    [46,46,46,43,43,43,43,43,43,43, 43,43,43,43,43,43,42,42,42,42],  # 14
    [47,46,46,45,42,42,42,42,42,42, 42,42,42,42,42,42,42,42,42,42],  # 15
    [49,43,43,42,42,42,42,42,42,42, 42,42,42,42,42,42,42,42,42,42],  # 16
    [46,46,46,46,45,45,45,44,44,44, 43,43,43,43,43,43,43,43,43,43],  # 17
    [45,45,45,45,45,45,42,42,42,42, 42,42,42,42,42,42,42,42,42,42],  # 18
    [46,46,46,46,46,46,45,45,45,43, 43,43,43,43,43,43,43,43,43,43],  # 19
]

# Calcular média, mínimo e máximo
dados_array = np.array(dados_seeds)
medias = np.mean(dados_array, axis=0).tolist()
minimos = np.min(dados_array, axis=0).tolist()
maximos = np.max(dados_array, axis=0).tolist()

# gerações
geracoes = list(range(len(dados_seeds[0])))

plt.figure(figsize=(14, 8))

# 1. Região min–max
plt.fill_between(geracoes, minimos, maximos, alpha=0.2, color='gray')

# 2. Curvas
plt.plot(geracoes, minimos, '--', linewidth=2, color='blue',  label='Mínimo')
plt.plot(geracoes, maximos, '--', linewidth=2, color='green', label='Máximo')
plt.plot(geracoes, medias, 's-', linewidth=3, markersize=9, color='red',
         markerfacecolor='white', markeredgecolor='red', markeredgewidth=2,
         label='Média', zorder=20)

# Configurações
plt.xlabel('Geração', fontsize=12)
plt.ylabel('Fitness (Comprimento)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.ylim(40, 52)
plt.xticks(geracoes)
plt.yticks(range(40, 53, 2))

# Legenda **dentro** do gráfico
plt.legend(loc='upper right', frameon=True, fontsize=10)

plt.tight_layout()
plt.savefig('ispp_plotar_robustez_min_max_media.png', dpi=300, bbox_inches='tight')
plt.show()
