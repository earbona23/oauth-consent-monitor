"""Reporte de consola: los consentimientos sospechosos primero, en rojo."""
from __future__ import annotations

_COL = {"critico": "\033[91m", "alto": "\033[93m", "medio": "\033[96m",
        "bajo": "\033[92m", "desconocido": "\033[95m"}
_RESET = "\033[0m"
_ROJO = "\033[91m"


def render(evaluacion: dict, demo: bool, color: bool = True) -> str:
    def c(txt, col):
        return f"{col}{txt}{_RESET}" if color else txt

    r = evaluacion["resumen"]
    out = []
    if demo:
        out.append("  ●  DATOS DEMO — consentimientos sintéticos, ningún tenant real  ●\n")
    out.append("MONITOR DE CONSENTIMIENTOS OAUTH")
    out.append("=" * 58)
    out.append(f"Consentimientos           : {r['consentimientos']}")
    out.append(c(f"Sospechosos (ilícito?)    : {r['sospechosos']}", _ROJO if r['sospechosos'] else ""))
    out.append(f"Con scope crítico         : {r['criticos']}")
    out.append(f"Consentidos por un usuario: {r['por_usuario']}")
    out.append("")

    for e in evaluacion["consentimientos"]:
        cab = f"{e['app']}"
        quien = "admin (todo el tenant)" if e["consent_type"] == "AllPrincipals" else f"usuario {e['principal']}"
        if e["sospechoso"]:
            out.append(c(f"⚠ SOSPECHOSO  {cab}", _ROJO))
        else:
            out.append(f"  {cab}")
        out.append(f"      consentido por: {quien}   ·   riesgo máx: "
                   + c(e["nivel_max"], _COL.get(e["nivel_max"], "")))
        for s in e["scopes_detalle"]:
            if s["nivel"] in ("alto", "critico"):
                out.append(f"        • {c(s['scope'], _COL.get(s['nivel'], ''))} ({s['nivel']}) — {s['porque']}")
        for sig in e["señales"]:
            out.append(c(f"        ⚠ {sig}", _ROJO))
        out.append("")

    out.append("Herramienta de SOLO LECTURA. No revoca ni modifica ningún consentimiento.")
    return "\n".join(out)
