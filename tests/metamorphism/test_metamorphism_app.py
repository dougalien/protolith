"""Metamorphism's windows: the pages, the inputs, a small run end to end, Stop, and the files."""
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from metamorphism import bulk, pseudosection
from metamorphism.app.server import make_server, parse_inputs

PELITE = bulk.PRESETS["pelite"]


@pytest.fixture(scope="module")
def server():
    httpd = make_server(0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def call(httpd, path, body=None, origin=None, host=None):
    port = httpd.server_address[1]
    headers = {"Host": host or f"127.0.0.1:{port}", "Content-Type": "application/json"}
    if origin:
        headers["Origin"] = origin
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


def wait(st, seconds=300):
    end = time.time() + seconds
    while st.status == "running" and time.time() < end:
        with st.cond:
            st.cond.wait(timeout=2)
    return st.status


def test_pages_and_their_files(server):
    for path in ("/control", "/results"):
        status, body, _ = call(server, path)
        page = body.decode()
        assert status == 200 and "<h1>Kafka</h1>" in page and "/static/kafka_mark.svg" in page
        for ref in ("/static/app.css", "/static/meta.css", "/static/common.js"):
            assert ref in page and call(server, ref)[0] == 200
    assert call(server, "/static/control.js")[0] == call(server, "/static/results.js")[0] == 200
    status, ico, _ = call(server, "/favicon.ico")
    assert status == 200 and ico[:4] == b"\x00\x00\x01\x00"     # the K as a Windows .ico
    info = json.loads(call(server, "/api/presets")[1])
    assert "pelite" in info["presets"] and "aluminous pelite" in info["presets"]
    assert {c["kind"] for c in info["cards"]} == {"grid", "point"}
    for c in info["cards"]:                     # every card's run passes the server's own checks
        assert c["rock"] in info["presets"]
        parse_inputs({"bulk": info["presets"][c["rock"]]["wt"], "system": c["system"], "water": c["water"],
                      "kind": c["kind"], "t": c["t"], "p": c["p"]})


def test_refuses_other_hosts_and_origins(server):
    assert call(server, "/api/state", host="evil.example")[0] == 403
    assert call(server, "/api/stop", {}, origin="http://evil.example")[0] == 403
    assert call(server, "/static/../server.py")[0] == 404


def test_inputs_are_checked():
    b, run = parse_inputs({"bulk": PELITE, "kind": "grid", "t": [450, 650, 50], "p": [2, 10, 2]})
    assert run["t"] == [450, 500, 550, 600, 650] and run["p"] == [2, 4, 6, 8, 10] and b.water == "excess"
    bad = [{"bulk": {}, "kind": "point", "t": 500, "p": 5},
           {"bulk": PELITE, "kind": "point", "t": 500, "p": 0},
           {"bulk": PELITE, "kind": "point", "t": "hot", "p": 5},
           {"bulk": PELITE, "kind": "grid", "t": [600, 500, 10], "p": [2, 4, 1]},
           {"bulk": PELITE, "kind": "grid", "t": [300, 1000, 1], "p": [1, 30, 1]},
           {"bulk": {**PELITE, "Xx": 1}, "kind": "point", "t": 500, "p": 5}]
    for d in bad:
        with pytest.raises(ValueError):
            parse_inputs(d)


def test_a_small_pseudosection_end_to_end(server):
    st = server.state
    status, body, _ = call(server, "/api/run", {"bulk": PELITE, "name": "pelite", "kind": "grid",
                                                "t": [500, 550, 50], "p": [6, 6, 1]})
    assert status == 200, body
    assert call(server, "/api/run", {"bulk": PELITE, "kind": "point", "t": 500, "p": 5})[0] == 400  # one at a time
    assert wait(st) == "done", st.message
    snap = json.loads(call(server, "/api/state")[1])
    g = snap["grid"]
    assert g["done"] == [True] and all(c is not None and c >= 0 for c in g["cells"][0])
    assert g["fields"] and all(f["label"].endswith("H2O") for f in g["fields"])
    assert "Qz" in g["minerals"] and g["modes"][0][0]["Qz"] > 20
    pt = json.loads(call(server, "/api/point?i=0&j=1")[1])
    assert pt["t_c"] == 550 and pt["p_kbar"] == 6 and pt["minerals"]
    assert call(server, "/api/point?i=3&j=0")[0] == 404

    status, body, headers = call(server, "/api/sample?i=0&j=1")
    assert status == 200 and "550C_6kbar.sample" in headers["Content-Disposition"]
    smp = json.loads(body)
    assert smp["written_by"]["app"] == "Metamorphism" and smp["fluid"] is None
    assert smp["conditions"]["p_bar"] == 6000 and smp["provenance"]["run"]["phase_set"] == "metapelite"
    assert json.loads(call(server, "/api/sample?i=0&j=1&fluid=1")[1])["fluid"] is not None

    # the pseudosection file opens again as it was
    status, body, _ = call(server, "/api/pseudosection")
    assert status == 200
    saved = json.loads(body)
    assert call(server, "/api/open-pseudosection", saved)[0] == 200
    again = json.loads(call(server, "/api/state")[1])
    assert [f["label"] for f in again["grid"]["fields"]] == [f["label"] for f in g["fields"]]
    assert call(server, "/api/open-pseudosection", {"format": "something else"})[0] == 400

    # a sample opens as the rock, and samples written from it name it as their parent
    status, body, _ = call(server, "/api/open-sample", smp)
    opened = json.loads(body)
    assert status == 200 and set(opened["parts"]) == {"whole", "rock"}
    assert call(server, "/api/run", {"bulk": opened["parts"]["rock"], "name": "again", "kind": "point", "t": 560,
                                     "p": 6, "from_sample": True})[0] == 200
    assert wait(st) == "done", st.message
    assert json.loads(call(server, "/api/sample")[1])["parent"] == smp["id"]
    assert json.loads(call(server, "/api/state")[1])["can_send"] is False
    assert call(server, "/api/send-sample", {"i": 0, "j": 0})[0] == 404       # Reaction lives in Protolith


def test_stop_ends_the_worker_processes():
    b = bulk.from_wt_pct(PELITE, "excess")
    stop = threading.Event()
    threading.Timer(3.0, stop.set).start()
    t0 = time.time()
    with pytest.raises(pseudosection.Stopped):
        pseudosection.compute(b, [450, 500, 550, 600, 650, 700], [4, 8], workers=2, stop=stop)
    assert time.time() - t0 < 30
