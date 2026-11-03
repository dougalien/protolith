"""The sample file: one rock and/or fluid at a stated temperature and pressure, passed between modules.

A sample is a *state*, not a picture of a result.  It holds the bulk composition, the conditions, and
each phase with its own oxide composition, so the module that opens it can recompute everything itself
with its own thermodynamic data.  No module trusts another module's derived numbers.

File layout (JSON, ``.sample``), version 1:

    format, version          "protolith-sample", 1
    id, parent               this sample's id, and the id of the sample it came from (or null)
    written_by, written_at   {"app": "Magma", "version": "0.0.1"}, ISO time
    note                     free text
    conditions               {"t_c", "p_bar", "fo2" (buffer text or null), "log_fo2" (or null)}
    bulk_wt_pct              oxide wt% of the whole sample (melt + solids + fluid), normalized to 100
    total_grams              grams of the whole sample
    melt                     {"grams", "wt_pct"} or null
    phases                   [{"name", "grams", "wt_pct", "end_members", "formula", "model"}]
                             end_members: mole fractions in the named model's own end members
    fluid                    {"grams", "wt_pct"} or null (a fluid's species come in a later version)
    provenance               {"engine", "dataset", "run"}: which thermodynamic data made it, and how

Oxide names follow Magma's list (SiO2 ... CO2), iron as FeO and Fe2O3 separately.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

FORMAT = "protolith-sample"
VERSION = 1
SUFFIX = ".sample"

OXIDE_NAMES = ("SiO2", "TiO2", "Al2O3", "Fe2O3", "Cr2O3", "FeO", "MnO", "MgO", "NiO", "CoO", "CaO",
               "Na2O", "K2O", "P2O5", "H2O", "CO2")


class SampleError(ValueError):
    """A sample file that cannot be read: the message says what is wrong, in plain words."""


@dataclass
class Phase:
    name: str                                   # the writing module's phase name, e.g. "olivine"
    grams: float
    wt_pct: dict[str, float]                    # the phase's own oxide composition
    end_members: dict[str, float] = field(default_factory=dict)
    formula: str = ""
    model: str = ""                             # e.g. "HP olivine (Holland, Green and Powell 2018)"


@dataclass
class Sample:
    conditions: dict
    bulk_wt_pct: dict[str, float]
    total_grams: float
    phases: list[Phase] = field(default_factory=list)
    melt: dict | None = None
    fluid: dict | None = None
    provenance: dict = field(default_factory=dict)
    note: str = ""
    written_by: dict = field(default_factory=dict)
    written_at: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent: str | None = None

    # ---- file --------------------------------------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        return {"format": FORMAT, "version": VERSION, **d}

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        if path.suffix != SUFFIX:
            path = path.with_suffix(SUFFIX)
        if not self.written_at:
            self.written_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        path.write_text(json.dumps(self.to_dict(), indent=1), encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, d: dict) -> "Sample":
        if not isinstance(d, dict) or d.get("format") != FORMAT:
            raise SampleError("this is not a Protolith sample file")
        v = d.get("version")
        if not isinstance(v, int) or v > VERSION:
            raise SampleError(f"sample file version {v} is newer than this app reads (version {VERSION}); "
                              f"update the app")
        try:
            phases = [Phase(**p) for p in d.get("phases", [])]
            s = cls(conditions=dict(d["conditions"]), bulk_wt_pct=_oxides(d["bulk_wt_pct"]),
                    total_grams=float(d["total_grams"]), phases=phases, melt=d.get("melt"),
                    fluid=d.get("fluid"), provenance=d.get("provenance", {}), note=d.get("note", ""),
                    written_by=d.get("written_by", {}), written_at=d.get("written_at", ""),
                    id=d.get("id") or uuid.uuid4().hex, parent=d.get("parent"))
        except (KeyError, TypeError) as e:
            raise SampleError(f"sample file is missing or has a wrong entry: {e}") from None
        for p in s.phases:
            p.wt_pct = _oxides(p.wt_pct)
            if p.grams < 0:
                raise SampleError(f"{p.name} has a negative mass")
        for key in ("t_c", "p_bar"):
            if not isinstance(s.conditions.get(key), (int, float)):
                raise SampleError(f"conditions need a number for {key}")
        return s

    @classmethod
    def load(cls, path: str | Path) -> "Sample":
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SampleError(f"sample file is not valid JSON ({e.msg}, line {e.lineno})") from None
        return cls.from_dict(d)

    # ---- views -------------------------------------------------------------------------------
    @property
    def solid_grams(self) -> float:
        return sum(p.grams for p in self.phases)

    def child(self, **changes) -> "Sample":
        """A new sample made from this one: a new id, this one as its parent."""
        d = self.to_dict()
        d.update(changes, id=uuid.uuid4().hex, parent=self.id, written_at="")
        return Sample.from_dict(d)


def _oxides(wt) -> dict[str, float]:
    if not isinstance(wt, dict):
        raise SampleError("an oxide composition must be a table of oxide: wt%")
    unknown = sorted(set(wt) - set(OXIDE_NAMES))
    if unknown:
        raise SampleError(f"unknown oxide(s): {', '.join(unknown)}")
    out = {ox: float(v) for ox, v in wt.items() if float(v) != 0.0}
    if any(v < 0 for v in out.values()):
        raise SampleError("an oxide amount is negative")
    return out


def normalized(wt: dict[str, float]) -> dict[str, float]:
    s = sum(wt.values())
    return {ox: 100.0 * v / s for ox, v in wt.items() if v > 0} if s > 0 else {}


def mix(parts: list[tuple[float, dict[str, float]]]) -> dict[str, float]:
    """Oxide wt% of several (grams, wt%) parts together."""
    out: dict[str, float] = {}
    for g, wt in parts:
        s = sum(wt.values())
        for ox, v in wt.items():
            out[ox] = out.get(ox, 0.0) + g * v / s if s > 0 else out.get(ox, 0.0)
    return normalized(out)
