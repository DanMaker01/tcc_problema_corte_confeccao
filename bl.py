
# ---------------------------------------------
from typing import List, Tuple
from malha import Malha
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

# ---------------------------------------------
class Bottom_Left():
    def __init__(self, M:Malha, seq, NFP, DIFP):    # precisa passar o T?não! ##### implementar
        self.M : Malha = M
        self.NFP = NFP
        self.DIFP = DIFP
        self.seq_demanda = seq                      # seq = [0,0,1,1,2,2,2,2,3,3,4]
        pass

    def rodar(self):
        pecas_posicionadas = []                     # pecas = [(t,(x,y)), (t,(x,y)), ...]
        for i,t in enumerate(self.seq_demanda):
            S = self.DIFP[t]
            if len(S)<1:
                print("erro de IFP, refine a manhã ou aumente as dimensões")
            for r in pecas_posicionadas:
                u,vertice = r
                translacao = vertice
                NFP_tr = self._transladar_poligono(self.NFP[u,t],translacao)
                NFP_tr_discreto = self._discretizar_poligono(NFP_tr,self.M,S,somente_interior=True)
                S = self._remover_pontos(S,NFP_tr_discreto)
                if len(S)<1:
                    print(f"erro de NFP_{u}_{t}. não coube na malha.")
                    return []               # já mata?
            if len(S)<1:
                print(f"nao sobraram pontos para posicionar peça {i}. refine a malha ou aumente as dimensões")
                return []                   # já mata?
            else:
                vertice = self._escolhe_bottom_left(S)
                pecas_posicionadas.append((t,vertice))
        return pecas_posicionadas
    
    def _discretizar_poligono(self, poligono:Polygon, malha:Malha, pontos_a_verificar:list[Tuple],
                              somente_interior:bool=False, epsilon :float = 1e-6):
        
        adaptive_epsilon = max(epsilon,min(malha.gx(),malha.gy()) * 0.001)
        
        if somente_interior:
            poligono_robusto = poligono.buffer(-adaptive_epsilon) if poligono.area > adaptive_epsilon else poligono
        else:
            poligono_robusto = poligono.buffer(adaptive_epsilon)

        poligono_preparado = prep(poligono_robusto)

        minx, miny, maxx, maxy = poligono.bounds
        minx -= adaptive_epsilon
        miny -= adaptive_epsilon
        maxx += adaptive_epsilon
        maxy += adaptive_epsilon
        
        pontos_contidos = []
        for ponto in pontos_a_verificar: #### implementando
            # Pular pontos fora da bounding box
            x, y = ponto
            if not (minx <= x <= maxx and miny <= y <= maxy):
                continue
                
            # Teste robusto
            if poligono_preparado.contains(Point(ponto)):
                pontos_contidos.append(ponto)
            elif not somente_interior:
                # Para inclusão de borda, verificar proximidade
                if poligono.boundary.distance(Point(ponto)) <= adaptive_epsilon:
                    pontos_contidos.append(ponto)
        
        return pontos_contidos
    

    def _escolhe_bottom_left(self,S):
        '''
        conjunto de pontos S = {d0,d1,...,dN}
        '''
        if len(S) == 0:
            print("erro, não tem onde colocar.")
        else:
            # print(S)
            # return sorted(S)[0]
            return S[0] ##### não precisa nem ordenar
    def _transladar_poligono(self,poligono:Polygon, translacao: tuple) -> Polygon:        
        dx, dy = translacao
        return Polygon([(x + dx, y + dy) for x, y in poligono.exterior.coords])
    
    def _remover_pontos(self,pontos_base: list, pontos_a_remover: list) -> list:
        to_remove = set(pontos_a_remover)                   
        return [p for p in pontos_base if p not in to_remove]