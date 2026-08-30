"""Consentimientos DEMO sintéticos, deterministas. Datos INVENTADOS.

Pensados para mostrar el rango: una app legítima consentida por admin con scopes bajos,
una app de productividad razonable, y —el caso que importa— una app de OTRA organización
que un USUARIO consintió con Mail.Read + offline_access: el patrón exacto del ataque de
consentimiento ilícito (persistencia + exfiltración de correo desde una app de terceros).

`antes()` y `despues()` permiten ver el modo diff: entre las dos aparece un consentimiento
nuevo y sospechoso.
"""
from __future__ import annotations


def _c(app, app_id, consent_type, principal, scopes, multi_tenant=False):
    return {"app": app, "app_id": app_id, "consent_type": consent_type,
            "principal": principal, "scopes": scopes, "multi_tenant": multi_tenant}


def antes() -> list[dict]:
    return [
        _c("Portal interno de RRHH", "int-hr", "AllPrincipals", "",
           ["User.Read", "openid", "profile"]),
        _c("Cliente de calendario del equipo", "cal-app", "AllPrincipals", "",
           ["User.Read", "offline_access"]),
    ]


def despues() -> list[dict]:
    return [
        _c("Portal interno de RRHH", "int-hr", "AllPrincipals", "",
           ["User.Read", "openid", "profile"]),
        _c("Cliente de calendario del equipo", "cal-app", "AllPrincipals", "",
           ["User.Read", "offline_access"]),
        # NUEVO y SOSPECHOSO: app de otro tenant, consentida por UN usuario, con
        # Mail.Read + offline_access. Consentimiento ilícito de manual.
        _c("Free PDF Converter Pro", "ext-pdf", "Principal", "ana.gomez@contoso.com",
           ["Mail.Read", "offline_access", "User.Read"], multi_tenant=True),
        # Un caso alto pero consentido por ADMIN (menos sospechoso que el anterior).
        _c("Suite de firma electrónica", "esign", "AllPrincipals", "",
           ["Files.Read.All", "User.Read"]),
    ]
