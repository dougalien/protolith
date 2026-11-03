# Reaction on Protolith's shared core

Reaction can now build its thermodynamic data on Protolith's Holland & Powell core instead of OBIGT alone.
This is step 3 of the plan's build order ("Reaction moves onto the core, checked against its own existing
test results"). It is a choice, not yet the default: the control window's **Data** menu (or
`REACTION_DATABASE=hp`) switches it, and every run records which data it used. OBIGT stays the default
until the differences listed in [HP_COMPARISON.md](HP_COMPARISON.md) have been read and accepted.

## What comes from where (`database="hp"`)

| Part | Source | Code |
| --- | --- | --- |
| Minerals the HP dataset holds (81 of Reaction's, plus 22 OBIGT lacks: ulvöspinel, hercynite, geikielite, pyrophanite, tephroite, spessartine, heulandite, stilbite, celadonite, chloritoid, staurolite and others) | Holland & Powell ds6.36, computed by `protolith.core.hp` | `reaction/thermo/hp_minerals.py` |
| Aqueous species of Na, K, Ca, Mg, Al, Si, C and Cl (43, among them Na+, K+, Ca+2, Mg+2, Al+3, SiO2, HCO3-, their chloride, hydroxide, carbonate and silicate complexes) | Miron, Wagner, Kulik and Heinrich (2016, GCA 187), Miron, Wagner, Kulik and Lothenbach (2017, AJS 317): HKF parameters fitted to mineral solubility experiments with the HP minerals, as tabulated in ThermoFun's aq17 dataset | `reaction/data/miron_aq17.tsv` (written by `scripts/extract_aq17.py`) |
| Dissolved Ti | rutile solubility (Knauss et al. 2001; Antignano and Manning 2008), now on HP rutile, so rutile's solubility is unchanged | `reaction/thermo/titanium.py` |
| Everything else (Fe, Mn, S, P, F and trace-metal species, gases, OBIGT-only minerals such as gibbsite, the clays, sulfates, halite and sylvite) | OBIGT, moved onto the new scale by the bridge | `hp_minerals.Bridged` |

## The energy scale

HP tabulates G = H − TS with H from the elements and S the third-law entropy. OBIGT and HKF use the apparent
Gibbs energy of formation, whose value at 25 °C is ΔfG°. The two differ by T_r × S(elements of the formula),
a constant per mineral that is added. Checked against the ds62 values of the aq17 dataset: albite −3712.00
kJ, halite −384.25, diaspore −920.83, quartz −856.43 (ours −856.27; ds6.36 revised quartz slightly).

## The bridge

Mixing the two traditions naively breaks things, and the first test showed how: with HP halite and Miron's
Na+ and Cl-, halite came out a full log unit too soluble at 25 °C (log K 0.56 against the measured 1.58).
Miron et al. moved Na+ and K+ some 5.7 kJ above OBIGT's to fit the HP alkali silicates, and halite's HP
energy is calorimetric, outside that fit. So:

1. **Species that stay OBIGT's keep their own log K.** Each one is moved with its basis species: its G gains,
   per atom of Na, K, Ca, Mg, Al, Si, C or Cl, the difference between Miron's and OBIGT's basis species at
   the same T and P. NaSO4-, CaSO4°, gibbsite, anhydrite, CO2(aq), halite and the rest therefore dissolve and
   associate exactly as before, against Miron's basis species.
2. **Fe and Mn have HP minerals but no refitted aqueous species.** One constant per atom moves all of OBIGT's
   Fe (and Mn) species, fitted so the HP Fe minerals (fayalite, magnetite, hematite, siderite, the Fe
   silicates) dissolve as close as possible to OBIGT's, 25–300 °C. It comes out at +0.94 kJ per Fe and
   −0.44 kJ per Mn. The per-mineral residuals are in the comparison report; the largest (daphnite −11.9 kJ,
   grunerite +10.7, siderite −8.3) are real disagreements between the datasets, not fitting noise.
3. **Halite and sylvite stay OBIGT's** (bridged as in 1), for the reason above.

Pyrite stays OBIGT's because Reaction's element-entropy table has no sulfur. Albite,low and K-feldspar,low are
dropped on this data, as they are the same minerals as HP albite and microcline (one name, not a tie).

## What changes (details in [HP_COMPARISON.md](HP_COMPARISON.md))

- **Most minerals move little.** Of the 81 minerals that switch to HP data, 46 change log K by 0.5 or
  less anywhere from 25 to 300 °C (quartz, calcite, albite, K-feldspar, muscovite, kaolinite, corundum,
  magnetite among them). The rest are sheet silicates, amphiboles and zeolites with many atoms, where a
  few kJ per formula add up: antigorite (13 log units over its 48 Mg), wairakite 6.1, sudoite 5.3, pargasite
  5.0, laumontite 3.9, anthophyllite 3.7, tremolite 2.6. These are the disagreements between the two
  traditions that the plan expected, not errors; the zeolites are where HP is least tested at low T.
- **Low-temperature waters hardly move.** The evaporating lake, boiling, calcite kinetics and the sinking
  foram end within 0.1 pH unit and form the same minerals; magnesite and dolomite saturation shift by up to
  a log unit (Mg+2 is about 2 kJ lower in Miron's fit).
- **Basalt alteration** forms the same main assemblage (actinolite, albite, chlorite, clinopyroxene,
  epidote-clinozoisite, quartz, sphene). Manganese now goes into spessartine garnet instead of alabandite,
  and the small magnetite and pyrrhotite are gone.
- **Serpentinization** forms chrysotile beside the serpentine solid solution, and antigorite is strongly
  supersaturated on HP data (saturation index 5) without forming.
- **Supercritical seawater (390-410 °C, 300 bar)** is the big one: final pH 8.2 instead of 5.9, with much
  less NaCl° and HCl° ion pairing and brucite near saturation, and more points the solver cannot finish
  (5 against 1). This is next to water's critical point, where HKF is least reliable on either data; the
  two disagree there and neither should be trusted without checking against experiments.

## Inside Protolith

`protolith.reaction_link` recasts a Magma rock onto more minerals when Reaction is on this data: a spinel's
ulvöspinel and hercynite, an ilmenite's geikielite and pyrophanite, and manganese as tephroite and spessartine.
What OBIGT had to leave as a glass of left-over oxides now goes on as minerals.

## Not done yet

- The default is still OBIGT. Switching it is one line in `reaction/app/config.py` once the comparison is
  accepted.
- The Miron fit was made with ds62; the core carries ds6.36, which revised some minerals by a few kJ
  (muscovite 8.0, tremolite 4.4, laumontite 4.0, paragonite 3.7). Those minerals' solubilities move by that
  much against Miron's own fit.
- Fe, Ti and S aqueous species fitted to HP minerals (the plan's step 2 for the other elements) would replace
  the Fe bridge.
- Reaction's solid solutions (`data/solid_solutions.tsv`) still use Reaction's own mixing models on top of
  the HP end members, not HP's solution models.
