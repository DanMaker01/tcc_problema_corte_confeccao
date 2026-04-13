from old_version.modelo_final import Modelo
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

def instancia_marques_mix(escala_1, escala_2):
    '''
    retorna as peças para montar marques_{escala_1} e peças para marques_{escala_2} numa faixa só
    '''
    
    marquesA, qA = instancia_marques(escala_1)
    marquesB, qB = instancia_marques(escala_2)

    T_final = marquesA + marquesB
    q_final = qA + qB

    return T_final, q_final


# ---------------------------------------------------------------------------------

def rodar_diversas_malhas_msm_sequencia():
    from src.bl import Bottom_Left
    from shapely.geometry import Polygon, Point
    from shapely.prepared import prep
    from src.nfp_generator import calculate_nfp
    from src.ifp_generator import calculate_ifp

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

        # plotar_ispp(W,L,R,C,T,res,titulo=f"largura:{largura}",mostrar_plot=False,salvar_arquivo=f"ispp_malha_{W}_{L}_{R}_{C}.png")
        
def rodar_robustez():
    modelo = Modelo()
    # ISPP
    W=104
    L=75
    R=105   
    C=76
    modelos_tamanhos = [1.0]
    Q = [1]
    #
    lista_seeds = range(12,20)                      #já fiz: [0,10) 10gen, [10,20) 10gen, [0,10) 20gen
    geracoes = 20
    #
    for seed_atual in lista_seeds:
        largura_bin = 110
        for i,escala in enumerate(modelos_tamanhos):
            nome = f"seed_{seed_atual}_marques_{escala}_{W}_{L}_{R}_{C}"
            T,q = instancia_marques(escala)
            modelo.adicionar_modelo_roupa(nome,T,q,W,L,R,C,Q[i]) ### não deveria ir Q aqui, tem que reformular pra salvar as instancias, escolher quais vai usar e mandar rodar o PCME
        nome_conjunto = f"{geracoes}gen_seed_{seed_atual}_marques_pp_p_m_g_gg"
        modelo.rodar(largura_bin=largura_bin, nome_conjunto=nome_conjunto, geracoes=geracoes,seed=seed_atual)       # rodar só os que estiverem neste dicionário
    # modelo.rodar(largura_bin=largura_bin)
  
def rodar_marques():
    modelo = Modelo()
    # ISPP
    W=104
    L=75
    R=105   
    C=76
    modelos_tamanhos = [0.85, 0.9, 1.0, 1.06, 1.13]
    Q = [16,16,32,32,16]
    str_Q = "_".join([str(x) for x in Q])
    
    geracoes=10
    seed=42
    #
    
    largura_bin = 110
    for i,escala in enumerate(modelos_tamanhos):
        nome = f"marques_{escala}_{W}_{L}_{R}_{C}"
        T,q = instancia_marques(escala)
        modelo.adicionar_modelo_roupa(nome,T,q,W,L,R,C,Q[i]) ### não deveria ir Q aqui, tem que reformular pra salvar as instancias, escolher quais vai usar e mandar rodar o PCME
    nome_conjunto = f"{geracoes}gen_marques_pp_p_m_g_gg_{str_Q}"
    modelo.rodar(largura_bin=largura_bin, nome_conjunto=nome_conjunto, geracoes=geracoes,seed=seed)       # rodar só os que estiverem neste dicionário
    # modelo.rodar(largura_bin=largura_bin)



def histograma_robustez_ispp(salvar_imagem=False, mostrar_plot=True):
    import matplotlib.pyplot as plt
    import numpy as np

    dados = [
        46.0, 42.0, 44.0, 43.0, 42.0, 42.0, 43.0, 43.0, 43.0, 45.0, 43.0, 45.0,
        42.0, 43.0, 43.0, 42.0, 42.0, 44.0, 42.0, 43.0, 42.0, 43.0, 43.0, 42.0,
        43.0, 42.0, 43.0, 43.0, 42.0, 43.0, 42.0, 42.0, 43.0, 42.0, 43.0, 42.0,
        43.0, 42.0, 43.0, 43.0, 43.0, 44.0, 42.0, 43.0, 43.0, 43.0, 43.0, 43.0,
        43.0, 43.0, 42.0, 44.0, 42.0, 43.0, 43.0, 43.0, 45.0, 42.0, 42.0, 43.0,
        42.0, 43.0, 43.0, 43.0, 43.0, 43.0
    ]

    media = np.mean(dados)
    mediana = np.median(dados)
    total_dados = len(dados)

    plt.figure(figsize=(12, 7))

    # bins quebrados em limites corretos para centralizar
    bins = np.arange(41.5, 47.5, 1)

    n, bins, patches = plt.hist(
        dados,
        bins=bins,
        edgecolor='black',
        alpha=0.7,
        color='skyblue'
    )

    # Adiciona texto centralizado em cada barra
    for i in range(len(n)):
        if n[i] > 0:
            porcentagem = (n[i] / total_dados) * 100
            x_center = (bins[i] + bins[i+1]) / 2  # centro exato
            plt.text(
                x_center, n[i] + 0.3,
                f"{int(n[i])} ({porcentagem:.1f}%)",
                ha='center', va='bottom',
                fontweight='bold', fontsize=11,
                bbox=dict(boxstyle='round,pad=0.2',
                          facecolor='white', alpha=0.8)
            )

    # Lines
    plt.axvline(media, color='red', linestyle='--', linewidth=2,
                label=f'Média = {media:.2f}')
    plt.axvline(mediana, color='orange', linestyle=':', linewidth=2,
                label=f'Mediana = {mediana:.2f}')

    # Eixos e ajustes
    plt.title('Histograma - Robustez ISPP', fontsize=14, fontweight='bold')
    plt.xlabel('Valores')
    plt.ylabel('Frequência')

    # ticks no centro das barras
    plt.xticks(np.arange(42, 47, 1))

    plt.grid(axis='y', alpha=0.3)
    plt.legend()
    plt.ylim(0, max(n) + 6)

    if salvar_imagem:
        plt.savefig('histograma_robustez_ispp.png', dpi=300, bbox_inches='tight')

    if mostrar_plot:
        plt.tight_layout()
        plt.show()
    else:
        plt.close()

    print("=== ESTATÍSTICAS ===")
    print(f"Média: {media:.2f}")
    print(f"Mediana: {mediana:.2f}")
    print(f"Total de dados: {total_dados}")

    print("\n=== FREQUÊNCIAS ===")
    for i, valor in enumerate(range(42, 47)):
        porcentagem = (n[i] / total_dados) * 100
        print(f"Valor {valor}: {int(n[i])} ocorrências ({porcentagem:.1f}%)")

def rodar_pcme_pares_e_unidades():
    modelo = Modelo()
    W=104
    L=122
    R=105
    C=123

    largura_bin = 110
    modelos_tamanhos = [0.85,0.9,1.0,1.06,1.13]
    Q = [1, 2, 2, 2 ,1]
    
    geracoes = 2

    #unid
    for i,escala in enumerate(modelos_tamanhos):
        nome = f"marques_{escala}_{W}_{L}_{R}_{C}"
        T,q = instancia_marques(escala)
        modelo.adicionar_modelo_roupa(nome,T,q,W,L,R,C,Q[i])
    #pares
    for _i, escala_i in enumerate(modelos_tamanhos):
        for _j in range(_i, len(modelos_tamanhos)):   # j >= i
            escala_j = modelos_tamanhos[_j]

            nome = f"marques_{escala_i}_+_{escala_j}_{W}_{L}_{R}_{C}"
            T, q = instancia_marques_mix(escala_1=escala_i, escala_2=escala_j)
            modelo.adicionar_modelo_roupa(nome, T, q, W, L, R, C, 0)

    #rodar
    nome_conjunto = f"{geracoes}gen_marques_mix"
    modelo.rodar(largura_bin,nome_conjunto,geracoes=geracoes,seed=42,pares_inclusos=True)
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
# rodar método principal
# ---------------------------------------------------------------------------------
def main():
    # rodar_robustez()
    # histograma_robustez_ispp(salvar_imagem="ispp_histograma_robustez_marques")
    # rodar_pcme_pares_e_unidades()
    rodar_marques()
    pass

# ---------------------------------------------------------------------------------
main()
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

