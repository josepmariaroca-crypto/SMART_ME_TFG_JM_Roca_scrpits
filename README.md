# SMART_ME_TFG_JM_Roca_scrpits
The source code used in this thesis — data download from Copernicus Marine (Python) and statistical and spatial analysis (R) — is publicly available at the repository indicated below, together with a README detailing the operation of each script.
# Environmental Data Download and Analysis Scripts

This repository contains the source code used in the thesis to (1) download
bottom-layer environmental variables from Copernicus Marine reanalysis
products, and (2) perform the multi-year, seasonal statistical and spatial
analysis of those variables (descriptive statistics, PCA, clustering,
environmental similarity, and Marine Protected Area prioritisation).

The full methodology and results are described in the thesis itself; this
document explains how to set up, configure, and run each script.

## Repository contents

```
.
├── download_copernicus_bottom_variable.py   # Python — data download (CMEMS)
├── analysis_environmental.R                 # R — statistical & spatial analysis
├── README.md                                # this file
└── LICENSE
```

## 1. `download_copernicus_bottom_variable.py`

### What it does

Downloads a user-specified variable from a Copernicus Marine (CMEMS)
reanalysis or forecast product for a given spatial bounding box and time
period, then extracts its value at the seabed (bottom layer) using the
product's bathymetry / land-sea mask. The result is saved as a single
NetCDF file.

This script is generic: it can be re-run for any CMEMS physical or
biogeochemical variable (temperature, salinity, currents, pH, nitrates,
oxygen, etc.) simply by editing the configuration block — no code changes
are required.

### Requirements

- Python ≥ 3.9
- Packages: `copernicusmarine`, `xarray`, `numpy`, `rioxarray`
- A free Copernicus Marine account, registered at
  <https://data.marine.copernicus.eu>

Install dependencies:

```bash
pip install copernicusmarine xarray numpy rioxarray
```

Before the first run, authenticate once (credentials are then cached
locally):

```bash
copernicusmarine login
```

### Configuration

All user-editable parameters are grouped in the `CONFIG` dictionary at the
top of the script:

| Parameter | Description |
|---|---|
| `output_dir` | Folder where downloaded files and results are saved |
| `dataset_id` | CMEMS product ID for the variable of interest |
| `bathymetry_dataset_id` | CMEMS static product ID providing the bathymetry/mask for the same domain |
| `variables` | Variable name(s) as defined in the dataset (e.g. `so` for salinity, `thetao` for temperature) |
| `start_date`, `end_date` | Time period to download (`YYYY-MM-DD`) |
| `lat_min`, `lat_max`, `lon_min`, `lon_max` | Bounding box (decimal degrees) |

Dataset IDs can be found by browsing the product catalogue at
<https://data.marine.copernicus.eu>.

### Usage

```bash
python download_copernicus_bottom_variable.py
```

### Output

A single NetCDF file named `bottom_<variable>_<start_date>_<end_date>.nc`,
saved in `output_dir`, containing the bottom-layer value of the requested
variable over the specified domain and period.

To reproduce all variables used in the thesis analysis (Section 2), run
this script once per variable, changing `dataset_id` and `variables` in
`CONFIG` accordingly (see the variable list in Section 2 below).

---

## 2. `analysis_environmental.R`

### What it does

Performs the full multi-year, seasonal environmental analysis used in the
thesis, restricted to the deep zone (depth > 200 m) of the study area
(Catalan Sea, NW Mediterranean). The script is organised in sequential
blocks:

1. Reading and reprojection of static layers (bathymetry, rugosity,
   substrate, distance to reference point)
2. Reading and seasonal aggregation of yearly NetCDF variables
3. Descriptive statistics, normality tests, and seasonal comparisons
4. Multivariate analysis: PCA, correlation structure, clustering (k-means)
5. Mahalanobis environmental similarity to a reference site
6. Marine Protected Area (MPA) prioritisation (via `prioritizr`), using
   fishery CPUE data as a conservation feature
7. Figure generation (maps, panels, synthesis plot)

### Requirements

R ≥ 4.2, with the following packages installed:

```r
install.packages(c(
  "rlang", "ncdf4", "terra", "tidyterra", "sf", "stars",
  "FactoMineR", "factoextra", "cluster", "dbscan", "mgcv", "vegan",
  "prioritizr", "marmap", "ggplot2", "tidyverse", "viridis", "corrplot",
  "ggrepel", "patchwork", "rnaturalearth", "rnaturalearthdata", "fpc",
  "ggdendro", "MASS", "Kendall", "car", "spdep"
))
```

> `prioritizr` requires a solver backend (e.g. `lpsymphony` or a Gurobi
> licence) — see the [`prioritizr` documentation](https://prioritizr.net)
> for installation details.

### Expected directory structure

The script expects a project folder (`dir_project`, set at the top of the
script) containing all input data, organised as follows:

```
<dir_project>/
├── temperatura_fons_med_<year>/temperatura_fondo_<year>.nc
├── salinitat_fons_med_<year>/salinidad_fondo_<year>.nc
├── corrent_fons_med_<year>/corrientes_fondo_<year>.nc
├── phyc_columna_med_<year>/phyc_integrada_<year>.nc
├── ph_fons_med_bgc_<year>/ph_fondo_<year>.nc
├── oxigen_fons_med_<year>/oxigeno_fondo_<year>.nc
├── npp_med_<year>/npp_integrada_<year>.nc
├── nitrats_fons_med_<year>/nitratos_fondo_<year>.nc
├── mld_med_<year>/mld_<year>.nc
├── fosfats_fons_med_<year>/fosfatos_fondo_<year>.nc
├── EMODnet_Seabed_Substrate_1M/EMODnet_Seabed_substrate_1M.gdb
├── Batimetria/gebco_2025_n42.5_s38.0_w-1.0_e5.0.nc
├── mapes_distancia/grid_distances.csv
└── RESULTATS/              # created automatically; all outputs are saved here
```

The bottom-layer NetCDF files (temperature, salinity, currents, pH,
oxygen, nitrates, phosphates, etc.) are generated using the Python script
described in Section 1, run once per variable and year. The static layers
(bathymetry, substrate, distance grid) must be obtained separately from
GEBCO, EMODnet, and the user's own reference grid, respectively, and
placed in the corresponding sub-folders.

### Configuration

At the top of the script (`BLOCK 0`), adjust as needed:

| Parameter | Description |
|---|---|
| `dir_project` | Path to the project folder described above |
| `years` | Vector of years to include in the analysis |
| `extent_WGS84` | Geographic extent of the study area |
| `crs_work`, `res_m` | Working coordinate reference system and raster resolution |
| `ref_point` | Reference point (UTM) used for the environmental similarity analysis |
| `DEPTH_THRESHOLD_M` | Depth threshold (m) separating the continental shelf from the deep zone analysed |
| `K_CLUSTERS` | Number of k-means clusters per season |

### Usage

```bash
Rscript analysis_environmental.R
```

The script runs end-to-end and prints progress messages to the console
for each block.

### Output

All figures (`.png`) and raster layers (`.tif`) are saved to
`<dir_project>/RESULTATS/`. Key synthesis figures are prefixed with
`FINAL_`.

---

## Data sources

- **Copernicus Marine Service** — physical and biogeochemical reanalysis
  products: <https://data.marine.copernicus.eu>
- **EMODnet** — seabed substrate: <https://emodnet.ec.europa.eu>
- **GEBCO** — bathymetry: <https://www.gebco.net>

Raw input data are **not redistributed in this repository**; they must be
downloaded directly from the sources above (using the provided Python
script for the Copernicus Marine variables), in accordance with each
provider's data licence and terms of use.

## Citation

If you use this code, please cite it as:

> Roca, J.M. (2026). *Environmental data download and analysis scripts
> for Spatial ecological upscaling and prioritisation of marine monitoring and restoration areas in the north-western Mediterranean using open-access environmental data*. Zenodo. https://doi.org/[DOI]

(See `CITATION.cff` for a machine-readable citation file, and the Zenodo
record for the full citation in multiple formats.)

## License

This code is released under the [MIT License](LICENSE) (or specify
another license if preferred).

## Contact

Josep Maria Roca Chapinal - josep.maria.roca@estudiantat.upc.edu
