"""Reaction's profiles: inside Protolith, Reaction is the hydrothermal module and Weathering the
low-temperature one; each window offers its own starting cards and examples under its own name."""
import http.client
import json
import threading

import pytest

from reaction.app.profiles import PROFILES, profile
from reaction.app.scenario import EXAMPLES, STARTING_CARDS
from reaction.app.server import make_server

from test_app import FakeEngine, ScriptedModel


def test_profiles_name_real_cards_and_split_them():
    for p in PROFILES.values():
        assert set(p.cards) <= set(STARTING_CARDS) and set(p.examples) <= set(EXAMPLES)
        assert p.default in p.cards
    hot, cold = PROFILES["hydrothermal"], PROFILES["surface"]
    assert not set(hot.cards) & set(cold.cards) and not set(hot.examples) & set(cold.examples)
    assert set(hot.cards) | set(cold.cards) == set(STARTING_CARDS)          # every card has a home
    assert set(hot.examples) | set(cold.examples) == set(EXAMPLES)
    assert {"kinetics", "forams"} <= set(cold.examples)          # calcite and a foram dissolving
    for k in cold.examples:                                       # the low-T examples really are cool
        assert EXAMPLES[k].changes.get("t_start_c", 25) <= 40, k
    with pytest.raises(ValueError):
        profile("lunar")


@pytest.fixture
def weathering(tmp_path):
    httpd = make_server(0, workspace=tmp_path, engine=FakeEngine(), model=ScriptedModel(broken=True), profile="surface")
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def _req(httpd, method, path, body=None):
    port = httpd.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request(method, path, body=None if body is None else json.dumps(body),
                 headers={"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"})
    r = conn.getresponse()
    data = r.read()
    conn.close()
    return r.status, data


def test_weathering_window(weathering):
    page = _req(weathering, "GET", "/control")[1].decode()
    assert "<h1>Weathering</h1>" in page and "<title>Weathering:" in page and "/static/weathering_mark.svg" in page
    assert _req(weathering, "GET", "/static/weathering_mark.svg")[0] == 200
    st = json.loads(_req(weathering, "GET", "/api/state")[1])
    assert st["profile"]["name"] == "Weathering"
    assert [c["key"] for c in st["starting_cards"]] == list(PROFILES["surface"].cards)
    assert [e["key"] for e in st["examples"]] == list(PROFILES["surface"].examples)
    assert st["card"]["fluid"] == "gsl_brine"                    # a fresh session starts on the brine card
    assert _req(weathering, "POST", "/api/example", {"key": "forams"})[0] == 200
    assert _req(weathering, "POST", "/api/example", {"key": "vent_energy"})[0] == 400   # Reaction's, not here
    assert _req(weathering, "POST", "/api/reset", {"start": "seawater"})[0] == 400
    assert _req(weathering, "POST", "/api/reset", {})[0] == 200


def test_reaction_alone_keeps_everything(tmp_path):
    httpd = make_server(0, workspace=tmp_path, engine=FakeEngine(), model=ScriptedModel(broken=True))
    try:
        st = httpd.session.snapshot()
        assert len(st["starting_cards"]) == len(STARTING_CARDS) and len(st["examples"]) == len(EXAMPLES)
        assert st["profile"]["name"] == "Reaction"
    finally:
        httpd.server_close()
