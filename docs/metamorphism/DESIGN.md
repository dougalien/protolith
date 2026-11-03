# Metamorphism: design notes

Metamorphism finds the stable mineral assemblage of a rock at a given temperature and pressure, at one
point or over a T-P grid (a pseudosection). It runs on Protolith's Holland & Powell core
(`protolith.core.hp`), the same minimizer Magma uses. This package imports the core and nothing else:
no Magma and no Reaction.

## What is in this first version

| Piece | Where | What it does |
| --- | --- | --- |
| Bulk | `metamorphism/bulk.py` | Takes oxide wt% and converts it to the core's eleven components. Ferric iron is kept and the system is closed to oxygen. MnO, P2O5, CO2, NiO and CoO are left out and listed. |
| Water | `bulk.Bulk.water` | `"bulk"` uses the analysis's own H2O, so a rock can be undersaturated. `"excess"` adds enough water for a free fluid at every point. |
| One point | `metamorphism/point.py` | `equilibrium(bulk, t_c, p_kbar)` returns minerals with mode (wt% of the rock without free fluid), oxide composition, end members, structural formula, and An / Mg# / garnet end members. |
| Names | `metamorphism/names.py` | Whitney and Evans (2010) abbreviations. Where one model covers several minerals, composition decides between them (Pl/Kfs, Ms/Pg, Cpx/Omp/Jd/Pgt, Amp/Gln/Cum, Ilm/Hem, Spl/Mag, Ep/Czo). |
| Pseudosection | `metamorphism/pseudosection.py` | `compute(bulk, t_c, p_kbar)` solves the grid. Each pressure row is solved from low to high T, warm-starting from the previous point, and rows run in parallel processes. Connected cells with the same assemblage form a field. Each field has a label, a variance (F = C - phases + 2) and a label point. Boundaries are the cell edges between fields, and `mode_grid` gives one mineral's mode for contouring. Results save and load as JSON. |
| Samples | `protolith/metamorphism_link.py` | `bulk_from_sample(sample, part="whole"/"rock"/"melt")` and `to_sample(point, bulk)`, with the source sample as parent. |
| Command line | `python -m metamorphism point ...` / `grid ...` | Gives access to everything above until the module has a window. |

## The data

Phases are the core's igneous set (Holland, Green and Powell 2018). It already includes the metapelite
biotite, white mica (with margarite as an end member), chlorite, garnet, cordierite and epidote, and the
pure phases kyanite, sillimanite and andalusite. On Douglas's request (2026-11-03) three Al-rich
minerals of the metapelite set of White, Powell, Holland, Johnson and Green (2014, J. Metamorphic Geol.
32, 261-286) are added to the core. Their numbers are as distributed in MAGEMin (`st_W14`, `ctd_W14`,
`sa_W14` in `src/TC_database/tc_gss_function.c` and `objective_functions.c`):

* **staurolite** (`st`): mstm, fst, msto (Fe3+), mstt (Ti)
* **chloritoid** (`ctd`): mctd, fctd, ctdo (Fe3+)
* **sapphirine** (`sa`): spr4, spr5, fspm, spro (ordered), ospr (Fe3+)

The core has no MnO, so the Mn end members (mnstm, mnct) and their sites are left out. With MnO = 0
this gives the same model. The three are not in `minimize.SOLUTION_PHASES`, which is Magma's default.
`point.PHASES` switches them on for Metamorphism.

Checks so far (`tests/metamorphism/test_point.py`): an aluminous, Ca-poor pelite with water in excess
gives Cld + Chl + Ms + Qz at 450-540 °C. It gives Grt + St + Bt + Ms + Qz at 580-620 °C and 8 kbar,
which is the Barrovian chloritoid-to-staurolite sequence. A Mg-Al granulite at 1100 °C and 9 kbar gives
sapphirine + quartz. The aluminosilicate grid matches the polymorph with the lowest G in every cell.

## Known limits, and what comes next

1. **Speed.** A point takes 1 to 12 s, and a point where a phase appears can take up to a minute and a
   half. An 11 × 11 grid of a pelite takes several minutes on four cores.
2. **No window yet.** The next step is a Metamorphism window in the Protolith shell. It will draw the
   fields and boundaries, show a field's phases on click, contour modes, and offer Save sample / Send to
   Reaction.
3. **Stepped boundaries.** Boundaries follow the grid. Refining along boundaries (bisecting edges
   between fields) would give smooth reaction lines at a fraction of the cost of a finer grid.
4. **The rest of the metapelite set.** The metapelite-specific liquid, garnet with Mn, opx, ilmenite
   (ilmm), spinel and magnetite. MnO needs a new core component.
5. **Validation against MAGEMin or Perple_X** on published pseudosections, point by point.
