# O Problema do Corte de Tecido

## Termos:

- Faixa de tecido: Trecho de tecido de altura fixa e largura variável.
- Bin: Retangulo de tecido com altura e largura fixas, de onde serão cortados os Produtos finais.
- Produto final: Conjunto de Itens, que devem ser cortados juntos.
- Item: Peça poligonal que compõe um Produto final.

## Objetos:

### Malha
- W,L
- R,C
- gx(), gy()
- D()
- n_to_coord(), coord_to_n()

### Poligono
- pontos            #(o primeiro ponto é chamado de Referência e *precisa ser (0,0)*)
- bounding_box() 

### Modelo (Heuristica? Meta-heuristica?)
- debug_visualizacao
- 

### BRKGA-Ordem
- code()
- decode()
- fitness()

### BL
- 

### BRKGA-Bins
- code()
- decode()
- fitness()



## Pseudo-códigos:


### BRKGA
Dado a quantidade da demanda, e qtd da população 
gera uma população de vetores do tamanho da demanda, de componentes entre [0,1]
Ordena pelos componentes.
manda evoluir


### BL
Dada a Malha, IFP, NFP e fila de Demanda.
Para cada peça p do tipo t da Demanda,
- S = IFP_t
- Para cada peça r do tipo u já posicionada,
- - S = S - NFP_r,p
- Escolhe o ponto BL.


### BRKGA
Dado as larguras das camisas

### Memória Persistente
T


### Modelo
Parametros: W,L,R,C,T,q

Carregar:
- Verifica se tem o NFP deste T. (T/NFP_u_t)
- Verifica se tem o IFP deste T. (T/IFP_t)
- Verifica se tem o IFP discretizado deste T e Malha. (T/Malha_W_L_R_C_DIFP_t)

Pré processamento:
- Dado T, gera NFPs, salva numa pasta. (perceber se já tem)
- Dado W,L,R,C, gera a Malha. 
- Dado a Malha e T, gera IFP e salva. (perceber se já tem)

......

Menor comprimento que contém os itens (de cada variedade):
- BRKGA pra melhor ordem, ele roda um BL como fitness (evitar BLs redundanes,)
- Salvar menor comprimento para cada Produto final.

Menor número de bins gastos para cumprir a demanda:
- BRKGA 1D
