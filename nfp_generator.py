# -----------------------------------------------------------------------
# Gerador de NFP --------------------------------------------------------
# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
# Dependências
# -----------------------------------------------------------------------
from shapely.geometry import Polygon, MultiPolygon
import pyclipper

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
def to_clipper_coords(polygon, scale=100000):
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
def from_clipper_coords(clipper_paths, scale=100000):
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
def calculate_nfp(polygon_a:Polygon, polygon_b:Polygon, ref_point_a=(0, 0), ref_point_b=(0, 0)):
    """
    Calcula o No-Fit Polygon (NFP) entre dois polígonos considerando pontos de referência.
    
    Args:
        polygon_a: Polígono de referência (fixo)
        polygon_b: Polígono que se move  
        ref_point_a: Ponto de referência do polígono A (default: origem)
        ref_point_b: Ponto de referência do polígono B (default: origem)
    
    Returns:
        O NFP mostrando as posições válidas do ponto de referência de B
    """
    
    if type(polygon_a) == list:
        polygon_a = Polygon(polygon_a)

    if type(polygon_b) == list:
        polygon_b = Polygon(polygon_b)

    # 1. Translada polígono A para que ref_point_a fique na origem
    a_translation_x = -ref_point_a[0]
    a_translation_y = -ref_point_a[1]
    
    centered_a_coords = [(x + a_translation_x, y + a_translation_y) 
                         for x, y in polygon_a.exterior.coords[:-1]]
    centered_a = Polygon(centered_a_coords)
    
    # Copiar buracos do polígono A se existirem
    if polygon_a.interiors:
        hole_paths = []
        for interior in polygon_a.interiors:
            hole_coords = [(x + a_translation_x, y + a_translation_y) 
                          for x, y in interior.coords[:-1]]
            hole_paths.append(hole_coords)
        centered_a = Polygon(centered_a_coords, holes=hole_paths)
    
    # 2. Translada polígono B para que ref_point_b fique na origem, depois reflete
    b_translation_x = -ref_point_b[0]
    b_translation_y = -ref_point_b[1]
    
    centered_b_coords = [(x + b_translation_x, y + b_translation_y) 
                         for x, y in polygon_b.exterior.coords[:-1]]
    
    # Reflete o polígono B em torno da origem
    reflected_b_coords = [(-x, -y) for x, y in centered_b_coords]
    reflected_b = Polygon(reflected_b_coords)
    
    # Copiar buracos do polígono B se existirem
    if polygon_b.interiors:
        hole_paths = []
        for interior in polygon_b.interiors:
            hole_coords = [(x + b_translation_x, y + b_translation_y) 
                          for x, y in interior.coords[:-1]]
            reflected_hole_coords = [(-x, -y) for x, y in hole_coords]
            hole_paths.append(reflected_hole_coords)
        reflected_b = Polygon(reflected_b_coords, holes=hole_paths)
    
    # 3. Converter para coordenadas do clipper
    subj_paths = to_clipper_coords(centered_a)
    clip_paths = to_clipper_coords(reflected_b)
    
    if not subj_paths or not clip_paths:
        return None

    # 4. Calcular NFP usando Minkowski Sum para o exterior
    subj_exterior_clipper = subj_paths[0]
    clip_exterior_clipper = clip_paths[0]
    
    nfp_exterior_paths = pyclipper.MinkowskiSum(subj_exterior_clipper, clip_exterior_clipper, True)
    nfp_centered = from_clipper_coords(nfp_exterior_paths)

    if nfp_centered is None:
        return None

    # 5. Tratar buracos (se houver)
    # Buracos do polígono A
    for i in range(1, len(subj_paths)):
        hole_minkowski_paths = pyclipper.MinkowskiSum(subj_paths[i], clip_exterior_clipper, True)
        hole_polygon = from_clipper_coords(hole_minkowski_paths)
        if hole_polygon and hole_polygon.is_valid:
            nfp_centered = nfp_centered.difference(hole_polygon)

    # Buracos do polígono B (refletidos)
    for i in range(1, len(clip_paths)):
        hole_minkowski_paths = pyclipper.MinkowskiSum(subj_exterior_clipper, clip_paths[i], True)
        hole_polygon = from_clipper_coords(hole_minkowski_paths)
        if hole_polygon and hole_polygon.is_valid:
            nfp_centered = nfp_centered.difference(hole_polygon)

    # 6. Translada o NFP de volta para a posição correta
    # O NFP mostra posições do ponto de referência de B
    # Precisamos compensar as translações feitas anteriormente
    if nfp_centered:
        # A translação final deve colocar o NFP na posição relativa correta
        final_translation_x = ref_point_a[0]  # Volta polígono A para posição original
        final_translation_y = ref_point_a[1]
        
        if isinstance(nfp_centered, MultiPolygon):
            translated_polygons = []
            for poly in nfp_centered.geoms:
                if poly.exterior:
                    exterior_coords = [(x + final_translation_x, y + final_translation_y) 
                                     for x, y in poly.exterior.coords[:-1]]
                    
                    holes = []
                    for interior in poly.interiors:
                        hole_coords = [(x + final_translation_x, y + final_translation_y) 
                                      for x, y in interior.coords[:-1]]
                        holes.append(hole_coords)
                    
                    translated_polygons.append(Polygon(exterior_coords, holes=holes))
            
            nfp_final = MultiPolygon(translated_polygons) if len(translated_polygons) > 1 else translated_polygons[0]
        else:
            if nfp_centered.exterior:
                exterior_coords = [(x + final_translation_x, y + final_translation_y) 
                                 for x, y in nfp_centered.exterior.coords[:-1]]
                
                holes = []
                for interior in nfp_centered.interiors:
                    hole_coords = [(x + final_translation_x, y + final_translation_y) 
                                  for x, y in interior.coords[:-1]]
                    holes.append(hole_coords)
                
                nfp_final = Polygon(exterior_coords, holes=holes)
            else:
                return None
        
        return nfp_final
    
    return None
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Exemplo
# --------------------------------------------------------------------------------
def plot_nfp_example(poly_a_coords, poly_b_coords, nfp_result, title):
    """
    Plota os polígonos A, B e o NFP resultante
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    poly_a = Polygon(poly_a_coords)
    poly_b = Polygon(poly_b_coords)
    # Plotar polígono A (fixo)
    if poly_a.exterior:
        exterior_coords = list(poly_a.exterior.coords)
        polygon_a = MplPolygon(exterior_coords, closed=True, alpha=0.7, color='blue', label='Polígono A (fixo)')
        ax.add_patch(polygon_a)
        
        # Marcar primeiro vértice do polígono A
        first_vertex_a = exterior_coords[0]
        ax.plot(first_vertex_a[0], first_vertex_a[1], 'bo', markersize=8, label='1º vértice A')
    
    # Plotar polígono B (móvel)
    if poly_b.exterior:
        exterior_coords = list(poly_b.exterior.coords)
        polygon_b = MplPolygon(exterior_coords, closed=True, alpha=0.7, color='red', label='Polígono B (móvel)')
        ax.add_patch(polygon_b)
        
        # Marcar primeiro vértice do polígono B
        first_vertex_b = exterior_coords[0]
        ax.plot(first_vertex_b[0], first_vertex_b[1], 'ro', markersize=8, label='1º vértice B')
    
    # Plotar NFP
    if nfp_result:
        if isinstance(nfp_result, MultiPolygon):
            for i, poly in enumerate(nfp_result.geoms):
                if poly.exterior:
                    exterior_coords = list(poly.exterior.coords)
                    nfp_patch = MplPolygon(exterior_coords, closed=True, alpha=0.5, 
                                         color='green', linestyle='--', linewidth=2, 
                                         fill=False, label='NFP' if i == 0 else "")
                    ax.add_patch(nfp_patch)
                    
                    # Marcar primeiro vértice do NFP
                    first_vertex_nfp = exterior_coords[0]
                    ax.plot(first_vertex_nfp[0], first_vertex_nfp[1], 'go', markersize=6, 
                           label='1º vértice NFP' if i == 0 else "")
        else:
            if nfp_result.exterior:
                exterior_coords = list(nfp_result.exterior.coords)
                nfp_patch = MplPolygon(exterior_coords, closed=True, alpha=0.5, 
                                     color='green', linestyle='--', linewidth=2, 
                                     fill=False, label='NFP')
                ax.add_patch(nfp_patch)
                
                # Marcar primeiro vértice do NFP
                first_vertex_nfp = exterior_coords[0]
                ax.plot(first_vertex_nfp[0], first_vertex_nfp[1], 'go', markersize=6, 
                       label='1º vértice NFP')
    
    # Configurações do gráfico
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # Ajustar limites automaticamente
    all_polygons = [poly_a, poly_b]
    if nfp_result:
        all_polygons.append(nfp_result)
    
    x_min, y_min, x_max, y_max = float('inf'), float('inf'), float('-inf'), float('-inf')
    for poly in all_polygons:
        bounds = poly.bounds
        x_min = min(x_min, bounds[0])
        y_min = min(y_min, bounds[1])
        x_max = max(x_max, bounds[2])
        y_max = max(y_max, bounds[3])
    
    margin = max(x_max - x_min, y_max - y_min) * 0.1
    ax.set_xlim(x_min - margin, x_max + margin)
    ax.set_ylim(y_min - margin, y_max + margin)
    
    plt.tight_layout()
    plt.show()
# --------------------------------------------------------------------------------
        
# --------------------------------------------------------------------------------
def run_teste_A():

    curvo = [(0,0),(3,0),(3,4),(0,4),(0,2),(1,2),(1,3),(2,3),(2,1),(0,1),]             # 0
    # quadrado = [(0,0),(0,0.9999999999),(0.9999999999,0.9999999999),(0.9999999999,0)]   # 1
    quadrado = [(0,0),(0,1),(1,1),(1,0)]                                               # 1
    
    nfp = calculate_nfp(curvo,quadrado)

    if nfp:
        plot_nfp_example(curvo,quadrado,nfp,"NFP_0,1")

if __name__ == '__main__':
    run_teste_A()
    