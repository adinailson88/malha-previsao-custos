from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from statistics import mean, median


RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados"
CSV_DIR = RAIZ / "dados_csv"
SAIDA_JSON = DADOS / "analise_gam.json"
SAIDA_CSV = CSV_DIR / "analise_gam.csv"
FONTE = DADOS / "previsao_custo_temporal.json"


def _num(valor):
    if valor in (None, ""):
        return None
    try:
        n = float(str(valor).replace(",", "."))
    except ValueError:
        return None
    return n if math.isfinite(n) else None


def _data(valor: str) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None


def _serie_temporal():
    matriz = json.loads(FONTE.read_text(encoding="utf-8"))
    cab = [str(c) for c in matriz[0]]
    idx_periodo = cab.index("Periodo") if "Periodo" in cab else 0
    idx_alvo = cab.index("Custo Real (R$)")
    serie = []
    for linha in matriz[1:]:
        if not linha or not linha[idx_periodo]:
            break
        alvo = _num(linha[idx_alvo] if idx_alvo < len(linha) else None)
        data = _data(linha[idx_periodo])
        if alvo is None or data is None:
            continue
        serie.append({"periodo": data.date().isoformat(), "mes": data.month, "y": alvo})
    return serie


def _melhor_rmse_publicado():
    matriz = json.loads(FONTE.read_text(encoding="utf-8"))
    idx = next((i for i, linha in enumerate(matriz) if linha and linha[0] == "Modelo" and len(linha) > 2 and linha[2] == "RMSE"), -1)
    if idx < 0:
        return None
    cab = [str(c) for c in matriz[idx]]
    idx_modelo = cab.index("Modelo")
    idx_rmse = cab.index("RMSE")
    candidatos = []
    for linha in matriz[idx + 1:]:
        if not linha or not linha[0]:
            break
        rmse = _num(linha[idx_rmse] if idx_rmse < len(linha) else None)
        if rmse is not None:
            candidatos.append({"modelo": linha[idx_modelo], "RMSE": rmse})
    if not candidatos:
        return None
    melhor = min(candidatos, key=lambda x: x["RMSE"])
    return {"modelo": melhor["modelo"], "RMSE": round(melhor["RMSE"], 4)}


def _ols_slope(valores):
    n = len(valores)
    if n < 2:
        return None
    xs = list(range(n))
    mx = mean(xs)
    my = mean(valores)
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, valores)) / den


def _iqr_outliers(valores):
    if len(valores) < 4:
        return 0
    vals = sorted(valores)
    meio = len(vals) // 2
    q1 = median(vals[:meio])
    q3 = median(vals[-meio:])
    iqr = q3 - q1
    if iqr == 0:
        return 0
    return sum(1 for v in vals if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr)


def _sazonalidade(serie):
    por_mes = {}
    for item in serie:
        por_mes.setdefault(item["mes"], []).append(item["y"])
    medias = {mes: mean(vals) for mes, vals in por_mes.items() if vals}
    if not medias:
        return {"status": "insuficiente", "evidencia": "Sem medias mensais calculaveis."}
    mes_max = max(medias, key=medias.get)
    mes_min = min(medias, key=medias.get)
    return {
        "status": "detectavel",
        "mes_maior_media": mes_max,
        "mes_menor_media": mes_min,
        "amplitude_media_mensal": round(medias[mes_max] - medias[mes_min], 4),
        "evidencia": f"Maior custo medio no mes {mes_max}; menor custo medio no mes {mes_min}.",
    }


def _add_month(periodo: str, passos: int) -> str:
    data = datetime.fromisoformat(periodo)
    mes = data.month - 1 + passos
    ano = data.year + mes // 12
    mes = mes % 12 + 1
    return data.replace(year=ano, month=mes).date().isoformat()


def _features(i: int, mes: int, n_ref: int):
    x = i / max(1, n_ref - 1)
    ang = 2 * math.pi * mes / 12
    return [
        1.0,
        x,
        x * x,
        math.sin(ang),
        math.cos(ang),
        math.sin(2 * ang),
        math.cos(2 * ang),
    ]


def _solve_linear(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            return None
        if pivot != col:
            m[col], m[pivot] = m[pivot], m[col]
        div = m[col][col]
        for j in range(col, n + 1):
            m[col][j] /= div
        for r in range(n):
            if r == col:
                continue
            fator = m[r][col]
            for j in range(col, n + 1):
                m[r][j] -= fator * m[col][j]
    return [m[i][n] for i in range(n)]


def _fit_ridge(x_rows, y_vals, alpha=1e-6):
    p = len(x_rows[0])
    xtx = [[0.0 for _ in range(p)] for _ in range(p)]
    xty = [0.0 for _ in range(p)]
    for row, y in zip(x_rows, y_vals):
        for i in range(p):
            xty[i] += row[i] * y
            for j in range(p):
                xtx[i][j] += row[i] * row[j]
    for i in range(1, p):
        xtx[i][i] += alpha
    return _solve_linear(xtx, xty)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _metricas(real, pred):
    pares = [(r, p) for r, p in zip(real, pred) if r is not None and p is not None]
    if not pares:
        return {}
    erros = [p - r for r, p in pares]
    mae = mean(abs(e) for e in erros)
    rmse = (mean(e * e for e in erros)) ** 0.5
    mape_vals = [abs((p - r) / r) for r, p in pares if r != 0]
    return {
        "n": len(pares),
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "MAPE_percentual": round(mean(mape_vals) * 100, 4) if mape_vals else None,
    }


def _benchmark_aditivo(serie, horizonte=12):
    if len(serie) < 48:
        return {
            "status": "insuficiente",
            "metodo": "base_aditiva_fourier_log1p",
            "evidencia": "Menos de 48 observacoes historicas para holdout de 12 meses.",
        }
    treino = serie[:-horizonte]
    teste = serie[-horizonte:]
    n_ref = len(treino)
    x_train = [_features(i, item["mes"], n_ref) for i, item in enumerate(treino)]
    y_train = [math.log1p(max(0.0, item["y"])) for item in treino]
    beta = _fit_ridge(x_train, y_train)
    if beta is None:
        return {
            "status": "falhou",
            "metodo": "base_aditiva_fourier_log1p",
            "evidencia": "Sistema linear singular no ajuste aditivo.",
        }
    pred_teste = []
    for k, item in enumerate(teste, start=len(treino)):
        z = _dot(_features(k, item["mes"], n_ref), beta)
        pred_teste.append(max(0.0, math.expm1(z)))
    metricas = _metricas([x["y"] for x in teste], pred_teste)
    full_ref = len(serie)
    x_full = [_features(i, item["mes"], full_ref) for i, item in enumerate(serie)]
    y_full = [math.log1p(max(0.0, item["y"])) for item in serie]
    beta_full = _fit_ridge(x_full, y_full) or beta
    forecast = []
    ultimo = serie[-1]["periodo"]
    for h in range(1, horizonte + 1):
        periodo = _add_month(ultimo, h)
        mes = datetime.fromisoformat(periodo).month
        z = _dot(_features(len(serie) + h - 1, mes, full_ref), beta_full)
        forecast.append({"periodo": periodo, "previsao": round(max(0.0, math.expm1(z)), 2)})
    return {
        "status": "executado",
        "metodo": "base_aditiva_fourier_log1p",
        "familia_operacional": "Gaussian sobre log1p(custo), compativel com avaliacao preliminar de Gamma/log",
        "holdout_meses": horizonte,
        "metricas_holdout": metricas,
        "coeficientes": [round(v, 6) for v in beta_full],
        "forecast_12_meses": forecast,
        "leitura": "Benchmark aditivo executavel sem dependencias novas; revisar pontos influentes antes de inferencia GAM completa.",
    }


def gerar():
    serie = _serie_temporal()
    valores = [x["y"] for x in serie]
    n = len(valores)
    media = mean(valores) if valores else 0
    desvio = (sum((v - media) ** 2 for v in valores) / (n - 1)) ** 0.5 if n > 1 else 0
    cv = desvio / media if media else None
    slope = _ols_slope(valores)
    outliers = _iqr_outliers(valores)
    status = "adequado_com_transformacao" if n >= 36 else "parcial"
    benchmark = _benchmark_aditivo(serie)
    melhor_publicado = _melhor_rmse_publicado()
    rmse_benchmark = (benchmark.get("metricas_holdout") or {}).get("RMSE")
    if melhor_publicado and rmse_benchmark is not None:
        delta = rmse_benchmark - melhor_publicado["RMSE"]
        comparacao = {
            "status": "pior_que_melhor_modelo_publicado" if delta > 0 else "melhor_que_melhor_modelo_publicado",
            "modelo_publicado_referencia": melhor_publicado["modelo"],
            "rmse_modelo_publicado": melhor_publicado["RMSE"],
            "rmse_benchmark_aditivo": rmse_benchmark,
            "delta_rmse": round(delta, 4),
        }
    else:
        comparacao = {
            "status": "informacao_insuficiente",
            "evidencia": "Informação insuficiente para verificar.",
        }
    resultado = {
        "artefato": "analise_gam",
        "eixo": "previsao_custos",
        "fonte": str(FONTE.relative_to(RAIZ)).replace("\\", "/"),
        "status_geral": status,
        "alvo": "Custo Real (R$)",
        "familia_recomendada": "Gamma com link log ou Gaussian sobre log1p(custo)",
        "suporte_amostral": {
            "observacoes_historicas": n,
            "minimo_operacional": 36,
            "media": round(media, 4) if valores else None,
            "coeficiente_variacao": round(cv, 4) if cv is not None else None,
            "outliers_iqr": outliers,
        },
        "efeitos_aditivos": [
            {
                "termo": "s(tendencia)",
                "status": "recomendado" if n >= 36 else "parcial",
                "evidencia": f"Inclinacao linear preliminar por mes: R$ {slope:.2f}." if slope is not None else "Informação insuficiente para verificar.",
            },
            {
                "termo": "s(mes, cyclic=True)",
                **_sazonalidade(serie),
            },
            {
                "termo": "tratamento de cauda",
                "status": "obrigatorio",
                "evidencia": f"Foram detectados {outliers} outliers por IQR; custos exigem transformacao/diagnostico de influencia.",
            },
        ],
        "benchmark_aditivo": benchmark,
        "comparacao_modelos_publicados": comparacao,
        "recomendacao_dashboard": "Exibir GAM como modelo explicavel de custo, sempre junto da transformacao e do aviso de cauda longa.",
        "proximas_validacoes": [
            "Ajustar GAM com validacao temporal rolling-origin e comparar contra GradientBoosting, Theta e Ensemble.",
            "Testar log1p(custo) e familia Gamma antes de qualquer afirmacao inferencial.",
            "Revisar residuos e pontos influentes antes de usar curvas suaves no artigo.",
        ],
        "limites": [
            "Este artefato diagnostica adequacao e desenho do GAM; nao declara superioridade empirica.",
            "Sem benchmark temporal executado, usar a frase: Informação insuficiente para verificar.",
        ],
    }
    DADOS.mkdir(exist_ok=True)
    CSV_DIR.mkdir(exist_ok=True)
    SAIDA_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    with SAIDA_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["campo", "valor"])
        w.writerow(["status_geral", resultado["status_geral"]])
        w.writerow(["familia_recomendada", resultado["familia_recomendada"]])
        w.writerow(["observacoes_historicas", n])
        w.writerow(["coeficiente_variacao", resultado["suporte_amostral"]["coeficiente_variacao"]])
        w.writerow(["outliers_iqr", outliers])
        bench = resultado["benchmark_aditivo"]
        mets = bench.get("metricas_holdout", {})
        w.writerow(["benchmark_status", bench.get("status")])
        w.writerow(["benchmark_metodo", bench.get("metodo")])
        w.writerow(["benchmark_RMSE", mets.get("RMSE")])
        w.writerow(["benchmark_MAE", mets.get("MAE")])
        comp = resultado["comparacao_modelos_publicados"]
        w.writerow(["comparacao_status", comp.get("status")])
        w.writerow(["comparacao_modelo_referencia", comp.get("modelo_publicado_referencia")])
        w.writerow(["comparacao_delta_rmse", comp.get("delta_rmse")])
    print(f"Gerado {SAIDA_JSON.relative_to(RAIZ)} e {SAIDA_CSV.relative_to(RAIZ)}")


if __name__ == "__main__":
    gerar()
