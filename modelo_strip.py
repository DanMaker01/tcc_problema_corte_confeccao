# ---------------------------------------------------------------------------
# Modelo heurístico para o Problema irregular  ISPP 
# ---------------------------------------------------------------------------
# Este código é parte do projeto de TCC 
# Danillo Mendes Santiago
# 10414592
# ICMC, 2025
# ---------------------------------------------------------------------------
from typing import List, Tuple
from shapely.geometry import Polygon, Point
import os
from pathlib import Path
from shapely.prepared import prep
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import ifp_generator
import nfp_generator

from malha import Malha
from bl import Bottom_Left
from brkga import BRKGA_ordem

class Modelo_Menor_Faixa():
    def __init__(self, W,L,R,C,T,q, nome_pasta=None):
        existe_solucao = self._verificar_requisitos_para_modelo(W,L,R,C,T,q)
        if existe_solucao != True:
            print("problema ao iniciar modelo, revise seus parâmetros.")
            return
        # senao:
        self.malha:Malha = Malha(W,L,R,C)   # gera ao criar a classe, rápido
        self.NFP : dict[int,int] = None     # NFP(u,t) = poligono
        # self.IFP = None                     # IFP(t) = poligono
        self.DIFP:list = None                    # DIFP(t,M) = subconjunto de M
        self.T = T                          # vetor de tipos (poligonos)
        self.q = q                          # vetor da demanda dos itens de cada tipo
        # suporte ao BRKGA_ordem e BL
        self.sequencias_resolvidas = {}     # {[0,1,1,2] : 48, [0,2,1,1]: 43, ... } 
        self.nome_pasta = nome_pasta
        pass
    # Principal --------------------------------------------------------------------------------
    def rodar(self):
        # dados a Malha, T e q,
        self._pre_processamento()                           # carrega na memória: IFP Discreto e NFP
        brkga_resultado_strip = self._iniciar_brkga_ordem(100,0.3,0.4,generations=1)   # acha a faixa de menor comprimento
        self._salvar_menor_strip(self.malha,brkga_resultado_strip)
        return brkga_resultado_strip        # resultado = (melhor_sequencia, melhor_fitness)        
    # Subrotinas --------------------------------------------------------------------------------
    def _verificar_requisitos_para_modelo(self,W,L,R,C,T,q):
        if W <= 0 or L<=0 or R <=0 or C <=0:
            return False
        if T in [None, [],{}]:
            return False
        if q in [None,[],{}]:
            return False
        return True
    def _pre_processamento(self):

        DIFP = self._carregar_todos_DIFP(self.T, self.malha)  #tenta carregar.
        if DIFP == None:                        #se nao achou, gera e salva.
            print("não achou DIFP, calculando todos DIFP e salvando.")
            DIFP = self._calcular_todos_DIFP(self.T, self.malha)
            self._salvar_todos_DIFP(self.T,self.malha, DIFP)    # já que calculou, salva.
        print("os DIFP foram carregados na memória.")
        self.DIFP = DIFP        # atribui os valores carregados ou gerados.  

        # NFP gera na hora, é rápido. -----------
        NFP = {}
        for u in range(len(self.T)):
            for t in range(len(self.T)):
                NFP[u,t] = self._gerar_nfp(self.T[u],self.T[t])
                # self._plotar_poligono(self.malha, NFP[u,t],f"NFP_{u}_{t}")
        self.NFP = NFP
        print("todos os NFP foram gerados.")
        pass
    def _iniciar_brkga_ordem(self, pop_size=100,elite_frac=0.3,mutant_frac=0.4, generations=10):
        print("iniciando brkga-ordem, para achar a menor faixa, dados T, q e Malha.")
        brkga_ordem = BRKGA_ordem(sum(self.q), self._rodar_BL,pop_size=pop_size,
                                  mutant_frac=mutant_frac,elite_frac=elite_frac,seed=42)
        brkga_resultado = brkga_ordem.evolve(self.q, generations=generations)

        # best_sequence, best_fitness = brkga_resultado
        # # roda um bl pra montar a solução pra melhor sequencia achada. 
        # # ###Só pra printar?
        # bl = Bottom_Left(self.malha,best_sequence,self.NFP,self.DIFP)
        # bl_resultado = bl.rodar()
        # bl_resultado_pontos = [item[1] for item in bl_resultado]
        # W,L,R,C = self.malha.W,self.malha.L,self.malha.R,self.malha.C

        # self._plotar_resultado(self.malha,bl_resultado_pontos,best_sequence, f"Menor faixa que contém os poligonos: {best_fitness},W:{W},L:{L},R:{R},C:{C}",
        #                        salvar_arquivo=f"{W}_{L}_{R}_{C}/{bl_resultado.__str__()}_{self.q}.png",nao_plotar=True)
        
        return brkga_resultado      # (self.best_sequence, self.best_fitness)
    # Auxiliares--------------------------------------------------------------------------------
    def _transformar_poligono_em_str(self, t):
        str = ""
        for vertice in t:
            x,y = vertice
            str += f"{x}-{y};"
        return str
    def _transformar_malha_em_str(self, malha:Malha):
        str = f"{malha.W}_{malha.L}_{malha.R}_{malha.C}"
        return str
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
    def _transladar_poligono(self, poligono_original, translacao):
        """
        Translada um polígono para uma nova posição.
        
        Args:
            poligono_original: Polígono original (lista de vértices)
            translacao: Tupla (dx, dy) com o deslocamento
            
        Returns:
            Polígono Shapely transladado
        """
        try:
            dx, dy = translacao
            
            # Translada cada vértice
            vertices_transladados = [(x + dx, y + dy) for x, y in poligono_original]
            
            # Cria polígono Shapely
            return Polygon(vertices_transladados)
                
        except Exception as e:
            print(f"Erro ao transladar polígono: {e}")
            return poligono_original
    # Plotagem--------------------------------------------------------------------------------
    def _calcular_area_utilizada_sequencia(self,T,sequencia):      # 
    # def _calcular_area_utilizada_sequencia(T,sequencia):      # estava assim
        """
        Calcula a área total utilizada pela sequência de polígonos posicionados.
        
        Args:
            sequencia: Lista de ints (tipo)
            
        Returns:
            Área total utilizada
        """
        area_total = 0
        for tipo in sequencia:
            if 0 <= tipo < len(self.T):
                poligono_original = Polygon(T[tipo])
                area_total += poligono_original.area
        return area_total
        
    def _plotar_resultado(self, malha, pontos, sequencia, titulo="Resultado do Posicionamento", 
                        mostrar_grade=True, mostrar_numeros=True, mostrar_pontos_difp=False,
                        salvar_arquivo=None, nao_plotar=False):
        """
        Plota o resultado final do posicionamento na forma [(t,(x,y)), (t,(x,y)), ...].
        
        Args:
            malha: Objeto Malha com atributos W, L, C, R
            pontos: Lista de pontos DIFP disponíveis [(x1, y1), (x2, y2), ...]
            sequencia: Lista de tuplas (tipo, ponto_posicao)
            titulo: Título do gráfico
            mostrar_grade: Se True, mostra a grade da malha
            mostrar_numeros: Se True, mostra números dos itens na sequência
            mostrar_pontos_difp: Se True, mostra os pontos DIFP em fundo
            salvar_arquivo: Caminho para salvar o gráfico
        """
        try:
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Configura limites do gráfico
            ax.set_xlim(0, malha.L)
            ax.set_ylim(0, malha.W)
            ax.set_aspect('equal')
            
            # Desenha o retângulo da área útil
            retangulo = patches.Rectangle((0, 0), malha.L, malha.W, 
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
            
            # Plota cada polígono posicionado da sequência
            for i, tipo in enumerate(sequencia):
                # Verifica se o tipo é válido
                if 0 <= tipo < len(self.T):
                    # Obtém o polígono original do tipo
                    poligono_original = self.T[tipo]
                    
                    # Translada o polígono para a posição especificada
                    poligono_posicionado = self._transladar_poligono(poligono_original, pontos[i])
                    
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
                                        linewidth=1.5,
                                        label=label)
                    ax.add_patch(patch)
                    
                    # Marca o ponto de posicionamento (referência)
                    ax.scatter([pontos[i][0]], [pontos[i][1]], 
                            color='black', s=40, zorder=10, marker='x', linewidth=2)
                    
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
            
            # Plota os pontos DIFP disponíveis em fundo (opcional)
            if mostrar_pontos_difp and pontos:
                x_vals = [p[0] for p in pontos]
                y_vals = [p[1] for p in pontos]
                ax.scatter(x_vals, y_vals, color='gray', s=6, alpha=0.2, 
                        zorder=1, label=f'Pontos DIFP ({len(pontos)})')
            
            # Desenha a grade da malha se solicitado
            if mostrar_grade:
                # Linhas verticais
                for i in range(0, malha.L + 1, malha.C):
                    ax.axvline(x=i, color='blue', alpha=0.1, linestyle='-', linewidth=0.3)
                
                # Linhas horizontais
                for i in range(0, malha.W + 1, malha.R):
                    ax.axhline(y=i, color='blue', alpha=0.1, linestyle='-', linewidth=0.3)
                
                # Pontos da grade (opcional)
                pontos_grade_x = []
                pontos_grade_y = []
                for x in range(0, malha.L + 1, malha.C):
                    for y in range(0, malha.W + 1, malha.R):
                        pontos_grade_x.append(x)
                        pontos_grade_y.append(y)
                
                ax.scatter(pontos_grade_x, pontos_grade_y, color='blue', s=2, alpha=0.1, 
                        marker='+', zorder=1)
            
            # Configurações do gráfico
            ax.set_xlabel('Comprimento (L)')
            ax.set_ylabel('Largura (W)')
            ax.set_title(titulo, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.2)
            
            # Remove legendas duplicadas e organiza a legenda
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=9)
            
            # Calcula estatísticas
            total_itens = len(sequencia)
            area_utilizada = self._calcular_area_utilizada_sequencia(self.T,sequencia)
            area_total = malha.W * malha.L
            utilizacao = (area_utilizada / area_total) * 100 if area_total > 0 else 0
            
            # Adiciona informações detalhadas
            info_text = f"""Malha: {malha.W} × {malha.L}
    Resolução: {malha.R} × {malha.C}
    Itens posicionados: {total_itens}
    Tipos utilizados: {len(tipos_utilizados)}
    Área utilizada: {area_utilizada:.1f} ({utilizacao:.1f}%)
    Pontos DIFP: {len(pontos) if pontos else 0}"""
            
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9),
                fontsize=10, fontfamily='monospace')
            
            # Salva o gráfico se solicitado
            if salvar_arquivo:
                plt.savefig(salvar_arquivo, dpi=300, bbox_inches='tight')
                print(f"Gráfico do resultado salvo em: {salvar_arquivo}")
            
            if not nao_plotar:
                plt.tight_layout()
                plt.show()
            
            return fig, ax
            
        except Exception as e:
            print(f"Erro ao plotar resultado: {e}")
            import traceback
            traceback.print_exc()
            plt.close()
            return None, None
    def _plotar_pontos(self, malha, pontos, titulo="Visualização da Malha e Pontos", 
                   mostrar_grade=True, salvar_arquivo=None):
        """
        Plota a malha e os pontos em um gráfico.
        
        Args:
            malha: Objeto Malha com atributos W, L, C, R
            pontos: Lista de pontos [(x1, y1), (x2, y2), ...] ou dicionário de pontos
            titulo: Título do gráfico
            mostrar_grade: Se True, mostra a grade da malha
            salvar_arquivo: Caminho para salvar o gráfico (opcional)
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Configura limites do gráfico
            ax.set_xlim(0, malha.L)
            ax.set_ylim(0, malha.W)
            ax.set_aspect('equal')
            
            # Desenha o retângulo da área útil
            retangulo = patches.Rectangle((0, 0), malha.L, malha.W, 
                                        linewidth=2, edgecolor='black', 
                                        facecolor='lightgray', alpha=0.3)
            ax.add_patch(retangulo)
            
            # Prepara os pontos para plotagem
            if isinstance(pontos, dict):
                # Se for dicionário, extrai os valores
                pontos_lista = list(pontos.values())
            else:
                pontos_lista = pontos
            
            # Extrai coordenadas x e y
            if pontos_lista:
                x_vals = [p[0] for p in pontos_lista]
                y_vals = [p[1] for p in pontos_lista]
                
                # Plota os pontos
                ax.scatter(x_vals, y_vals, color='red', s=20, zorder=5, label=f'Pontos ({len(pontos_lista)})')
            
            # Desenha a grade da malha se solicitado
            if mostrar_grade:
                # Linhas verticais
                for i in range(0, malha.L + 1, malha.C):
                    ax.axvline(x=i, color='blue', alpha=0.2, linestyle='-', linewidth=0.5)
                
                # Linhas horizontais
                for i in range(0, malha.W + 1, malha.R):
                    ax.axhline(y=i, color='blue', alpha=0.2, linestyle='-', linewidth=0.5)
                
                # Pontos da grade
                pontos_grade_x = []
                pontos_grade_y = []
                for x in range(0, malha.L + 1, malha.C):
                    for y in range(0, malha.W + 1, malha.R):
                        pontos_grade_x.append(x)
                        pontos_grade_y.append(y)
                
                ax.scatter(pontos_grade_x, pontos_grade_y, color='blue', s=5, alpha=0.5, 
                        marker='+', label='Grade')
            
            # Configurações do gráfico
            ax.set_xlabel('Comprimento (L)')
            ax.set_ylabel('Largura (W)')
            ax.set_title(titulo)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Adiciona informações da malha
            info_text = f"Malha: W={malha.W}, L={malha.L}\nResolução: C={malha.C}, R={malha.R}"
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Salva o gráfico se solicitado
            if salvar_arquivo:
                plt.savefig(salvar_arquivo, dpi=300, bbox_inches='tight')
                print(f"Gráfico salvo em: {salvar_arquivo}")
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Erro ao plotar pontos: {e}")
            plt.close()
    def _plotar_poligono(self, malha, poligono, titulo="Visualização do Polígono na Malha",
                        mostrar_grade=True, mostrar_vertices=True, preencher=True,
                        cor_poligono='blue', cor_vertices='red', cor_malha='lightgray',
                        salvar_arquivo=None, mostrar_bounds=True):
        """
        Plota um polígono na malha.
        
        Args:
            malha: Objeto Malha com atributos W, L, C, R
            poligono: Polígono Shapely ou lista de vértices
            titulo: Título do gráfico
            mostrar_grade: Se True, mostra a grade da malha
            mostrar_vertices: Se True, mostra os vértices do polígono
            preencher: Se True, preenche o polígono com cor
            cor_poligono: Cor do polígono
            cor_vertices: Cor dos vértices
            cor_malha: Cor da área da malha
            salvar_arquivo: Caminho para salvar o gráfico
            mostrar_bounds: Se True, mostra a bounding box do polígono
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Configura limites do gráfico
            ax.set_xlim(0, malha.L)
            ax.set_ylim(0, malha.W)
            ax.set_aspect('equal')
            
            # Desenha o retângulo da área útil da malha
            retangulo_malha = patches.Rectangle((0, 0), malha.L, malha.W, 
                                            linewidth=2, edgecolor='black', 
                                            facecolor=cor_malha, alpha=0.3)
            ax.add_patch(retangulo_malha)
            
            # Converte para Polygon se for lista de vértices
            if isinstance(poligono, list):
                poligono_shapely = Polygon(poligono)
            else:
                poligono_shapely = poligono
            
            # Extrai coordenadas do polígono
            if hasattr(poligono_shapely, 'exterior'):
                x, y = poligono_shapely.exterior.xy
            else:
                # Se for LinearRing ou outra estrutura
                x = [p[0] for p in poligono_shapely]
                y = [p[1] for p in poligono_shapely]
            
            # Plota o polígono
            patch_poligono = patches.Polygon(list(zip(x, y)), 
                                        closed=True, 
                                        edgecolor=cor_poligono,
                                        facecolor=cor_poligono if preencher else 'none',
                                        alpha=0.6 if preencher else 1.0,
                                        linewidth=2,
                                        label=f'Polígono (área: {poligono_shapely.area:.2f})')
            ax.add_patch(patch_poligono)
            
            # Plota os vértices do polígono
            if mostrar_vertices:
                ax.scatter(x, y, color=cor_vertices, s=50, zorder=5, 
                        label=f'Vértices ({len(x)})')
                
                # Conecta os pontos com linhas para melhor visualização
                ax.plot(x, y, color=cor_poligono, linewidth=1, alpha=0.8)
            
            # Mostra a bounding box do polígono
            if mostrar_bounds and hasattr(poligono_shapely, 'bounds'):
                minx, miny, maxx, maxy = poligono_shapely.bounds
                largura_bbox = maxx - minx
                altura_bbox = maxy - miny
                
                bbox = patches.Rectangle((minx, miny), largura_bbox, altura_bbox,
                                    linewidth=1, edgecolor='orange', 
                                    facecolor='none', linestyle='--',
                                    label=f'BBox: {largura_bbox:.1f}×{altura_bbox:.1f}')
                ax.add_patch(bbox)
            
            # Desenha a grade da malha se solicitado
            if mostrar_grade:
                # Linhas verticais
                for i in range(0, malha.L + 1, malha.C):
                    ax.axvline(x=i, color='gray', alpha=0.2, linestyle='-', linewidth=0.5)
                
                # Linhas horizontais
                for i in range(0, malha.W + 1, malha.R):
                    ax.axhline(y=i, color='gray', alpha=0.2, linestyle='-', linewidth=0.5)
                
                # Pontos da grade
                pontos_grade_x = []
                pontos_grade_y = []
                for x in range(0, malha.L + 1, malha.C):
                    for y in range(0, malha.W + 1, malha.R):
                        pontos_grade_x.append(x)
                        pontos_grade_y.append(y)
                
                ax.scatter(pontos_grade_x, pontos_grade_y, color='gray', s=3, alpha=0.3, 
                        marker='+', label='Grade da malha')
            
            # Configurações do gráfico
            ax.set_xlabel('Comprimento (L)')
            ax.set_ylabel('Largura (W)')
            ax.set_title(titulo)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Adiciona informações detalhadas
            info_text = f"""Malha: W={malha.W}, L={malha.L}
    Resolução: C={malha.C}, R={malha.R}
    Área: {poligono_shapely.area:.2f}
    Centroide: ({poligono_shapely.centroid.x:.2f}, {poligono_shapely.centroid.y:.2f})"""
            
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                fontsize=9)
            
            # Salva o gráfico se solicitado
            if salvar_arquivo:
                plt.savefig(salvar_arquivo, dpi=300, bbox_inches='tight')
                print(f"Gráfico salvo em: {salvar_arquivo}")
            
            plt.tight_layout()
            plt.show()
            
            return fig, ax
            
        except Exception as e:
            print(f"Erro ao plotar polígono: {e}")
            plt.close()
            return None, None
    # Memória --------------------------------------------------------------------------------
    def _salvar_arquivo(self, nome_arquivo: str, conteudo: list) -> bool:
        """
        Salva uma lista de valores numéricos em um arquivo, um valor por linha.
        
        Args:
            nome_arquivo: Caminho do arquivo a ser salvo
            conteudo: Lista de valores numéricos para salvar
            
        Returns:
            True se o arquivo foi salvo com sucesso, False caso contrário
        """
        try:
            # Cria os diretórios pais se não existirem
            Path(nome_arquivo).parent.mkdir(parents=True, exist_ok=True)
            
            # Converte cada elemento para string e junta com quebras de linha
            conteudo_str = '\n'.join(str(item) for item in conteudo)
            
            with open(nome_arquivo, 'w') as f:
                f.write(conteudo_str)
            
            print(f"Arquivo salvo com sucesso: {nome_arquivo}")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar arquivo {nome_arquivo}: {e}")
            return False
    def _carregar_arquivo(self, nome_arquivo: str) -> list:
        """
        Carrega o conteúdo de um arquivo retornando uma lista de inteiros.
        
        Args:
            nome_arquivo: Caminho do arquivo a ser carregado
            
        Returns:
            Lista de inteiros com o conteúdo do arquivo
            Lista vazia se o arquivo não existir ou ocorrer um erro
        """
        def extrair_valores_split(self,texto: str):
            """
            Extrai valores x e y usando split e replace.
            
            Args:
                texto: String no formato '(x,y)'
                
            Returns:
                Tupla (x, y) como inteiros ou None se não encontrar
            """
            try:
                # Remove parênteses e divide pela vírgula
                texto_limpo = texto.strip().replace('(', '').replace(')', '').replace(' ','')
                partes = texto_limpo.split(',')
                
                if len(partes) == 2:
                    x = float(partes[0])
                    y = float(partes[1])
                    return x, y
                return None
            except (ValueError, AttributeError):
                return None
            
        try:
            if not os.path.exists(nome_arquivo):
                print(f"Arquivo não encontrado: {nome_arquivo}")
                return []
                
            with open(nome_arquivo, 'r') as f:
                linhas = f.read().splitlines()
                
            # Filtra linhas vazias e converte para inteiro
            valores = []
            for linha in linhas:
                x,y = extrair_valores_split(self,linha)
                if linha:  # Ignora linhas vazias
                    try:
                        valores.append((x,y))
                    except ValueError:
                        print(f"Aviso: Valor '{linha}' não é um número inteiro válido. Linha ignorada.")
                        
            return valores
            
        except Exception as e:
            print(f"Erro ao carregar arquivo {nome_arquivo}: {e}")
            return []
    def _carregar_todos_DIFP(self,T,malha):         # retorna IFP Discreto ou None
        DIFP = []
        str_malha = self._transformar_malha_em_str(malha)
        for i,t in enumerate(T):
            str_t = self._transformar_poligono_em_str(t)
            difp_t = self._carregar_arquivo(f"{self.nome_pasta}/{str_malha}/{str_t}.difp")
            if difp_t == []:
                return None                 # se nao conseguiu abrir arquivo, sai.
            else:
                DIFP.append(difp_t)
                # self._plotar_pontos(malha, difp_t,titulo=f"IFP_{i} carregado.")
        
        return DIFP
    def _salvar_todos_DIFP(self,T,malha, DIFP):
        str_malha = self._transformar_malha_em_str(malha)
        for t in range(len(T)):
            str_t = self._transformar_poligono_em_str(T[t])
            nome_arquivo = f"{self.nome_pasta}/{str_malha}/{str_t}.difp"
            self._salvar_arquivo(nome_arquivo, DIFP[t])
        pass            

    def _calcular_todos_DIFP(self, T, malha:Malha): #retora pontos d, tal que, f(d)=(x,y)
        DIFP = []
        pontos_malha = malha.retornar_pontos_malha().values()
        for t in range(len(T)):
            lista_vertices_poligono_t = T[t]
            ifp_t = self._gerar_ifp_poligono(malha,lista_vertices_poligono_t)

            difp_t = self._discretizar_poligono(ifp_t,malha,pontos_malha,somente_interior=False)
            DIFP.append(difp_t)
            # self._plotar_pontos(malha,difp_t,f"IFP_{t} calculado.")
        print("calculou IFP-Discreto dos poligonos em T.")
        return DIFP
    def _gerar_ifp_poligono(self,malha, t:list) -> Polygon:
        retangulo_polygon = Polygon([(0,0),(malha.L,0),(malha.L,malha.W),(0,malha.W)])
        t_polygon = Polygon(t)
        ifp = ifp_generator.calculate_ifp(retangulo_polygon, t_polygon)
        return ifp 
    # --------------------------------------------------------------------------------
    def _gerar_nfp(self,u:list,t:list):         # retorna dicionario de NFP_{u,t}:poligono
        u_polygon = Polygon(u)        
        t_polygon = Polygon(t)
        nfp = nfp_generator.calculate_nfp(u_polygon,t_polygon)
        return nfp
    # --------------------------------------------------------------------------------
    
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
# ---------------------------------------------------------------------------