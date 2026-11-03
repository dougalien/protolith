# Reaction on the shared core: what changes

Written by `scripts/compare_databases.py` on 2026-11-03. Old: OBIGT/HKF (current). New: Holland & Powell minerals, Miron aqueous species, OBIGT for the rest.

- 103 minerals come from the Holland & Powell dataset (Protolith's shared core) and 43 aqueous species from Miron et al. (2016, 2017), fitted to those minerals; the other species are OBIGT's, moved onto that scale through their basis species so their own log K are kept; OBIGT's Fe species also by +0.94 kJ per Fe, the bridge fitted on the HP Fe minerals; OBIGT's Mn species also by -0.44 kJ per Mn, the bridge fitted on the HP Mn minerals.

## 1. log K of the minerals that changed data

Dissolution to Reaction's basis species at water saturation (1 bar to 100 C). `new` marks a mineral OBIGT does not have.

| mineral | 25 C OBIGT | 25 C HP | 100 C OBIGT | 100 C HP | 200 C OBIGT | 200 C HP | 300 C OBIGT | 300 C HP | largest change |
|---|---|---|---|---|---|---|---|---|---|
| acmite |  | -7.99 |  | -5.86 |  | -4.22 |  | -3.26 | new |
| akermanite | 48.02 | 47.67 | 36.85 | 36.57 | 27.16 | 26.93 | 20.39 | 20.18 | 0.35 |
| albite | 0.95 | 1.26 | -1.22 | -0.98 | -3.47 | -3.28 | -5.23 | -5.09 | 0.31 |
| albite,high | 2.43 | 2.84 | -0.22 | 0.10 | -2.87 | -2.61 | -4.89 | -4.67 | 0.41 |
| almandine | 40.17 | 39.91 | 24.07 | 23.90 | 9.75 | 9.66 | -0.83 | -0.88 | 0.26 |
| amesite |  | 67.60 |  | 41.18 |  | 18.59 |  | 2.11 | new |
| analcime | 6.92 | 5.96 | 3.48 | 2.74 | 0.35 | -0.19 | -1.93 | -2.34 | 0.96 |
| andalusite | 13.68 | 13.71 | 5.51 | 5.52 | -1.80 | -1.80 | -7.31 | -7.33 | 0.03 |
| andradite | 19.01 | 17.80 | 14.30 | 13.34 | 9.80 | 9.04 | 6.02 | 5.38 | 1.21 |
| annite | 29.43 | 29.63 | 19.37 | 19.54 | 10.42 | 10.57 | 3.76 | 3.92 | 0.20 |
| anorthite | 24.53 | 23.83 | 13.74 | 13.17 | 4.05 | 3.60 | -3.17 | -3.55 | 0.71 |
| anthophyllite | 70.09 | 73.81 | 50.78 | 53.75 | 33.78 | 36.13 | 21.81 | 23.79 | 3.73 |
| antigorite | 488.44 | 501.68 | 362.51 | 373.04 | 256.10 | 264.65 | 181.99 | 189.58 | 13.24 |
| aragonite | 2.09 | 1.95 | 1.01 | 0.87 | -0.34 | -0.49 | -1.97 | -2.11 | 0.15 |
| bixbyite | 9.35 | 9.51 | 7.45 | 7.58 | 5.87 | 5.97 | 4.54 | 4.63 | 0.16 |
| brucite | 16.38 | 16.78 | 12.52 | 12.84 | 9.38 | 9.63 | 7.25 | 7.45 | 0.40 |
| Ca-Al-pyroxene | 32.86 | 31.05 | 20.46 | 19.08 | 9.56 | 8.53 | 1.53 | 0.74 | 1.80 |
| calcite | 2.00 | 1.79 | 0.91 | 0.71 | -0.47 | -0.65 | -2.10 | -2.28 | 0.21 |
| celadonite |  | 8.61 |  | 5.08 |  | 1.57 |  | -1.16 | new |
| chloritoid |  | 24.87 |  | 13.99 |  | 4.54 |  | -2.43 | new |
| chrysotile | 31.41 | 33.08 | 23.40 | 24.72 | 16.67 | 17.69 | 12.01 | 12.83 | 1.67 |
| clinochlore | 59.69 | 61.54 | 39.50 | 40.95 | 22.36 | 23.48 | 10.03 | 10.94 | 1.85 |
| clinozoisite | 40.74 | 39.81 | 24.29 | 23.48 | 9.57 | 8.88 | -1.45 | -2.05 | 0.93 |
| coesite | -3.36 | -3.16 | -2.55 | -2.39 | -2.00 | -1.88 | -1.64 | -1.54 | 0.19 |
| cordierite | 47.45 | 48.10 | 24.90 | 25.57 | 4.74 | 5.41 | -10.11 | -9.46 | 0.67 |
| corundum | 18.27 | 18.10 | 9.05 | 8.92 | 1.00 | 0.88 | -5.01 | -5.11 | 0.17 |
| cummingtonite |  | 74.13 |  | 54.00 |  | 36.32 |  | 23.93 | new |
| daphnite | 47.65 | 46.18 | 30.12 | 28.69 | 14.89 | 13.50 | 3.60 | 2.25 | 1.47 |
| diaspore | 7.19 | 7.04 | 3.26 | 3.15 | -0.14 | -0.22 | -2.70 | -2.75 | 0.15 |
| diopside | 21.33 | 21.63 | 16.11 | 16.35 | 11.46 | 11.64 | 8.13 | 8.27 | 0.30 |
| dolomite | 3.20 | 3.31 | 0.65 | 0.68 | -2.33 | -2.35 | -5.71 | -5.77 | 0.10 |
| eastonite |  | 47.32 |  | 28.93 |  | 12.93 |  | 1.19 | new |
| enstatite | 11.63 | 12.18 | 8.47 | 8.91 | 5.71 | 6.05 | 3.77 | 4.06 | 0.55 |
| epidote | 23.80 | 22.75 | 13.02 | 12.37 | 3.20 | 2.86 | -4.43 | -4.57 | 1.04 |
| fayalite | 19.38 | 19.50 | 13.71 | 13.81 | 8.77 | 8.84 | 5.20 | 5.26 | 0.12 |
| Fe-chloritoid |  | 19.17 |  | 9.54 |  | 1.08 |  | -5.27 | new |
| Fe-epidote |  | 9.73 |  | 4.49 |  | -0.56 |  | -4.89 | new |
| Fe-pumpellyite |  | 75.57 |  | 47.21 |  | 21.91 |  | 2.89 | new |
| Fe-staurolite |  | 161.57 |  | 77.65 |  | 3.42 |  | -52.28 | new |
| ferro-actinolite | 50.60 | 51.87 | 36.89 | 37.63 | 24.24 | 24.50 | 14.91 | 14.84 | 1.26 |
| ferrosilite | 7.82 | 7.84 | 5.42 | 5.45 | 3.26 | 3.29 | 1.67 | 1.71 | 0.03 |
| forsterite | 28.16 | 29.26 | 20.70 | 21.57 | 14.37 | 15.04 | 9.98 | 10.52 | 1.10 |
| gehlenite | 54.98 | 54.18 | 37.69 | 37.04 | 22.64 | 22.12 | 11.75 | 11.32 | 0.81 |
| geikielite |  | 10.09 |  | 5.61 |  | 1.78 |  | -0.94 | new |
| glaucophane | 35.02 | 35.66 | 22.55 | 23.16 | 11.05 | 11.75 | 2.51 | 3.39 | 0.87 |
| graphite | 61.27 | 61.26 | 46.87 | 46.84 | 34.37 | 34.33 | 25.66 | 25.62 | 0.04 |
| grossular | 50.04 | 48.39 | 34.39 | 33.08 | 20.43 | 19.40 | 10.07 | 9.22 | 1.64 |
| grunerite | 42.20 | 44.35 | 28.72 | 30.33 | 16.26 | 17.41 | 7.04 | 7.88 | 2.15 |
| hedenbergite | 19.48 | 18.70 | 14.62 | 13.98 | 10.20 | 9.69 | 6.99 | 6.55 | 0.77 |
| hematite | -15.12 | -15.40 | -12.67 | -12.89 | -10.67 | -10.84 | -9.74 | -9.88 | 0.28 |
| hercynite |  | 30.96 |  | 18.15 |  | 7.02 |  | -1.18 | new |
| heulandite |  | -0.98 |  | -5.38 |  | -9.92 |  | -13.45 | new |
| ilmenite | 3.25 | 3.00 | 0.10 | -0.09 | -2.67 | -2.81 | -4.73 | -4.84 | 0.25 |
| iron | 57.58 | 57.43 | 44.28 | 44.16 | 33.10 | 33.00 | 25.65 | 25.57 | 0.15 |
| jadeite | 6.53 | 6.74 | 3.45 | 3.62 | 0.58 | 0.70 | -1.60 | -1.51 | 0.21 |
| K-feldspar | -1.33 | -1.77 | -2.71 | -3.06 | -4.38 | -4.65 | -5.83 | -6.03 | 0.44 |
| K-feldspar,high | -0.17 | -0.26 | -1.94 | -1.86 | -3.92 | -3.73 | -5.55 | -5.31 | 0.24 |
| kalsilite | 10.87 | 11.23 | 6.78 | 7.04 | 3.10 | 3.27 | 0.33 | 0.45 | 0.35 |
| kaolinite | 4.89 | 4.53 | -0.59 | -0.85 | -5.59 | -5.71 | -9.48 | -9.43 | 0.36 |
| kyanite | 13.41 | 13.44 | 5.39 | 5.40 | -1.80 | -1.80 | -7.23 | -7.24 | 0.03 |
| larnite | 38.92 | 38.86 | 30.60 | 30.56 | 23.40 | 23.37 | 18.37 | 18.35 | 0.06 |
| laumontite | 13.62 | 9.76 | 6.19 | 3.35 | -0.65 | -2.64 | -5.77 | -7.23 | 3.86 |
| lawsonite | 18.91 | 18.40 | 10.50 | 10.10 | 3.00 | 2.69 | -2.68 | -2.94 | 0.51 |
| lime | 32.69 | 32.77 | 25.87 | 25.93 | 20.10 | 20.14 | 16.17 | 16.20 | 0.08 |
| magnesite | 1.94 | 2.75 | 0.31 | 0.93 | -1.44 | -0.97 | -3.29 | -2.92 | 0.81 |
| magnetite | -4.94 | -4.88 | -5.52 | -5.48 | -6.11 | -6.09 | -7.05 | -7.05 | 0.06 |
| manganosite | 18.36 | 18.38 | 14.09 | 14.11 | 10.51 | 10.52 | 8.03 | 8.04 | 0.02 |
| margarite | 37.61 | 36.41 | 19.27 | 18.33 | 3.02 | 2.28 | -9.20 | -9.78 | 1.19 |
| meionite | 81.22 | 81.45 | 46.21 | 46.15 | 14.51 | 14.19 | -9.63 | -10.11 | 0.48 |
| merwinite | 73.26 | 72.36 | 56.75 | 56.02 | 42.53 | 41.94 | 32.63 | 32.13 | 0.90 |
| Mg-Tschermak pyroxene |  | 33.09 |  | 19.95 |  | 8.50 |  | 0.15 | new |
| monticellite | 31.94 | 32.14 | 24.40 | 24.55 | 17.93 | 18.03 | 13.41 | 13.48 | 0.20 |
| muscovite | 11.35 | 11.57 | 2.36 | 2.54 | -5.94 | -5.79 | -12.41 | -12.28 | 0.22 |
| nepheline | 13.78 | 12.45 | 8.78 | 7.73 | 4.41 | 3.60 | 1.25 | 0.58 | 1.33 |
| paragonite | 13.53 | 13.93 | 3.86 | 4.18 | -4.92 | -4.67 | -11.64 | -11.44 | 0.40 |
| pargasite | 101.92 | 96.91 | 69.60 | 65.95 | 41.45 | 38.93 | 21.25 | 19.43 | 5.01 |
| periclase | 21.37 | 21.73 | 16.11 | 16.40 | 11.72 | 11.96 | 8.73 | 8.93 | 0.36 |
| phlogopite | 38.22 | 39.32 | 26.36 | 27.32 | 16.06 | 16.92 | 8.65 | 9.44 | 1.10 |
| prehnite | 32.18 | 31.45 | 20.40 | 19.78 | 9.81 | 9.26 | 1.90 | 1.39 | 0.72 |
| pseudowollastonite | 14.07 | 13.94 | 11.04 | 10.92 | 8.33 | 8.21 | 6.40 | 6.28 | 0.12 |
| pumpellyite | 78.73 | 79.55 | 50.20 | 50.37 | 24.85 | 24.43 | 5.85 | 5.03 | 0.82 |
| pyrope | 56.80 | 58.18 | 37.18 | 38.28 | 20.08 | 20.93 | 7.78 | 8.47 | 1.38 |
| pyrophanite |  | 5.27 |  | 2.15 |  | -0.56 |  | -2.56 | new |
| pyrophyllite | -1.68 | -1.47 | -5.87 | -5.71 | -10.16 | -10.03 | -13.63 | -13.51 | 0.20 |
| quartz | -4.01 | -3.89 | -3.09 | -3.00 | -2.45 | -2.37 | -2.02 | -1.97 | 0.11 |
| rhodochrosite | 0.25 | -0.12 | -0.68 | -0.96 | -1.86 | -2.07 | -3.35 | -3.51 | 0.36 |
| riebeckite |  | -7.81 |  | -7.02 |  | -7.15 |  | -7.88 | new |
| rutile | -7.67 | -7.67 | -7.65 | -7.65 | -7.72 | -7.72 | -7.85 | -7.85 | 0.00 |
| siderite | -0.19 | -1.90 | -1.50 | -2.76 | -3.02 | -3.91 | -4.76 | -5.40 | 1.71 |
| sillimanite | 14.12 | 14.08 | 5.82 | 5.79 | -1.60 | -1.63 | -7.19 | -7.21 | 0.05 |
| spessartine |  | 40.01 |  | 25.24 |  | 12.14 |  | 2.41 | new |
| sphene | 2.44 | 2.43 | 0.31 | 0.30 | -1.75 | -1.76 | -3.33 | -3.35 | 0.02 |
| spinel | 35.23 | 35.57 | 21.57 | 21.87 | 9.81 | 10.05 | 1.26 | 1.45 | 0.34 |
| staurolite |  | 184.27 |  | 95.58 |  | 17.55 |  | -40.47 | new |
| stilbite |  | -5.03 |  | -7.07 |  | -9.57 |  | -11.72 | new |
| sudoite | 36.62 | 41.95 | 18.55 | 22.66 | 2.74 | 5.58 | -9.10 | -7.29 | 5.34 |
| talc | 22.19 | 23.88 | 15.92 | 17.30 | 10.30 | 11.42 | 6.31 | 7.26 | 1.69 |
| tephroite |  | 24.01 |  | 18.19 |  | 13.20 |  | 9.65 | new |
| tremolite | 63.36 | 66.01 | 46.92 | 49.01 | 32.21 | 33.83 | 21.70 | 23.00 | 2.64 |
| tschermakite |  | 79.18 |  | 49.99 |  | 24.15 |  | 5.14 | new |
| ulvospinel |  | 17.61 |  | 10.49 |  | 4.36 |  | -0.06 | new |
| wairakite | 18.03 | 11.89 | 8.66 | 4.40 | 0.05 | -2.63 | -6.34 | -8.00 | 6.14 |
| wollastonite | 13.53 | 13.21 | 10.65 | 10.38 | 8.06 | 7.84 | 6.21 | 6.02 | 0.33 |

## 2. The bridge

OBIGT species of these elements are moved by one constant per atom, fitted on the HP minerals of the element (25-300 C). Residual: how far each mineral's HP energy still sits from OBIGT's after the bridge, kJ per formula (negative: HP more stable).

- **Fe**: +0.94 kJ per atom. Residuals: daphnite -11.9, siderite -8.3, andradite -6.9, hedenbergite -4.6, epidote -3.5, hematite -1.6, almandine -1.0, iron -0.9, magnetite +0.2, ferrosilite +0.3, fayalite +0.7, annite +1.4, ferro-actinolite +3.1, grunerite +10.7
- **Mn**: -0.44 kJ per atom. Residuals: rhodochrosite -1.9, manganosite +0.1, bixbyite +0.9

Kept from OBIGT: pyrite: no entropy for element S; OBIGT's is kept

## 3. The examples on both databases

### Basalt alteration (`solid_solutions`)

- Forms on both: actinolite, albite, anhydrite, brucite, chlorite, clinopyroxene, epidote-clinozoisite, hydroxyapatite, pyrite, quartz, sphene
- Only on OBIGT: alabandite, epidote, magnetite, plagioclase, pyrrhotite
- Only on HP: garnet, spessartine
- Final pH: 5.42 (OBIGT), 5.45 (HP)
- Largest changes in final saturation index (log Q/K): anhydrite -9.42 to -3.93; Mg-cronstedtite -5.05 to -3.59; sulfur -4.59 to -3.20; S_liq -4.54 to -3.15; pyrite -1.12 to -0.00
- Run time: 27 s (OBIGT), 29 s (HP)

### Evaporating lake (`lake`)

- Forms on both: anhydrite, calcite, epsomite, halite, hydromagnesite, sylvite
- Final pH: 6.11 (OBIGT), 6.12 (HP)
- Largest changes in final saturation index (log Q/K): magnesite 2.82 to 2.01; brucite -3.78 to -4.18; calcite -0.76 to -0.54; aragonite -0.84 to -0.70; dolomite 2.80 to 2.70
- Run time: 4 s (OBIGT), 4 s (HP)

### Boiling (`boiling`)

- Forms on both: calcite
- Final pH: 6.78 (OBIGT), 6.79 (HP)
- Largest changes in final saturation index (log Q/K): anhydrite -2.50 to -2.71; coesite -0.37 to -0.50; quartz 0.12 to 0.04; wollastonite -2.84 to -2.79; aragonite -0.11 to -0.16
- Run time: 2 s (OBIGT), 1 s (HP)

### Supercritical seawater (`phase_separation`)

- Forms on both: anhydrite, brucite
- Final pH: 5.87 (OBIGT), 8.17 (HP)
- Largest changes in final saturation index (log Q/K): brucite -5.01 to -0.35; periclase -5.78 to -1.14; halite -1.90 to -1.74; anhydrite -1.74 to -1.65; ice -1.09 to -1.08
- Run time: 11 s (OBIGT), 34 s (HP)

### Serpentinization (`serpentinization`)

- Forms on both: anhydrite, brucite, magnetite, pyrite, pyrrhotite, serpentine
- Only on OBIGT: hematite
- Only on HP: Mg-cronstedtite, chrysotile
- Final pH: 5.37 (OBIGT), 5.72 (HP)
- Largest changes in final saturation index (log Q/K): antigorite -0.46 to 5.17; dolomite -2.42 to -1.55; anhydrite -17.84 to -17.01; calcite -2.35 to -1.54; aragonite -2.48 to -1.70
- Run time: 2 s (OBIGT), 3 s (HP)

### Calcite dissolving (`kinetics`)

- Forms on both: calcite
- Final pH: 9.87 (OBIGT), 9.78 (HP)
- Largest changes in final saturation index (log Q/K): magnesite -1.50 to -2.44; brucite -2.10 to -2.66; dolomite -0.76 to -1.21; aragonite -0.09 to -0.16; calcite -0.00 to -0.00
- Run time: 2 s (OBIGT), 2 s (HP)

### A foram sinking below the CCD (`forams`)

- Forms on both: calcite
- Final pH: 7.84 (OBIGT), 7.80 (HP)
- Largest changes in final saturation index (log Q/K): magnesite 0.13 to -0.90; dolomite 0.39 to -0.00; anhydrite -1.53 to -1.77; gypsum -1.10 to -1.34; hexahydrite -1.49 to -1.73
- Run time: 2 s (OBIGT), 1 s (HP)

### Vent fluid meets seawater (`vent_energy`)

- Forms on both: nothing
- Final pH: 7.21 (OBIGT), 7.26 (HP)
- Largest changes in final saturation index (log Q/K): antigorite -63.47 to -87.58; sudoite 10.44 to 3.63; wairakite -4.84 to 1.39; anthophyllite -19.76 to -25.19; tremolite -13.55 to -17.83
- Run time: 2 s (OBIGT), 2 s (HP)

