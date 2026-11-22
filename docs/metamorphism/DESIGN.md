# Protolith: design notes

Protolith finds the stable mineral assemblage of a rock at a given temperature and pressure: at one
point, along a P-T path, or over a T-P grid (a pseudosection). The calculations are in the
`metamorphism` package, which runs on the Holland & Powell core (`protolith.core.hp`) and imports
nothing else.

## Parts

| Piece | Where | What it does |
| --- | --- | --- |
| Bulk | `metamorphism/bulk.py` | Takes oxide wt% and converts it to the core's twelve components (IUPAC 2013 atomic weights). Ferric iron is kept and the system is closed to oxygen. Oxides the phase set cannot use are left out and listed. |
| Water | `bulk.Bulk.water` | `"bulk"` uses the analysis's own H2O, so a rock can be undersaturated. `"excess"` adds enough water for a free fluid at every point. |
| One point | `metamorphism/point.py` | `equilibrium(bulk, t_c, p_kbar)` returns minerals with mode (wt% of the rock without free fluid), oxide composition, end members, structural formula, and An / Mg# / garnet end members. |
| Names | `metamorphism/names.py` | Whitney and Evans (2010) abbreviations. Where one model covers several minerals, composition decides between them (Pl/Kfs, Ms/Pg/Mrg, Cpx/Omp/Jd/Pgt, Ilm/Hem, Spl/Mag, Ep/Czo). Amphibole is named by its B-site group after Hawthorne et al. (2012): calcic (Amp), sodic (Gln) or Mg-Fe-Mn (Cum), with the two B cations taken as Ca first, then Na, then Mg-Fe-Mn (a simplification of the full site assignment). |
| P-T path | `metamorphism/path.py` | Points spaced evenly along a path of waypoints, solved in parallel stretches with warm starts. |
| Pseudosection | `metamorphism/pseudosection.py` | `compute(bulk, t_c, p_kbar)` solves the grid. Each pressure row is solved from low to high T, warm-starting from the previous point, and rows run in parallel processes. Connected cells with the same assemblage form a field. Each field has a label, a variance (F = C - phases + 2) and a label point. Boundaries are the cell edges between fields, and `mode_grid` gives one mineral's mode for shading. Results save and load as JSON. |
| Facies background | `metamorphism/facies.py` | Schematic facies fields after Spear (1993) and Winter (2010), and the Al2SiO5 and muscovite + quartz lines computed from ds6.2. |
| Samples | `protolith/sample.py`, `protolith/metamorphism_link.py` | The `.sample` file (JSON): a rock's conditions, bulk and phases. `bulk_from_sample` reads one in; `to_sample` writes a point out, with the source sample as parent. |
| Web app | `metamorphism/web/app.py`, `streamlit_app.py` | The Streamlit Input and Results windows. Each visitor has a private workspace id in the address (`?w=`) shared by their two windows. |
| Desktop app | `metamorphism/app` | The same two windows served locally (`python -m metamorphism.app`, port 8810). |
| Command line | `python -m metamorphism point ...` / `grid ...` | The same calculations without a window. |

## The data

There are two **phase sets** (`protolith.core.hp.minimize.PHASE_SETS`), chosen with `Bulk.system`:

* **metapelite** (default): the solution models of White, Powell, Holland, Johnson and Green (2014,
  J. Metamorphic Geol. 32, 261-286) on the ds6.2 dataset, in MnNCKFMASHTO. The models are melt, feldspar,
  biotite, garnet (with spessartine), epidote, margarite and muscovite micas, opx, sapphirine, cordierite,
  staurolite, chlorite, chloritoid, spinel and ilmenite. The pure phases are quartz and its polymorphs,
  the Al2SiO5 polymorphs, rutile, titanite, zoisite, corundum and pure H2O.
* **igneous**: the igneous set of Holland, Green and Powell (2018) on ds6.36. It takes Cr2O3 and no MnO.

All parameter values are those distributed in MAGEMin (Riel et al. 2022,
github.com/ComputationalThermodynamics/MAGEMin); the code is written from the papers' equations.

* `scripts/extract_hp_dataset.py` writes the ds6.2 and ds6.36 end-member tables
  (`core/data/hp_ds62.tsv`, `hp_ds636.tsv`) from MAGEMin's `src/TC_database/TC_endmembers.c`.
* `scripts/port_magemin_mp.py` reads MAGEMin's metapelite models (`G_SS_mp_*` in `tc_gss_function.c`,
  `px_mp_*` and `obj_mp_*` in `objective_functions.c`), recasts each in the core's form (site fractions
  linear in the end-member proportions, or a ratio of two linear forms for the melt's and spinel's
  Fe/(Fe+Mg)), checks that the fit is exact, and writes `core/hp/solutions_mp.py`.
* The igneous models in `core/hp/solutions.py` are written by hand. MAGEMin names one spinel end member
  `qndm`; it is made from `usp` and is called `usp` here.

As MAGEMin does by default, the metapelite set uses spinel rather than its alternative magnetite model
(`mt`), and ilmenite without geikielite and pyrophanite (`ilm`) rather than `ilmm`. Pass them in `phases`
to use them instead. MnO is the core's twelfth component; the igneous set has no Mn end members.

## Checks

* Both end-member tables and `solutions_mp.py` are reproduced exactly by the two scripts from MAGEMin's
  sources.
* The fifteen igneous models give the same end members, W, van Laar sizes, g0 and chemical potentials as
  the same models read from MAGEMin's `G_SS_ig_*` functions, to 1e-9 kJ.
* `tests/core/test_hp_metapelite_magemin.py` compares five points of MAGEMin's reference grid for the
  metapelite set (`test/test_diagram_test0_mp.jl`, the world median pelite of Forshaw and Pattison (2023)
  with water in excess, 0-12 kbar, 300-900 °C). `scripts/compare_mp_magemin.py` runs all 48 points; each
  gives MAGEMin's assemblage and a system G within 0.0005 kJ/mol.
* `tests/core/test_hp_minimize.py` compares the igneous set with MAGEMin 2.1.0 equilibria.
* `tests/core/test_hp_metapelite.py` checks each of the 17 metapelite models for self-consistency: pure
  end members, site fractions, and mu = dG/dn.
* `tests/core/test_hp_endmembers.py` checks the end members against the Al2SiO5 triple point (Pattison
  1992), albite = jadeite + quartz (Holland 1980), quartz = coesite (Bose and Ganguly 1995) and IAPWS-95
  water.
* `tests/metamorphism/test_point.py`: an aluminous pelite gives Cld + Chl + Ms + Qz at 500 °C and 6 kbar,
  and Grt (almandine with some spessartine) + St + Bt + Ms + Qz at 600 °C and 8 kbar.

## Known limits

1. **Speed.** A point takes one to a few seconds. On four processor cores, a 6 x 5 grid of a pelite
   takes about 25 s and the 9 x 4 grid of the world median pelite about 100 s.
2. **Modes are shaded, not contoured.** Contour lines would need a finer grid than most runs have.
3. **Stepped boundaries.** Boundaries follow the grid. Refining along boundaries (bisecting edges
   between fields) would give smooth reaction lines at a fraction of the cost of a finer grid.
4. **Metabasites.** There is no metabasite set (Green et al. 2016) yet. The igneous set stands in for
   mafic rocks; it has no subsolidus chlorite-actinolite-epidote greenschist assemblage in the cards' range.
