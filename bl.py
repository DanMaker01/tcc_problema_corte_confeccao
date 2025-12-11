
# ---------------------------------------------
from typing import List, Tuple
from shapely.geometry import Polygon, Point, MultiPoint
from shapely.affinity import translate
from shapely.prepared import prep
import numpy as np


# ---------------------------------------------
class Bottom_Left():
    def __init__(self, W,L,R,C, seq, NFP, DIFP):
        self.W=W
        self.L=L
        self.R=R
        self.C=C
        self.seq_demanda = seq  # seq = [0,0,1,1,2,2,2,2,3,3,4]
        self.NFP = NFP
        self.DIFP = DIFP
        
        # Pré-cálculo de parâmetros da malha
        self.gx = L/(C-1)
        self.gy = W/(R-1)
        self.epsilon = 1e-6
        self.adaptive_epsilon = max(self.epsilon, min(self.gx, self.gy) * 0.001)
        pass

    def rodar(self,verbose = False):
        pecas_posicionadas = []                     # pecas = [(t,(x,y)), (t,(x,y)), ...]
        for i,t in enumerate(self.seq_demanda):
            # Converter a lista de pontos S para um array NumPy
            S_list = [p[1] for p in self.DIFP[t]]
            S_array = np.array(S_list)
            
            if S_array.size == 0:
                print("erro de IFP, refine a manhã ou aumente as dimensões")
                return []
                
            for r in pecas_posicionadas:
                u, vertice = r
                translacao = vertice
                
                # 1. Translação do NFP
                NFP_poly = Polygon(self.NFP[u,t])
                NFP_tr = translate(NFP_poly, xoff=translacao[0], yoff=translacao[1])
                
                # 2. Discretização e remoção de pontos (vetorizado)
                # O método _discretizar_poligono_np agora retorna um array booleano
                # indicando quais pontos em S_array estão DENTRO do NFP_tr.
                pontos_invalidos_mask = self._discretizar_poligono_np(NFP_tr, S_array, somente_interior=True)
                
                # A máscara é True para pontos a serem removidos (dentro do NFP)
                # Usamos a negação (~) para manter apenas os pontos válidos (fora do NFP)
                S_array = S_array[~pontos_invalidos_mask]
                
                if S_array.size == 0:
                    if verbose:
                        print(f"após NFP_{u}_{t}, a peça {t} não coube. refine a malha ou aumente as dimensões.",end="")
                    return []
                    
            if S_array.size == 0:
                if verbose:
                    print(f"RARO: nao sobraram pontos para posicionar peça {t}. refine a malha ou aumente as dimensões")
                return []
            else:
                # O vertice escolhido é o primeiro ponto no array NumPy, convertido de volta para tupla
                vertice = tuple(S_array[0])
                pecas_posicionadas.append((t,vertice))
                
        return pecas_posicionadas

    def _discretizar_poligono_np(self, poligono:Polygon, pontos_a_verificar:np.ndarray,
                                 somente_interior:bool=False) -> np.ndarray:
        '''
        Versão otimizada que recebe e retorna arrays NumPy.
        Retorna uma máscara booleana (True para pontos contidos/a remover).
        A checagem de borda (lenta) foi removida, pois o algoritmo BL só precisa da checagem de interior (somente_interior=True) para NFP.
        '''
        
        if somente_interior:
            poligono_robusto = poligono.buffer(-self.adaptive_epsilon) if poligono.area > self.adaptive_epsilon else poligono
        else:
            poligono_robusto = poligono.buffer(self.adaptive_epsilon)

        # Usar MultiPoint para checagem vetorizada
        # Nota: A criação de MultiPoint pode ser lenta para um número muito grande de pontos,
        # mas é muito mais rápida do que criar Point por ponto e chamar .contains().
        
        # 1. Bounding Box Check (ainda é mais rápido em NumPy)
        minx, miny, maxx, maxy = poligono.bounds
        minx -= self.adaptive_epsilon
        miny -= self.adaptive_epsilon
        maxx += self.adaptive_epsilon
        maxy += self.adaptive_epsilon
        
        # Máscara inicial para pontos dentro da Bounding Box
        bbox_mask = (pontos_a_verificar[:, 0] >= minx) & \
                    (pontos_a_verificar[:, 0] <= maxx) & \
                    (pontos_a_verificar[:, 1] >= miny) & \
                    (pontos_a_verificar[:, 1] <= maxy)
        
        # Pontos que precisam de checagem geométrica (dentro da BBox)
        pontos_para_checar = pontos_a_verificar[bbox_mask]
        
        if pontos_para_checar.size == 0:
            return np.zeros(pontos_a_verificar.shape[0], dtype=bool)

        # 2. Checagem Geométrica (Shapely/GEOS)
        # Criação de MultiPoint
        multi_point = MultiPoint(pontos_para_checar)
        
        # Checagem de contenção
        # O método .within() de MultiPoint é a forma mais eficiente de checar
        # a contenção de múltiplos pontos em um polígono com Shapely.
        # No entanto, para garantir a corretude do algoritmo de empacotamento,
        # que depende da precisão do buffer negativo, vamos usar a checagem
        # de contenção ponto a ponto, mas apenas para os pontos dentro da BBox,
        # para garantir a equivalência com a lógica original robusta.
        
        # Otimização: Criar um array de objetos Point para checagem
        points_to_check = [Point(p) for p in pontos_para_checar]
        
        # Preparar o polígono para checagem rápida
        poligono_preparado = prep(poligono_robusto)
        
        # Checagem de contenção (list comprehension é mais rápido que loop puro)
        pontos_contidos_mask_check = np.array([poligono_preparado.contains(p) for p in points_to_check], dtype=bool)
        
        # 3. Reconstrução da Máscara
        # Criar a máscara final com o tamanho original
        final_mask = np.zeros(pontos_a_verificar.shape[0], dtype=bool)
        
        # Atribuir os resultados da checagem geométrica apenas para os pontos que estavam na BBox
        final_mask[bbox_mask] = pontos_contidos_mask_check
        

        
        return final_mask
    
    
    def _escolhe_bottom_left(self,S):
        '''
        conjunto de pontos S = array NumPy
        '''
        if S.size == 0:
            print("erro, não tem onde colocar.")
            return None
        else:
            return tuple(S[0]) # retorna o primeiro elemento como tupla
            
    def _transladar_poligono(self,poligono:Polygon, translacao: tuple) -> Polygon:        
        dx, dy = translacao
        # Usando a função translate do shapely.affinity
        return translate(poligono, xoff=dx, yoff=dy)
    
    # O método _remover_pontos não é mais necessário, pois a remoção é feita
    # diretamente com indexação booleana do NumPy em rodar().
    # def _remover_pontos(self, pontos_base: list, pontos_a_remover: list) -> list:
    #     to_remove = set(map(tuple, pontos_a_remover))
    #     return [p for p in pontos_base if tuple(p) not in to_remove]
