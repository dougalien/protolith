# Protolith

Protolith finds the stable mineral assemblage of a rock at a given temperature and pressure: at one
point, along a P-T path, or over a T-P grid (a pseudosection). It minimizes the Gibbs energy of the rock
on the Holland and Powell (2011) thermodynamic dataset, with two sets of solution models:

* **metapelite**: White et al. (2014) on ds6.2, in MnNCKFMASHTO (garnet, staurolite, chloritoid,
  cordierite, the micas, chlorite, melt and the rest);
* **igneous**: Holland, Green and Powell (2018) on ds6.36, for basalts and other mafic rocks.

The parameter values are those distributed in MAGEMin (Riel et al. 2022). The metapelite set reproduces
MAGEMin's own reference grid for its world median pelite at all 48 points (assemblage, and system Gibbs
energy within 0.0005 kJ/mol). The design notes are in [docs/metamorphism/DESIGN.md](docs/metamorphism/DESIGN.md).

## Using it

On the web, Protolith has two windows: **Input** (a rock from a card, a preset or typed oxides; the phase
set; water from the rock or in excess; one point, a P-T path or a grid) and **Results** (the assemblage,
modes and compositions, the path on a facies diagram, or the pseudosection). Both follow one run, so the
Results window can sit on a second screen. Runs can be saved as CSV, and any point as a `.sample` file.

To run it yourself:

    pip install -r requirements.txt
    streamlit run streamlit_app.py

The same two windows also run as a local desktop app (`python -m metamorphism.app`), and the
calculations run from the command line (`python -m metamorphism point ...` or `grid ...`).

## Layout

| Path | What it is |
| --- | --- |
| `src/metamorphism/` | the calculations (bulk, point, path, pseudosection, mineral names, facies background) and the two windows (`web/` for Streamlit, `app/` for the desktop) |
| `src/protolith/core/` | the Holland & Powell core: end-member datasets, solution models and the minimizer (no user interface) |
| `src/protolith/sample.py` | the `.sample` file (a rock's conditions, bulk and phases, as JSON) |
| `scripts/` | how the data were produced: `extract_hp_dataset.py` and `port_magemin_mp.py` read MAGEMin's sources; `compare_mp_magemin.py` runs MAGEMin's 48-point reference grid |
| `tests/` | the core's tests, the module's tests and the sample file's tests |
| `packaging/protolith/` | the Windows exe build and the icon |

## Tests

    python -m pip install numpy scipy streamlit plotly pytest
    python -m pytest

## How to cite

If you use Protolith in a study or a class, please cite it, and cite the dataset and solution models
behind your result (the app's "Sources and how to cite" panel lists them). GitHub's "Cite this
repository" button gives the reference from `CITATION.cff`:

> Dougalien Systems (2026) Protolith: metamorphic phase equilibria on the Holland and Powell data,
> version 0.1.0. https://github.com/dougalien/protolith

## License and credits

Protolith is free software under the GNU General Public License, version 3 or later (`LICENSE`).
Anyone may use, copy, change and share it at no cost; copies and changed versions that are passed on
must stay under the same license. It comes with no warranty.

The thermodynamic data and solution models are the work of T.J.B. Holland, R. Powell, R.W. White,
E.C.R. Green and their coauthors (Holland and Powell 2011; White et al. 2014; Green et al. 2016;
Holland, Green and Powell 2018). Their parameter values were taken from MAGEMin (Riel, Kaus, Green and
Berlie 2022), which is distributed under the GPL-3.0; the code here is written from the papers'
equations. The world median pelite is from Forshaw and Pattison (2023). Mineral abbreviations follow
Whitney and Evans (2010).
