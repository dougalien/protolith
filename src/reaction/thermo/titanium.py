"""Dissolved titanium: Ti(OH)4(aq), Ti(OH)3+ and Ti(OH)5-, from rutile solubility.

OBIGT lists rutile, ilmenite and titanite, but no dissolved Ti species, so without this module none of
them can take part in a run and the titanium of a rock is left out.  Here the three Ti(IV) hydrolysis
species are defined by their equilibrium with rutile, measured from 100 to 300 C at 200 bar over pH 1
to 13 (Knauss, Dibley, Bourcier and Shaw 2001, Applied Geochemistry 16, 1115-1128):

    rutile + H+ + H2O   = Ti(OH)3+          log Ks3      (Table 3)
    rutile + 2 H2O      = Ti(OH)4(aq)       log Ks4
    rutile + 3 H2O      = Ti(OH)5- + H+     log Ks5

The 25 C values come from their van't Hoff regression (Table 5: Delta G_r 298 = 33.3, 43.5 and 112.0
kJ/mol).  The printed tables in the PDF lost their minus signs; every log K here is negative, as the
Delta G_r values of Table 5 require.  Each log K is fitted here to log K = a + b/T + c log10 T, the form
the authors used, weighted by their errors.

Pressure: the experiments were at 200 bar.  For Ti(OH)4(aq) the volume of reaction of Antignano and
Manning (2008, Chemical Geology 255, 283-293; rutile = TiO2,aq, Delta V_r = -3.4 cm3/mol) carries log
Ks4 to other pressures; the two charged species have no measured volume and are held at their 200 bar
values.

High temperature: from 700 C Ti(OH)4(aq) follows Antignano and Manning's rutile solubility in pure
water (their Eq. 10, measured at 7 to 20 kbar), which is 4 to 5 log units above an extrapolation of the
low-temperature data.  Between 300 and 700 C nothing has been measured; log Ks4 is a straight line in
1/T between the two at the same pressure.  A smooth model that fits both data sets (density or heat
capacity forms were tried) extrapolates badly, so this bridge is used instead and every run above 300 C
says that titanium is extrapolated there.  The charged species follow their low-temperature fits.
"""
from __future__ import annotations

import math

import numpy as np

from ..constants import LN10, R

T_MEASURED = (298.15, 573.15)           # K: 25 C (van't Hoff) to the highest measured temperature
P_MEASURED = 200.0                      # bar
DV_TIOH4 = -3.4                         # cm3/mol, Antignano and Manning (2008), Table 2
SOURCE = ("Knauss, Dibley, Bourcier and Shaw (2001) Appl. Geochem. 16, 1115-1128; pressure "
          "dependence of Ti(OH)4 from Antignano and Manning (2008) Chem. Geol. 255, 283-293")

# Knauss et al. (2001): T (C) -> (log K, 1-sigma), Table 3; 25 C from Table 5 (sigma assumed 0.2)
_KS = {
    "Ks3": {100: (-5.44, 0.032), 150: (-5.42, 0.106), 200: (-5.28, 0.055), 250: (-5.03, 0.046),
            300: (-4.61, 0.112)},
    "Ks4": {100: (-7.72, 0.150), 150: (-7.66, 0.202), 200: (-7.57, 0.153), 250: (-7.93, 0.202),
            300: (-7.92, 1.111)},
    "Ks5": {100: (-17.83, 0.068), 150: (-17.08, 0.138), 200: (-16.43, 0.132), 250: (-15.88, 0.018),
            300: (-15.35, 0.057)},
}
_DG298 = {"Ks3": 33.3e3, "Ks4": 43.5e3, "Ks5": 112.0e3}      # J/mol, Table 5 ("this work")


def _fit(key: str) -> np.ndarray:
    pts = [(298.15, -_DG298[key] / (R * 298.15 * LN10), 0.2)]
    pts += [(t + 273.15, v, e) for t, (v, e) in _KS[key].items()]
    t = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    w = 1.0 / np.array([p[2] for p in pts])
    a = np.c_[np.ones_like(t), 1.0 / t, np.log10(t)]
    coef, *_ = np.linalg.lstsq(a * w[:, None], y * w, rcond=None)
    return coef


COEF = {k: _fit(k) for k in _KS}


# Antignano and Manning (2008), Eq. 10: rutile solubility in pure H2O at 700-1000 C, 7-20 kbar,
# log c (ppm Ti by weight) = 6.173 - 5425/T + 178.4 P/T, T in K and P in GPa
AM08_T = 973.15                          # K: lowest temperature of their equation's range
AM08_P = 7000.0                          # bar: lowest pressure measured
M_TI = 47.867


def am08_log_m(t_k: float, p_bar: float) -> float:
    """log10 molality of TiO2,aq (= Ti(OH)4(aq)) at rutile saturation in pure water (dilute: ppm by
    weight over 1000 M_Ti gives mol per kg)."""
    return 6.173 - 5425.0 / t_k + 178.4 * (p_bar / 1e4) / t_k - math.log10(M_TI * 1000.0)


def _knauss(key: str, t_k: float, p_bar: float) -> float:
    a, b, c = COEF[key]
    out = a + b / t_k + c * math.log10(t_k)
    if key == "Ks4":
        out -= DV_TIOH4 * 0.1 * (p_bar - P_MEASURED) / (R * t_k * LN10)      # cm3 * bar = 0.1 J
    return out


def log_k(key: str, t_k: float, p_bar: float = P_MEASURED) -> float:
    """log10 K of rutile + n H2O (+ H+) = the species.  Ks4 (rutile = Ti(OH)4(aq), water at unit
    activity) follows Knauss et al. to 300 C, Antignano and Manning's equation from 700 C, and is
    linear in 1/T between the two at the same pressure.  Nothing was measured between 300 and 700 C,
    nor above 300 C below 7 kbar, so values there are a bridge, flagged as extrapolated."""
    if key != "Ks4" or t_k <= T_MEASURED[1]:
        return _knauss(key, t_k, p_bar)
    hi = am08_log_m(max(t_k, AM08_T), p_bar)
    if t_k >= AM08_T:
        return hi
    lo = _knauss(key, T_MEASURED[1], p_bar)
    f = (1.0 / T_MEASURED[1] - 1.0 / t_k) / (1.0 / T_MEASURED[1] - 1.0 / AM08_T)
    return lo + f * (hi - lo)


def measured(key: str, t_k: float, p_bar: float) -> bool:
    """True inside the conditions the data cover (25 to 300 C; for Ti(OH)4 also 700 to 1000 C at 7 kbar
    and above)."""
    if T_MEASURED[0] - 1e-6 <= t_k <= T_MEASURED[1] + 1e-6:
        return True
    return key == "Ks4" and AM08_T - 1e-6 <= t_k <= 1273.15 + 1e-6 and p_bar >= AM08_P - 1e-6


class TiProvider:
    """Gibbs energy (J/mol) of one Ti species from rutile, water and H+ and its log K."""

    def __init__(self, key: str, rutile, water, proton, n_water: float, n_proton: float):
        self.key, self.rutile, self.water, self.proton = key, rutile, water, proton
        self.n_water, self.n_proton = n_water, n_proton

    def gibbs(self, t_k, p_bar):
        g = (self.rutile.gibbs(t_k, p_bar) + self.n_water * self.water.gibbs(t_k, p_bar)
             + self.n_proton * self.proton.gibbs(t_k, p_bar))
        return g - R * t_k * LN10 * log_k(self.key, t_k, p_bar)

    def extrapolated(self, t_k):
        # the provider is asked without a pressure: only the temperature range can be judged here
        return not (T_MEASURED[0] - 1e-6 <= t_k <= T_MEASURED[1] + 1e-6
                    or (self.key == "Ks4" and AM08_T - 1e-6 <= t_k <= 1273.15 + 1e-6))


# name, formula, elements, charge, key, H2O and H+ on the reactant side (with rutile)
SPECIES = (
    ("Ti(OH)4", "Ti(OH)4", {"Ti": 1.0, "O": 4.0, "H": 4.0}, 0.0, "Ks4", 2.0, 0.0),
    ("Ti(OH)3+", "Ti(OH)3+", {"Ti": 1.0, "O": 3.0, "H": 3.0}, 1.0, "Ks3", 1.0, 1.0),
    ("Ti(OH)5-", "Ti(OH)5-", {"Ti": 1.0, "O": 5.0, "H": 5.0}, -1.0, "Ks5", 3.0, -1.0),
)
MASTER = "Ti(OH)4"
