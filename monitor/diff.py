"""Diff de dos capturas de consentimientos: reporta SOLO lo nuevo o cambiado.

El valor de vigilar consentimientos no es la foto de hoy, es lo que APARECIÓ desde la
última vez: una app recién consentida con Mail.Read, un scope agregado a una app que ya
existía. Eso es lo que merece una alerta — un consentimiento ilícito es, por definición,
algo nuevo que nadie esperaba.
"""
from __future__ import annotations


def _clave(c: dict) -> tuple:
    # Un consentimiento se identifica por (app, quién consintió).
    return (c.get("app_id", c.get("app")), c.get("consent_type"), c.get("principal", ""))


def comparar(anterior: list[dict], actual: list[dict]) -> dict:
    antes = {_clave(c): c for c in anterior}
    ahora = {_clave(c): c for c in actual}

    nuevos = [ahora[k] for k in ahora if k not in antes]

    scopes_ampliados = []
    for k, actual_c in ahora.items():
        if k not in antes:
            continue
        s_antes = set(antes[k].get("scopes", []))
        s_ahora = set(actual_c.get("scopes", []))
        agregados = sorted(s_ahora - s_antes)
        if agregados:
            scopes_ampliados.append({
                "app": actual_c.get("app"),
                "principal": actual_c.get("principal", ""),
                "scopes_agregados": agregados,
            })

    return {
        "consentimientos_nuevos": nuevos,
        "scopes_ampliados": scopes_ampliados,
        "resumen": {
            "nuevos": len(nuevos),
            "ampliados": len(scopes_ampliados),
        },
    }
