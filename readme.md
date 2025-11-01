# O Problema do Corte de Tecido

## Problemas:
- Ao salvar .difp o poligono não pode ter muitos vertices, pois o nome fica muito grande.
- Arredondamento numérico no NFP, para NFP complicados
- Tentar acelerar o BL
- Tentar acelerar os BRKGA

## Termos:
- Faixa de tecido: Trecho de tecido de altura fixa e largura variável.
- Bin: Retangulo de tecido com altura e largura fixas, de onde serão cortados os Produtos finais.
- Produto final: Conjunto de Itens, que devem ser cortados juntos.
- Item: Peça poligonal que compõe um Produto final.

## Pseudo-códigos:
### BRKGA p/ menor faixa
```python
# exemplo
for i in range(10):
    print(i)
```


### BL
Dada a Malha, IFP-Discreto, NFP e fila de Demanda.
Para cada peça p do tipo t na Demanda:
- S = IFP_t
- Para cada peça r do tipo u já posicionada,
- - S = S - NFP_r,p
- Escolhe o ponto BL.
```python
# exemplo
for i in range(10):
    print(i)
```


### BRKGA p/ bin
Dado as larguras das camisas
```python
# exemplo
for i in range(10):
    print(i)
```

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
