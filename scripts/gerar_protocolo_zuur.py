#!/usr/bin/env python3
"""Gera diagnostico de exploracao de dados segundo Zuur et al. (2010)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados"
CSV_DIR = RAIZ / "dados_csv"
SAIDA_JSON = DADOS / "protocolo_zuur.json"
SAIDA_CSV = CSV_DIR / "protocolo_zuur.csv"

REFERENCIA = (
    "Zuur, A.F., Ieno, E.N. & Elphick, C.S. (2010). A protocol for data "
    "exploration to avoid common statistical problems. Methods in Ecology and "
    "Evolution, 1(1), 3-14. doi:10.1111/j.2041-210X.2009.00001.x"
)


def carregar(nome: str) -> list:
    caminho = DADOS / nome
    if not caminho.exists():
        return []
    return json.loads(caminho.read_text(encoding="utf-8"))


def numero(valor) -> float | None:
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return float(valor)
    if isinstance(valor, str):
        texto = valor.strip().replace("R$", "").replace("%", "").replace(".", "").replace(",", ".")
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None
    return None


def linhas_tabela(tabela: list) -> tuple[list[str], list[list]]:
    if not tabela or not isinstance(tabela[0], list):
        return [], []
    return [str(c) for c in tabela[0]], [r for r in tabela[1:] if any(str(c).strip() for c in r)]


def iqr(valores: list[float]) -> dict:
    xs = sorted(v for v in valores if v is not None)
    if not xs:
        return {"n": 0, "status": "Informação insuficiente para verificar."}
    def pct(p: float) -> float:
        pos = (len(xs) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(xs) - 1)
        frac = pos - lo
        return xs[lo] * (1 - frac) + xs[hi] * frac
    q1, q3 = pct(0.25), pct(0.75)
    dist = q3 - q1
    li, ls = q1 - 1.5 * dist, q3 + 1.5 * dist
    return {
        "n": len(xs), "min": round(xs[0], 2), "q1": round(q1, 2), "q3": round(q3, 2),
        "max": round(xs[-1], 2), "outliers_baixos": sum(1 for v in xs if v < li),
        "outliers_altos": sum(1 for v in xs if v > ls),
    }


def contar_resultados(pressupostos: list, pressuposto: str) -> dict:
    cab, linhas = linhas_tabela(pressupostos)
    try:
        i_tipo = cab.index("Pressuposto")
        i_res = cab.index("Resultado")
    except ValueError:
        return {"status": "Informação insuficiente para verificar."}
    recs = [str(r[i_res]) for r in linhas if len(r) > max(i_tipo, i_res) and str(r[i_tipo]) == pressuposto]
    return {"n_testes": len(recs), "ok": sum("OK" in r for r in recs), "atencao": sum("ATEN" in r.upper() or "CRIT" in r.upper() for r in recs)}


def main() -> int:
    temporal = carregar("previsao_custo_temporal.json")
    validacao = carregar("previsao_custo_validacao.json")
    pressupostos = carregar("previsao_custo_pressupostos.json")
    residuos = carregar("previsao_custo_residuos.json")
    qqplot = carregar("previsao_custo_qqplot.json")
    diagnostico = carregar("previsao_custo_diagnostico.json")

    cab, linhas = linhas_tabela(temporal)
    real_idx = cab.index("Custo Real (R$)") if "Custo Real (R$)" in cab else None
    vencedor_idx = len(cab) - 1
    historico = [
        numero(r[real_idx]) for r in linhas
        if real_idx is not None and len(r) > max(real_idx, vencedor_idx) and str(r[vencedor_idx]) in ("In-sample", "Backtest (out-of-sample)")
    ]
    historico = [v for v in historico if v is not None]

    faltantes = [
        nome for nome, dados in [
            ("dados/previsao_custo_diagnostico.json", diagnostico),
            ("dados/previsao_custo_residuos.json", residuos),
            ("dados/previsao_custo_qqplot.json", qqplot),
            ("dados/previsao_custo_pressupostos.json", pressupostos),
        ] if not dados
    ]

    passos = [
        {"passo": 1, "titulo": "Outliers em Y e covariaveis", "status": "verificado", "evidencia": "dados/previsao_custo_temporal.json", "resultado": iqr(historico), "mudanca_minima": "Exibir outliers do custo mensal e manter tratamento ja existente no motor."},
        {"passo": 2, "titulo": "Homogeneidade de variancia", "status": "precisa calcular", "evidencia": "dados/previsao_custo_pressupostos.json", "resultado": contar_resultados(pressupostos, "Homocedasticidade"), "mudanca_minima": "Sincronizar/exportar PREVISAO_CUSTO_PRESSUPOSTOS do hub."},
        {"passo": 3, "titulo": "Normalidade", "status": "precisa calcular", "evidencia": "dados/previsao_custo_pressupostos.json e dados/previsao_custo_qqplot.json", "resultado": contar_resultados(pressupostos, "Normalidade"), "mudanca_minima": "Publicar Q-Q plot e testes de residuos de custo ja gerados pelo motor."},
        {"passo": 4, "titulo": "Zeros ou ausencia estrutural", "status": "verificado", "evidencia": "dados/previsao_custo_temporal.json", "resultado": {"n_zeros": sum(1 for v in historico if v == 0), "n_observacoes": len(historico)}, "mudanca_minima": "Distinguir mes sem custo registrado de dado ausente."},
        {"passo": 5, "titulo": "Colinearidade entre covariaveis", "status": "precisa calcular", "evidencia": "dados/previsao_custo_pressupostos.json", "resultado": contar_resultados(pressupostos, "Multicolinearidade"), "mudanca_minima": "Sincronizar VIF de regressores exogenos do motor de custos."},
        {"passo": 6, "titulo": "Relacoes entre Y e X", "status": "precisa calcular", "evidencia": "dados/previsao_custo_granger.json", "resultado": {"status": "Informação insuficiente para verificar."}, "mudanca_minima": "Adicionar previsao_custo_granger.json quando o hub publicar a aba correspondente."},
        {"passo": 7, "titulo": "Interacoes", "status": "precisa calcular", "evidencia": "dados/previsao_custo_por_categoria.json", "resultado": {"status": "Informação insuficiente para verificar."}, "mudanca_minima": "Publicar resumo de custo por categoria quando houver recortes suficientes."},
        {"passo": 8, "titulo": "Independencia temporal", "status": "parcial", "evidencia": "dados/previsao_custo_validacao.json", "resultado": {"folds_validacao": max(0, len(validacao) - 1) if isinstance(validacao, list) else 0, "independencia": contar_resultados(pressupostos, "Independência")}, "mudanca_minima": "Manter rolling-origin e publicar Durbin-Watson/Ljung-Box de custo."},
    ]

    out = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "repositorio": "malha-previsao-custos",
        "eixo": "previsao mensal de custos",
        "referencia": REFERENCIA,
        "escopo": "Exploracao sobre snapshots publicos do eixo de custos; sem base bruta e sem credenciais.",
        "diagnostico_do_que_falta": faltantes,
        "passos": passos,
        "metodo_artigo": (
            "No eixo de custos, o protocolo de Zuur et al. (2010) deve ser aplicado sobre a serie mensal "
            "de valores em reais, com diagnostico de outliers monetarios, heterocedasticidade, normalidade "
            "dos residuos, colinearidade de variaveis exogenas e independencia temporal por validacao "
            "rolling-origin. Nesta versao, o repositorio ja permite explorar a serie e a validacao, mas "
            "a publicacao dos snapshots de residuos, Q-Q plot, diagnostico e pressupostos ainda e necessaria "
            "para completar os oito passos."
        ),
    }

    SAIDA_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    CSV_DIR.mkdir(exist_ok=True)
    with SAIDA_CSV.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["passo", "titulo", "status", "evidencia", "mudanca_minima"])
        for p in passos:
            writer.writerow([p["passo"], p["titulo"], p["status"], p["evidencia"], p["mudanca_minima"]])
    print(f"OK {SAIDA_JSON}")
    print(f"OK {SAIDA_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
