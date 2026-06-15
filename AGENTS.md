# Malha Previsao de Custos - Instrucoes de Sessao

Ao iniciar qualquer sessao neste repositorio, ler o `README.md` e `docs/CONTRATO_DADOS.md`.

Este repositorio e derivado do hub:
https://github.com/adinailson88/malha-ia

Escopo permitido:

1. Previsao temporal de custos em reais.
2. Dashboard e snapshots `previsao_custo_*`.
3. Workflows de sincronizacao dos snapshots publicos.
4. Documentacao do Artigo 3.

Fora do escopo:

1. Classificacao de chamados.
2. Previsao de quantidade de chamados.
3. ODS/ESG.
4. Base bruta completa `CHAMADOS`.

Regra de dados:

`malha-ia` permanece como hub central. Este repositorio deve guardar apenas snapshots e artefatos pertinentes ao eixo de custos. Nao exigir `AUTENTICACAO_GOOGLE` neste repositorio; o acesso autenticado a planilha fica centralizado no hub.
