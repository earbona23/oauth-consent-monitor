"""Config del monitor. Demo por defecto, live solo con credenciales, secretos NUNCA en
el repo.

Permisos de Graph que necesita (SOLO LECTURA):
  Directory.Read.All          — service principals y oauth2PermissionGrants
  (User.Read.All ayuda a resolver el UPN de quien consintió; opcional)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

RAIZ = Path(__file__).resolve().parent.parent
CONFIG_LOCAL = RAIZ / "config.yaml"

SCOPES = ("Directory.Read.All", "User.Read.All")


@dataclass
class Config:
    modo: str = "demo"
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = field(default="", repr=False)

    @property
    def es_demo(self) -> bool:
        return self.modo != "live"


def cargar(modo: str = "demo") -> Config:
    cfg = Config(modo=modo)
    if cfg.es_demo:
        return cfg
    if yaml is None:
        raise SystemExit("Modo --live necesita PyYAML: pip install -r requirements.txt")
    datos: dict = {}
    if CONFIG_LOCAL.exists():
        datos = yaml.safe_load(CONFIG_LOCAL.read_text(encoding="utf-8")) or {}
    cfg.tenant_id = os.getenv("OCM_TENANT_ID", datos.get("tenant_id", ""))
    cfg.client_id = os.getenv("OCM_CLIENT_ID", datos.get("client_id", ""))
    cfg.client_secret = os.getenv("OCM_CLIENT_SECRET", datos.get("client_secret", ""))
    faltan = [n for n, v in (("tenant_id", cfg.tenant_id), ("client_id", cfg.client_id),
                             ("client_secret", cfg.client_secret)) if not v]
    if faltan:
        raise SystemExit(
            "Modo --live pero falta: " + ", ".join(faltan) + ".\n"
            "Copiá config.example.yaml a config.yaml, o exportá "
            "OCM_TENANT_ID / OCM_CLIENT_ID / OCM_CLIENT_SECRET."
        )
    return cfg
