"""Riesgo de un consentimiento OAuth y detección del patrón de consentimiento ilícito.

Dos capas:
  1. El riesgo del SCOPE (del catálogo editable rules/consent_risk.yaml).
  2. Las SEÑALES DE CONSENTIMIENTO ILÍCITO, que no dependen de un solo scope sino de la
     combinación: persistencia + datos, consentimiento de usuario (no de admin), y app
     de otro tenant. Es la combinación la que delata el ataque, no el scope aislado.
"""
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CATALOGO = Path(__file__).resolve().parent.parent / "rules" / "consent_risk.yaml"

PESOS = {"critico": 100, "alto": 40, "medio": 10, "bajo": 2, "desconocido": 15}
_ORDEN = ["bajo", "desconocido", "medio", "alto", "critico"]

# Scopes que, combinados con offline_access, forman el patrón persistencia + exfiltración.
_DATOS = {"Mail.Read", "Mail.ReadWrite", "Mail.ReadWrite.Shared", "Mail.Send",
          "Files.Read.All", "Files.ReadWrite.All", "Contacts.Read", "Notes.Read.All"}


class CatalogoRiesgo:
    def __init__(self, ruta: Path | None = None) -> None:
        if yaml is None:
            raise SystemExit("Se necesita PyYAML: pip install -r requirements.txt")
        self._d: dict = yaml.safe_load((ruta or CATALOGO).read_text(encoding="utf-8")) or {}

    def nivel(self, scope: str) -> str:
        e = self._d.get(scope)
        return e["nivel"] if e else "desconocido"

    def porque(self, scope: str) -> str:
        e = self._d.get(scope)
        return e["porque"] if e else "Scope no catalogado: revisar qué alcanza."

    def peso(self, scope: str) -> int:
        return PESOS[self.nivel(scope)]


def evaluar(consent: dict, cat: CatalogoRiesgo) -> dict:
    """Recibe un consentimiento normalizado (ver collect.py) y lo puntúa + marca señales."""
    scopes = consent.get("scopes", [])
    peso = sum(cat.peso(s) for s in scopes)

    nivel_max = "bajo"
    for s in scopes:
        if _ORDEN.index(cat.nivel(s)) > _ORDEN.index(nivel_max):
            nivel_max = cat.nivel(s)

    señales: list[str] = []
    tiene_datos = any(s in _DATOS for s in scopes)
    if "offline_access" in scopes and tiene_datos:
        señales.append("Persistencia + acceso a datos (offline_access con un scope de datos)")
    if consent.get("consent_type") == "Principal" and nivel_max in ("alto", "critico"):
        # Consentimiento de UN usuario (no de admin) a un scope peligroso: el vector clásico.
        señales.append("Consentido por un usuario (no un admin) con un scope de alto riesgo")
    if consent.get("multi_tenant"):
        señales.append("App de otra organización (multi-tenant)")

    # 'sospechoso' = patrón de consentimiento ilícito: al menos una señal Y un scope peligroso.
    sospechoso = bool(señales) and nivel_max in ("alto", "critico")

    return {
        "app": consent.get("app", "?"),
        "app_id": consent.get("app_id", ""),
        "consent_type": consent.get("consent_type", "?"),
        "principal": consent.get("principal", ""),
        "scopes": scopes,
        "peso": peso,
        "nivel_max": nivel_max,
        "señales": señales,
        "sospechoso": sospechoso,
        "scopes_detalle": sorted(
            ({"scope": s, "nivel": cat.nivel(s), "porque": cat.porque(s)} for s in scopes),
            key=lambda x: -_ORDEN.index(x["nivel"]),
        ),
    }


def evaluar_todos(consents: list[dict], cat: CatalogoRiesgo) -> dict:
    evaluados = sorted((evaluar(c, cat) for c in consents),
                       key=lambda x: (not x["sospechoso"], -x["peso"]))
    return {
        "resumen": {
            "consentimientos": len(evaluados),
            "sospechosos": sum(1 for e in evaluados if e["sospechoso"]),
            "criticos": sum(1 for e in evaluados if e["nivel_max"] == "critico"),
            "por_usuario": sum(1 for e in evaluados if e["consent_type"] == "Principal"),
        },
        "consentimientos": evaluados,
    }
