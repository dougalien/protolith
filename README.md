# Protolith

An open geochemical calculator in four modules on shared thermodynamic data: Magma (melting and
crystallization), Metamorphism (stable assemblages and pseudosections), Reaction (hot water and rock) and
Weathering (water and rock at the surface). Each module stands alone; a **sample**
(a rock and/or fluid at a stated T and P) carries the result of one module into the next.

Protolith is built from copies of the two existing apps. **Magma and Reaction themselves are not
changed**: they keep their own folders, repositories and exes. Where each copy came from is in
[docs/ORIGINS.md](docs/ORIGINS.md).

Plan: [Linking Magma and Reaction: feasibility and architecture](https://claude.ai/artifact/KqQF2Kz2euZdrhDm1zK1TG)

## Layout

| Path | What it is |
| --- | --- |
| `src/magma/` | the Magma module (melting, crystallization; Holland & Powell and MELTS engines) |
| `src/reaction/` | the Reaction module (speciation, reaction paths, kinetics, transport); inside Protolith it also runs as Weathering, with the low-temperature cards (`reaction/app/profiles.py`) |
| `src/metamorphism/` | the Metamorphism module (stable assemblages at T and P, pseudosections; on the HP core) |
| `src/protolith/core/` | the shared thermodynamic core: the Holland & Powell dataset, solution models and solver (no user interface) |
| `src/protolith/` | shared code: the core, the sample file and the links between modules |
| `src/protolith/app/` | the shell: the home window, and every module running in one program |
| `tests/core/`, `tests/magma/`, `tests/reaction/`, `tests/metamorphism/`, `tests/protolith/` | the core's tests, each module's own tests, plus the link tests |
| `docs/magma/`, `docs/reaction/`, `docs/metamorphism/` | each module's own design notes and README |
| `packaging/protolith/` | the build of Protolith.exe (one file with every module) |
| `packaging/magma/`, `packaging/reaction/` | the original exe builds, kept for reference |

## The shared core

`protolith.core.hp` is the Holland & Powell system every module computes with: the ds6.36 end members
(`endmembers`, ds6.36 and ds6.2), the igneous solution models including melt and fluid (`solutions`), the
metapelite set of White et al. (2014) (`solutions_mp`), and the Gibbs energy
minimizer with its oxygen buffer and warm starts (`minimize`). It came out of Magma, which now runs its
HP engine (`magma.hp.engine`, the adapter from wt% to paths) on it. The core imports nothing from the
modules or the shell, so it can be tested and released on its own (`python -m pytest tests/core`).

Reaction can run on this core: its **Data** menu (or `REACTION_DATABASE=hp`) takes the minerals from the HP
dataset here and the aqueous species fitted to them (Miron et al. 2016, 2017), with a bridge that keeps
every remaining OBIGT species' own log K. OBIGT stays the default until the differences are accepted:
[docs/reaction/HP_CORE.md](docs/reaction/HP_CORE.md) explains the design, and
[docs/reaction/HP_COMPARISON.md](docs/reaction/HP_COMPARISON.md) (from `scripts/compare_databases.py`) lists
every change.

Metamorphism runs the same minimizer at one T and P or over a T-P grid (a pseudosection). By default it
uses the full metapelite set of White et al. (2014) on ds6.2, with MnO (`solutions_mp`, ported from
MAGEMin and checked against MAGEMin's own results). The igneous set is the other choice.
Its rock can come from a `.sample` file (the whole sample, the rock or the melt), and any point can be
saved as one. Its window opens from Protolith's home window (or alone with `python -m metamorphism.app`):
pick a card or a rock, run one point or a grid, and click any cell of the diagram for its minerals, to
save as a sample or send to Reaction. From the command line:

    python -m metamorphism point --rock pelite --t 600 --p 6
    python -m metamorphism grid --rock metabasite --t 450 750 25 --p 2 12 1 --out mb.pseudosection

[docs/metamorphism/DESIGN.md](docs/metamorphism/DESIGN.md) has the design, the checks and the next steps.

## Reaction and Weathering

Inside Protolith, Reaction's engine serves two windows. **Reaction** is the hydrothermal module: its
starting cards are seawater, fresh water heated to 300 °C and a vent fluid, and its examples are basalt
alteration, serpentinization, boiling, supercritical seawater and vent energy. **Weathering** is the
low-temperature module: its cards are the evaporating brine and the contaminated stream, and its
examples are calcite dissolving, a foram sinking below the CCD, flow-through weathering of a soil, the
evaporating lake and metals on stream clays. Each window keeps its own saved session; any card can still be
edited into any run. Reaction on its own (`python -m reaction.app`) keeps every card.

## The sample file (version 1)

`protolith.sample.Sample` reads and writes `.sample` files (JSON): conditions, bulk oxide composition,
each phase with its own oxide composition and end members, melt, fluid, and which thermodynamic data made
it. `protolith.magma_link.from_step` turns any step of a Magma run into a sample.
`protolith.reaction_link.to_reactants` recasts its solids onto minerals in Reaction's database, ready for
the reactant card.

In the apps: Magma's results window has **Save sample** (pick a step, and the melt and rock or the
rock alone; a fractional run saves the cumulate piled up so far). Reaction's card has **Open sample**:
the rock goes on as minerals, the melt as a glass of its oxides, at the grams in the rock box.

Inside Protolith the file can be skipped: **Send to Reaction**, next to Save sample, puts the step
straight on Reaction's card and brings Reaction's window forward.

Nothing is dropped silently: whatever Reaction has no mineral for is listed with its grams and a sentence
for the card. Titanium now goes on as rutile, ilmenite or sphene and dissolves as Ti(OH)4, Ti(OH)3+ and
Ti(OH)5- (`src/reaction/thermo/titanium.py`, from Knauss et al. 2001 and Antignano and Manning 2008).

## Running

    python -m pip install numpy scipy pytest
    python -m pytest

The Reaction tests need its reference data (EQ3/6 and CHNOSZ OBIGT files), which is never committed:
`scripts/fetch_references.ps1` downloads it into `%LOCALAPPDATA%\Reaction\external`, the folder the
Reaction app already uses. Without it those tests are skipped or fail with a message saying so.

Protolith, with every module and its home window:

    python -m protolith.app

`Protolith.exe` does the same. GitHub builds it on every push to main (the "Latest Windows build"
release) and on every pull request (an artifact of the run); `packaging\protolith\build_exe.ps1` builds
it locally. Each module can still run on its own, from this folder:

    python -m magma.app
    python -m reaction.app

## Rules carried over from both apps

- Every number comes from the solver; every datum is cited.
- Parameter values may come from published papers and open datasets (Holland & Powell, ThermoEngine,
  MAGEMin, OBIGT), always cited; equations are written here, and no code from those projects is copied.
