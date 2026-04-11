# -----------------------------------------------------
from old_version.brkga import BRKGA_bins
from old_version.instancia import Instancia
# -----------------------------------------------------

# -----------------------------------------------------
class Modelo_BPP:
    def __init__(self,modelos_roupas:dict, largura_bin:float):
        existe_solucao = self._verificar_requisitos_solucao(modelos_roupas,largura_bin)
        if not existe_solucao:
            print("nao há solucao para o BPP com esses parametros",modelos_roupas,largura_bin)
            return
        self.modelos_roupas = modelos_roupas
        self.largura_bin = largura_bin
        pass

    def _verificar_requisitos_solucao(self,modelos_roupas,largura_bin)->bool:
        '''
        True se cumpre os requisitos
        False se NÃO CUMPRE os requisitos
        '''
        if largura_bin <= 0 or modelos_roupas == None:
            return False
        else:
            return True
        

    def rodar(self,gens=100000,seed=42, pares_inclusos=False):
        brkga_resultado_bins = self._iniciar_brkga_bins(generations=gens,seed=seed,pares_inclusos=pares_inclusos)  #diminuindo para testes em casa
        return brkga_resultado_bins         # (num_bins, desperdicio, seq_corte,largura_bin, historico)
        
    def _iniciar_brkga_bins(self,pop_size=100,elite_frac=0.3,mutant_frac=0.4,generations=100000,seed=42,pares_inclusos=False):
        print(f"iniciando brkga-bins, para achar o menor numero de bins dada a demanda Q e larguras das faixas l. gens={generations}")
        # monta
        larg_itens = {}
        demanda   = {}
        for str_modelo, inst in self.modelos_roupas.items():
            inst:Instancia
            larg_itens[str_modelo] = inst.l
            demanda[str_modelo]   = inst.Q
        # roda
        brkga_bins = BRKGA_bins(larg_itens,demanda,self.largura_bin,pop_size=pop_size,elite_frac=elite_frac,mutant_frac=mutant_frac,seed=seed,pares_inclusos=pares_inclusos)
        brkga_resultado = brkga_bins.evolve(num_geracoes=generations)
        brkga_resultado = (brkga_resultado[0],brkga_resultado[1],brkga_resultado[2],self.largura_bin,brkga_resultado[3] )
        return brkga_resultado          # (num_bins, desperdicio, seq_corte,largura_bin, historico)
        

# -----------------------------------------------------