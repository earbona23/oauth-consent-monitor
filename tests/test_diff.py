from monitor.demo import demo_data
from monitor.diff import comparar


def test_detecta_el_consentimiento_nuevo():
    d = comparar(demo_data.antes(), demo_data.despues())
    apps = {c["app"] for c in d["consentimientos_nuevos"]}
    assert "Free PDF Converter Pro" in apps
    assert d["resumen"]["nuevos"] == 2   # PDF Converter + firma electrónica


def test_detecta_scopes_ampliados():
    antes = [{"app": "App", "app_id": "a1", "consent_type": "Principal",
              "principal": "u@x.com", "scopes": ["User.Read"]}]
    despues = [{"app": "App", "app_id": "a1", "consent_type": "Principal",
                "principal": "u@x.com", "scopes": ["User.Read", "Mail.Read"]}]
    d = comparar(antes, despues)
    assert d["resumen"]["nuevos"] == 0
    assert d["scopes_ampliados"][0]["scopes_agregados"] == ["Mail.Read"]


def test_sin_cambios_no_reporta_nada():
    d = comparar(demo_data.despues(), demo_data.despues())
    assert d["resumen"]["nuevos"] == 0 and d["resumen"]["ampliados"] == 0
