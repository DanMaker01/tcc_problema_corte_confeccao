# Gerador de IFP
# Funcionando 19/10


import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LinearRing
import pyclipper

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

def to_clipper_coords(polygon, scale=10000000):
    """
    Converte um polígono Shapely (exterior e interiores) para o formato de coordenadas inteiras esperado pelo pyclipper.
    Retorna uma lista de caminhos (Path), onde o primeiro é o exterior e os subsequentes são os interiores.
    """
    paths = []
    if isinstance(polygon, Polygon):
        # Exterior
        if polygon.exterior:
            paths.append([[int(x * scale), int(y * scale)] for x, y in polygon.exterior.coords[:-1]])
        # Interiores (buracos)
        for interior in polygon.interiors:
            paths.append([[int(x * scale), int(y * scale)] for x, y in interior.coords[:-1]])
    return paths

def from_clipper_coords(clipper_paths, scale=10000000):
    """
    Converte caminhos do formato pyclipper (coordenadas inteiras) de volta para Shapely Polygon ou MultiPolygon.
    Lida com múltiplos caminhos que podem formar um polígono com buracos ou um MultiPolygon.
    """
    polygons = []
    for path in clipper_paths:
        if len(path) >= 3:  # Um polígono precisa de pelo menos 3 pontos
            coords = [(x / scale, y / scale) for x, y in path]
            polygons.append(Polygon(coords))
    
    if not polygons:
        return None
    elif len(polygons) == 1:
        return polygons[0]
    else:
        # Tenta construir um MultiPolygon ou um Polygon com buracos
        # Esta lógica pode precisar de refinamento para casos complexos de buracos aninhados ou múltiplos anéis.
        # Por simplicidade, vamos unir todos os polígonos resultantes.
        result = polygons[0]
        for i in range(1, len(polygons)):
            result = result.union(polygons[i])
        return result
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


def calculate_ifp(container_rectangle: Polygon, piece_polygon: Polygon) -> Polygon:
    """
    Versão simplificada do IFP para comparação - baseada apenas na bounding box.
    """
    
    # Converter para Polygon se forem listas de pontos
    if not isinstance(piece_polygon, Polygon):
        piece_polygon = Polygon(piece_polygon)
    
    if not isinstance(container_rectangle, Polygon):
        container_rectangle = Polygon(container_rectangle)
    # Extrair largura e altura do container
    min_x, min_y, max_x, max_y = container_rectangle.bounds
    container_width = max_x - min_x
    container_height = max_y - min_y
    
    # Calcular bounding box da peça
    piece_bounds = piece_polygon.bounds
    piece_width = piece_bounds[2] - piece_bounds[0]
    piece_height = piece_bounds[3] - piece_bounds[1]
    
    # Calcular os limites para o ponto de referência (primeiro vértice)
    left_limit = -piece_bounds[0]
    right_limit = container_width - piece_bounds[2]
    bottom_limit = -piece_bounds[1]
    top_limit = container_height - piece_bounds[3]
    
    # Verificar se há solução válida
    if left_limit > right_limit or bottom_limit > top_limit:
        return Polygon()
    
    # Criar polígono retangular do IFP
    result_vertices = [
        (left_limit, bottom_limit),
        (right_limit, bottom_limit),
        (right_limit, top_limit),
        (left_limit, top_limit),
        (left_limit, bottom_limit)
    ]
    
    return Polygon(result_vertices)

def plot_on_axis(ax, container, piece, ifp_result, title):
    """Função auxiliar para plotar em um axis específico"""
    # Plotar container
    if container.exterior:
        exterior_coords = list(container.exterior.coords)
        container_patch = MplPolygon(exterior_coords, closed=True, alpha=0.7, color='blue', label='Container')
        ax.add_patch(container_patch)
    
    # Plotar peça
    if piece.exterior:
        exterior_coords = list(piece.exterior.coords)
        piece_patch = MplPolygon(exterior_coords, closed=True, alpha=0.7, color='red', label='Peça')
        ax.add_patch(piece_patch)
    
    # Plotar IFP
    if ifp_result and not ifp_result.is_empty:
        if isinstance(ifp_result, MultiPolygon):
            for poly in ifp_result.geoms:
                if poly.exterior:
                    exterior_coords = list(poly.exterior.coords)
                    ifp_patch = MplPolygon(exterior_coords, closed=True, alpha=0.5, 
                                         color='green', linestyle='--', linewidth=2, 
                                         fill=False, label='IFP')
                    ax.add_patch(ifp_patch)
        else:
            if ifp_result.exterior:
                exterior_coords = list(ifp_result.exterior.coords)
                ifp_patch = MplPolygon(exterior_coords, closed=True, alpha=0.5, 
                                     color='green', linestyle='--', linewidth=2, 
                                     fill=False, label='IFP')
                ax.add_patch(ifp_patch)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # Ajustar limites
    all_polygons = [container, piece]
    if ifp_result and not ifp_result.is_empty:
        all_polygons.append(ifp_result)
    
    x_min, y_min, x_max, y_max = float('inf'), float('inf'), float('-inf'), float('-inf')
    for poly in all_polygons:
        if poly and poly.is_valid and not poly.is_empty:
            minx, miny, maxx, maxy = poly.bounds
            x_min = min(x_min, minx)
            y_min = min(y_min, miny)
            x_max = max(x_max, maxx)
            y_max = max(y_max, maxy)
    
    if x_min != float('inf'):
        margin = 0.1 * max(x_max - x_min, y_max - y_min)
        ax.set_xlim(x_min - margin, x_max + margin)
        ax.set_ylim(y_min - margin, y_max + margin)


def exemplo_1():
    # Exemplo de uso: Container retangular e peça retangular
    container_height = 5  # W
    container_width = 6  # L
    container_polygon_rect = Polygon([(0, 0), (container_width, 0), (container_width, container_height), (0, container_height)])

    # Diferentes exemplos de peças para teste
    piece_examples = [
        Polygon([(0,0), (3,0), (3,2), (2,2), (2,1), (1,1), (1,2), (0,2)]),  # Peça com recorte
        Polygon([(0.0, 0.0), (1.1, 2.1), (0.9, 2.1)]),  # Triângulo
        Polygon([(0,0),(1,-1),(1,1)]),  # Triângulo assimétrico
        Polygon([(0,0), (2,0), (2,1), (0,1)])  # Retângulo 
    ]
    
    titles = [
        "Peça com Recorte",
        "Triângulo",
        "Triângulo Assimétrico", 
        "Retângulo"
    ]
    
    for i, (piece_polygon, title) in enumerate(zip(piece_examples, titles)):
        # Calcular IFP
        ifp_result = calculate_ifp(container_polygon_rect, piece_polygon)
        
        print(f"\n=== {title} ===")
        print(f"Container: {container_polygon_rect.bounds}")
        print(f"Peça: {piece_polygon.bounds}")
        print(f"IFP: {ifp_result.bounds if not ifp_result.is_empty else 'Vazio'}")
        
        # Plotar o resultado
        fig, ax = plt.subplots(figsize=(10, 8))
        plot_on_axis(ax, container_polygon_rect, piece_polygon, ifp_result, f'IFP - {title}')
        plt.tight_layout()
        plt.savefig(f"ifp_exemplo1_{i+1}.png")
        plt.show()
        plt.close()

def exemplo_2():
    # Exemplo de uso: Container retangular e peças complexas
    container_height = 4900  # W
    container_width = 8000  # L
    container_polygon_rect = Polygon([(0, 0), (container_width, 0), (container_width, container_height), (0, container_height)])

    tipos_t = [
        [(0,86), (966,142), (1983,0), (2185,238), (2734,217), (3000,767), (2819,900),
        (2819,1360), (3000,1493), (2734,2043), (2185,2022), (1983,2260), (966,2118), (0,2174)],

        [(0,0), (3034,0), (3034,261), (0,261)],

        [(0,173), (1761,0), (2183,650), (2183,1010), (1761,1660), (0,1487)],

        [(74,0), (870,119), (1666,0), (1740,125), (870,305), (0,125)],

        [(0,0), (411,65), (800,0), (1189,65), (1600,0), (1500,368), (800,286), (100,368)],

        [(0,0), (936,0), (936,659), (0,659)],

        [(56,73), (1066,143), (1891,0), (2186,288), (2573,241), (2676,926), (2594,1366), (0,1366)],

        [(0,0), (2499,0), (2705,387), (2622,934), (2148,967), (1920,1152), (1061,1059), (0,1125)]
    ]
    
    # Calcular IFP para cada tipo
    lista_ifp = []
    for i, t in enumerate(tipos_t):
        piece_polygon = Polygon(t)
        
        print(f"\n=== Tipo {i+1} ===")
        print(f"Peça bounds: {piece_polygon.bounds}")
        print(f"Container bounds: {container_polygon_rect.bounds}")
        
        # Calcular IFP
        ifp_result = calculate_ifp(container_polygon_rect, piece_polygon)
        lista_ifp.append(ifp_result)
        
        print(f"IFP: {ifp_result.bounds if not ifp_result.is_empty else 'Vazio'}")
        
        # Plotar resultado
        fig, ax = plt.subplots(figsize=(12, 10))
        plot_on_axis(ax, container_polygon_rect, piece_polygon, ifp_result, f'IFP - Tipo {i+1}')
        plt.tight_layout()
        plt.savefig(f"ifp_tipo_{i+1}.png")
        plt.show()
        plt.close()
    
    # Resumo final
    print(f"\n=== RESUMO FINAL ===")
    print(f"Total de peças processadas: {len(tipos_t)}")
    for i, ifp in enumerate(lista_ifp):
        status = "VÁLIDO" if not ifp.is_empty else "INVÁLIDO (não cabe)"
        print(f"Tipo {i+1}: {status}")


if __name__ == '__main__':
    
    exemplo_1()
    exemplo_2()
    
    
