# Malha Previsao de Custos

Repositorio do eixo de previsao de custos do ecossistema Malha IA. O objetivo e separar o Artigo 3, mantendo aqui apenas motor, dashboard, snapshots e documentacao relacionados a custos mensais de manutencao predial.

Repositorio-hub de dados: [adinailson88/malha-ia](https://github.com/adinailson88/malha-ia)  
Dashboard previsto: `https://adinailson88.github.io/malha-previsao-custos/`

## Escopo

Este repositorio trata exclusivamente da previsao temporal de custos em reais. A base operacional completa permanece no hub `malha-ia`; este repositorio consome snapshots pequenos e reproduziveis.

Ficam fora deste repositorio:

1. Classificacao de chamados.
2. Previsao de quantidade de chamados.
3. ODS/ESG.
4. Atualizacao reversa GLPI.
5. Base bruta completa `CHAMADOS` como fonte primaria.

## Componentes

1. `motor_previsao_custos.py`: motor Python especifico para previsao de custos.
2. `dashboard.html`: painel estatico de previsao de custos em R$/mes.
3. `dados/previsao_custo_temporal.json`: serie historica, backtest e forecast por modelo.
4. `dados/previsao_custo_detalhes.json`: parametros, equacoes e configuracoes dos modelos.
5. `dados/previsao_custo_incertezas.json`: intervalos e distribuicoes de incerteza.
6. `dados/previsao_custo_validacao.json`: validacao rolling-origin.
7. `scripts/baixar_dados_hub.py`: baixa snapshots publicos do hub `malha-ia`.
8. `scripts/exportar_dados_csv.py`: gera CSVs canonicos para auditoria e artigo.
9. `.github/workflows/previsao_custo_global.yml`: workflow de compatibilidade que sincroniza as previsoes publicas do hub.
10. `.github/workflows/atualizar-dados-hub.yml`: workflow periodico para atualizar snapshots a partir do hub.

## Execucao local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r execucao_offline\requirements.txt
```

Validacao sintatica:

```powershell
python -m py_compile motor_previsao_custos.py
python -m py_compile scripts\baixar_dados_hub.py
python -m py_compile scripts\exportar_dados_csv.py
python -m py_compile scripts\exportar_dados_json.py
```

Atualizar snapshots a partir do hub:

```powershell
python scripts\baixar_dados_hub.py
python scripts\exportar_dados_csv.py
```

## Recalculo autenticado

O recalculo completo contra Google Sheets fica centralizado no repositorio `malha-ia`, que publica os snapshots em `dados/*.json`. Este repositorio nao precisa de `AUTENTICACAO_GOOGLE` para atualizar o dashboard.

## Particionamento do ecossistema

A estrategia de divisao do `malha-ia` em repositorios menores, a relacao com os artigos e a decisao entre importar dados do hub ou acessar diretamente a planilha estao documentadas em:

[`docs/PARTICIONAMENTO_REPOSITORIOS_E_ARTIGOS.md`](docs/PARTICIONAMENTO_REPOSITORIOS_E_ARTIGOS.md)

## Licenca

Informação insuficiente para verificar.
