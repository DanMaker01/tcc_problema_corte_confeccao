import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

cores = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 
         'pink', 'gray', 'olive', 'cyan', 'magenta', 'yellow',
         'navy', 'teal', 'coral', 'indigo']

T_marques = [
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

multiplicidade = [2, 2, 1, 1, 2, 2, 1, 1]

# Expandir sequência considerando multiplicidades
pecas_expandido = []
tipos_expandido = []

tipos = {}
tipo_id = 0
tipo_da_peca = []

for poly in T_marques:
    tup = tuple(poly)
    if tup not in tipos:
        tipos[tup] = tipo_id
        tipo_id += 1
    tipo_da_peca.append(tipos[tup])

for poly, tipo, mult in zip(T_marques, tipo_da_peca, multiplicidade):
    for _ in range(mult):
        pecas_expandido.append(poly)
        tipos_expandido.append(tipo)

# Plotagem em duas linhas
plt.figure(figsize=(30, 16), dpi=300)

x_offset = 0
y_offset = 0
spacing_x = 10
spacing_y = 30
line_width = 190  # largura máxima da linha

for poly, tipo in zip(pecas_expandido, tipos_expandido):
    # altura da peça
    max_y_poly = max(y for _, y in poly)
    
    # se passar da largura da linha, pular para próxima linha
    if x_offset + max(x for x, _ in poly) > line_width:
        x_offset = 0
        y_offset += spacing_y + max_y_poly

    shifted = [(x + x_offset, y + y_offset) for (x, y) in poly]

    patch = Polygon(
        shifted, closed=True, edgecolor='black',
        facecolor=cores[tipo % len(cores)], alpha=0.7
    )
    plt.gca().add_patch(patch)

    min_x = min(x for x, _ in shifted)
    max_x = max(x for x, _ in shifted)
    min_y = min(y for _, y in shifted)
    max_y = max(y for _, y in shifted)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2  # centro vertical

    # texto no centro da peça
    plt.text(cx, cy, f"{tipo}",
             ha='center', va='center',
             fontsize=20, weight='bold', color='black')

    x_offset += (max_x - min_x) + spacing_x

plt.axis('equal')
plt.axis('off')
plt.title("T = Marques", fontsize=24)
plt.savefig("T_marques.png", dpi=300, bbox_inches='tight')
plt.show()
