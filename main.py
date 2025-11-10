# ---------------------------------
from modelo_strip import Modelo_Menor_Faixa
from brkga import BRKGA_bins
# ---------------------------------


# ---------------------------------
# Funções
# ---------------------------------


# ---------------------------------
# Modelos Strip
# ---------------------------------
def rodar_modelo_strip(W,L,R,C,T,q,nome_pasta=None):
    modelo = Modelo_Menor_Faixa(W,L,R,C,T,q,nome_pasta=nome_pasta)
    melhor_faixa_encontrada = modelo.rodar()
    
    return melhor_faixa_encontrada      # resultado = (melhor_sequencia, melhor_fitness)
# ---------------------------------
def rodar_strip_albano(W,L,R,C,escalar):
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
    return rodar_modelo_strip(W,L,R,C,T_escalado,demanda_q)
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
    return rodar_modelo_strip(W,L,R,C,T_escalado,demanda_q)
def rodar_strip_marques(W,L,R,C,escalar=1, mult_demanda=1):    
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
    demanda_q = (2,2,1,1,2,2,1,1)
    demanda_q = tuple(mult_demanda*x for x in demanda_q)           #multiplicar demanda

    #
    nome_pasta = f"marques_{escalar}"
    print(nome_pasta)
    return rodar_modelo_strip(W,L,R,C,T_escalado,demanda_q,nome_pasta=nome_pasta)
# ------------------------------------------------------------------
def gerar_demanda_p_m_g_gg(qtd_p,qtd_m,qtd_g,qtd_gg):
    p = 0.9
    m = 1.0
    g = 1.06
    gg= 1.13

    demanda = {
        p  : qtd_p,
        m   : qtd_m,
        g   : qtd_g,
        gg  : qtd_gg,
        }

    return demanda  
def _transformar_malha_em_str(malha):
        str = f"{malha.W}_{malha.L}_{malha.R}_{malha.C}"
        return str
    
def _carregar_menor_strip(nome_pasta,malha):
    """Tenta carregar o arquivo menor_strip.bl da malha."""
    str_malha = _transformar_malha_em_str(malha)
    caminho = f"{nome_pasta}/{str_malha}/menor_strip.bl"

    menor_strip = self._carregar_arquivo(caminho)
    if menor_strip == [] or menor_strip is None:
        return None

    return tuple(menor_strip)  # converte [lista_strip, valor] -> (lista_strip, valor)
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


def _salvar_menor_strip(self, malha, menor_strip: tuple[list, float]):
    """Salva o menor_strip (lista, valor) no arquivo .bl da malha."""
    str_malha = self._transformar_malha_em_str(malha)
    caminho = f"{self.nome_pasta}/{str_malha}/menor_strip.bl"

    lista_strip, valor = menor_strip
    conteudo = [lista_strip, valor]

    # Garante que o diretório existe
    import os
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    self._salvar_arquivo(caminho, conteudo)

def rodar_modelo_marques(W,L,R,C,demanda_tamanhos:dict, largura_bin):
    '''
    demanda_tamanhos : dict[float,int]
    '''
    ## BRKGA-ordem  ---------------------------------------------------------------
    resultado_menores_strip = {}                            # dict = {escala_tam:float, menor_largura_achada:float}
    for escala_tam, ___qtd in demanda_tamanhos.items():     # para cada modelo_tamanho [P,M,G,GG]
        print(f"\n< < < rodando brkga-strip para tam: {escala_tam} > > >")
        ___melhor_seq, melhor_fitness  = rodar_strip_marques(W,L,R,C,escala_tam)

        resultado_menores_strip[escala_tam] = melhor_fitness
    
    print("Menores Faixas encontradas:")
    for modelo_tam, largura_faixa  in resultado_menores_strip.items():
        print(f"modelo_tamanho:{modelo_tam}, largura_faixa:{largura_faixa}")

    # resultado_menores_strip = {0.9:37.9,  ##forçando resultado para debug - apagar
    #                            1.0:43.0,
    #                            1.06:53.26,
    #                            1.13:59.52}
   
    ## BRGKA-bins -------------------------------------------------------------------
    brkga_bin = BRKGA_bins(resultado_menores_strip,demanda_tamanhos,largura_bin,seed=42)
    resultado_brkga_bin = brkga_bin.evolve(num_geracoes=10000)
    num_bins, desperdicio_total, sequencia_de_corte, historico_fitness = resultado_brkga_bin
    print("larguras:",resultado_menores_strip,"\n")
    print(f"num_bins:{num_bins}, desperdicio total:{round(desperdicio_total,10)}, sequencia_de_corte:{sequencia_de_corte}\n")
    demanda_str = "_".join(f"{k}-{v}" for k, v in demanda_tamanhos.items())
    brkga_bin.plotar_resultado_bins(sequencia_de_corte,num_bins,desperdicio_total,historico_fitness,nome_arquivo=f"{W}_{L}_{R}_{C}/{demanda_str}_{largura_bin}.png")
# ---------------------------------
def debug():
    
    #rodar_metodo(W, L, R, C, escala)

    # rodar_strip_marques(104,75,105,76, 0.94)
    # rodar_strip_marques(104,75,105,76, 1.00)
    # rodar_strip_marques(104,75,105,76, 1.06)
    # rodar_strip_marques(104,75,105,76, 1.13)
    
    # rodar_strip_albano(104,50,105,51, 1.00)
    
    # rodar_strip_blazewics(15,20,151,201, 1.00)
    pass 

def main():
    #modelo(W,L,R,C,demanda,largura_bin)
    for j in range(1,5+1):                                      #j de 1 a 5
        dem = gerar_demanda_p_m_g_gg(j,2*j,2*j,j)
        print("rodando modelo marques para demanda:", dem)
        rodar_modelo_marques(104,75,105,76,dem,largura_bin=129) 
    return

# ---------------------------------
# debug()      # teste
main()      # execução principal
# ---------------------------------