# ---------------------------------------------------------------------------------
import ifp_generator 
import nfp_generator 
from modelo_ISPP import *
from modelo_BPP import *
import json
import os
from datetime import datetime
from typing import List, Tuple
from shapely.geometry import Polygon, Point
from shapely.prepared import prep
from instancia import Instancia
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import traceback
import time
# ---------------------------------------------------------------------------------

class Modelo:
    def __init__(self):
        self.diretorio_instancias = "instancias"
        self.modelos_roupas:dict = {}              #str_modelo:Instancia
        self.largura_bin   :float
        pass
    def adicionar_modelo_roupa(self,str_modelo,poligonos_T:list,demanda_itens_q:list,W,L,R,C,demanda_produto_Q:int,largura_l=None,IFP=None,NFP=None):
        inst = Instancia(poligonos_T,demanda_itens_q,W,L,R,C,demanda_produto_Q,largura_l,IFP,NFP)
        self.modelos_roupas[str_modelo]= inst
        # self._salvar_instancia(str_modelo,inst)
    def _limpar_modelos_roupa(self):
        self.modelos_roupas.clear()
    def adicionar_modelo_demanda_Q(self,str_modelo, demanda_Q):     ######implementar
        pass
    # -----------------------------------------------------------------
    def rodar(self, largura_bin):
        self.largura_bin = largura_bin          #gambi
        self._carregar_modelos_roupas()
        self._pre_processamento()           # carregar IFP e NFP
   
        # ISPP para cada modelo de roupa
        for modelo_str, inst in self.modelos_roupas.items():
            inst:Instancia
            if inst.l == None:                              # se não tem a largura, calcula-a.
                print("largura não calculada. resolvendo ISPP para a o modelo",modelo_str)
                t0 = time.time()
                seq,larg,pecas_posicionadas = self.resolver_ispp(inst.W,inst.L,inst.R,inst.C,inst.T,inst.q,inst.NFP,inst.IFP)
                print(f"ISPP demorou {time.time()-t0} seg.")
                inst.l = larg
                self._salvar_json_instancia(modelo_str,inst)                        
                self._plotar_ispp(inst.W,inst.L,inst.R,inst.C,inst.T,pecas_posicionadas,salvar_arquivo=f"{modelo_str}_menor_strip_{inst.l}.png",mostrar_plot=False)
        # agora todos modelos tem sua largura.
        
        # BPP
        t0=time.time()
        print(f"BPP demorou {time.time()-t0} seg.")
        # num_bins, desperdicio, seq_corte, largura_bin, hist = self.resolver_bpp(self.modelos_roupas,self.largura_bin,gens=1000)    # (num_bins, desperdicio, seq_corte,largura_bin, historico)
        num_bins, desperdicio, seq_corte, largura_bin, hist = self.resolver_bpp(self.modelos_roupas,self.largura_bin,gens=500000)    # (num_bins, desperdicio, seq_corte,largura_bin, historico)
        nome_instancias_bpp = ""
        str_Q = "Q"
        for modelo_str, inst in self.modelos_roupas.items():
            nome_instancias_bpp += modelo_str+"_"
            str_Q += f"_{str(inst.Q)}"
        nome_instancias_bpp += str_Q
        self._salvar_json_resultado_bpp(num_bins,desperdicio,seq_corte,largura_bin,hist,nome_instancias_bpp)
        self._plotar_resultado_bpp(num_bins,seq_corte,largura_bin,nome=nome_instancias_bpp)
        # Finaliza
        pass
    # -----------------------------------------------------------------------------
    def _carregar_modelos_roupas(self,lista_nomes=None):            ###### está sobrepondo as instancias dadas pelo usuário sempre
        if lista_nomes==None:
            lista_nomes=[]
            for modelo_str, inst in self.modelos_roupas.items():
                lista_nomes.append(modelo_str)

        for nome in lista_nomes:
            result = self._carregar_instancia(nome)
            if result != None:
                self.modelos_roupas[nome] = result
    def _pre_processamento(self) -> bool:                                #corrigir
        '''
        Carrega IFP e NFP das instancias
        '''
        # modificou_modelos_roupas = False
        for modelo_str, inst in self.modelos_roupas.items():
            inst:Instancia
            if inst.IFP==None:
                print(modelo_str,"está sem IFP. Calculando...")
                inst.IFP = self._calcular_todos_IFP_D(inst.W,inst.L,inst.R,inst.C,inst.T)
                self._salvar_json_instancia(modelo_str,inst)
                # modificou_modelos_roupas=True
            if inst.NFP==None:
                print(modelo_str,"está sem NFP. Calculando...")
                inst.NFP = self._calcular_todos_NFP(inst.T) 
                self._salvar_json_instancia(modelo_str,inst)
                # modificou_modelos_roupas=True
        pass
    def resolver_ispp(self,W,L,R,C,T:list,q:list,NFP,IFP_D):
        #verificar se é possível
        #verificar se é possível
        #verificar se é possível###############
        modelo_ispp = Modelo_ISPP(W,L,R,C,T,q,NFP,IFP_D)
        resultado_menor_faixa = modelo_ispp.rodar()
        return resultado_menor_faixa        # (best_sequence, best_fitness, best_pecas_posicionadas )
    def resolver_bpp(self,modelos:dict, largura_bin:float,gens=100000):
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
        resultado_brkga_bin = modelo_bpp.rodar(gens=gens)    # (num_bins, desperdicio, seq_corte,largura_bin, historico)
        # resultado_brkga_bin = modelo_bpp.evolve(num_geracoes=10000)
        return resultado_brkga_bin                  # (num_bins, desperdicio, seq_corte,largura_bin, historico)
    # -----------------------------------------------------------------------------
    
    # -----------------------------------------------------------------
    def _salvar_json_instancia(self, nome_modelo, instancia:Instancia):
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
    def _gerar_img_resultado(self, resultado_bins,nome):
        pass
    def _salvar_json_resultado_bpp(self, num_bins, desperdicio, sequencia_de_corte, largura_bin, historico, nome):
        """
        Salva o resultado completo do BPP em JSON incluindo largura_bin e histórico.
        
        Args:
            num_bins: Número total de bins utilizados
            desperdicio: Total de desperdício/sobra
            sequencia_de_corte: Lista de bins com sequência de itens
            largura_bin: Largura/capacidade do bin
            historico: Histórico de evolução do algoritmo
            nome: Nome do arquivo para salvar
        """
        try:
            if not os.path.exists("resultados"):
                os.makedirs("resultados")
            
            caminho_arquivo = os.path.join("resultados", f"{nome}.json")

            # Estrutura completa do resultado
            resultado_completo = {
                "metadata": {
                    "data_criacao": datetime.now().isoformat(),
                    "nome_arquivo": nome,
                    "versao": "1.0"
                },
                "parametros": {
                    "largura_bin": largura_bin,
                    "num_bins": num_bins,
                    "desperdicio_total": desperdicio,
                    "taxa_utilizacao": 1 - (desperdicio / (num_bins * largura_bin)) if num_bins > 0 else 0
                },
                "sequencia_de_corte": sequencia_de_corte,
                "historico_evolucao": historico,
                "estatisticas": {
                    "melhor_desperdicio": min(historico) if historico else 0,
                    "pior_desperdicio": max(historico) if historico else 0,
                    "desperdicio_medio": sum(historico) / len(historico) if historico else 0,
                    "num_geracoes": len(historico)
                }
            }

            def converter_para_json(obj):
                if isinstance(obj, dict):
                    return {str(k): converter_para_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [converter_para_json(item) for item in obj]
                elif isinstance(obj, tuple):
                    return list(obj)
                elif isinstance(obj, (int, float)):
                    return float(obj) if isinstance(obj, float) else obj
                elif hasattr(obj, '__dict__'):
                    return converter_para_json(obj.__dict__)
                else:
                    return obj

            resultado_serializavel = converter_para_json(resultado_completo)

            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(resultado_serializavel, f, indent=2, ensure_ascii=False)
            
            print(f"Resultado salvo com sucesso em {caminho_arquivo}")
            print(f"Bins: {num_bins}, Desperdício: {desperdicio:.2f}, Utilização: {resultado_completo['parametros']['taxa_utilizacao']:.1%}")
            
            return resultado_completo
            
        except Exception as e:
            print(f"Erro ao salvar resultado: {e}")
            traceback.print_exc()
            return None
    # -----------------------------------------------------------------
    def _salvar_modelos_roupas(self):               
        for modelo_str, instancia in self.modelos_roupas.items():
            self._salvar_json_instancia(modelo_str,instancia)
        pass
    # -----------------------------------------------------------------
    def _plotar_ispp(self, W, L, R, C, T, seq, pontos=None, titulo="Resultado do ISPP", 
                    mostrar_grade=True, mostrar_numeros=True, mostrar_pontos_difp=False,
                    salvar_arquivo=None, mostrar_plot=True):
        """
        Plota o resultado do ISPP (Irregular Strip Packing Problem)
        
        Args:
            W: Largura da faixa
            L: Comprimento da faixa
            R: Número de linhas da grade
            C: Número de colunas da grade
            T: Lista de polígonos dos tipos
            seq: Sequência de posicionamento [(tipo, (x,y)), ...]
            pontos: Lista de pontos DIFP disponíveis (opcional)
            titulo: Título do gráfico
            mostrar_grade: Se True, mostra a grade da malha
            mostrar_numeros: Se True, mostra números dos itens na sequência
            mostrar_pontos_difp: Se True, mostra os pontos DIFP em fundo
            salvar_arquivo: Caminho para salvar o gráfico
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            from shapely.geometry import Polygon
            
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Configura limites do gráfico
            ax.set_xlim(0, L)
            ax.set_ylim(0, W)
            ax.set_aspect('equal')
            
            # Desenha o retângulo da área útil
            retangulo = patches.Rectangle((0, 0), L, W, 
                                        linewidth=2, edgecolor='black', 
                                        facecolor='lightgray', alpha=0.2)
            ax.add_patch(retangulo)
            
            # Cores para diferentes tipos de polígonos
            cores = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 
                    'pink', 'gray', 'olive', 'cyan', 'magenta', 'yellow',
                    'navy', 'teal', 'coral', 'indigo']
            
            # Dicionário para contar ocorrências de cada tipo e controle de legenda
            contador_tipos = {}
            tipos_utilizados = set()
            
            # Função auxiliar para transladar polígono
            def _transladar_poligono(poligono, ponto):
                """Translada um polígono para uma posição específica"""
                if isinstance(poligono, Polygon):
                    # Para objetos Polygon do shapely
                    return Polygon([(x + ponto[0], y + ponto[1]) for x, y in poligono.exterior.coords])
                else:
                    # Para lista de vértices
                    return [(x + ponto[0], y + ponto[1]) for x, y in poligono]
            
            # Função auxiliar para calcular área utilizada
            def _calcular_area_utilizada_sequencia(T, sequencia):
                """Calcula a área total utilizada pela sequência"""
                area_total = 0.0
                for tipo, posicao in sequencia:
                    if 0 <= tipo < len(T):
                        poligono = T[tipo]
                        if isinstance(poligono, Polygon):
                            area_total += poligono.area
                        else:
                            # Calcula área manualmente para lista de vértices
                            poly = Polygon(poligono)
                            area_total += poly.area
                return area_total
            
            # Plota cada polígono posicionado da sequência
            for i, (tipo, posicao) in enumerate(seq):
                # Verifica se o tipo é válido
                if 0 <= tipo < len(T):
                    # Obtém o polígono original do tipo
                    poligono_original = T[tipo]
                    
                    # Translada o polígono para a posição especificada
                    poligono_posicionado = _transladar_poligono(poligono_original, posicao)
                    
                    # Conta ocorrências do tipo
                    if tipo not in contador_tipos:
                        contador_tipos[tipo] = 0
                    contador_tipos[tipo] += 1
                    tipos_utilizados.add(tipo)
                    
                    # Cor baseada no tipo
                    cor = cores[tipo % len(cores)]
                    
                    # Extrai coordenadas do polígono posicionado
                    if isinstance(poligono_posicionado, Polygon):
                        x, y = poligono_posicionado.exterior.xy
                    else:
                        # Se for lista de vértices
                        x = [p[0] for p in poligono_posicionado]
                        y = [p[1] for p in poligono_posicionado]
                    
                    # Label para legenda (apenas na primeira ocorrência de cada tipo)
                    label = f'Tipo {tipo}' if contador_tipos[tipo] == 1 else ""
                    
                    # Plota o polígono posicionado
                    patch = patches.Polygon(list(zip(x, y)), 
                                        closed=True, 
                                        edgecolor=cor, 
                                        facecolor=cor,
                                        alpha=0.7,
                                        linewidth=1.0,
                                        label=label)
                    ax.add_patch(patch)
                    
                    # # Marca o ponto de posicionamento (referência)
                    # ax.scatter([posicao[0]], [posicao[1]], 
                    #         color='black', s=40, zorder=10, marker='x', linewidth=2)
                    
                    # Adiciona número da sequência no centroide do polígono
                    if mostrar_numeros:
                        if isinstance(poligono_posicionado, Polygon):
                            centroid = poligono_posicionado.centroid
                            centroid_x, centroid_y = centroid.x, centroid.y
                        else:
                            # Calcula centroide manualmente para lista de vértices
                            centroid_x = sum(x) / len(x)
                            centroid_y = sum(y) / len(y)
                        
                        ax.text(centroid_x, centroid_y, str(i+1), 
                            fontsize=9, fontweight='bold',
                            ha='center', va='center',
                            bbox=dict(boxstyle='circle', facecolor='white', alpha=0.9),
                            zorder=15)
            
            # Plota os pontos DIFP disponíveis em fundo (opcional) #####retirar
            if mostrar_pontos_difp and pontos:
                x_vals = [p[0] for p in pontos]
                y_vals = [p[1] for p in pontos]
                ax.scatter(x_vals, y_vals, color='gray', s=6, alpha=0.2, 
                        zorder=1, label=f'Pontos DIFP ({len(pontos)})')
            
            # Desenha a grade da malha se solicitado
            if mostrar_grade:
                # Calcula espaçamento da grade
                gx = L / (C - 1) if C > 1 else L
                gy = W / (R - 1) if R > 1 else W
                
                # Linhas verticais
                for i in range(C):
                    x = i * gx
                    ax.axvline(x=x, color='blue', alpha=0.1, linestyle='-', linewidth=0.3)
                
                # Linhas horizontais
                for i in range(R):
                    y = i * gy
                    ax.axhline(y=y, color='blue', alpha=0.1, linestyle='-', linewidth=0.3)
                
                # Pontos da grade (opcional)
                pontos_grade_x = []
                pontos_grade_y = []
                for i in range(C):
                    for j in range(R):
                        pontos_grade_x.append(i * gx)
                        pontos_grade_y.append(j * gy)
                
                ax.scatter(pontos_grade_x, pontos_grade_y, color='blue', s=2, alpha=0.1, 
                        marker='+', zorder=1)
            
            # Calcula comprimento utilizado
            comprimento_utilizado = 0
            for tipo, pos in seq:
                if 0 <= tipo < len(T):
                    poligono = T[tipo]
                    if isinstance(poligono, Polygon):
                        max_x_poligono = max(x for x, y in poligono.exterior.coords)
                    else:
                        max_x_poligono = max(x for x, y in poligono)
                    comprimento_total = pos[0] + max_x_poligono
                    if comprimento_total > comprimento_utilizado:
                        comprimento_utilizado = comprimento_total
            
            # Linha vertical pontilhada para mostrar a largura
            if comprimento_utilizado > 0:
                ax.axvline(x=comprimento_utilizado, color='red', linestyle='--', 
                          linewidth=1.5, alpha=0.9, 
                          label=f'Comprimento utilizado: {comprimento_utilizado:.1f}')
            
            # Configurações do gráfico
            ax.set_xlabel('Comprimento (L)')
            ax.set_ylabel('Largura (W)')
            ax.set_title(titulo, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.2)
            
            # Remove legendas duplicadas e organiza a legenda
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=9)
            
            # # Calcula estatísticas
            # total_itens = len(seq)
            # area_utilizada = _calcular_area_utilizada_sequencia(T, seq)
            # area_total = W * L
            # # utilizacao = (area_utilizada / area_total) * 100 if area_total > 0 else 0
            
    #         # Adiciona informações detalhadas
    #         info_text = f"""Malha: {W} × {L}
    # Resolução: {R} × {C}
    # Itens posicionados: {total_itens}
    # Tipos utilizados: {len(tipos_utilizados)}
    # Comprimento utilizado: {comprimento_utilizado:.1f}
    # Pontos DIFP: {len(pontos) if pontos else 0}"""
            
    #         ax.text(0.02, 0.98, info_text, transform=ax.transAxes, verticalalignment='top',
    #             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9),
    #             fontsize=10, fontfamily='monospace')
            
            # Salva o gráfico se solicitado
            if salvar_arquivo:
                pasta = "instancias"
                if not os.path.exists(pasta):
                    os.makedirs(pasta)
                caminho_completo = pasta+"/"+salvar_arquivo
                plt.savefig(caminho_completo, dpi=300, bbox_inches='tight')
                print(f"Gráfico do ISPP salvo em: {caminho_completo}")
            if mostrar_plot:
                plt.tight_layout()
                plt.show()
                
            
            return fig, ax
            
        except Exception as e:
            print(f"Erro ao plotar resultado ISPP: {e}")
            import traceback
            traceback.print_exc()
            return None, None    
    def _plotar_resultado_bpp(self, num_bins, seq, largura_bin, nome="resultado"):
        """
        Plota resultado dos bins com as peças
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import numpy as np
            import os
            
            # Configurar cores para diferentes modelos
            cores_disponiveis = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
            
            # Mapear modelos para cores
            modelos_unicos = set()
            for bin in seq:
                for item in bin:
                    modelos_unicos.add(item)
            
            cor_por_modelo = {}
            for i, modelo in enumerate(modelos_unicos):
                cor_por_modelo[modelo] = cores_disponiveis[i % len(cores_disponiveis)]
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Parâmetros de desenho
            altura_bin = 1.0
            espacamento_vertical = 1.5
            margem = 0.5
            
            # Calcular desperdício total
            area_total_bins = len(seq) * largura_bin * altura_bin
            area_utilizada = 0
            
            # Desenhar cada bin
            for i, bin in enumerate(seq):
                y = i * espacamento_vertical
                
                # Desenhar contorno do bin
                rect = patches.Rectangle((0, y), largura_bin, altura_bin, 
                                    linewidth=2, edgecolor='black', facecolor='none')
                ax.add_patch(rect)
                
                # Adicionar itens no bin
                x_atual = 0
                soma_larguras = 0
                
                for item in bin:
                    # Obter largura do item
                    if item in self.modelos_roupas:
                        largura_item = self.modelos_roupas[item].l
                    else:
                        largura_item = largura_bin * 0.1  # Fallback
                    
                    # Desenhar item
                    cor = cor_por_modelo[item]
                    item_rect = patches.Rectangle((x_atual, y), largura_item, altura_bin,
                                                facecolor=cor, edgecolor='black', alpha=0.7)
                    ax.add_patch(item_rect)
                    
                    # Adicionar texto do modelo e largura se houver espaço
                    if largura_item > largura_bin * 0.15:  # Aumentei o limite para caber mais texto
                        texto_nome = item.split('_')[1] if '_' in item else item
                        texto_largura = f'{largura_item:.1f}'
                        # Texto em duas linhas: nome e largura
                        ax.text(x_atual + largura_item/2, y + altura_bin/2 + 0.15, 
                            texto_nome, ha='center', va='center', fontsize=6, fontweight='bold')
                        ax.text(x_atual + largura_item/2, y + altura_bin/2 - 0.15, 
                            f'({texto_largura})', ha='center', va='center', fontsize=5)
                    elif largura_item > largura_bin * 0.08:
                        # Para itens menores, mostrar apenas o nome
                        texto_nome = item.split('_')[1] if '_' in item else item
                        ax.text(x_atual + largura_item/2, y + altura_bin/2, texto_nome,
                            ha='center', va='center', fontsize=6, fontweight='bold')
                    
                    x_atual += largura_item
                    soma_larguras += largura_item
                    area_utilizada += largura_item * altura_bin
                
                # Informações do bin - apenas a utilização
                utilizacao = (soma_larguras / largura_bin) * 100
                
                ax.text(largura_bin + 0.1, y + altura_bin/2, 
                    f'{utilizacao:.1f}%', 
                    va='center', fontsize=8)  # Fonte menor
                
                # Número do bin
                ax.text(-0.5, y + altura_bin/2, f'Bin {i+1}', 
                    ha='right', va='center', fontweight='bold', fontsize=9)  # Fonte menor
            
            # Calcular métricas finais
            desperdicio_total = ((area_total_bins - area_utilizada) / area_total_bins) * 100
            area_desperdicada = area_total_bins - area_utilizada
            
            # Configurar eixos
            max_y = len(seq) * espacamento_vertical
            ax.set_xlim(-2, largura_bin + 2)
            ax.set_ylim(-1, max_y)
            ax.set_xlabel('Largura', fontsize=10)  # Fonte menor
            ax.set_ylabel('Bins', fontsize=10)  # Fonte menor
            
            # Título com informações de desperdício
            ax.set_title(f'Resultado - {num_bins} bins | Largura do bin: {largura_bin}\n'
                        f'Desperdício Total: {desperdicio_total:.1f}% | Área Desperdiçada: {area_desperdicada:.1f}', 
                        fontsize=11)  # Fonte um pouco menor
            
            # Grade
            ax.grid(True, alpha=0.3, axis='x')
            
            # Legenda com fonte menor - mostra nome e largura
            legend_elements = []
            for modelo, cor in cor_por_modelo.items():
                if modelo in self.modelos_roupas:
                    largura = self.modelos_roupas[modelo].l
                    nome_legenda = f"{modelo.split('_')[1]} ({largura:.1f})"
                else:
                    nome_legenda = modelo
                legend_elements.append(patches.Patch(facecolor=cor, label=nome_legenda))
            
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1), 
                    fontsize=8)  # Fonte menor na legenda
            
            # Ajustar layout
            plt.tight_layout()
            
            # Salvar se necessário
            if not os.path.exists("resultados"):
                os.makedirs("resultados")
            
            caminho_imagem = os.path.join("resultados", f"{nome}.png")
            plt.savefig(caminho_imagem, dpi=200, bbox_inches='tight')
            print(f"Plot salvo em: {caminho_imagem}")
            
            plt.show()
            
        except Exception as e:
            print(f"Erro ao plotar resultado: {e}")
            import traceback
            traceback.print_exc()
    # -----------------------------------------------------------------
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
