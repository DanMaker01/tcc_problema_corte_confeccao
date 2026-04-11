# ---------------------------------------------
from typing import List, Tuple
from shapely.geometry import Polygon, Point
from shapely.affinity import translate
from shapely.prepared import prep
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MplPolygon

# ---------------------------------------------
class Bottom_Left():
    def __init__(self, W, L, R, C, seq, NFP, DIFP, T=None, debug=False):
        self.W = W
        self.L = L
        self.R = R
        self.C = C
        self.seq_demanda = seq
        self.DIFP = DIFP
        self.T = T
        self.debug = debug
        self.debug_step = 0
        
        # PRÉ-CALCULA TODOS OS NFPs
        self.nfp_cache = {}  # {key: (poligono_prep, bounds)}
        for key, coords in NFP.items():
            poly = Polygon(coords)
            # Prepara o polígono reduzido para checagem
            if poly.area > 1e-9:
                poly_robusto = poly.buffer(-1e-7)
            else:
                poly_robusto = poly
            self.nfp_cache[key] = (prep(poly_robusto), poly.bounds)
        
        # Parâmetros da malha
        self.gx = L/(C-1)
        self.gy = W/(R-1)
        self.epsilon = 1e-6
        self.adaptive_epsilon = max(self.epsilon, min(self.gx, self.gy) * 0.001)
    
    def _plot_pontos(self, pontos, cor='blue', marker='o', size=20, label=None):
        """Plota pontos no gráfico atual."""
        if len(pontos) > 0:
            x = [p[0] for p in pontos]
            y = [p[1] for p in pontos]
            plt.scatter(x, y, c=cor, marker=marker, s=size, alpha=0.6, label=label)
    
    def _plot_poligono(self, poligono, cor, alpha=0.3, label=None):
        """Plota um polígono no gráfico atual."""
        if isinstance(poligono, Polygon):
            x, y = poligono.exterior.xy
            plt.fill(x, y, alpha=alpha, fc=cor, ec='black', linewidth=1, label=label)
    
    def _plot_peca(self, peca_tipo, posicao, cor='green', alpha=0.5):
        """Plota uma peça posicionada."""
        poligono = Polygon(self.T[peca_tipo])
        poligono_transladado = translate(poligono, xoff=posicao[0], yoff=posicao[1])
        self._plot_poligono(poligono_transladado, cor, alpha, label=f'Peça {peca_tipo}')
        
        # Adiciona texto com o tipo
        centro = poligono_transladado.centroid
        plt.text(centro.x, centro.y, f'{peca_tipo}', 
                ha='center', va='center', fontsize=8, fontweight='bold')
    
    def _plot_nfp(self, nfp_prep, bounds, translacao, cor='red', alpha=0.2):
        """Plota um NFP transladado."""
        # Reconstrói o polígono NFP a partir dos bounds (aproximado)
        minx, miny, maxx, maxy = bounds
        minx += translacao[0]
        miny += translacao[1]
        maxx += translacao[0]
        maxy += translacao[1]
        
        retangulo = patches.Rectangle((minx, miny), maxx-minx, maxy-miny, 
                                      linewidth=2, edgecolor=cor, 
                                      facecolor=cor, alpha=alpha)
        plt.gca().add_patch(retangulo)
    
    def _plot_estado_atual(self, t, pecas_posicionadas, S_array, pontos_antes_nfp=None, 
                           nfp_key=None, nfp_bounds=None, pos_u=None):
        """Plota o estado atual do algoritmo."""
        self.debug_step += 1
        
        plt.figure(figsize=(14, 10))
        
        # Desenha o container
        container = patches.Rectangle((0, 0), self.L, self.W, linewidth=3, 
                                      edgecolor='black', facecolor='none', 
                                      linestyle='--', label='Container')
        plt.gca().add_patch(container)
        
        # Desenha peças já posicionadas
        for tipo_u, pos_u_plot in pecas_posicionadas:
            self._plot_peca(tipo_u, pos_u_plot, 'lightgreen', 0.5)
        
        # Desenha pontos antes do NFP (se houver)
        if pontos_antes_nfp is not None and len(pontos_antes_nfp) > 0:
            self._plot_pontos(pontos_antes_nfp, 'blue', 'o', 30, 'Pontos antes do NFP')
        
        # Desenha NFP atual (se houver)
        if nfp_key is not None and nfp_bounds is not None and pos_u is not None:
            self._plot_nfp(None, nfp_bounds, pos_u, 'red', 0.15)
            plt.text(pos_u[0], pos_u[1], f'NFP_{nfp_key}', 
                    fontsize=10, color='red', fontweight='bold')
        
        # Desenha pontos após NFP
        if len(S_array) > 0:
            self._plot_pontos(S_array, 'green', 's', 40, 'Pontos válidos')
        
        # Destaca o ponto escolhido
        if len(S_array) > 0:
            indices_ordenados = np.lexsort((S_array[:, 1], S_array[:, 0]))
            ponto_escolhido = S_array[indices_ordenados[0]]
            plt.scatter(ponto_escolhido[0], ponto_escolhido[1], c='red', marker='*', 
                       s=200, zorder=5, label='Ponto escolhido')
        
        # Desenha a peça a ser posicionada (transparente)
        if len(S_array) > 0:
            poligono_peca = Polygon(self.T[t])
            poligono_transladado = translate(poligono_peca, 
                                            xoff=ponto_escolhido[0], 
                                            yoff=ponto_escolhido[1])
            self._plot_poligono(poligono_transladado, 'orange', 0.3, f'Peça {t} (nova)')
        
        # Configurações do gráfico
        plt.xlabel('X (Comprimento)', fontsize=12)
        plt.ylabel('Y (Altura)', fontsize=12)
        plt.title(f'Passo {self.debug_step}: Posicionando peça {t}\n'
                  f'Peças já posicionadas: {len(pecas_posicionadas)} | '
                  f'Pontos candidatos: {len(S_array)}', 
                  fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.xlim(-5, self.L + 5)
        plt.ylim(-5, self.W + 5)
        plt.legend(loc='upper right', fontsize=8)
        plt.gca().set_aspect('equal')
        
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def rodar(self, verbose=False):
        pecas_posicionadas = []
        
        for t in self.seq_demanda:
            # print(f"\n{'='*60}")
            # print(f"Posicionando peça tipo {t}")
            # print(f"{'='*60}")
            
            pontos = self.DIFP[t]
            
            if not pontos:
                print(f"ERRO: IFP vazio para peça {t}")
                return []
            
            S_array = np.array(pontos, dtype=float)
            # print(f"Pontos iniciais no IFP: {len(S_array)}")
            
            if self.debug:
                self._plot_estado_atual(t, pecas_posicionadas, S_array, 
                                       pontos_antes_nfp=pontos,
                                       nfp_key=None, nfp_bounds=None, pos_u=None)
            
            # Aplica restrições dos NFPs das peças já posicionadas
            for tipo_u, pos_u in pecas_posicionadas:
                nfp_key = (tipo_u, t)
                if nfp_key not in self.nfp_cache:
                    print(f"ERRO: NFP ({tipo_u},{t}) não encontrado")
                    return []
                
                # print(f"\n  Aplicando NFP com peça {tipo_u} em {pos_u}")
                
                nfp_prep, (minx, miny, maxx, maxy) = self.nfp_cache[nfp_key]
                
                # Salva pontos antes do NFP para debug
                pontos_antes = S_array.copy() if self.debug else None
                
                # Translada os bounds
                minx += pos_u[0] - self.adaptive_epsilon
                miny += pos_u[1] - self.adaptive_epsilon
                maxx += pos_u[0] + self.adaptive_epsilon
                maxy += pos_u[1] + self.adaptive_epsilon
                
                # Filtro bounding box rápido
                bbox_mask = (S_array[:, 0] >= minx) & (S_array[:, 0] <= maxx) & \
                            (S_array[:, 1] >= miny) & (S_array[:, 1] <= maxy)
                
                pontos_bbox = S_array[bbox_mask]
                # print(f"    Pontos dentro do bounding box do NFP: {len(pontos_bbox)}")
                
                if len(pontos_bbox) > 0:
                    # Verifica pontos dentro do NFP transladado
                    dentro = []
                    for p in pontos_bbox:
                        p_trans = (p[0] - pos_u[0], p[1] - pos_u[1])
                        if nfp_prep.covers(Point(p_trans)):
                            dentro.append(True)
                            # print(f"    Ponto {p} está DENTRO do NFP")
                        else:
                            dentro.append(False)
                    
                    # Aplica máscara
                    mascara_remover = np.zeros(len(S_array), dtype=bool)
                    mascara_remover[bbox_mask] = dentro
                    S_array = S_array[~mascara_remover]
                    
                    # print(f"    Pontos removidos: {sum(dentro)}")
                    # print(f"    Pontos restantes: {len(S_array)}")
                
                if self.debug:
                    self._plot_estado_atual(t, pecas_posicionadas, S_array,
                                           pontos_antes_nfp=pontos_antes,
                                           nfp_key=nfp_key, nfp_bounds=self.nfp_cache[nfp_key][1],
                                           pos_u=pos_u)
                
                if len(S_array) == 0:
                    if verbose:
                        print(f"Peça {t} não coube após NFP com peça {tipo_u}")
                    return []
            
            if len(S_array) == 0:
                if verbose:
                    print(f"Peça {t} não tem posições disponíveis")
                return []
            
            # Ordenação left-bottom (primeiro x, depois y)
            indices_ordenados = np.lexsort((S_array[:, 1], S_array[:, 0]))
            vertice = tuple(S_array[indices_ordenados[0]])
            
            # print(f"\nPontos candidatos finais: {len(S_array)}")
            # print(f"\n✓ Peça {t} posicionada em ({vertice[0]:.2f}, {vertice[1]:.2f})")
            
            pecas_posicionadas.append((t, vertice))
            
            if self.debug:
                # Mostra estado final após posicionar
                plt.figure(figsize=(14, 10))
                container = patches.Rectangle((0, 0), self.L, self.W, linewidth=3,
                                            edgecolor='black', facecolor='none',
                                            linestyle='--')
                plt.gca().add_patch(container)
                
                for tipo_u, pos_u in pecas_posicionadas:
                    self._plot_peca(tipo_u, pos_u, 'lightgreen', 0.5)
                
                plt.xlabel('X (Comprimento)', fontsize=12)
                plt.ylabel('Y (Altura)', fontsize=12)
                plt.title(f'Estado após posicionar peça {t} - Total: {len(pecas_posicionadas)} peças',
                         fontsize=14, fontweight='bold')
                plt.grid(True, alpha=0.3, linestyle='--')
                plt.xlim(-5, self.L + 5)
                plt.ylim(-5, self.W + 5)
                plt.gca().set_aspect('equal')
                plt.tight_layout()
                plt.show()
                plt.close()
        
        # print(f"\n{'='*60}")
        # print(f"Posicionamento concluído! Total de peças: {len(pecas_posicionadas)}")
        # print(f"{'='*60}")
        
        return pecas_posicionadas