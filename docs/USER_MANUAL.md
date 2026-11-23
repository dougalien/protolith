# Protolith user manual

Protolith version 0.1.0. This manual describes the web version of Protolith (the one that runs in a
browser). The desktop version has the same two windows and a few extra tools, listed in
[Running Protolith on your own computer](#9-running-protolith-on-your-own-computer).

Contents

1. [What Protolith does](#1-what-protolith-does)
2. [Getting started](#2-getting-started)
3. [The Input window](#3-the-input-window)
4. [The Results window](#4-the-results-window)
5. [Reading the results](#5-reading-the-results)
6. [A worked example: the Barrovian pelite](#6-a-worked-example-the-barrovian-pelite)
7. [Limits and cautions](#7-limits-and-cautions)
8. [Using Protolith in a class](#8-using-protolith-in-a-class)
9. [Running Protolith on your own computer](#9-running-protolith-on-your-own-computer)
10. [How to cite, sources and license](#10-how-to-cite-sources-and-license)

## 1. What Protolith does

Protolith finds the minerals that are stable in a rock of a given bulk composition at a given
temperature and pressure. It does this by Gibbs energy minimization: of all the ways the rock's
oxides could be shared among minerals, melt and water, it finds the one with the lowest total Gibbs
energy. It can do this:

* at **one point** (one temperature and pressure);
* along a **P-T path** (points spaced evenly along a line through a few temperature, pressure points);
* over a **pseudosection** (a grid of temperature and pressure, with the points grouped into
  assemblage fields).

The thermodynamic data are the internally consistent dataset of Holland and Powell (2011). There are
two sets of solution models, called **phase sets** in the app:

| Phase set | Models | Dataset | Oxides it uses |
| --- | --- | --- | --- |
| Metapelite (the default) | White et al. (2014) | ds6.2 | SiO₂, TiO₂, Al₂O₃, FeO, Fe₂O₃, MnO, MgO, CaO, Na₂O, K₂O, H₂O |
| Igneous | Holland, Green and Powell (2018) | ds6.36 | the same, with Cr₂O₃ in place of MnO |

The metapelite set has models for melt, feldspar, biotite, garnet, epidote, white micas,
orthopyroxene, sapphirine, cordierite, staurolite, chlorite, chloritoid, spinel and ilmenite, and the
pure phases quartz and its polymorphs, kyanite, sillimanite, andalusite, rutile, titanite, zoisite,
corundum and water. Use it for mudstones and other aluminous rocks. The igneous set has models for
melt, fluid, olivine, orthopyroxene, clinopyroxene, garnet, spinel, ilmenite, feldspar, amphibole,
biotite, white mica, cordierite, epidote and chlorite, and the pure phases quartz and its polymorphs,
the Al₂SiO₅ polymorphs, rutile, titanite, corundum and nepheline. Use it for basalts and other mafic
rocks.

The parameter values are those distributed with MAGEMin (Riel et al. 2022). With the metapelite set,
Protolith gives the same assemblage as MAGEMin at all 48 points of MAGEMin's own reference grid (the
world median pelite with water in excess, 300 to 900 °C and up to 12 kbar), with the same total Gibbs
energy to within 0.0005 kJ/mol.

Every number Protolith shows is computed by Protolith itself, on the server, when you press Run.

## 2. Getting started

Protolith opens in two browser windows:

* the **Input** window, where you choose a rock and a run and press Run;
* the **Results** window, which shows the run as it fills in.

The **Open results window** button at the top right of the Input window opens the Results window in a
new tab, which you can drag to a second screen. Both windows follow the same run. The address of each
window ends in `?w=` and a random code: that code is your private workspace, and it is what joins the
two windows. Someone else who opens Protolith gets a workspace of their own.

The quickest start:

1. Click one of the cards under **Start from a card** (for example *Barrovian pelite* under
   P-T paths). The card fills in the rock, the phase set, the water and the run.
2. Press **Run**.
3. Open the Results window and watch the minerals come in.

A short line under the cards describes the card you chose. The same text appears when you hold the
pointer over a card.

## 3. The Input window

### 3.1 Starting cards

Each card loads a rock and a run that shows that rock well. All cards use water in excess.

| Group | Card | Rock | Phase set | Run |
| --- | --- | --- | --- | --- |
| P-T paths | Barrovian pelite | pelite | metapelite | 450 °C, 4 kbar → 600 °C, 7.5 kbar → 700 °C, 8 kbar; 16 points |
| | Low-pressure (Buchan) pelite | pelite | metapelite | 450 °C, 2.5 kbar → 700 °C, 3.5 kbar; 16 points |
| | Aluminous pelite | aluminous pelite | metapelite | 450 °C, 5 kbar → 650 °C, 9 kbar; 16 points |
| | Metabasite | metabasite | igneous | 500 °C, 4 kbar → 750 °C, 8 kbar; 12 points |
| Pseudosections | Barrovian pelite | pelite | metapelite | 450 to 700 °C by 50; 2 to 10 kbar by 2 |
| | World median pelite | world median pelite | metapelite | 400 to 800 °C by 50; 2 to 8 kbar by 2 |
| | Metabasite | metabasite | igneous | 500 to 800 °C by 50; 2 to 12 kbar by 2 |
| One point | Chloritoid schist | aluminous pelite | metapelite | 500 °C, 6 kbar |
| | Staurolite schist | aluminous pelite | metapelite | 600 °C, 8 kbar |
| | Sillimanite gneiss | pelite | metapelite | 650 °C, 5 kbar |

After a card is loaded you can change anything before pressing Run.

### 3.2 The rock

**Rock** picks one of four built-in compositions. The line under it says where each comes from:

| Rock | What it is |
| --- | --- |
| pelite | A typical shale-derived pelite, rounded; not a published analysis. |
| aluminous pelite | An Al- and Fe-rich, Ca-poor mudstone, rounded; the kind that grows chloritoid and staurolite. |
| world median pelite | Forshaw and Pattison (2023), the default rock of MAGEMin's metapelite set. Its H₂O is the 5 mol of MAGEMin's water-undersaturated version of that rock. |
| metabasite | A MORB-like basalt with the water of a hydrated sea floor, rounded. |

**Name** is what the Results window calls the rock. Change it when you type in your own analysis.

**Oxides, wt%** holds twelve boxes: SiO₂, TiO₂, Al₂O₃, Cr₂O₃, FeO, Fe₂O₃, MnO, MgO, CaO, Na₂O, K₂O
and H₂O. You can type any analysis into them.

* The analysis does not have to add up to 100. The total is shown under the boxes, and the analysis is
  normalized to 100 for the run.
* Iron can be given as FeO, as Fe₂O₃, or both. Protolith keeps the ferric iron you give it: the rock
  is closed to oxygen, so the Fe₂O₃ in the analysis sets how oxidized the rock is.
* Each phase set leaves out the oxides it has no models for: Cr₂O₃ for the metapelite set, MnO for the
  igneous set. The line under the boxes names what will be left out. Left-out oxides still count in the
  100 g of rock, so the minerals add up to 100 g less what was left out.

### 3.3 Minerals and water

**Phase set** chooses *Metapelite (White et al. 2014)* or *Igneous (Holland et al. 2018)*; see
[section 1](#1-what-protolith-does).

**Water** has two settings:

* **In excess**: water is added until there is a free fluid at every point, the usual assumption for
  prograde metamorphism, where the rock loses water as it heats. Protolith gives the solver either the
  rock's own water or half the moles of all its other components, whichever is larger; if a point still
  comes out with no fluid, it is solved again with three times that water.
* **The rock's own**: only the H₂O in the analysis. The rock can then run short of water, and
  water-poor assemblages (or melting that is limited by water) appear.

### 3.4 The run

**Kind** chooses the run:

* **A P-T path.** Type one temperature (°C) and pressure (kbar) per line, separated by a comma, for
  example `450, 4`. At least two lines are needed. **Points along the path** (2 to 60) are spaced evenly
  along the whole path, the first and last lines included. In spacing them, 100 °C counts as far as
  1 kbar.
* **A pseudosection (T-P grid).** Give the temperature axis (from, to, step, in °C) and the pressure axis
  (from, to, step, in kbar). The line under the boxes gives the number of points. A grid can have at most
  1600 points.
* **One temperature and pressure.**

Temperatures must be between 100 and 1500 °C, and pressures above 0 and at most 60 kbar. These are the
limits of the input boxes, not of the models; see [section 7](#7-limits-and-cautions).

**Run** starts the calculation and **Stop** ends it. While a run is going, the Input window shows a
progress bar (points of a path, or pressure rows of a pseudosection) and the controls are locked. When
it ends, a line says how long it took. If an input cannot be used (a path line that is not a pair of
numbers, a temperature out of range), a message says what is wrong and nothing runs.

A point takes one to a few seconds. Paths and pseudosections are spread over the server's processors,
so their speed depends on the server. As a guide, on four processor cores a 6 × 5 pseudosection of a
pelite takes about 25 s and the 9 × 4 world median pelite grid about 100 s.

## 4. The Results window

The heading names the rock and the kind of run. The line under it gives the phase set, the water
setting, the number of components the solver used, the run number and any oxides left out. A progress
bar shows while the run is going, and the results appear as they come in.

### 4.1 A P-T path

* **Minerals coming in and going out**: a list of each point where the assemblage changes, with the
  minerals that appear (in bold) and those that disappear.
* **The path on a facies diagram**: the path over schematic metamorphic facies fields (after Spear 1993
  and Winter 2010), with the kyanite = andalusite, kyanite = sillimanite and andalusite = sillimanite lines
  and the muscovite + quartz = K-feldspar + Al₂SiO₅ + H₂O line. These four lines are computed by
  Protolith from the ds6.2 dataset for the pure minerals; in a real rock the micas and feldspars are
  solid solutions and the reaction moves. Hold the pointer over a point of the path to read its
  temperature, pressure and assemblage. Points still running are grey.
* **Modes along the path**: the amount of each mineral (wt% of the rock) stacked against temperature.
* **Key**: the full name of every abbreviation shown.

### 4.2 A pseudosection

* **The diagram**: each cell is one equilibrium, calculated at the centre of the cell. Cells with the
  same assemblage that touch along an edge form a **field**. Each field carries a number; fields are
  shaded by variance (darker means more degrees of freedom); and lines are drawn along the cell edges
  between fields. Hold the pointer over a cell to read its field and assemblage. A cell where the solver
  failed is left blank and reads "failed".
* **The field table**: each field's number, assemblage, variance and number of cells. The same
  assemblage can appear as two fields if its cells do not touch.
* **Key**: the full name of every abbreviation shown.

The boundaries follow the grid, so they are stepped. A finer grid moves them closer to the true reaction
lines, at the cost of more points.

### 4.3 One point

The assemblage, the temperature and pressure, and the variance, then a table with one row per mineral:
its abbreviation, its name, its amount (wt% of the rock) and its structural formula. When there is a
free fluid, a line under the table gives its amount in grams per 100 g of rock.

### 4.4 Saving results

When a run has finished:

* **Download the table (CSV)** saves the run as a spreadsheet file:

  | Run | Columns |
  | --- | --- |
  | P-T path | `T_C`, `P_kbar`, `assemblage`, then one `<mineral>_wt_pct` column per mineral |
  | Pseudosection | `T_C`, `P_kbar`, `field` (the number on the diagram), `assemblage`, one row per cell |
  | One point | `mineral`, `name`, `wt_pct_of_rock`, `formula` |

* **Save sample** (for a path or a point) saves one point as a `.sample` file: a JSON text file with the
  conditions, the bulk composition, and each mineral and any melt with its own oxide composition, end
  members and formula. For a path, choose the point under **Sample from**. The free water is not
  included, so the sample is the rock as it would be collected.

Your workspace is kept only in the server's memory. It can be cleared when it has not been used for
12 hours or when the server restarts, so download anything you want to keep.

### 4.5 Notes on the models

The **Notes on the models** panel at the foot of the Results window summarizes the models and
conventions (the same points as in this manual). The **Sources and how to cite** panel, on both
windows, lists every source the app's data and methods come from.

## 5. Reading the results

### 5.1 Modes

Modes are **wt% of the rock without its free fluid**: the minerals plus any melt add up to 100. With
water in excess, the amount of free fluid depends on how much water the solver was given, so it has no
meaning of its own; it is reported apart and left out of the modes. A mineral under 0.01 wt% is treated
as a trace: it is left out of the assemblage and the table.

### 5.2 Assemblage labels

Assemblages are written with the mineral abbreviations of Whitney and Evans (2010), in a fixed order
(melt first, then garnet, pyroxenes, amphiboles, micas and so on to the oxides), with `H2O` (shown as
H₂O) for a free fluid. A mineral that appears twice, as two coexisting compositions across a solvus, is
written with a count, for example `2Amp` for two amphiboles.

### 5.3 Variance

The variance shown is the phase rule, F = C − P + 2, where C is the number of components the solver was
given and P is the number of phases, the free fluid included. For a pelite on the metapelite set
C = 11 (SiO₂, Al₂O₃, CaO, MgO, FeO, K₂O, Na₂O, TiO₂, O, H₂O, MnO; O stands for the oxygen of the ferric
iron). At 450 °C and 4 kbar the Barrovian pelite has eight phases (Bt Ms Chl Ep Pl Qz Rt H₂O), so
F = 11 − 8 + 2 = 5. Low-variance fields are narrow on a pseudosection; high-variance fields are broad.

### 5.4 Mineral names

One solution model can stand for more than one mineral. Protolith names each phase from its
composition, with these rules:

| Model | Named | Rule |
| --- | --- | --- |
| feldspar | K-feldspar (Kfs) or plagioclase (Pl) | Kfs when the sanidine end member is over half |
| white mica | paragonite (Pg), margarite (Mrg) or muscovite (Ms) | Pg or Mrg when that end member is over half; otherwise Ms |
| ilmenite-hematite | hematite (Hem) or ilmenite (Ilm) | Hem when the hematite end members are over half |
| spinel | magnetite (Mag) or spinel (Spl) | Mag when the magnetite and ulvöspinel end members are over half |
| epidote | clinozoisite (Czo) or epidote (Ep) | Czo when the clinozoisite end member is over half |
| clinopyroxene | jadeite (Jd), omphacite (Omp), pigeonite (Pgt) or clinopyroxene (Cpx) | Jd when the jadeite end member is over 0.8, Omp over 0.2; otherwise Pgt when Ca/(Ca+Mg+Fe) is under 0.25, else Cpx |
| amphibole | glaucophane (Gln), cummingtonite (Cum) or amphibole (Amp) | by the B-site group of Hawthorne et al. (2012): the two B-site cations are filled with Ca, then Na, then Mg-Fe-Mn; Gln when B-site Na is 1.5 or more, Cum when B-site Mg-Fe-Mn is 1.5 or more, otherwise Amp, a calcic amphibole such as hornblende |

The amphibole site assignment is a simplification of the full scheme of Hawthorne et al. (2012).

### 5.5 Structural formulae

Formulae are cations per a fixed number of anhydrous oxygens (for example 6 for pyroxenes, 12 for
garnet, 11 for micas, 23 for amphibole, 46 for staurolite), with the hydroxyl written after. All iron is
written as Fe, ferrous and ferric together. Pure minerals (quartz, kyanite, rutile and so on) show their
own formula.

## 6. A worked example: the Barrovian pelite

Load the **Barrovian pelite** card under P-T paths and press Run. The path goes from 450 °C, 4 kbar
through 600 °C, 7.5 kbar to 700 °C, 8 kbar in 16 points. The Results window lists these changes:

| Temperature, pressure | Change |
| --- | --- |
| 463 °C, 4.3 kbar | epidote out |
| 515 °C, 5.5 kbar | garnet and ilmenite in |
| 541 °C, 6.1 kbar | rutile out |
| 592 °C, 7.3 kbar | staurolite in; chlorite out |
| 700 °C, 8.0 kbar | kyanite and melt in; staurolite out |

Some things to notice:

* Biotite is present from the first point, so for this rock the model puts biotite in below 450 °C.
* Garnet appears at 515 °C but stays under 1 wt% up to 554 °C, and reaches 2.2 wt% at 579 °C. A
  mineral that is stable is not always one you would see in a hand specimen.
* Chlorite falls from 11.6 wt% at 450 °C to 4.6 wt% at 579 °C before it goes out as staurolite comes
  in.
* At the last point, 700 °C and 8 kbar, the rock holds 25 wt% melt with kyanite (6.4 wt%), and muscovite
  has fallen to 6 wt% from 16.5 wt% at the point before.

For a single point, the **Staurolite schist** card (aluminous pelite, 600 °C, 8 kbar) gives
Grt Bt Ms St Qz Ilm H₂O with variance 6: muscovite 31.8, quartz 23.3, staurolite 19.8, garnet 17.1,
biotite 6.6 and ilmenite 1.4 wt%. The garnet is
Ca0.05Mg0.39Fe2.52Mn0.08Al1.97Si3.00O12, an almandine.

## 7. Limits and cautions

* **The model is only as good as its data.** Results are the stable assemblage for the models of White
  et al. (2014) or Holland, Green and Powell (2018). Where those models differ from nature, so will
  Protolith.
* **Checked range.** The metapelite set is checked against MAGEMin from 300 to 900 °C and up to 12 kbar.
  The input boxes accept 100 to 1500 °C and up to 60 kbar; outside the checked range, treat results with
  care, and outside the range the models were made for, do not rely on them.
* **Equilibrium only.** Each point is full equilibrium of the whole rock. Protolith does not model
  reaction rates, overstepping, zoned minerals or the removal of melt or fluid as the rock heats: the
  bulk composition is the same at every point of a path.
* **Metabasites.** There is no dedicated metabasite set (Green et al. 2016) in Protolith. The igneous set
  stands in for mafic rocks, and it gives no greenschist chlorite-actinolite-epidote assemblage over the
  range of the cards.
* **Stepped boundaries.** Pseudosection boundaries follow the cells of the grid. Use a finer step to
  place a reaction more closely.
* **No melt below 500 °C.** As in MAGEMin, the melt model is switched off below 500 °C.
* **Free fluid.** With water in excess the amount of fluid is arbitrary; only its presence matters.
* **Left-out oxides.** Oxides a phase set cannot use (and P₂O₅, CO₂, NiO or CoO in an analysis) are not
  in the calculation, so phases such as apatite, carbonates or (with the metapelite set) chromite cannot
  form.
* **What the web window shows.** The web Results window gives modes and structural formulae. The
  desktop window also gives An of plagioclase, Mg# and garnet end members, lists trace minerals, and
  marks points where the solver did not fully converge.

## 8. Using Protolith in a class

Some ways to use the cards:

* Run the **Barrovian** and **Buchan** paths on the same pelite and compare where the aluminosilicates
  and cordierite appear. The only difference between the two runs is pressure.
* Run the **Chloritoid schist** and **Staurolite schist** points, which use the same rock, and ask which
  minerals took the place of chloritoid and chlorite.
* Run the **Barrovian pelite** pseudosection, then put the Barrovian path's temperatures and pressures
  on it and compare the assemblages.
* Change one oxide of a preset (raise Al₂O₃, or lower CaO) and run the same point again, to see how
  bulk composition controls the assemblage.
* Switch water from **In excess** to **The rock's own** and see where the rock runs short of water.

Several students can use Protolith at the same time: each browser that opens the app gets its own
workspace. Anyone given the full address of a window, with its `?w=` code, sees and can change that
workspace, so students should open the app from its plain address rather than share links.

## 9. Running Protolith on your own computer

Protolith is free to download from https://github.com/dougalien/protolith. With Python installed:

    pip install -r requirements.txt
    streamlit run streamlit_app.py

This opens the same web app on your own computer, running on its own processors.

The same two windows also run as a desktop app (`python -m metamorphism.app`, with `src` on the Python
path). Its Results window adds: An, Mg# and garnet end members for each mineral; trace minerals; a
mark where the solver did not fully converge; shading a pseudosection by the amount of one mineral;
downloading the diagram as an SVG image; saving a pseudosection and opening it again later; and
opening a `.sample` file as the rock (the whole sample, the minerals only, or the melt only).

The calculations also run from the command line, for example:

    python -m metamorphism point --rock pelite --t 600 --p 6
    python -m metamorphism grid --rock pelite --t 450 700 50 --p 2 10 2

## 10. How to cite, sources and license

If you use Protolith in a study or a class, please cite it, and cite the dataset and solution models
behind your result:

> Dougalien Systems (2026) Protolith: metamorphic phase equilibria on the Holland and Powell data,
> version 0.1.0. https://github.com/dougalien/protolith

The main works behind the results:

* Holland, T.J.B. and Powell, R. (2011) An improved and extended internally consistent thermodynamic
  dataset for phases of petrological interest, involving a new equation of state for solids.
  J. Metamorphic Geol. 29, 333-383. https://doi.org/10.1111/j.1525-1314.2010.00923.x
* White, R.W., Powell, R., Holland, T.J.B., Johnson, T.E. and Green, E.C.R. (2014) New mineral
  activity-composition relations for thermodynamic calculations in metapelitic systems. J. Metamorphic
  Geol. 32, 261-286. https://doi.org/10.1111/jmg.12071
* Holland, T.J.B., Green, E.C.R. and Powell, R. (2018) Melting of peridotites through to granites: a
  simple thermodynamic model in the system KNCFMASHTOCr. J. Petrology 59, 881-900.
  https://doi.org/10.1093/petrology/egy048
* Riel, N., Kaus, B.J.P., Green, E.C.R. and Berlie, N. (2022) MAGEMin, an efficient Gibbs energy
  minimizer: application to igneous systems. Geochem. Geophys. Geosyst. 23, e2022GC010427.
  https://doi.org/10.1029/2022GC010427

Also cited in this manual:

* Forshaw, J.B. and Pattison, D.R.M. (2023) Major-element geochemistry of pelites. Geology 51, 39-43.
  https://doi.org/10.1130/G50542.1
* Green, E.C.R., White, R.W., Diener, J.F.A., Powell, R., Holland, T.J.B. and Palin, R.M. (2016)
  Activity-composition relations for the calculation of partial melting equilibria in metabasic rocks.
  J. Metamorphic Geol. 34, 845-869. https://doi.org/10.1111/jmg.12211
* Hawthorne, F.C., Oberti, R., Harlow, G.E., Maresch, W.V., Martin, R.F., Schumacher, J.C. and Welch,
  M.D. (2012) Nomenclature of the amphibole supergroup. Am. Mineral. 97, 2031-2048.
  https://doi.org/10.2138/am.2012.4276
* Spear, F.S. (1993) Metamorphic Phase Equilibria and Pressure-Temperature-Time Paths. Mineralogical
  Society of America, Washington, DC.
* Whitney, D.L. and Evans, B.W. (2010) Abbreviations for names of rock-forming minerals. Am. Mineral.
  95, 185-187. https://doi.org/10.2138/am.2010.3371
* Winter, J.D. (2010) An Introduction to Igneous and Metamorphic Petrology, 2nd edition. Prentice Hall,
  Upper Saddle River, NJ.

The full list is in the app's **Sources and how to cite** panel.

Protolith is free software under the GNU General Public License, version 3 or later. It comes with no
warranty. To report a problem, use **Report a problem** at the foot of either window
(https://github.com/dougalien/protolith/issues).
