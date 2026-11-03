# Where Protolith's code came from

Copied on 2026-11-03. The originals stay as they are; changes made here do not flow back.

| Module | Source | Commit |
| --- | --- | --- |
| `src/magma`, `tests/magma`, `docs/magma`, `packaging/magma` | github.com/dougalien/magma, `main` | d72e965 |
| `src/reaction`, `tests/reaction`, `docs/reaction`, `packaging/reaction`, `scripts` | github.com/dougalien/Reaction, `main` (the local clone in `Dougalien Systems\Reaction`) | 53b68e0 |

Test results right after the copy (Linux, Python 3.13, numpy and scipy current):

- Reaction: 492 passed, with its reference data installed.
- Magma: 206 passed, 1 skipped (21 minutes).
- Protolith link tests: 12 passed.

Changes since the copy that touch the copied code: on 2026-11-03 Magma's Holland & Powell dataset,
solution models and solver (`magma/hp/endmembers.py`, `solutions.py`, `minimize.py`, `data/hp_ds636.tsv`
and their tests) moved to the shared core in `src/protolith/core/`; Magma keeps `magma/hp/engine.py`.
