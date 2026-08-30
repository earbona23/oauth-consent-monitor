"""oauth-consent-monitor — vigila los consentimientos OAuth de un tenant M365.

  python -m monitor.cli --demo                      # evalúa consentimientos demo
  python -m monitor.cli snapshot --salida hoy.json  # capturar (demo)
  python -m monitor.cli snapshot --live --salida hoy.json
  python -m monitor.cli diff ayer.json hoy.json     # qué se consintió nuevo
  python -m monitor.cli --live                       # evaluar el tenant real

Código de salida 3 si hay algún consentimiento SOSPECHOSO (patrón de consentimiento
ilícito), para usarlo como alerta en CI o en un cron.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from monitor.config import cargar
from monitor.diff import comparar
from monitor.report import console
from monitor.risk import CatalogoRiesgo, evaluar_todos


def _capturar(cfg) -> list[dict]:
    if cfg.es_demo:
        from monitor.demo import demo_data
        return demo_data.despues()
    from monitor.collect import recolectar
    from monitor.graph import GraphClient
    g = GraphClient(cfg.tenant_id, cfg.client_id, cfg.client_secret)
    return recolectar(g, cfg.tenant_id)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Monitor de consentimientos OAuth (solo lectura)")
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("snapshot", help="Capturar los consentimientos actuales")
    ps.add_argument("--live", action="store_true")
    ps.add_argument("--salida", type=Path, required=True)

    pd = sub.add_parser("diff", help="Comparar dos capturas")
    pd.add_argument("anterior", type=Path)
    pd.add_argument("actual", type=Path)
    pd.add_argument("--json", type=Path)

    p.add_argument("--live", action="store_true", help="Evaluar el tenant real")
    p.add_argument("--demo", action="store_true", help="Modo demo (es el comportamiento por defecto)")
    p.add_argument("--sin-color", action="store_true")
    args = p.parse_args(argv)

    cat = CatalogoRiesgo()

    if args.cmd == "snapshot":
        cfg = cargar(modo="live" if args.live else "demo")
        snap = _capturar(cfg)
        args.salida.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Snapshot escrito: {args.salida} ({len(snap)} consentimientos)", file=sys.stderr)
        return 0

    if args.cmd == "diff":
        anterior = json.loads(args.anterior.read_text(encoding="utf-8"))
        actual = json.loads(args.actual.read_text(encoding="utf-8"))
        d = comparar(anterior, actual)
        # Evaluar riesgo SOLO de lo nuevo, que es lo que amerita atención.
        ev_nuevos = evaluar_todos(d["consentimientos_nuevos"], cat)
        salida = {
            "resumen": {**d["resumen"], "nuevos_sospechosos": ev_nuevos["resumen"]["sospechosos"]},
            "consentimientos_nuevos": ev_nuevos["consentimientos"],
            "scopes_ampliados": d["scopes_ampliados"],
        }
        if args.json:
            args.json.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Informe escrito: {args.json}", file=sys.stderr)
        else:
            print(console.render(ev_nuevos, demo=False, color=not args.sin_color))
        return 3 if ev_nuevos["resumen"]["sospechosos"] else 0

    # Por defecto: evaluar (demo o live)
    cfg = cargar(modo="live" if args.live else "demo")
    ev = evaluar_todos(_capturar(cfg), cat)
    print(console.render(ev, demo=cfg.es_demo, color=not args.sin_color))
    return 3 if ev["resumen"]["sospechosos"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
