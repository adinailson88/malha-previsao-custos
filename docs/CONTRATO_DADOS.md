# Contrato de dados - previsao de custos

## Fonte central

O repositorio `adinailson88/malha-ia` permanece como hub central dos dados. Este repositorio usa snapshots pequenos para dashboard, auditoria e reprodutibilidade do eixo de previsao de custos.

## Arquivos pertinentes

| Aba no Google Sheets | Arquivo JSON | Papel |
|---|---|---|
| `PREVISAO_CUSTO_TEMPORAL` | `dados/previsao_custo_temporal.json` | Serie mensal de custo real, backtest e forecast por modelo |
| `PREVISAO_CUSTO_DETALHES` | `dados/previsao_custo_detalhes.json` | Parametros, equacoes, AIC/BIC e configuracoes dos modelos |
| `PREVISAO_CUSTO_INCERTEZAS` | `dados/previsao_custo_incertezas.json` | Intervalos, percentis e desvio previsto por modelo |
| `PREVISAO_CUSTO_VALIDACAO` | `dados/previsao_custo_validacao.json` | Validacao rolling-origin |
| `CONTEXTO_SAZONAL` | `dados/contexto_sazonal.json` | Contexto de sazonalidade usado pelos motores |
| `FILTROS_DISPONIVEIS` | `dados/filtros_disponiveis.json` | Sufixos para futuras visoes filtradas |
| `Area Manutencao` | `dados/area_manutencao.json` | Area construida e area total como variaveis exogenas/contextuais |

## Indicador-alvo

O alvo do eixo e o custo mensal de manutencao, em reais, extraido da coluna Q da planilha operacional `CHAMADOS`.

Unidade de leitura do dashboard: `R$/mes`.

## Modelos

O snapshot temporal pode conter `ARIMA`, `SARIMAX-12`, `SARIMAX-6`, `Holt-Winters`, `Prophet/UC`, `Theta`, `GradientBoosting`, `LSTM_Forecast` e `Ensemble`.

Nem todos os modelos precisam estar preenchidos em todas as linhas. O dashboard deve tratar vazios como dados ausentes.

## Regioes da serie

| Regiao | Significado |
|---|---|
| `In-sample` | Ajuste historico dentro da janela de treino |
| `Backtest (out-of-sample)` | Previsao validada fora da amostra |
| `Forecast` | Projecao apos o ultimo ponto observado |

## Regra de fronteira

`CHAMADOS` nao deve ser duplicado aqui como fonte primaria. Quando for necessario recalcular custos, usar o fluxo autenticado do hub `malha-ia`; este repositorio consome os snapshots publicos resultantes.

## Secret

Os workflows deste repositorio nao dependem de `AUTENTICACAO_GOOGLE`. A credencial Google, quando necessaria, fica restrita ao hub `malha-ia`.

## Limitacoes

Os arquivos JSON publicados sao snapshots. Se a planilha, o periodo ou os modelos forem atualizados no hub, este repositorio precisa rodar o workflow leve de atualizacao ou receber novo commit dos dados.
