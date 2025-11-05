# ---------------------------------
from modelo import Modelo
# ---------------------------------


# ---------------------------------
# Funções
# ---------------------------------

# ---------------------------------
def rodar_modelo(W,L,R,C,T,q):
    modelo = Modelo(W,L,R,C,T,q)
    brkga_resultado = modelo.rodar()
    return brkga_resultado
# ---------------------------------

# ---------------------------------
# Modelos de teste
# ---------------------------------
def rodar_albano(W,L,R,C,escalar):
    T_albano = [
            [(0,0), (966,56), (1983,-86), (2185,152), (2734,131), (3000,681), (2819,814), (2819,1274), (3000,1407), (2734,1957), (2185,1936), (1983,2174), (966,2032), (0,2088)],

            [(0,0), (3034,0), (3034,261), (0,261)],

            [(0,0), (1761,-173), (2183,477), (2183,837), (1761,1487), (0,1314)],

            [(0,0), (796,119), (1592,0), (1666,125), (796,305), (-74,125)],

            [(0,0), (411,65), (800,0), (1189,65), (1600,0), (1500,368), (800,286), (100,368)],

            [(0,0), (936,0), (936,659), (0,659)],

            [(0,0), (1010,70), (1835,-73), (2130,215), (2517,168), (2620,853), (2538,1293), (-56,1293)],

            [(0,0), (2499,0), (2705,387), (2622,934), (2148,967), (1920,1152), (1061,1059), (0,1125)]
            ]
    T_escalado = []
    for poligono in T_albano:
        poligono_escalado = [(round(x*escalar,7),round(y*escalar,7)) for x,y in poligono]
        T_escalado.append(poligono_escalado)
    demanda_q = (1,1,2,2,2,2,1,1)
    return rodar_modelo(W,L,R,C,T_escalado,demanda_q)

def rodar_strip_blazewics(W,L,R,C,escalar):
    T_blazewics = [
            [(0,0), (2,-1), (4,0), (4,3), (2,4), (0,3)],

            [(0,0), (3,0), (2,2), (3,4), (3,5),(1,5), (-1,3), (-1,1)],

            [(0,0), (2,0), (3,1),(3,3), (2,4), (0,4), (-1,3), (-1,1)],

            [(0,0), (2,1),(4,0),(3,2),(4,5),(2,4),(0,5),(1,3)],

            [(0,0), (5,0),(5,5),(4,5),(3,3),(2,2),(0,1)],

            [(0,0), (2,3),(-2,3)],

            [(0,0), (2,0),(2,2), (0,2)],
            ]
    T_escalado = []
    for poligono in T_blazewics:
        poligono_escalado = [(round(x*escalar,7),round(y*escalar,7)) for x,y in poligono]
        T_escalado.append(poligono_escalado)
    demanda_q = (1,1,1,1,1,1,1)
    demanda_q = tuple(2*x for x in demanda_q)           #dobrando a demanda
    return rodar_modelo(W,L,R,C,T_escalado,demanda_q)

def rodar_strip_marques(W,L,R,C,escalar, mult_demanda):    
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
        poligono_escalado = [(round(x*escalar,7),round(y*escalar,7)) for x,y in poligono]
        T_escalado.append(poligono_escalado)
    demanda_q = (1,1,1,1,1,1,1)
    demanda_q = tuple(mult_demanda*x for x in demanda_q)           #multiplicar demanda
    return rodar_modelo(W,L,R,C,T_escalado,demanda_q)

# ---------------------------------
def debug():
    
    #rodar_metodo(W, L, R, C, escala)
    rodar_strip_marques(74,225,75,601, 1.00, 3)
    
    # rodar_blazewics_tamanhos(15,20,151,201, 1.00)
    
    # strip_p  = rodar_albano_tamanhos(W,L,R,C,0.94)
    # strip_g  = rodar_albano_tamanhos(W,L,R,C,1.06)
    # strip_gg = rodar_albano_tamanhos(W,L,R,C,1.13)
    # print(f"P:{strip_p[1]}, M:{strip_m[1]}, G:{strip_g[1]}, GG:{strip_gg[1]}")
    # print(f"P:{strip_p[0]}, M:{strip_m[0]}, G:{strip_g[0]}, GG:{strip_gg[0]}")
    pass 
    
# def main():
#     return
# ---------------------------------
debug()      # teste
# main()      # execução principal
# ---------------------------------