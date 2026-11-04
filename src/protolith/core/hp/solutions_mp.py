"""The metapelite set: the solution models of White, Powell, Holland, Johnson and Green (2014, J. Metamorphic
Geol. 32, 261-286), on the ds6.2 dataset (MnNCKFMASHTO).

Written by scripts/port_magemin_mp.py from MAGEMin's sources (the ``G_SS_mp_*`` functions of
src/TC_database/tc_gss_function.c and ``px_mp_*`` / ``obj_mp_*`` of objective_functions.c): the numbers
are MAGEMin's, taken at Douglas's request (2026-11-03), and the form is the core's (site fractions
linear in the end-member proportions, or a ratio of two linear forms).  Do not edit by hand; run the
script again.

Names are MAGEMin's: liq, fsp, bi, g, ep, ma (margarite-rich white mica), mu, opx, sa, cd, st, chl, ctd,
sp, mt, ilm (Mn- and Mg-free ilmenite-hematite) and ilmm (with geikielite and pyrophanite).
"""
from __future__ import annotations

from .solutions import A, HPSolution, _pairs, em

DS = "62"


LIQ_MP = HPSolution(
    "liq",
    (
     em("q4L", (4.0, "qL"), dataset=DS),
     em("abL", (1.0, "abL"), dataset=DS),
     em("kspL", (1.0, "kspL"), dataset=DS),
     em("anL", (1.0, "anL"), dataset=DS),
     em("slL", (1.6, "silL"), dqf=(-23.0, 0.0, 0.0), dataset=DS),
     em("fo2L", (2.0, "foL"), dqf=(-10.0, 0.0, 0.0), dataset=DS),
     em("fa2L", (2.0, "faL"), dqf=(-9.0, 0.0, -1.3), dataset=DS),
     em("h2oL", (1.0, "h2oL"), dataset=DS),
    ),
    ('fac', 'pq', 'xab', 'xksp', 'pan', 'psil', 'pol', 'ph2o'),
    {
     "q4L": {"fac": 1.0, "pq": 1.0},
     "abL": {"fac": 1.0, "xab": 1.0},
     "kspL": {"fac": 1.0, "xksp": 1.0},
     "anL": {"fac": 1.0, "pan": 1.0},
     "slL": {"fac": 1.0, "psil": 1.0},
     "fo2L": {"fac": 1.0, "pol": 1.0},
     "fa2L": {"fac": 1.0, "pol": 1.0},
     "h2oL": {"ph2o": 1.0}},
    {
     "q4L": A(fac=1.0, pq=1.0),
     "abL": A(fac=1.0, xab=1.0),
     "kspL": A(fac=1.0, xksp=1.0),
     "anL": A(fac=1.0, pan=1.0),
     "slL": A(fac=1.0, psil=1.0),
     "fo2L": A(fac=1.0, pol=1.0, xMg=5.0),
     "fa2L": A(fac=1.0, pol=1.0, xFe=5.0),
     "h2oL": A(ph2o=2.0)},
    _pairs(8, [(12.0, 0.0, -0.4), (-2.0, 0.0, -0.5), 5.0, 12.0, (12.0, 0.0, -0.4), 14.0, (17.0, 0.0, -0.5), (-6.0, 0.0, 3.0), 0.0, 12.0, 10.0, 2.0, (-1.5, 0.0, -0.3), (0.0, 0.0, -1.0), 12.0, 12.0, 12.0, (9.5, 0.0, -0.3), 0.0, 0.0, 0.0, (7.5, 0.0, -0.5), 12.0, 12.0, 11.0, 18.0, (11.0, 0.0, -0.5), 12.0]),
    ratios={"xFe": ({"fa2L": 0.5}, {"fo2L": 0.5, "fa2L": 0.5}), "xMg": ({"fo2L": 0.5}, {"fo2L": 0.5, "fa2L": 0.5})},
)

FSP_MP = HPSolution(
    "fsp",
    (
     em("ab", (1.0, "ab"), dataset=DS),
     em("an", (1.0, "an"), dataset=DS),
     em("san", (1.0, "san"), dataset=DS),
    ),
    ('xNaA', 'xCaA', 'xKA', 'xAlTB', 'xSiTB'),
    {
     "ab": {"xNaA": 1.0, "xAlTB": 0.25, "xSiTB": 0.75},
     "an": {"xCaA": 1.0, "xAlTB": 0.5, "xSiTB": 0.5},
     "san": {"xKA": 1.0, "xAlTB": 0.25, "xSiTB": 0.75}},
    {
     "ab": A(1.7548, xNaA=1.0, xAlTB=0.25, xSiTB=0.75),
     "an": A(2.0, xCaA=1.0, xAlTB=0.5, xSiTB=0.5),
     "san": A(1.7548, xKA=1.0, xAlTB=0.25, xSiTB=0.75)},
    _pairs(3, [(14.6, -0.00935, -0.04), (24.1, -0.00957, 0.338), (48.5, 0.0, -0.13)]),
    v=(0.674, 0.55, 1.0),
)

BI_MP = HPSolution(
    "bi",
    (
     em("phl", (1.0, "phl"), dataset=DS),
     em("annm", (1.0, "ann"), dqf=(-3.0, 0.0, 0.0), dataset=DS),
     em("obi", (0.666666666667, "phl"), (0.333333333333, "ann"), dqf=(-3.0, 0.0, 0.0), dataset=DS),
     em("east", (1.0, "east"), dataset=DS),
     em("tbi", (1.0, "phl"), (-1.0, "br"), (1.0, "ru"), dqf=(55.0, 0.0, 0.0), dataset=DS),
     em("fbi", (1.0, "east"), (0.5, "andr"), (-0.5, "gr"), dqf=(-3.0, 0.0, 0.0), dataset=DS),
     em("mmbi", (1.0, "mnbi"), dqf=(-7.89, 0.0, 0.0), dataset=DS),
    ),
    ('xMgM3', 'xMnM3', 'xFeM3', 'xFe3M3', 'xTiM3', 'xAlM3', 'xMgM12', 'xMnM12', 'xFeM12', 'xSiT', 'xAlT', 'xOHV', 'xOV'),
    {
     "phl": {"xMgM3": 1.0, "xMgM12": 1.0, "xSiT": 0.5, "xAlT": 0.5, "xOHV": 1.0},
     "annm": {"xFeM3": 1.0, "xFeM12": 1.0, "xSiT": 0.5, "xAlT": 0.5, "xOHV": 1.0},
     "obi": {"xFeM3": 1.0, "xMgM12": 1.0, "xSiT": 0.5, "xAlT": 0.5, "xOHV": 1.0},
     "east": {"xAlM3": 1.0, "xMgM12": 1.0, "xAlT": 1.0, "xOHV": 1.0},
     "tbi": {"xTiM3": 1.0, "xMgM12": 1.0, "xSiT": 0.5, "xAlT": 0.5, "xOV": 1.0},
     "fbi": {"xFe3M3": 1.0, "xMgM12": 1.0, "xAlT": 1.0, "xOHV": 1.0},
     "mmbi": {"xMnM3": 1.0, "xMnM12": 1.0, "xSiT": 0.5, "xAlT": 0.5, "xOHV": 1.0}},
    {
     "phl": A(4.0, xAlT=1.0, xMgM3=1.0, xSiT=1.0, xMgM12=2.0, xOHV=2.0),
     "annm": A(4.0, xAlT=1.0, xFeM3=1.0, xSiT=1.0, xFeM12=2.0, xOHV=2.0),
     "obi": A(4.0, xAlT=1.0, xFeM3=1.0, xSiT=1.0, xMgM12=2.0, xOHV=2.0),
     "east": A(xAlM3=1.0, xAlT=2.0, xMgM12=2.0, xOHV=2.0),
     "tbi": A(4.0, xAlT=1.0, xSiT=1.0, xTiM3=1.0, xMgM12=2.0, xOV=2.0),
     "fbi": A(xFe3M3=1.0, xAlT=2.0, xMgM12=2.0, xOHV=2.0),
     "mmbi": A(4.0, xAlT=1.0, xMnM3=1.0, xSiT=1.0, xMnM12=2.0, xOHV=2.0)},
    _pairs(7, [12.0, 4.0, 10.0, 30.0, 8.0, 9.0, 8.0, 15.0, 32.0, 13.6, 6.3, 7.0, 24.0, 5.6, 8.1, 40.0, 1.0, 13.0, 40.0, 30.0, 11.6]),
)

G_MP = HPSolution(
    "g",
    (
     em("py", (1.0, "py"), dataset=DS),
     em("alm", (1.0, "alm"), dataset=DS),
     em("spss", (1.0, "spss"), dataset=DS),
     em("gr", (1.0, "gr"), dataset=DS),
     em("kho", (1.0, "py"), (-1.0, "gr"), (1.0, "andr"), dqf=(27.0, 0.0, 0.0), dataset=DS),
    ),
    ('xMgX', 'xFeX', 'xMnX', 'xCaX', 'xAlY', 'xFe3Y'),
    {
     "py": {"xMgX": 1.0, "xAlY": 1.0},
     "alm": {"xFeX": 1.0, "xAlY": 1.0},
     "spss": {"xMnX": 1.0, "xAlY": 1.0},
     "gr": {"xCaX": 1.0, "xAlY": 1.0},
     "kho": {"xMgX": 1.0, "xFe3Y": 1.0}},
    {
     "py": A(xAlY=2.0, xMgX=3.0),
     "alm": A(xAlY=2.0, xFeX=3.0),
     "spss": A(xAlY=2.0, xMnX=3.0),
     "gr": A(xAlY=2.0, xCaX=3.0),
     "kho": A(xFe3Y=2.0, xMgX=3.0)},
    _pairs(5, [2.5, 2.0, 31.0, 5.4, 2.0, 5.0, 22.6, 0.0, 29.4, -15.3]),
    v=(1.0, 1.0, 1.0, 2.7, 1.0),
)

EP_MP = HPSolution(
    "ep",
    (
     em("cz", (1.0, "cz"), dataset=DS),
     em("ep", (1.0, "ep"), dataset=DS),
     em("fep", (1.0, "fep"), dataset=DS),
    ),
    ('xFeM1', 'xAlM1', 'xFeM3', 'xAlM3'),
    {
     "cz": {"xAlM1": 1.0, "xAlM3": 1.0},
     "ep": {"xAlM1": 1.0, "xFeM3": 1.0},
     "fep": {"xFeM1": 1.0, "xFeM3": 1.0}},
    {
     "cz": A(xAlM1=1.0, xAlM3=1.0),
     "ep": A(xAlM1=1.0, xFeM3=1.0),
     "fep": A(xFeM1=1.0, xFeM3=1.0)},
    _pairs(3, [1.0, 3.0, 1.0]),
)

MA_MP = HPSolution(
    "ma",
    (
     em("mut", (1.0, "mu"), dqf=(1.0, 0.0, 0.0), dataset=DS),
     em("celt", (1.0, "cel"), dqf=(5.0, 0.0, 0.0), dataset=DS),
     em("fcelt", (1.0, "fcel"), dqf=(5.0, 0.0, 0.0), dataset=DS),
     em("pat", (1.0, "pa"), dqf=(4.0, 0.0, 0.0), dataset=DS),
     em("ma", (1.0, "ma"), dataset=DS),
     em("fmu", (1.0, "mu"), (0.5, "andr"), (-0.5, "gr"), dqf=(25.0, 0.0, 0.0), dataset=DS),
    ),
    ('xKA', 'xNaA', 'xCaA', 'xMgM2A', 'xFeM2A', 'xAlM2A', 'xAlM2B', 'xFe3M2B', 'xSiT1', 'xAlT1'),
    {
     "mut": {"xKA": 1.0, "xAlM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 0.5, "xAlT1": 0.5},
     "celt": {"xKA": 1.0, "xMgM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 1.0},
     "fcelt": {"xKA": 1.0, "xFeM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 1.0},
     "pat": {"xNaA": 1.0, "xAlM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 0.5, "xAlT1": 0.5},
     "ma": {"xCaA": 1.0, "xAlM2A": 1.0, "xAlM2B": 1.0, "xAlT1": 1.0},
     "fmu": {"xKA": 1.0, "xAlM2A": 1.0, "xFe3M2B": 1.0, "xSiT1": 0.5, "xAlT1": 0.5}},
    {
     "mut": A(4.0, xAlM2A=1.0, xAlM2B=1.0, xAlT1=1.0, xKA=1.0, xSiT1=1.0),
     "celt": A(xAlM2B=1.0, xKA=1.0, xMgM2A=1.0, xSiT1=2.0),
     "fcelt": A(xAlM2B=1.0, xFeM2A=1.0, xKA=1.0, xSiT1=2.0),
     "pat": A(4.0, xAlM2A=1.0, xAlM2B=1.0, xAlT1=1.0, xNaA=1.0, xSiT1=1.0),
     "ma": A(xAlM2A=1.0, xAlM2B=1.0, xCaA=1.0, xAlT1=2.0),
     "fmu": A(4.0, xAlM2A=1.0, xAlT1=1.0, xFe3M2B=1.0, xKA=1.0, xSiT1=1.0)},
    _pairs(6, [(0.0, 0.0, 0.2), (0.0, 0.0, 0.2), (10.12, 0.0034, 0.353), 34.0, 0.0, 0.0, (45.0, 0.0, 0.25), 50.0, 0.0, (45.0, 0.0, 0.25), 50.0, 0.0, 18.0, 30.0, 35.0]),
    v=(0.63, 0.63, 0.63, 0.37, 0.63, 0.63),
)

MU_MP = HPSolution(
    "mu",
    (
     em("mut", (1.0, "mu"), dataset=DS),
     em("cel", (1.0, "cel"), dataset=DS),
     em("fcel", (1.0, "fcel"), dataset=DS),
     em("pat", (1.0, "pa"), dataset=DS),
     em("ma", (1.0, "ma"), dqf=(5.0, 0.0, 0.0), dataset=DS),
     em("fmu", (1.0, "mu"), (0.5, "andr"), (-0.5, "gr"), dqf=(25.0, 0.0, 0.0), dataset=DS),
    ),
    ('xKA', 'xNaA', 'xCaA', 'xMgM2A', 'xFeM2A', 'xAlM2A', 'xAlM2B', 'xFe3M2B', 'xSiT1', 'xAlT1'),
    {
     "mut": {"xKA": 1.0, "xAlM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 0.5, "xAlT1": 0.5},
     "cel": {"xKA": 1.0, "xMgM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 1.0},
     "fcel": {"xKA": 1.0, "xFeM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 1.0},
     "pat": {"xNaA": 1.0, "xAlM2A": 1.0, "xAlM2B": 1.0, "xSiT1": 0.5, "xAlT1": 0.5},
     "ma": {"xCaA": 1.0, "xAlM2A": 1.0, "xAlM2B": 1.0, "xAlT1": 1.0},
     "fmu": {"xKA": 1.0, "xAlM2A": 1.0, "xFe3M2B": 1.0, "xSiT1": 0.5, "xAlT1": 0.5}},
    {
     "mut": A(4.0, xAlM2A=1.0, xAlM2B=1.0, xAlT1=1.0, xKA=1.0, xSiT1=1.0),
     "cel": A(xAlM2B=1.0, xKA=1.0, xMgM2A=1.0, xSiT1=2.0),
     "fcel": A(xAlM2B=1.0, xFeM2A=1.0, xKA=1.0, xSiT1=2.0),
     "pat": A(4.0, xAlM2A=1.0, xAlM2B=1.0, xAlT1=1.0, xNaA=1.0, xSiT1=1.0),
     "ma": A(xAlM2A=1.0, xAlM2B=1.0, xCaA=1.0, xAlT1=2.0),
     "fmu": A(4.0, xAlM2A=1.0, xAlT1=1.0, xFe3M2B=1.0, xKA=1.0, xSiT1=1.0)},
    _pairs(6, [(0.0, 0.0, 0.2), (0.0, 0.0, 0.2), (10.12, 0.0034, 0.353), 35.0, 0.0, 0.0, (45.0, 0.0, 0.25), 50.0, 0.0, (45.0, 0.0, 0.25), 50.0, 0.0, 15.0, 30.0, 35.0]),
    v=(0.63, 0.63, 0.63, 0.37, 0.63, 0.63),
)

OPX_MP = HPSolution(
    "opx",
    (
     em("en", (1.0, "en"), dataset=DS),
     em("fs", (1.0, "fs"), dataset=DS),
     em("fm", (0.5, "en"), (0.5, "fs"), dqf=(-6.6, 0.0, 0.0), dataset=DS),
     em("mgts", (1.0, "mgts"), dataset=DS),
     em("fopx", (1.0, "mgts"), (0.5, "andr"), (-0.5, "gr"), dqf=(2.0, 0.0, 0.0), dataset=DS),
     em("mnopx", (2.0, "pxmn"), dqf=(6.68, 0.0, 0.0), dataset=DS),
     em("odi", (1.0, "di"), dqf=(-0.1, 0.000211, 0.005), dataset=DS),
    ),
    ('xMgM1', 'xFeM1', 'xMnM1', 'xFe3M1', 'xAlM1', 'xMgM2', 'xFeM2', 'xMnM2', 'xCaM2', 'xSiT', 'xAlT'),
    {
     "en": {"xMgM1": 1.0, "xMgM2": 1.0, "xAlT": 1.0},
     "fs": {"xFeM1": 1.0, "xFeM2": 1.0, "xAlT": 1.0},
     "fm": {"xMgM1": 1.0, "xFeM2": 1.0, "xAlT": 1.0},
     "mgts": {"xAlM1": 1.0, "xMgM2": 1.0, "xSiT": 0.5, "xAlT": 0.5},
     "fopx": {"xFe3M1": 1.0, "xMgM2": 1.0, "xSiT": 0.5, "xAlT": 0.5},
     "mnopx": {"xMnM1": 1.0, "xMnM2": 1.0, "xAlT": 1.0},
     "odi": {"xMgM1": 1.0, "xCaM2": 1.0, "xAlT": 1.0}},
    {
     "en": A(xMgM1=1.0, xMgM2=1.0, xAlT=0.5),
     "fs": A(xFeM1=1.0, xFeM2=1.0, xAlT=0.5),
     "fm": A(xFeM2=1.0, xMgM1=1.0, xAlT=0.5),
     "mgts": A(1.4142, xAlM1=1.0, xMgM2=1.0, xAlT=0.25, xSiT=0.25),
     "fopx": A(1.4142, xFe3M1=1.0, xMgM2=1.0, xAlT=0.25, xSiT=0.25),
     "mnopx": A(xMnM1=1.0, xMnM2=1.0, xAlT=0.5),
     "odi": A(xCaM2=1.0, xMgM1=1.0, xAlT=0.5)},
    _pairs(7, [7.0, 4.0, (13.0, 0.0, -0.15), (11.0, 0.0, -0.15), 5.0, (32.2, 0.0, 0.12), 4.0, (13.0, 0.0, -0.15), (11.6, 0.0, -0.15), 4.2, (25.54, 0.0, 0.084), (17.0, 0.0, -0.15), (15.0, 0.0, -0.15), 5.1, (22.54, 0.0, 0.084), 1.0, (12.0, 0.0, -0.15), (75.4, 0.0, -0.94), (10.6, 0.0, -0.15), (73.4, 0.0, -0.94), (24.54, 0.0, 0.084)]),
    v=(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2),
)

SA_MP = HPSolution(
    "sa",
    (
     em("spr4", (1.0, "spr4"), dataset=DS),
     em("spr5", (1.0, "spr5"), dataset=DS),
     em("fspm", (1.0, "fspr"), dqf=(-2.0, 0.0, 0.0), dataset=DS),
     em("spro", (0.25, "spr4"), (0.75, "fspr"), dqf=(-3.5, 0.0, 0.0), dataset=DS),
     em("ospr", (1.0, "spr5"), (-0.5, "gr"), (0.5, "andr"), dqf=(-16.0, 0.0, 0.0), dataset=DS),
    ),
    ('xMgM3', 'xFeM3', 'xFe3M3', 'xAlM3', 'xMgM456', 'xFeM456', 'xSiT', 'xAlT'),
    {
     "spr4": {"xMgM3": 1.0, "xMgM456": 1.0, "xSiT": 1.0},
     "spr5": {"xAlM3": 1.0, "xMgM456": 1.0, "xAlT": 1.0},
     "fspm": {"xFeM3": 1.0, "xFeM456": 1.0, "xSiT": 1.0},
     "spro": {"xMgM3": 1.0, "xFeM456": 1.0, "xSiT": 1.0},
     "ospr": {"xFe3M3": 1.0, "xMgM456": 1.0, "xAlT": 1.0}},
    {
     "spr4": A(xMgM3=1.0, xSiT=1.0, xMgM456=3.0),
     "spr5": A(xAlM3=1.0, xAlT=1.0, xMgM456=3.0),
     "fspm": A(xFeM3=1.0, xSiT=1.0, xFeM456=3.0),
     "spro": A(xMgM3=1.0, xSiT=1.0, xFeM456=3.0),
     "ospr": A(xAlT=1.0, xFe3M3=1.0, xMgM456=3.0)},
    _pairs(5, [(10.0, 0.0, -0.02), 16.0, 12.0, (8.0, 0.0, -0.02), (19.0, 0.0, -0.02), (22.0, 0.0, -0.02), 1.0, 4.0, (17.6, 0.0, -0.02), (20.0, 0.0, -0.02)]),
)

CD_MP = HPSolution(
    "cd",
    (
     em("crd", (1.0, "crd"), dataset=DS),
     em("fcrd", (1.0, "fcrd"), dataset=DS),
     em("hcrd", (1.0, "hcrd"), dataset=DS),
     em("mncd", (1.0, "mncrd"), dqf=(-4.21, 0.0, 0.0), dataset=DS),
    ),
    ('xFeX', 'xMgX', 'xMnX', 'xH2OH', 'xvH'),
    {
     "crd": {"xMgX": 1.0, "xvH": 1.0},
     "fcrd": {"xFeX": 1.0, "xvH": 1.0},
     "hcrd": {"xMgX": 1.0, "xH2OH": 1.0},
     "mncd": {"xMnX": 1.0, "xvH": 1.0}},
    {
     "crd": A(xvH=1.0, xMgX=2.0),
     "fcrd": A(xvH=1.0, xFeX=2.0),
     "hcrd": A(xH2OH=1.0, xMgX=2.0),
     "mncd": A(xvH=1.0, xMnX=2.0)},
    _pairs(4, [8.0, 0.0, 6.0, 9.0, 4.0, 6.0]),
)

ST_MP = HPSolution(
    "st",
    (
     em("mstm", (1.0, "mst"), dqf=(-8.0, 0.0, 0.0), dataset=DS),
     em("fst", (1.0, "fst"), dataset=DS),
     em("mnstm", (1.0, "mnst"), dqf=(-0.19, 0.0, 0.0), dataset=DS),
     em("msto", (1.0, "mst"), (1.0, "andr"), (-1.0, "gr"), dqf=(9.0, 0.0, 0.0), dataset=DS),
     em("mstt", (1.0, "mst"), (-1.0, "cor"), (1.5, "ru"), dqf=(13.0, 0.0, 0.0), dataset=DS),
    ),
    ('xMgX', 'xFeX', 'xMnX', 'xAlY', 'xFe3Y', 'xTiY', 'xvY'),
    {
     "mstm": {"xMgX": 1.0, "xAlY": 1.0},
     "fst": {"xFeX": 1.0, "xAlY": 1.0},
     "mnstm": {"xMnX": 1.0, "xAlY": 1.0},
     "msto": {"xMgX": 1.0, "xFe3Y": 1.0},
     "mstt": {"xMgX": 1.0, "xTiY": 0.75, "xvY": 0.25}},
    {
     "mstm": A(xAlY=2.0, xMgX=4.0),
     "fst": A(xAlY=2.0, xFeX=4.0),
     "mnstm": A(xAlY=2.0, xMnX=4.0),
     "msto": A(xFe3Y=2.0, xMgX=4.0),
     "mstt": A(3.0792, xMgX=4.0, xTiY=1.5, xvY=0.5)},
    _pairs(5, [16.0, 12.0, 2.0, 20.0, 8.0, 18.0, 36.0, 14.0, 32.0, 30.0]),
)

CHL_MP = HPSolution(
    "chl",
    (
     em("clin", (1.0, "clin"), dataset=DS),
     em("afchl", (1.0, "afchl"), dataset=DS),
     em("ames", (1.0, "ames"), dataset=DS),
     em("daph", (1.0, "daph"), dataset=DS),
     em("ochl1", (-1.0, "clin"), (1.0, "afchl"), (1.0, "daph"), dqf=(3.0, 0.0, 0.0), dataset=DS),
     em("ochl4", (-0.2, "clin"), (1.0, "afchl"), (0.2, "daph"), dqf=(2.4, 0.0, 0.0), dataset=DS),
     em("f3clin", (1.0, "clin"), (-0.5, "gr"), (0.5, "andr"), dqf=(2.0, 0.0, 0.0), dataset=DS),
     em("mmchl", (1.0, "mnchl"), dqf=(-5.67, 0.0, 0.0), dataset=DS),
    ),
    ('xMgM1', 'xMnM1', 'xFeM1', 'xAlM1', 'xMgM23', 'xFeM23', 'xMgM4', 'xFeM4', 'xFe3M4', 'xAlM4', 'xSiT2', 'xAlT2'),
    {
     "clin": {"xMgM1": 1.0, "xAlM1": 1.0, "xAlM4": 1.0, "xSiT2": 0.5, "xAlT2": 0.5},
     "afchl": {"xMgM1": 1.0, "xAlM1": 1.0, "xMgM4": 1.0, "xSiT2": 1.0},
     "ames": {"xFeM1": 1.0, "xAlM1": 1.0, "xAlM4": 1.0, "xAlT2": 1.0},
     "daph": {"xMnM1": 1.0, "xFeM23": 1.0, "xAlM4": 1.0, "xSiT2": 0.5, "xAlT2": 0.5},
     "ochl1": {"xMgM1": 1.0, "xFeM23": 1.0, "xFeM4": 1.0, "xSiT2": 1.0},
     "ochl4": {"xMnM1": 1.0, "xAlM1": 1.0, "xMgM4": 1.0, "xSiT2": 1.0},
     "f3clin": {"xMgM1": 1.0, "xAlM1": 1.0, "xFe3M4": 1.0, "xSiT2": 0.5, "xAlT2": 0.5},
     "mmchl": {"xMgM23": 1.0, "xAlM4": 1.0, "xSiT2": 0.5, "xAlT2": 0.5}},
    {
     "clin": A(4.0, xAlM4=1.0, xAlT2=1.0, xMgM1=1.0, xSiT2=1.0, xAlM1=4.0),
     "afchl": A(xMgM1=1.0, xMgM4=1.0, xAlM1=4.0, xSiT2=2.0),
     "ames": A(xAlM4=1.0, xFeM1=1.0, xAlM1=4.0, xAlT2=2.0),
     "daph": A(4.0, xAlM4=1.0, xAlT2=1.0, xMnM1=1.0, xSiT2=1.0, xFeM23=4.0),
     "ochl1": A(xFeM4=1.0, xMgM1=1.0, xFeM23=4.0, xSiT2=2.0),
     "ochl4": A(xMgM4=1.0, xMnM1=1.0, xAlM1=4.0, xSiT2=2.0),
     "f3clin": A(4.0, xAlT2=1.0, xFe3M4=1.0, xMgM1=1.0, xSiT2=1.0, xAlM1=4.0),
     "mmchl": A(4.0, xAlM4=1.0, xAlT2=1.0, xSiT2=1.0, xMgM23=5.0)},
    _pairs(8, [17.0, 17.0, 20.0, 30.0, 21.0, 2.0, 6.0, 16.0, 37.0, 20.0, 4.0, 15.0, 23.0, 30.0, 29.0, 13.0, 19.0, 17.0, 18.0, 33.0, 22.0, 4.0, 24.0, 28.6, 19.0, 19.0, 22.0, 8.0]),
)

CTD_MP = HPSolution(
    "ctd",
    (
     em("mctd", (1.0, "mctd"), dataset=DS),
     em("fctd", (1.0, "fctd"), dataset=DS),
     em("mnct", (1.0, "mnctd"), dqf=(0.66, 0.0, 0.0), dataset=DS),
     em("ctdo", (1.0, "mctd"), (0.25, "andr"), (-0.25, "gr"), dqf=(13.5, 0.0, 0.0), dataset=DS),
    ),
    ('xAlM1A', 'xFe3M1A', 'xFeM1B', 'xMgM1B', 'xMnM1B'),
    {
     "mctd": {"xAlM1A": 1.0, "xMgM1B": 1.0},
     "fctd": {"xAlM1A": 1.0, "xFeM1B": 1.0},
     "mnct": {"xAlM1A": 1.0, "xMnM1B": 1.0},
     "ctdo": {"xFe3M1A": 1.0, "xMgM1B": 1.0}},
    {
     "mctd": A(xMgM1B=1.0, xAlM1A=0.5),
     "fctd": A(xFeM1B=1.0, xAlM1A=0.5),
     "mnct": A(xMnM1B=1.0, xAlM1A=0.5),
     "ctdo": A(xMgM1B=1.0, xFe3M1A=0.5)},
    _pairs(4, [4.0, 3.0, 1.0, 3.0, 5.0, 4.0]),
)

SP_MP = HPSolution(
    "sp",
    (
     em("herc", (1.0, "herc"), dataset=DS),
     em("sp", (1.0, "sp"), dataset=DS),
     em("mt", (1.0, "mt"), dataset=DS),
     em("usp", (1.0, "usp"), dataset=DS),
    ),
    ('xAl', 'xFe3', 'xTi'),
    {
     "herc": {"xAl": 1.0},
     "sp": {"xAl": 1.0},
     "mt": {"xFe3": 1.0},
     "usp": {"xTi": 1.0}},
    {
     "herc": A(xAl=1.0, xFe2=1.0),
     "sp": A(xAl=1.0, xMg=1.0),
     "mt": A(xFe2=1.0, xFe3=1.0),
     "usp": A(xFe2=1.0, xTi=1.0)},
    _pairs(4, [0.0, 18.5, 27.0, 40.0, 30.0, 0.0]),
    ratios={"xMg": ({"sp": 0.2}, {"herc": 0.2, "sp": 0.2, "mt": 0.2, "usp": 0.4}), "xFe2": ({"herc": 0.2, "mt": 0.2, "usp": 0.4}, {"herc": 0.2, "sp": 0.2, "mt": 0.2, "usp": 0.4})},
)

MT_MP = HPSolution(
    "mt",
    (
     em("imt", (1.0, "mt", "disordered"), dqf=(-1.8595, 0.003166, 0.0), dataset=DS),
     em("dmt", (1.0, "mt", "disordered"), dqf=(1.3305, -0.001184, 0.0), dataset=DS),
     em("usp", (1.0, "usp"), dataset=DS),
    ),
    ('xTiM', 'xFe3M', 'xFeM', 'xFe3T', 'xFeT'),
    {
     "imt": {"xFe3M": 0.5, "xFeM": 0.5, "xFe3T": 1.0},
     "dmt": {"xFe3M": 0.666666666667, "xFeM": 0.333333333333, "xFe3T": 0.666666666667, "xFeT": 0.333333333333},
     "usp": {"xTiM": 0.5, "xFeM": 0.5, "xFeT": 1.0}},
    {
     "imt": A(4.0, xFe3M=1.0, xFe3T=1.0, xFeM=1.0),
     "dmt": A(6.75, xFe3M=1.333333333333, xFe3T=0.666666666667, xFeM=0.666666666667, xFeT=0.333333333333),
     "usp": A(4.0, xFeM=1.0, xFeT=1.0, xTiM=1.0)},
    _pairs(3, [2.4, 1.0, -5.0]),
)

ILM_MP = HPSolution(
    "ilm",
    (
     em("oilm", (1.0, "ilm", "disordered"), dqf=(-13.6075, 0.009426, 0.0), dataset=DS),
     em("dilm", (1.0, "ilm", "disordered"), dqf=(1.9928, -0.0021, 0.0), dataset=DS),
     em("dhem", (1.0, "hem", "disordered"), dataset=DS),
    ),
    ('xFe2A', 'xTiA', 'xFe3A', 'xFe2B', 'xTiB', 'xFe3B'),
    {
     "oilm": {"xFe2A": 1.0, "xTiB": 1.0},
     "dilm": {"xFe2A": 0.5, "xTiA": 0.5, "xFe2B": 0.5, "xTiB": 0.5},
     "dhem": {"xFe3A": 1.0, "xFe3B": 1.0}},
    {
     "oilm": A(xFe2A=1.0, xTiB=1.0),
     "dilm": A(4.0, xFe2A=0.5, xFe2B=0.5, xTiA=0.5, xTiB=0.5),
     "dhem": A(xFe3A=1.0, xFe3B=1.0)},
    _pairs(3, [15.6, 26.6, 11.0]),
)

ILMM_MP = HPSolution(
    "ilmm",
    (
     em("oilm", (1.0, "ilm", "disordered"), dqf=(-13.6075, 0.009426, 0.0), dataset=DS),
     em("dilm", (1.0, "ilm", "disordered"), dqf=(1.9928, -0.0021, 0.0), dataset=DS),
     em("dhem", (1.0, "hem", "disordered"), dataset=DS),
     em("geik", (1.0, "geik"), dataset=DS),
     em("pnt", (1.0, "pnt"), dataset=DS),
    ),
    ('xFeA', 'xTiA', 'xMgA', 'xMnA', 'xFe3A', 'xFeB', 'xTiB'),
    {
     "oilm": {"xFeA": 1.0, "xTiB": 1.0},
     "dilm": {"xFeA": 0.5, "xTiA": 0.5, "xFeB": 0.5, "xTiB": 0.5},
     "dhem": {"xFe3A": 1.0},
     "geik": {"xMgA": 1.0, "xTiB": 1.0},
     "pnt": {"xMnA": 1.0, "xTiB": 1.0}},
    {
     "oilm": A(xFeA=1.0, xTiB=1.0),
     "dilm": A(4.0, xFeA=0.5, xFeB=0.5, xTiA=0.5, xTiB=0.5),
     "dhem": A(xFe3A=2.0),
     "geik": A(xMgA=1.0, xTiB=1.0),
     "pnt": A(xMnA=1.0, xTiB=1.0)},
    _pairs(5, [15.6, 26.6, 4.0, 2.0, 11.0, 4.0, 2.0, 36.0, 25.0, 4.0]),
)

SOLUTIONS_MP = {s.name: s for s in (LIQ_MP, FSP_MP, BI_MP, G_MP, EP_MP, MA_MP, MU_MP, OPX_MP, SA_MP, CD_MP, ST_MP, CHL_MP, CTD_MP, SP_MP, MT_MP, ILM_MP, ILMM_MP)}
