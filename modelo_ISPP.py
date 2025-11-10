# --------------------------------------------
from brkga import BRKGA_ordem
from bl import Bottom_Left
from typing import List, Tuple
# --------------------------------------------

# --------------------------------------------
class Modelo_ISPP:
    def __init__(self,W,L,R,C,T:list,q:list):
        existe_solucao = self._verificar_requisitos_para_modelo(W,L,R,C,T,q)
        if not existe_solucao:
            print("modelo ISPP não cumpre requisitos para ter solução:",W,L,R,C)
        # malha
        self.W = W
        self.L = L
        self.R = R
        self.C = C
        # modelo
        self.T = T
        self.q = q
        self.NFP    : dict
        self.IFP_D  : list
        # extra
        self.sequencias_resolvidas={}
        pass
    # Principal -----------------------------------------------
    def rodar(self):
        brkga_resultado_strip = self._iniciar_brkga_ordem(100,0.3,0.4,generations=1)   # acha a faixa de menor comprimento
        return brkga_resultado_strip                                    # resultado = (melhor_sequencia, melhor_fitness)    
    # Sub-rotinas ---------------------------------------------
    def _verificar_requisitos_para_modelo(self,W,L,R,C,T,q):
        if W <= 0 or L<=0 or R <=0 or C <=0:
            return False
        if T in [None, [],{}]:
            return False
        if q in [None,[],{}]:
            return False
        return True
    def _iniciar_brkga_ordem(self, pop_size=100,elite_frac=0.3,mutant_frac=0.4, generations=10):
        print("iniciando brkga-ordem, para achar a menor faixa, dados T, q e Malha.")
        brkga_ordem = BRKGA_ordem(sum(self.q), self._rodar_BL,pop_size=pop_size,
                                  mutant_frac=mutant_frac,elite_frac=elite_frac,seed=42)
        brkga_resultado = brkga_ordem.evolve(self.q, generations=generations)
        return brkga_resultado      # (self.best_sequence, self.best_fitness)
    # Auxiliares ----------------------------------------------

    # BL ----------------------------------------------    
    def _medir_largura_faixa_BL(self, pecas_posicionadas: List[Tuple[int, Tuple[float, float]]]) -> float:
        '''
        Calcula o comprimento L necessário para conter todas as peças posicionadas.
        
        Args:
            pecas_posicionadas: [(t,(x,y)), (t,(x,y)), ...] - lista de tuplas (tipo, posição)
            
        Returns:
            float: Maior coordenada x encontrada (comprimento necessário)
            se não cabe, retorna 9e9
        '''
        try:
            if not pecas_posicionadas or pecas_posicionadas == [] :
                return 9e9
            
            max_x = 0.0
            
            for tipo, posicao in pecas_posicionadas:
                x_pos, y_pos = posicao
                
                # Verifica se o tipo é válido
                if 0 <= tipo < len(self.T):
                    # Obtém o polígono do tipo
                    poligono = self.T[tipo]
                    
                    # Encontra o vértice mais à direita do polígono
                    max_x_poligono = max(x for x, y in poligono)
                    
                    # Calcula a posição mais à direita deste polígono posicionado
                    x_max_atual = x_pos + max_x_poligono
                    
                    # Atualiza o máximo global
                    if x_max_atual > max_x:
                        max_x = x_max_atual
            
            return round(max_x,10) 
            
        except Exception as e:
            print(f"Erro ao medir largura da faixa BL: {e}")
            # Fallback: retorna o maior x das posições se houver erro com os polígonos
            # if pecas_posicionadas:
            #     return max(pos[1][0] for pos in pecas_posicionadas)
            return 9e9

    def _rodar_BL(self,seq) -> float:   ### implementar
        largura_ja_existente = self.sequencias_resolvidas.get(tuple(seq))   #se já foi resolvido antes, adianta tempo
        # print(f"rodando BL, seq = {seq}")
        if largura_ja_existente != None:                                   
            return largura_ja_existente ####### salvar entre sessões??
        else:                
            M = self.malha
            NFP = self.NFP
            DIFP = self.DIFP
            bl = Bottom_Left(M,seq,NFP,DIFP)
            bl_resultado = bl.rodar()           # retorna lista com itens (t,(x,y))
            # bl_resultado_pontos = [bl_resultado[i][1] for i in range(len(bl_resultado))]
            # self._plotar_resultado(M,bl_resultado_pontos,seq)
            largura_resultado_bl = self._medir_largura_faixa_BL(bl_resultado)   
            self.sequencias_resolvidas[tuple(seq)] = largura_resultado_bl    #
            return largura_resultado_bl
    # --------------------------------------------------------------------------------

