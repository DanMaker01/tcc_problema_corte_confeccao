# -----------------------------------------------------
from brkga import BRKGA_bins
from instancia import Instancia
# -----------------------------------------------------

# -----------------------------------------------------
class Modelo_BPP:
    def __init__(self,modelos_roupas:dict, largura_bin:float):
        existe_solucao = self._verificar_requisitos_solucao(modelos_roupas,largura_bin)
        if not existe_solucao:
            print("nao há solucao para o BPP com esses parametros",modelos_roupas,largura_bin)
        self.modelos_roupas = modelos_roupas
        self.largura_bin = largura_bin
        pass
    def rodar(self):
        brkga_resultado_bins = self._iniciar_brkga_bins()
        return brkga_resultado_bins
        
    def _iniciar_brkga_bins(self,pop_size=100,elite_frac=0.3,mutant_frac=0.4,generations=10):
        # monta
        tam_itens = {}
        demanda   = {}
        for str_modelo, inst in self.modelos_roupas.items():
            inst:Instancia
            tam_itens[str_modelo] = inst.L
            demanda[str_modelo]   = inst.Q
        # roda
        brkga_bins = BRKGA_bins(tam_itens,demanda,self.largura_bin,pop_size=pop_size,elite_frac=elite_frac,mutant_frac=mutant_frac,seed=42)
        brkga_resultado = brkga_bins.evolve(num_geracoes=10000)
        return brkga_resultado          # (num_bins, desperdicio, seq_corte, historico)
        

# -----------------------------------------------------