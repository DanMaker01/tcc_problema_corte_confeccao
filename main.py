from modelo_final import Modelo
# ---------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------
def _escalar_poligono(poligono, escalar=1.0,arredondamento=7):
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
        T_escalado.append(_escalar_poligono(poligono,escala))
    q = [2,2,1,1,2,2,1,1]
    q_mult = [multiplicador_demanda*x for x in q]
    return T_escalado, q_mult
# ---------------------------------------------------------------------------------

def main():
    modelo = Modelo()
    # ISPP
    W=104
    L=75
    R=105   
    C=76
    # BPP
    # modelos_tamanhos = [0.85, 0.9, 1.0, 1.06, 1.13]
    # Q = [4,4,8,8,4]
    # modelos_tamanhos = [0.85, 0.9, 1.0, 1.06, 1.13]
    # Q = [1, 1, 1, 1, 1]
    modelos_tamanhos = [1.0]
    Q = [1]
    largura_bin = 110
    #

    for i,escala in enumerate(modelos_tamanhos):
        nome = f"TESTE_marques_{escala}_{W}_{L}_{R}_{C}_teste_melhor_sequencia_tam_M"
        T,q = instancia_marques(escala)
        modelo.adicionar_modelo_roupa(nome,T,q,W,L,R,C,Q[i]) ### não deveria ir Q aqui
    nome_conjunto = "marques_pp_p_m_g_gg"
    modelo.rodar(largura_bin=largura_bin, nome_conjunto=nome_conjunto)       # rodar só os que estiverem neste dicionário
    # modelo.rodar(largura_bin=largura_bin)

def debug():
    from bl import Bottom_Left
    from shapely.geometry import Polygon, Point
    from shapely.prepared import prep
    from nfp_generator import calculate_nfp
    from ifp_generator import calculate_ifp

    def gerar_pontos_malha(W,L,R,C) -> dict:
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
    def calcular_IFP_D(W,L,R,C,conjunto_pontos,poligono_t:list):
        retangulo_malha = [(0,0),(L,0),(L,W),(0,W)]
        ifp_poligono = calculate_ifp(retangulo_malha,poligono_t)
        ifp_d = discretizar_poligono(W,L,R,C,conjunto_pontos,ifp_poligono,somente_interior=False)
        return ifp_d
    def discretizar_poligono(W,L,R,C,pontos_a_verificar:dict,poligono_t:Polygon,somente_interior=False,epsilon=1e-7):
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
    def medir_largura_faixa_BL(T, pecas_posicionadas) -> float:
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
                if 0 <= tipo < len(T):
                    # Obtém o polígono do tipo
                    poligono = T[tipo]
                    
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
    def plotar_ispp(W, L, R, C, T, seq, pontos=None, titulo="Resultado do ISPP", 
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
            import os
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
                          label=f'largura: {comprimento_utilizado:.3f}')
            
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
            total_itens = len(seq)
            area_utilizada = _calcular_area_utilizada_sequencia(T, seq)
            area_total = W * L

            # Texto informativo
            info_text = (
                f"Malha: {W} × {L}   |   "
                f"Resolução: {R} × {C}   |   "
                f"Itens: {total_itens}   |   "
                f"Comprimento utilizado: {comprimento_utilizado:.3f}"
            )

            # Adiciona as informações logo abaixo do título
            ax.text(
                0.5, 1.05, info_text,
                transform=ax.transAxes,
                ha='center', va='bottom',
                fontsize=8, color='black',
            )

            # Salva o gráfico se solicitado
            if salvar_arquivo:
                pasta = "resultados_imagens"
                if not os.path.exists(pasta):
                    os.makedirs(pasta)
                caminho_completo =  salvar_arquivo
                # caminho_completo = pasta + "/" + salvar_arquivo              
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
    #-------
    

    W=104
    L=75
    T,q = instancia_marques()
    seq = [6,7,0,1,0,5,2,4,1,4,3,5]

    for R,C in [(53,38),(105,75), (209,151), (417,301), (833,601), (1665,1201)]:
        NFP = {}
        for u in range(len(T)):
            for t in range(len(T)):
                NFP[u,t] = calculate_nfp(Polygon(T[u]),Polygon(T[t]))
        IFP_D = []
        pontos_malha = gerar_pontos_malha(W,L,R,C)
        for poligono_t in T:
            ifp_d = calcular_IFP_D(W,L,R,C,pontos_malha,poligono_t)
            IFP_D.append(ifp_d)

        modelo_bl = Bottom_Left(W,L,R,C,seq,NFP,IFP_D)
        res = modelo_bl.rodar(verbose=True)
        print(res)
        
        largura = medir_largura_faixa_BL(T,res)
        print(f"malha:{W},{L},{R},{C}, largura:{largura}")

        plotar_ispp(W,L,R,C,T,res,titulo=f"largura:{largura}",mostrar_plot=False,salvar_arquivo=f"ispp_malha_{W}_{L}_{R}_{C}.png")
        
    

#rodar main
# main()
debug()

# ---------------------------------------------------------------------------------
