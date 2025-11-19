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
    R=416   
    C=301
    # BPP
    modelos_tamanhos = [0.85, 0.9, 1.0, 1.06, 1.13]
    Q = [4,4,8,8,4]
    # modelos_tamanhos = [0.85, 0.9, 1.0, 1.06, 1.13]
    # Q = [1, 1, 1, 1, 1]
    # modelos_tamanhos = [1.13]
    # Q = [1]
    largura_bin = 110
    #

    for i,escala in enumerate(modelos_tamanhos):
        nome = f"marques_{escala}_{W}_{L}_{R}_{C}"
        T,q = instancia_marques(escala)
        modelo.adicionar_modelo_roupa(nome,T,q,W,L,R,C,Q[i]) ### não deveria ir Q aqui
    nome_conjunto = "marques_pp_p_m_g_gg"
    modelo.rodar(largura_bin=largura_bin, nome_conjunto=nome_conjunto)       # rodar só os que estiverem neste dicionário
    # modelo.rodar(largura_bin=largura_bin)

#rodar main
main()

# ---------------------------------------------------------------------------------
