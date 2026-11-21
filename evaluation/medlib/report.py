"""Evaluate summaries against criteria.yaml, write report.md and compare BF/MF."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .config import CRITERIA_FILE

ALVO, MINIMO, NAO, INC, NM, COMP = ("CUMPRE_ALVO", "CUMPRE_MINIMO", "NAO_CUMPRE", "INCONCLUSIVO",
                                    "NAO_MEDIDA", "COMPARATIVA")

SECURITY = ["S01", "S02", "S03", "S04", "S12", "S16", "S17", "S18", "S05", "S21"]
UPLOAD = ["U01", "U20", "U19", "U18", "U04", "U08", "U09", "U25", "U15", "U17", "U10"]


def criteria() -> dict:
    return yaml.safe_load(CRITERIA_FILE.read_text())


def _matrix(sm: dict) -> tuple[str, str]:
    if sm.get("admitidos", 0) > 0:
        return NAO, f'{sm["admitidos"]} admitidos: {", ".join(sm.get("casos_admitidos", [])[:12])}'
    if sm.get("inconclusivos", 0) > 0:
        return INC, f'{sm["inconclusivos"]} inconclusivos: {", ".join(sm.get("casos_inconclusivos", [])[:12])}'
    if sm.get("controlos_total") and sm.get("controlos_ok") < sm.get("controlos_total"):
        return NAO, f'controlos {sm["controlos_ok"]}/{sm["controlos_total"]}'
    return ALVO, f'0 admitidos em {sm.get("tentativas", 0)} tentativas'


def evaluate(metric: str, sm: dict | None, crit: dict) -> tuple[str, str]:
    if not sm:
        return NM, ""
    c = crit.get(metric, {})
    try:
        if metric in ("S01", "S02", "S03", "S04", "S16", "S17"):
            return _matrix(sm)
        if metric == "S12":
            if sm.get("invalidas"):
                return INC, f'{sm["invalidas"]} repetições sem controlo positivo'
            if sm.get("censurado") or sm.get("limite_superior_max_ms") is None:
                return NAO, "sem corte durante a janela (>30 s)"
            up = sm["limite_superior_max_ms"]
            if sm.get("eventos_apos_limite", 0) > 0 or not sm.get("controlos_ok"):
                return NAO, f'{up:.0f} ms; eventos após limite={sm.get("eventos_apos_limite")}; controlos={sm.get("controlos_ok")}'
            if up <= c["alvo"]:
                return ALVO, f"{up:.0f} ms"
            return (MINIMO, f"{up:.0f} ms") if up <= c["minimo"] else (NAO, f"{up:.0f} ms")
        if metric == "S18":
            if sm["todas"] > c["minimo"]["todas"]:
                return NAO, f'{sm["todas"]} bindings em todas as interfaces'
            if sm["loopback"] <= c["alvo"]["loopback"]:
                return ALVO, "nenhuma porta interna publicada"
            return MINIMO, f'{sm["loopback"]} só em loopback'
        if metric in ("S05", "U15", "U17", "U18"):
            f = sm.get("fracao")
            if f is None:
                return INC, "sem tentativas"
            if metric == "U18" and sm.get("oom", 0) > c.get("oom", 0):
                return NAO, f'{sm["oom"]} OOM durante recusas'
            return (ALVO, f"{f:.0%}") if f >= c["alvo"] else (NAO, f"{f:.1%}")
        if metric in ("S21", "U10"):
            return COMP, "avaliada em `compare` contra a BF"
        if metric == "U01":
            worst = max((v["max_mib"] or 0) for v in sm["por_servico"].values())
            if any(v["por_tamanho"][s]["processo_morreu"] for v in sm["por_servico"].values() for s in v["por_tamanho"]):
                return NAO, "processo morreu durante uploads"
            return _le(worst, c["alvo"], c["minimo"], "MiB")
        if metric == "U04":
            vals = {k: sm[k]["max_delta_anon_mib"] for k in ("nginx", "seaweedfs")}
            if any(v is None for v in vals.values()):
                return INC, "sem amostras cgroup"
            if all(vals[k] <= c["alvo"][k] for k in vals):
                return ALVO, f"{vals}"
            if all(vals[k] <= c["minimo"][k] for k in vals):
                return MINIMO, f"{vals}"
            return NAO, f"{vals}"
        if metric == "U08":
            comp = sm["por_componente"]
            resid = any((v["residuo_max_kib"] or 0) > 0 for v in comp.values())
            ratio = max((v["max_razao_pico_sobre_F_mais_16MiB"] or 0) for v in comp.values())
            peak = max(v["pico_max_mib"] for v in comp.values())
            if resid:
                return NAO, "resíduos temporários após 60 s"
            if ratio > 1.0:
                return NAO, f"pico {ratio:.2f}×(F+16 MiB)"
            return (ALVO, f"pico máx. {peak} MiB") if peak <= c["alvo"]["pico_mib"] else (MINIMO, f"pico máx. {peak} MiB")
        if metric == "U09":
            vals = sm.get("amostras_500_ms") or []
            if not vals:
                return INC, "sem amostras de 500 MiB"
            if any(v is None for v in vals):
                return NAO, f'{sm.get("falhas_500")} uploads de 500 MiB falharam'
            return _lt(max(vals), c["alvo"], c["minimo"], "ms")
        if metric == "U19":
            if not sm.get("todas_401_403"):
                return NAO, f'estados {sm.get("status")}'
            gw = sm.get("gateway_delta_max_mib")
            if gw is None or gw > c["minimo"]["gateway_delta_mib"]:
                return NAO, f"gateway +{gw} MiB"
            t = sm.get("resposta_apos_cabecalhos_max_ms")
            return (ALVO, f"+{gw} MiB, {t:.0f} ms") if t is not None and t <= c["alvo"]["resposta_ms"] \
                else (MINIMO, f"+{gw} MiB, {t} ms")
        if metric == "U20":
            full = sm.get("rondas_3de3_sem_oom", 0)
            if full >= c["alvo"]["rondas_3de3"]:
                return ALVO, f"{full}/3 rondas"
            return (MINIMO, f"{full}/3 rondas") if full >= c["minimo"]["rondas_3de3"] else (NAO, f"{full}/3 rondas")
        if metric == "U25":
            if sm.get("pares_insuficientes"):
                return INC, "pares com menos de 100 pedidos durante os uploads"
            if sm.get("erros_total", 0) > 0:
                return NAO, f'{sm["erros_total"]} erros'
            r = sm.get("razao_max")
            if r is None:
                return INC, "sem razão"
            return (ALVO, f"{r:.2f}") if r <= c["alvo"]["razao"] else \
                ((MINIMO, f"{r:.2f}") if r <= c["minimo"]["razao"] else (NAO, f"{r:.2f}"))
    except (KeyError, TypeError, ValueError) as exc:
        return INC, f"resumo incompleto ({exc!r})"
    return INC, "métrica desconhecida"


def _le(v: float, alvo: float, minimo: float, unit: str) -> tuple[str, str]:
    if v <= alvo:
        return ALVO, f"{v} {unit}"
    return (MINIMO, f"{v} {unit}") if v <= minimo else (NAO, f"{v} {unit}")


def _lt(v: float, alvo: float, minimo: float, unit: str) -> tuple[str, str]:
    if v < alvo:
        return ALVO, f"{v:.0f} {unit}"
    return (MINIMO, f"{v:.0f} {unit}") if v < minimo else (NAO, f"{v:.0f} {unit}")


def _load(d: Path) -> tuple[dict, dict]:
    summary = json.loads((d / "summary.json").read_text()).get("metrics", {}) if (d / "summary.json").exists() else {}
    manifest = json.loads((d / "manifest.json").read_text()) if (d / "manifest.json").exists() else {}
    return summary, manifest


def write_report(d: Path) -> Path:
    summary, manifest = _load(d)
    crit = criteria()
    lines = [f"# Resultados {manifest.get('campaign', '?')} — {manifest.get('started_at', '')}", "",
             f"Commit `{manifest.get('git', {}).get('head', '?')}` · host `{manifest.get('host', {}).get('cpu', '?')}`",
             ""]
    statuses = {}
    for title, ids in (("RNF 1 — Segurança", SECURITY), ("RNF 2 — Eficiência no upload", UPLOAD)):
        lines += [f"## {title}", "", "| Métrica | Tipo | Mínimo | Alvo | Estado | Valor |", "|---|---|---|---|---|---|"]
        for m in ids:
            c = crit.get(m, {})
            st, val = evaluate(m, summary.get(m), crit)
            statuses[m] = st
            lines.append(f"| {m} | {c.get('tipo', '')} | {_fmt(c.get('minimo'))} | {_fmt(c.get('alvo'))} | {st} | {val} |")
        lines.append("")
    (d / "report.md").write_text("\n".join(lines))
    data = json.loads((d / "summary.json").read_text()) if (d / "summary.json").exists() else {"metrics": {}}
    data["estados"] = statuses
    (d / "summary.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return d / "report.md"


def _fmt(v) -> str:
    if isinstance(v, dict):
        return ", ".join(f"{k}={x}" for k, x in v.items())
    return "" if v is None else str(v)


COMPARABLE_KEYS = [("host", "cpu"), ("host", "machine"), ("docker", "ncpu"), ("docker", "mem_total"),
                   ("hashes", "criteria"), ("hashes", "cases"), ("hashes", "override_limits"), ("corpus_sha", None)]


def compare(bf_dir: Path, mf_dir: Path) -> str:
    bf, mbf = _load(bf_dir)
    mf, mmf = _load(mf_dir)
    crit = criteria()
    warnings = []
    for a, b in COMPARABLE_KEYS:
        va = mbf.get(a, {}).get(b) if b else mbf.get(a)
        vb = mmf.get(a, {}).get(b) if b else mmf.get(a)
        if va != vb:
            warnings.append(f"- manifesto difere em `{a}{'.' + b if b else ''}`: a comparação das métricas afetadas é inválida")
    if mbf.get("campaign") != "BF" or mmf.get("campaign") != "MF":
        warnings.append(f"- campanhas: {mbf.get('campaign')} vs {mmf.get('campaign')} (esperado BF vs MF)")
    lines = ["# Comparação BF vs MF", "", f"BF: `{bf_dir.name}` · MF: `{mf_dir.name}`", ""]
    if warnings:
        lines += ["## Avisos", ""] + warnings + [""]
    lines += ["| Métrica | BF | MF | Estado MF |", "|---|---|---|---|"]
    for m in SECURITY + UPLOAD:
        if m == "S21":
            st, bv, mv = _cmp_s21(bf.get(m), mf.get(m), crit[m])
        elif m == "U10":
            st, bv, mv = _cmp_u10(bf.get(m), mf.get(m), crit[m])
        else:
            bv = evaluate(m, bf.get(m), crit)[1]
            st, mv = evaluate(m, mf.get(m), crit)
        lines.append(f"| {m} | {bv} | {mv} | {st} |")
    out = "\n".join(lines) + "\n"
    (mf_dir / "compare.md").write_text(out)
    return out


def _cmp_s21(b, m, c):
    if not b or not m:
        return NM, "", ""
    deltas = {k: m[k]["mediana_ms"] - b[k]["mediana_ms"] for k in b if k in m}
    worst = max(deltas.values())
    st = ALVO if worst <= c["alvo"] else (MINIMO if worst <= c["minimo"] else NAO)
    return st, ", ".join(f"{k} {b[k]['mediana_ms']:.1f} ms" for k in b), \
        ", ".join(f"{k} {m[k]['mediana_ms']:.1f} ms (Δ {deltas[k]:+.1f})" for k in deltas)


def _cmp_u10(b, m, c):
    if not b or not m:
        return NM, "", ""
    bb, mm = b["mediana_total_ms_por_estrato"], m["mediana_total_ms_por_estrato"]
    ratios = {s: mm[s] / bb[s] for s in bb if s in mm and bb[s] and mm[s]}
    if not ratios:
        return INC, "", ""
    worst = max(ratios.values())
    st = ALVO if worst <= c["alvo"] else (MINIMO if worst <= c["minimo"] else NAO)
    return st, f"{len(bb)} estratos", f"razão máx. {worst:.2f}"
