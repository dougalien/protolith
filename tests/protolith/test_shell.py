"""Protolith's shell: the home window, every module in one program, and Magma's Send to Reaction."""
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from protolith.app.server import Shell

BASALT = {"SiO2": 50.5, "TiO2": 1.7, "Al2O3": 14.7, "FeO": 9.4, "Fe2O3": 1.1, "MgO": 7.6, "CaO": 11.4,
          "Na2O": 2.8, "K2O": 0.16}


def _call(port, path, body=None, origin=None):
    headers = {"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"}
    if origin:
        headers["Origin"] = origin
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


@pytest.fixture(scope="module")
def shell(tmp_path_factory):
    from reaction.app.assistant import Ollama

    sh = Shell().start(0, 0, 0, reaction_kw={"workspace": tmp_path_factory.mktemp("rx"),
                                             "model": Ollama("http://127.0.0.1:9", "none")})
    t = threading.Thread(target=sh.serve, daemon=True)
    t.start()
    yield sh
    sh.stop()
    t.join(timeout=10)
    assert not t.is_alive()


def _port(httpd):
    return httpd.server_address[1]


def test_home_lists_the_modules(shell):
    status, body = _call(_port(shell.home), "/")
    assert status == 200 and b"Protolith" in body
    status, body = _call(_port(shell.home), "/api/modules")
    mods = {m["key"]: m for m in json.loads(body)["modules"]}
    assert mods["magma"]["ready"] and mods["reaction"]["ready"]
    assert not mods["metamorphism"]["ready"] and not mods["surface"]["ready"]
    assert mods["magma"]["control"].endswith(f":{_port(shell.magma)}/control")
    for key in ("magma", "reaction"):            # every icon the home window asks for is there
        assert _call(_port(shell.home), f"/static/{key}_mark.svg")[0] == 200
    assert _call(_port(shell.home), "/favicon.ico")[0] == 200


def test_home_refuses_other_pages(shell):
    port = _port(shell.home)
    assert _call(port, "/api/quit", {}, origin="http://evil.example")[0] == 403
    assert not shell.stopped.is_set()
    assert _call(port, "/static/../server.py")[0] == 404


def test_magma_alone_cannot_send():
    from magma.app.server import make_server

    httpd = make_server(0)
    try:
        assert httpd.state.snapshot()["can_send"] is False
    finally:
        httpd.server_close()


def test_magma_sends_a_step_to_reaction(shell):
    from reaction.app import config

    if not (config.external_dir() / "OBIGT" / "inorganic_aq.csv").exists():
        pytest.skip("Reaction's reference data is not installed")
    st = shell.magma.state
    assert st.snapshot()["can_send"] is True
    st.start({"engine": "hp", "process": "crystallize", "mode": "equilibrium", "t_start": 1100, "t_end": 1100,
              "step": 10, "p_bar": 1000, "fo2": "QFM", "bulk": BASALT})
    end = time.time() + 300
    while st.status == "running" and time.time() < end:
        with st.cond:
            st.cond.wait(timeout=5)
    assert st.status == "done", st.message
    status, body = _call(_port(shell.magma), "/api/send-sample", {"step": "-1", "part": "all", "take": "both",
                                                                  "grams": 50})
    reply = json.loads(body)
    assert status == 200 and not reply["problems"], reply
    assert reply["open"].endswith(f":{_port(shell.reaction)}/control")
    card = shell.reaction.session.card
    names = [r["name"] for r in card.reactants]
    assert names == reply["reactants"] and "Magma glass 1100 °C" in names
    assert sum(r["amount"] for r in card.reactants) == pytest.approx(50.0, rel=2e-3)
