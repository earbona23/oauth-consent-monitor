"""Captura de los consentimientos OAuth del tenant vía Graph — SOLO LECTURA.

Enumera las concesiones de permisos delegados (`oauth2PermissionGrants`) y resuelve, por
cada una, la app (service principal cliente) y el usuario que consintió. Normaliza todo a
{ app, app_id, consent_type, principal, scopes, multi_tenant } para que el scoring y el
diff no tengan que conocer la forma cruda de Graph.

Distinto de un auditor de app registrations: acá el sujeto es el CONSENTIMIENTO —lo que un
usuario o admin le concedió a una app, típicamente de terceros—, no la definición de una
app propia.
"""
from __future__ import annotations

from monitor.graph import GraphClient, GraphError

# Tenant propio: se completa desde el primer SP; una app de OTRO tenant es multi-tenant.


def _mapa_sps(g: GraphClient) -> dict[str, dict]:
    mapa: dict[str, dict] = {}
    for sp in g.get_all("/servicePrincipals",
                        {"$select": "id,appId,displayName,appOwnerOrganizationId"}):
        mapa[sp["id"]] = sp
    return mapa


def _nombre_usuario(g: GraphClient, principal_id: str, cache: dict) -> str:
    if not principal_id:
        return ""
    if principal_id in cache:
        return cache[principal_id]
    try:
        u = g.get(f"/users/{principal_id}", {"$select": "userPrincipalName"})
        nombre = u.get("userPrincipalName", principal_id)
    except GraphError:
        nombre = principal_id
    cache[principal_id] = nombre
    return nombre


def recolectar(g: GraphClient, mi_tenant: str = "") -> list[dict]:
    sps = _mapa_sps(g)
    cache_usuarios: dict[str, str] = {}
    consents: list[dict] = []

    for grant in g.get_all("/oauth2PermissionGrants"):
        cliente = sps.get(grant.get("clientId", ""), {})
        owner = cliente.get("appOwnerOrganizationId", "")
        consents.append({
            "app": cliente.get("displayName", grant.get("clientId", "?")),
            "app_id": cliente.get("appId", ""),
            "consent_type": grant.get("consentType", "?"),  # AllPrincipals=admin, Principal=usuario
            "principal": _nombre_usuario(g, grant.get("principalId", ""), cache_usuarios),
            "scopes": [s for s in (grant.get("scope") or "").split() if s],
            "multi_tenant": bool(mi_tenant and owner and owner != mi_tenant),
        })
    return consents
