# ---------------------------------------------------------------------------------
import ifp_generator 
import nfp_generator 
from modelo_ISPP import Modelo_ISPP
from modelo_BPP import Modelo_BPP
import json
import os
from typing import List, Tuple
from shapely.geometry import Polygon, Point
from shapely.prepared import prep
from instancia import Instancia
# ---------------------------------------------------------------------------------

class Modelo:
    def __init__(self):
        self.diretorio_instancias = "instancias"
        self.modelos_roupas:dict = {}              #str_modelo:Instancia
        self.largura_bin   :float= 0
        pass
    def adicionar_modelo_roupa(self,str_modelo,poligonos_T:list,demanda_itens_q:list,W,L,R,C,demanda_produto_Q:int,largura_l=None,IFP=None,NFP=None):
        inst = Instancia(poligonos_T,demanda_itens_q,W,L,R,C,demanda_produto_Q,largura_l,IFP,NFP)
        self.modelos_roupas[str_modelo]= inst
        self._salvar_instancia(str_modelo,inst)
    def _limpar_modelos_roupa(self):
        self.modelos_roupas.clear()
    # -----------------------------------------------------------------
    def _salvar_instancia(self, nome_modelo, instancia:Instancia):
        """
        Salva uma instância em arquivo usando JSON
        """
        try:
            # Garantir que o diretório existe antes de salvar
            if not os.path.exists(self.diretorio_instancias):
                os.makedirs(self.diretorio_instancias)
            
            caminho_arquivo = os.path.join(self.diretorio_instancias, f"{nome_modelo}.json")
            
            # Função para converter objetos não serializáveis
            def converter_para_json(obj):
                if isinstance(obj, dict):
                    # Converter chaves que são tuplas para strings
                    new_dict = {}
                    for k, v in obj.items():
                        if isinstance(k, tuple):
                            # Converter tupla para string formatada
                            key_str = f"tuple_{k[0]}_{k[1]}" if len(k) == 2 else str(k)
                            new_dict[key_str] = converter_para_json(v)
                        else:
                            new_dict[k] = converter_para_json(v)
                    return new_dict
                elif isinstance(obj, list):
                    return [converter_para_json(item) for item in obj]
                elif isinstance(obj, tuple):
                    return [converter_para_json(item) for item in obj]  # Converte tupla em lista
                elif isinstance(obj, Polygon):
                    # Converter Polygon para lista de coordenadas
                    return [list(coord) for coord in obj.exterior.coords]
                elif hasattr(obj, '__dict__'):
                    # Converter objetos em dicionários
                    return converter_para_json(obj.__dict__)
                else:
                    # Tipos básicos que o JSON suporta
                    return obj
            
            # Converter a instância para um dicionário serializável
            dados_instancia = {
                'T': converter_para_json(instancia.T),
                'q': converter_para_json(instancia.q),
                'W': instancia.W,
                'L': instancia.L,
                'R': instancia.R,
                'C': instancia.C,
                'Q': instancia.Q,
                'l': instancia.l,
                'IFP': converter_para_json(instancia.IFP),
                'NFP': converter_para_json(instancia.NFP)
            }
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
                json.dump(dados_instancia, arquivo, indent=2, ensure_ascii=False)
            
            print(f"Instância '{nome_modelo}' salva com sucesso em {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar instância '{nome_modelo}': {e}")

    def _carregar_instancia(self, nome_modelo) -> Instancia:
        """
        Carrega uma instância de arquivo usando JSON
        """
        try:
            caminho_arquivo = os.path.join(self.diretorio_instancias, f"{nome_modelo}.json")
            
            if not os.path.exists(caminho_arquivo):
                print(f"Arquivo da instância '{nome_modelo}' não encontrado: {caminho_arquivo}")
                return None
            
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                dados_instancia = json.load(arquivo)
            
            # Função para converter de volta para o formato original
            def converter_de_json(obj):
                if isinstance(obj, dict):
                    new_dict = {}
                    for k, v in obj.items():
                        # Tentar converter chaves que eram tuplas de volta
                        if k.startswith('tuple_') and '_' in k:
                            try:
                                parts = k.split('_')
                                if len(parts) == 3:  # tuple_x_y
                                    key_tuple = (int(parts[1]), int(parts[2]))
                                    new_dict[key_tuple] = converter_de_json(v)
                                else:
                                    new_dict[k] = converter_de_json(v)
                            except:
                                new_dict[k] = converter_de_json(v)
                        else:
                            new_dict[k] = converter_de_json(v)
                    return new_dict
                elif isinstance(obj, list):
                    # Verificar se é uma lista de coordenadas (pode ser um Polygon)
                    if all(isinstance(item, list) and len(item) == 2 for item in obj):
                        # Pode ser um polígono - vamos manter como lista por enquanto
                        # O código que usa isso vai precisar converter para Polygon quando necessário
                        return obj
                    return [converter_de_json(item) for item in obj]
                else:
                    return obj
            
            # Aplicar conversão aos dados carregados
            dados_convertidos = converter_de_json(dados_instancia)
            
            # Recriar a instância a partir dos dados
            instancia = Instancia(
                T=dados_convertidos['T'],
                q=dados_convertidos['q'],
                W=dados_convertidos['W'],
                L=dados_convertidos['L'],
                R=dados_convertidos['R'],
                C=dados_convertidos['C'],
                Q=dados_convertidos['Q'],
                l=dados_convertidos.get('l'),
                IFP=dados_convertidos.get('IFP'),
                NFP=dados_convertidos.get('NFP')
            )
            
            print(f"Instância '{nome_modelo}' carregada com sucesso")
            return instancia
        
        except Exception as e:
            print(f"Erro ao carregar instância '{nome_modelo}': {e}")
            return None
    # -----------------------------------------------------------------
    def _salvar_modelos_roupas(self):               
        for modelo_str, instancia in self.modelos_roupas.items():
            self._salvar_instancia(modelo_str,instancia)
        pass
    def _carregar_modelos_roupas(self,lista_nomes):
        for nome in lista_nomes:
            self.modelos_roupas[nome] = self._carregar_instancia(nome)
    # -----------------------------------------------------------------
    def _salvar_resultado(self):                       #####implementar
        pass
    # -----------------------------------------------------------------
    def rodar(self):
        # Pré Carregar os NFP e IFP das instancias e salvar
        modificou_modelos = self._pre_processamento()           # carregar IFP e NFP
        if modificou_modelos:
            self._salvar_modelos_roupas()   

        # ISPP para cada modelo de roupa
        for modelo_str, inst in self.modelos_roupas.items():
            inst:Instancia
            if inst.l == None:                              # se não tem a largura, calcula-a.
                inst.l = self.resolver_ispp(inst.W,inst.L,inst.R,inst.C,inst.T,inst.q)
        self._salvar_modelos_roupas()                       # agora todos modelos tem sua largura. 
        
        # BPP
        resultado_bins = self.resolver_bpp(self.modelos_roupas,self.largura_bin)
        self._salvar_resultado(resultado_bins)
        # Finalizar
        pass
    # -----------------------------------------------------------------------------

    # -----------------------------------------------------------------------------
    def _pre_processamento(self) -> bool:                                #corrigir
        '''
        Carrega IFP e NFP das instancias
        '''
        modificou_modelos_roupas = False
        for modelo_str, inst in self.modelos_roupas.items():
            inst:Instancia
            if inst.IFP==None:
                inst.IFP = self._calcular_todos_IFP_D(inst.W,inst.L,inst.R,inst.C,inst.T)
                modificou_modelos_roupas= True
            if inst.NFP==None:
                inst.NFP = self._calcular_todos_NFP(inst.T) 
                modificou_modelos_roupas= True
        return modificou_modelos_roupas
    def resolver_ispp(self,W,L,R,C,T:list,q:list):
        #verificar se é possível
        #verificar se é possível
        #verificar se é possível###############
        modelo_ispp = Modelo_ISPP(W,L,R,C,T,q)
        resultado_menor_faixa = modelo_ispp.rodar()
        return resultado_menor_faixa
    def resolver_bpp(self,modelos:dict, largura_bin:float):
        ######verificar se é possível
        L = -1
        for modelo_str, instancia in modelos.items():
            instancia:Instancia
            if L <= 0:
                L = instancia.L
            if instancia.L != L:
                return f"os modelos de roupa tem alturas diferenes: {L} e {instancia.L}"     
        # ver se todos modelos tem mesma altura que retangulo[1]
        # ----------------------------------------
        modelo_bpp = Modelo_BPP(modelos,largura_bin)
        resultado_brkga_bin = modelo_bpp.rodar()
        # resultado_brkga_bin = modelo_bpp.evolve(num_geracoes=10000)
        return resultado_brkga_bin
    # -----------------------------------------------------------------------------
    def _gerar_pontos_malha(self,W,L,R,C) -> dict:
        '''
        Retorna um dicionario de elementos (d,(x,y)); d inteiro; x,y reais
        '''
        pontos = {}
        gx = L/(C-1)
        gy = W/(R-1)
        for i in range(C):
            for j in range(R):
                n = i*R+j
                pontos[n] = (i*gx, j*gy)
        return pontos       
    def _discretizar_poligono(self,W,L,R,C,pontos_a_verificar:dict,poligono_t:Polygon,somente_interior=False,epsilon=1e-7):
        gx = L/(C-1)
        gy = W/(R-1)
        epsilon_adapt = max(epsilon, min(gx,gy)*0.001)
        if somente_interior:
            poligono_robusto = poligono_t.buffer(-epsilon_adapt) if poligono_t.area > epsilon_adapt else poligono_t
        else:
            poligono_robusto = poligono_t.buffer(epsilon_adapt)

        poligono_prep = prep(poligono_robusto)
        minx,miny,maxx,maxy = poligono_t.bounds
        minx -= epsilon_adapt
        miny -= epsilon_adapt
        maxx += epsilon_adapt
        maxy += epsilon_adapt

        pontos_contidos = []
        for ponto_num, ponto_coords in pontos_a_verificar.items():
            x,y = ponto_coords
            if not (minx <= x <= maxx and miny <= y <= maxy):
                continue
                
            # Teste robusto
            if poligono_prep.contains(Point(ponto_coords)):
                pontos_contidos.append((ponto_num,ponto_coords))
            elif not somente_interior:
                # Para inclusão de borda, verificar proximidade
                if poligono_t.boundary.distance(Point(ponto_coords)) <= epsilon_adapt:
                    pontos_contidos.append((ponto_num,ponto_coords))
        
        return pontos_contidos

    def _calcular_IFP_D(self,W,L,R,C,conjunto_pontos,poligono_t:list):
        retangulo_malha = [(0,0),(L,0),(L,W),(0,W)]
        ifp_poligono = ifp_generator.calculate_ifp(retangulo_malha,poligono_t)
        ifp_d = self._discretizar_poligono(W,L,R,C,conjunto_pontos,ifp_poligono,somente_interior=False)
        return ifp_d
    def _calcular_todos_IFP_D(self,W,L,R,C,T):          ###### implementar
        IFP_D = []
        pontos_malha = self._gerar_pontos_malha(W,L,R,C)
        for poligono_t in T:
            ifp_d = self._calcular_IFP_D(W,L,R,C,pontos_malha,poligono_t)
            IFP_D.append(ifp_d)
        return IFP_D
    # -----------------------------------------------------------------------------
    def _calcular_NFP(self,u:list, t:list):
        nfp = nfp_generator.calculate_nfp(Polygon(u),Polygon(t))
        return nfp


    def _calcular_todos_NFP(self,T):                         ###### implementar
        NFP = {}
        for u in range(len(T)):
            for t in range(len(T)):
                NFP[u,t] = self._calcular_NFP(T[u],T[t])
        return NFP
# ---------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------
def escalar_poligono(poligono, escalar=1.0,arredondamento=7):
    return [(round(escalar*x,arredondamento),round(escalar*y,arredondamento)) for x,y in poligono]    
# ---------------------------------------------------------------------------------
def instancia_marques(escala=1.0, multiplicador_demanda=1):
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
    T_escalado = []
    for poligono in T_marques:
        T_escalado.append(escalar_poligono(poligono,escala))
    q = [2,2,1,1,2,2,1,1]
    q_mult = [multiplicador_demanda*x for x in q]
    return T_escalado, q_mult
# ---------------------------------------------------------------------------------

def main():
    modelo = Modelo()
    W=104
    L=75
    R=105
    C=76
    for escala in [0.9, 1.0, 1.06, 1.13]:
        nome = f"marques_{escala}_{W}_{L}_{R}_{C}"
        T,q = instancia_marques(escala)
        modelo.adicionar_modelo_roupa(nome,T,q,W,L,R,C,1)
        pass
    modelo.rodar()

#rodar main
main()

# ---------------------------------------------------------------------------------
