# Metamorphism: design notes

Metamorphism finds the stable mineral assemblage of a rock at a given temperature and pressure, at one
point or over a T-P grid (a pseudosection). It runs on Protolith's Holland & Powell core
(`protolith.core.hp`), the same minimizer Magma uses. This package imports the core and nothing else:
no Magma and no Reaction.

## What is in this first version

| Piece | Where | What it does |
| --- | --- | --- |
| Bulk | `metamorphism/bulk.py` | Takes oxide wt% and converts it to the core's twelve components. Ferric iron is kept and the system is closed to oxygen. Oxides the phase set cannot use are left out and listed. |
| Water | `bulk.Bulk.water` | `"bulk"` uses the analysis's own H2O, so a rock can be undersaturated. `"excess"` adds enough water for a free fluid at every point. |
| One point | `metamorphism/point.py` | `equilibrium(bulk, t_c, p_kbar)` returns minerals with mode (wt% of the rock without free fluid), oxide composition, end members, structural formula, and An / Mg# / garnet end members. |
| Names | `metamorphism/names.py` | Whitney and Evans (2010) abbreviations. Where one model covers several minerals, composition decides between them (Pl/Kfs, Ms/Pg, Cpx/Omp/Jd/Pgt, Amp/Gln/Cum, Ilm/Hem, Spl/Mag, Ep/Czo). |
| Pseudosection | `metamorphism/pseudosection.py` | `compute(bulk, t_c, p_kbar)` solves the grid. Each pressure row is solved from low to high T, warm-starting from the previous point, and rows run in parallel processes. Connected cells with the same assemblage form a field. Each field has a label, a variance (F = C - phases + 2) and a label point. Boundaries are the cell edges between fields, and `mode_grid` gives one mineral's mode for contouring. Results save and load as JSON. |
| Samples | `protolith/metamorphism_link.py` | `bulk_from_sample(sample, part="whole"/"rock"/"melt")` and `to_sample(point, bulk)`, with the source sample as parent. |
| Command line | `python -m metamorphism point ...` / `grid ...` | Gives access to everything above until the module has a window. |

## The data

Metamorphism runs on one of two **phase sets** (`protolith.core.hp.minimize.PHASE_SETS`), chosen with
`Bulk.system`:

* **metapelite** (default): the solution models of White, Powell, Holland, Johnson and Green (2014,
  J. Metamorphic Geol. 32, 261-286) on the ds6.2 dataset, in MnNCKFMASHTO. The models are melt, feldspar,
  biotite, garnet (with spessartine), epidote, margarite and muscovite micas, opx, sapphirine, cordierite,
  staurolite, chlorite, chloritoid, spinel and ilmenite. The pure phases are quartz and its polymorphs,
  the Al2SiO5 polymorphs, rutile, titanite, zoisite, corundum and pure H2O. Douglas asked for these on
  2026-11-03, first the Al-rich minerals and then MnO.
* **igneous**: the core's igneous set (Holland, Green and Powell 2018) on ds6.36, Magma's set. It takes
  Cr2O3 and no MnO.

The metapelite models are MAGEMin's numbers. `scripts/port_magemin_mp.py` reads MAGEMin's C sources
(`G_SS_mp_*` in `tc_gss_function.c`, `px_mp_*` and `obj_mp_*` in `objective_functions.c`). It recasts
each model in the core's form, with site fractions linear in the end-member proportions, or a ratio of
two linear forms for the melt's and spinel's Fe/(Fe+Mg). It checks that the fit is exact and writes
`src/protolith/core/hp/solutions_mp.py`. The ds6.2 dataset (`core/data/hp_ds62.tsv`) comes from
MAGEMin's `TC_endmembers.c` via `scripts/extract_hp_dataset.py`. The same script reproduces the committed
ds6.36 file exactly.

As MAGEMin does by default, the set uses spinel rather than its alternative magnetite model (`mt`). It
also uses ilmenite without geikielite and pyrophanite (`ilm`) rather than `ilmm`. Pass them in `phases` to
use them instead.

**MnO** is now the core's twelfth component, placed last so the first eleven keep their places. Magma
still leaves it out, because the igneous set has no Mn end members.

## Checks

* `tests/core/test_hp_metapelite_magemin.py` compares five points of MAGEMin's own reference grid for the
  set (`test/test_diagram_test0_mp.jl`, the world median pelite with water in excess, 2-8 kbar,
  400-800 °C). In each, the assemblage is MAGEMin's and the system G agrees to 0.0005 kJ/mol.
  `scripts/compare_mp_magemin.py` runs all 48 points (300-900 °C, 0-12 kbar). On 2026-11-03 all 48
  gave MAGEMin's assemblage and G within 0.0005 kJ/mol.
* `tests/core/test_hp_metapelite.py` checks each of the 17 models for self-consistency: pure end members,
  site fractions, and mu = dG/dn.
* `tests/metamorphism/test_point.py`: an aluminous pelite gives Cld + Chl + Ms + Qz at 500 °C and 6 kbar,
  and Grt (almandine with some spessartine) + St + Bt + Ms + Qz at 600 °C and 8 kbar.
* The aluminosilicate grid matches the polymorph with the lowest G in every cell.

## Known limits, and what comes next

1. **Speed.** A point takes 1 to 12 s, and a point where a phase appears can take up to a minute and a
   half. An 11 × 11 grid of a pelite takes several minutes on four cores.
2. **No window yet.** The next step is a Metamorphism window in the Protolith shell. It will draw the
   fields and boundaries, show a field's phases on click, contour modes, and offer Save sample / Send to
   Reaction.
3. **Stepped boundaries.** Boundaries follow the grid. Refining along boundaries (bisecting edges
   between fields) would give smooth reaction lines at a fraction of the cost of a finer grid.
4. **A metabasite set** (Green et al. 2016) for mafic rocks, ported the same way. The igneous set stands
   in for now.
