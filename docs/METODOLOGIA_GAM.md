# Camada GAM na previsao de custos

Este repositorio passa a documentar GAM como camada explicavel para custos mensais de manutencao. Como custos possuem cauda longa, zeros eventuais e pontos influentes, o GAM deve ser tratado com mais cautela que no eixo de quantidade de chamados.

## Papel metodologico

O desenho recomendado e usar familia Gamma com link log ou Gaussian sobre `log1p(custo)`, sempre registrando transformacao, pontos influentes e residuos. A camada GAM e adequada para explicar tendencia, sazonalidade mensal e efeito de covariaveis institucionais, mas nao substitui GradientBoosting, Theta, SARIMAX, LSTM_Forecast ou Ensemble sem benchmark temporal.

## Artefatos

- `scripts/gerar_analise_gam.py`: gera o diagnostico local de adequacao.
- `dados/analise_gam.json`: contrato consumido pelo dashboard.
- `dados_csv/analise_gam.csv`: resumo tabular para auditoria e artigo.

## Criterio de leitura

O dashboard deve mostrar a camada GAM junto do aviso de transformacao e cauda longa. Antes de usar curvas suaves em artigo, e necessario verificar influencia, autocorrelacao dos residuos e validacao rolling-origin.

O script tambem gera um `benchmark_aditivo` operacional sem dependencia nova, baseado em tendencia e sazonalidade Fourier sobre `log1p(custo)`. Esse benchmark serve para triagem e comparacao inicial; o ajuste GAM completo com familia Gamma/log continua dependendo de ambiente estatistico com `statsmodels`/`scipy` e revisao dos pontos influentes.

Quando o benchmark GAM nao tiver sido executado, a conclusao deve ser: Informação insuficiente para verificar.
