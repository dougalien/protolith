# Protolith

An open geochemical calculator: melting and crystallization of magma, water-rock reaction, and later
metamorphism and surface processes, on shared thermodynamic data. Each module stands alone; a **sample**
(a rock and/or fluid at a stated T and P) carries the result of one module into the next.

Protolith is built from copies of the two existing apps. **Magma and Reaction themselves are not
changed**: they keep their own folders, repositories and exes. Where each copy came from is in
[docs/ORIGINS.md](docs/ORIGINS.md).

Plan: [Linking Magma and Reaction: feasibility and architecture](https://claude.ai/artifact/KqQF2Kz2euZdrhDm1zK1TG)

## Layout

| Path | What it is |
| --- | --- |
| `src/magma/` | the Magma module (melting, crystallization; Holland & Powell and MELTS engines) |
| `src/reaction/` | the Reaction module (speciation, reaction paths, kinetics, transport) |
| `src/protolith/` | shared code: the sample file and the links between modules |
| `src/protolith/app/` | the shell: the home window, and every module running in one program |
| `tests/magma/`, `tests/reaction/`, `tests/protolith/` | each module's own tests, plus the link tests |
| `docs/magma/`, `docs/reaction/` | each module's own design notes and README |
| `packaging/protolith/` | the build of Protolith.exe (one file with every module) |
| `packaging/magma/`, `packaging/reaction/` | the original exe builds, kept for reference |

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
