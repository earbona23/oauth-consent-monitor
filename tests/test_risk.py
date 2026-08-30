from monitor.demo import demo_data
from monitor.risk import CatalogoRiesgo, evaluar, evaluar_todos

CAT = CatalogoRiesgo()


def _por_app(consents, app):
    return next(c for c in consents if c["app"] == app)


def test_mail_read_mas_offline_por_usuario_es_sospechoso():
    c = {"app": "X", "consent_type": "Principal", "principal": "u@x.com",
         "scopes": ["Mail.Read", "offline_access", "User.Read"], "multi_tenant": True}
    r = evaluar(c, CAT)
    assert r["sospechoso"] is True
    assert any("Persistencia" in s for s in r["señales"])
    assert any("usuario" in s for s in r["señales"])


def test_scope_alto_consentido_por_admin_no_marca_la_senal_de_usuario():
    c = {"app": "Y", "consent_type": "AllPrincipals", "principal": "",
         "scopes": ["Files.Read.All", "User.Read"], "multi_tenant": False}
    r = evaluar(c, CAT)
    assert not any("usuario" in s for s in r["señales"])


def test_scope_no_catalogado_es_desconocido_no_cero():
    c = {"consent_type": "Principal", "scopes": ["Scope.Inventado.All"]}
    r = evaluar(c, CAT)
    assert r["peso"] > 0
    assert r["scopes_detalle"][0]["nivel"] == "desconocido"


def test_offline_access_solo_no_es_sospechoso():
    # offline_access sin un scope de datos no forma el patrón.
    c = {"consent_type": "AllPrincipals", "scopes": ["offline_access", "User.Read"]}
    assert evaluar(c, CAT)["sospechoso"] is False


def test_el_sospechoso_del_demo_queda_primero():
    ev = evaluar_todos(demo_data.despues(), CAT)
    assert ev["consentimientos"][0]["sospechoso"] is True
    assert ev["consentimientos"][0]["app"] == "Free PDF Converter Pro"
    assert ev["resumen"]["sospechosos"] == 1
