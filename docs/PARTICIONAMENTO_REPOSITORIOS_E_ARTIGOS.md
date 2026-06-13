# Particionamento do Malha IA em repositorios menores e artigos

## 1. Objetivo geral

O repositorio `malha-ia` passa a funcionar como hub central de dados, arquitetura e integracao operacional. A partir dele, os eixos analiticos sao separados em repositorios menores, cada um associado a uma prioridade tecnica e a um artigo especifico.

Essa separacao reduz ruido, melhora a rastreabilidade metodologica e permite que cada artigo tenha um painel, um contrato de dados, um motor e uma documentacao propria.

## 2. Estrutura proposta

| Repositorio | Eixo | Papel no ecossistema | Artigo associado |
|---|---|---|---|
| `malha-ia` | Hub central | Fonte comum de dados, arquitetura, workflows globais e historico original | Base integradora |
| `malha-previsao-chamados` | Previsao de chamados | Modelagem temporal da quantidade de chamados | Artigo 2 |
| `malha-previsao-custos` | Previsao de custos | Modelagem temporal de custos mensais em reais | Artigo 3 |
| `malha-ods-esg` | ODS/ESG | Indicadores ODS 9, 11, 12 e classificacao ESG | Artigo ODS/ESG |
| `malha-estatisticas-associadas` | Estatisticas associadas | Analises complementares, associacoes, correlacoes e descricoes | Artigo/relatorio estatistico |
| repositorios futuros | Demais eixos | Modulos que nao pertencem aos grupos acima | A definir |

## 3. Regra central de arquitetura

O `malha-ia` nao deve ser abandonado. Ele deve ser enxugado e mantido como fonte de verdade operacional.

Os repositorios menores nao devem copiar a base bruta completa `CHAMADOS`. Eles devem guardar apenas:

1. motor especifico do eixo;
2. dashboard especifico;
3. snapshots JSON pertinentes;
4. CSVs derivados para auditoria e artigo;
5. contrato de dados;
6. workflows do eixo;
7. documentacao metodologica.

## 4. Fluxo recomendado de dados

```text
Google Sheets / CHAMADOS
        |
        | acesso autenticado, quando necessario
        v
malha-ia
        |
        | JSONs publicos enxutos em dados/
        v
repositorios menores
        |
        | dashboards, CSVs, documentacao e artigos
        v
GitHub Pages / artigo especifico
```

## 5. Dois modos de funcionamento

### 5.1. Modo leve: importar do hub

Este e o modo recomendado para leitura, painel, auditoria e escrita dos artigos.

Nesse modo, o repositorio menor:

1. baixa os JSONs publicados no `malha-ia`;
2. gera CSVs locais;
3. publica o dashboard no GitHub Pages;
4. documenta o contrato de dados;
5. nao acessa diretamente a planilha Google;
6. nao precisa de secret.

Exemplo:

```powershell
python scripts\baixar_dados_hub.py
python scripts\exportar_dados_csv.py
```

Vantagens:

1. reduz risco de expor credenciais;
2. deixa o repositorio mais simples;
3. facilita publicar painel publico;
4. evita duplicar a base `CHAMADOS`;
5. preserva o `malha-ia` como fonte comum.

### 5.2. Modo pesado: recalcular na planilha

Este modo so e necessario quando o repositorio menor precisa recalcular dados, escrever novas abas ou atualizar resultados diretamente no Google Sheets.

Nesse modo, o repositorio menor:

1. usa o motor Python do eixo;
2. autentica via Google Sheets API;
3. reconstrui `autenticacao_google.json` no workflow;
4. precisa do secret `AUTENTICACAO_GOOGLE`;
5. escreve ou atualiza abas na planilha operacional.

Exemplo no eixo de custos:

```powershell
python motor_previsao_custos.py --apenas-previsao-custos
```

## 6. API da planilha e secrets

Nem todo repositorio precisa acessar a planilha diretamente.

A API Google Sheets so e necessaria quando houver uma destas necessidades:

1. recalcular indicadores ou previsoes a partir da aba `CHAMADOS`;
2. criar ou atualizar abas no Google Sheets;
3. executar workflow pesado com motor Python;
4. validar dados diretamente na planilha operacional.

Para dashboard, artigo e leitura publica, basta importar os JSONs do `malha-ia`.

## 7. Secret `AUTENTICACAO_GOOGLE`

Quando o acesso direto a planilha for necessario, o workflow usa o secret:

```text
AUTENTICACAO_GOOGLE
```

O valor esperado nao e o JSON puro. O valor esperado e o conteudo do JSON da conta de servico convertido para Base64.

O workflow reconstrui a credencial assim:

```bash
echo "$AUTENTICACAO_GOOGLE" | base64 -d > autenticacao_google.json
```

Portanto:

1. o JSON da conta de servico fica fora do Git;
2. o valor Base64 fica no GitHub Secret;
3. o arquivo `autenticacao_google.json` e reconstruido apenas durante a execucao;
4. os repositorios publicos nao devem conter credenciais.

## 8. Quando usar apenas o hub

Usar apenas importacao do hub quando o objetivo for:

1. publicar dashboard;
2. escrever artigo;
3. gerar CSV para auditoria;
4. explicar metodologia;
5. preservar resultado ja calculado;
6. separar um eixo sem recalcular a planilha.

Nesse caso, o repositorio menor deve ter scripts como:

```powershell
python scripts\baixar_dados_hub.py
python scripts\exportar_dados_csv.py
```

## 9. Quando usar API direta

Usar API direta quando o objetivo for:

1. recalcular previsoes;
2. atualizar abas no Google Sheets;
3. gerar novos snapshots ainda inexistentes no hub;
4. rodar experimento automatizado;
5. produzir dados novos, e nao apenas consumir dados existentes.

Nesse caso, configurar o secret antes de executar o workflow pesado.

## 10. Como enxugar o `malha-ia`

Depois que os repositorios derivados estiverem estabilizados, o `malha-ia` pode ser reduzido para:

1. hub de dados publicados;
2. contratos comuns;
3. workflows globais de atualizacao;
4. documentacao de arquitetura;
5. historico e referencia dos motores originais;
6. ponte autenticada com Google Sheets.

O que pode sair gradualmente do `malha-ia`:

1. dashboards especificos ja migrados;
2. documentacao de artigo especifico;
3. CSVs duplicados sem uso no hub;
4. scripts que pertencem claramente a um unico eixo;
5. artefatos de desenvolvimento que nao sao fonte de verdade.

## 11. Beneficio para os artigos

Cada artigo passa a ter um repositorio proprio com escopo verificavel.

Isso facilita:

1. citar exatamente quais dados foram usados;
2. congelar snapshots;
3. revisar metodologia por eixo;
4. publicar painel especifico;
5. separar resultados de chamados, custos, ODS/ESG e estatisticas;
6. evitar que um artigo dependa de arquivos irrelevantes de outro eixo.

## 12. Decisao operacional recomendada

A estrategia mais segura e:

1. manter o `malha-ia` como hub central;
2. fazer os repositorios menores consumirem JSONs do hub por padrao;
3. deixar workflows pesados disponiveis, mas dependentes de secret;
4. configurar `AUTENTICACAO_GOOGLE` apenas nos repositorios que realmente forem recalcular dados;
5. nao duplicar `CHAMADOS`;
6. nao publicar credenciais;
7. documentar em cada repositorio a fronteira exata do eixo.

## 13. Resumo executivo

Para leitura, painel e artigo, basta importar do `malha-ia`.

Para recalcular, escrever ou atualizar a planilha, precisa API Google Sheets e secret.

O particionamento nao substitui o hub. Ele transforma o hub em uma base operacional comum e cria repositorios menores, mais limpos e diretamente associados aos artigos.
