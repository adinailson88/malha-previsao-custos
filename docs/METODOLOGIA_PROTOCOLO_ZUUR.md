# Protocolo de exploracao de dados - Zuur et al. (2010)

Este eixo aplica o protocolo de oito passos de Zuur, Ieno & Elphick (2010) aos snapshots publicos de previsao mensal de custos.

Referencia: Zuur, A.F., Ieno, E.N. & Elphick, C.S. (2010). A protocol for data exploration to avoid common statistical problems. Methods in Ecology and Evolution, 1(1), 3-14. doi:10.1111/j.2041-210X.2009.00001.x.

Aplicacao no artigo: a serie mensal de valores em reais deve ser explorada antes da inferencia preditiva. O diagnostico cobre outliers monetarios, heterocedasticidade, normalidade dos residuos, meses sem custo registrado, colinearidade de covariaveis exogenas, relacoes temporais exploratorias, interacoes por categoria e independencia temporal por validacao rolling-origin.

Artefatos:

1. `scripts/gerar_protocolo_zuur.py`
2. `dados/protocolo_zuur.json`
3. `dados_csv/protocolo_zuur.csv`
4. Bloco "Protocolo de exploracao de dados" em `dashboard.html`

Diagnostico atual: o repositorio ja permite explorar serie temporal e validacao, mas ainda precisa publicar ou sincronizar `previsao_custo_diagnostico.json`, `previsao_custo_residuos.json`, `previsao_custo_qqplot.json`, `previsao_custo_pressupostos.json`, `previsao_custo_granger.json` e `previsao_custo_por_categoria.json` para completar todos os passos.
