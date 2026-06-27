# -*- coding: utf-8 -*-
"""
download_copernicus_bottom_variable.py

Download a variable from a Copernicus Marine (CMEMS) reanalysis/forecast
product for a given region and time period, and extract its value at the
seabed (bottom layer) using the dataset's bathymetry/land-sea mask.

Requirements
------------
- copernicusmarine  (pip install copernicusmarine)
- xarray, numpy, rioxarray
- A registered Copernicus Marine account (credentials are requested
  interactively the first time you run `copernicusmarine login`, or can
  be set via environment variables / a config file — see package docs).

Usage
-----
Edit the CONFIG dictionary below and run:
    python download_copernicus_bottom_variable.py

Author: [your name]
"""

import os
import time
import warnings

import xarray as xr
import copernicusmarine

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION — edit these values for your own use case
# ============================================================

CONFIG = {
    # Output directory (relative to this script, or an absolute path)
    "output_dir": os.path.join(os.getcwd(), "output"),

    # Copernicus Marine dataset IDs
    # Browse available products at https://data.marine.copernicus.eu
    "dataset_id": "cmems_mod_med_phy-sal_my_4.2km_P1D-m",
    "bathymetry_dataset_id": "cmems_mod_med_phy_my_4.2km_static",

    # Variable(s) to download (must match the variable name(s) in the
    # dataset, e.g. 'so' for salinity, 'thetao' for temperature)
    "variables": ["so"],

    # Time period (YYYY-MM-DD)
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",

    # Bounding box (decimal degrees)
    "lat_min": 41.63,
    "lat_max": 41.72,
    "lon_min": 3.40,
    "lon_max": 3.50,
}


# ============================================================
# FUNCTIONS
# ============================================================

def setup_output_dir(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    return output_dir


def download_variable_dataset(cfg):
    """Open the requested variable as an xarray Dataset, subset in space
    and time, directly from the Copernicus Marine cloud service."""
    print("\nConnecting to Copernicus Marine and opening dataset...")

    ds = copernicusmarine.open_dataset(
        dataset_id=cfg["dataset_id"],
        variables=cfg["variables"],
        start_datetime=cfg["start_date"],
        end_datetime=cfg["end_date"],
        minimum_latitude=cfg["lat_min"],
        maximum_latitude=cfg["lat_max"],
        minimum_longitude=cfg["lon_min"],
        maximum_longitude=cfg["lon_max"],
    )

    # Standardise coordinate names if needed
    rename_map = {}
    if "lon" in ds.coords:
        rename_map["lon"] = "longitude"
    if "lat" in ds.coords:
        rename_map["lat"] = "latitude"
    if rename_map:
        ds = ds.rename(rename_map)

    print("Dataset loaded.")
    print(f"Dimensions: {dict(ds.sizes)}")
    return ds


def download_bathymetry_mask(cfg):
    """Download the static bathymetry/mask file associated with the
    product and return it as an xarray Dataset."""
    print("\nDownloading bathymetry / land-sea mask...")

    copernicusmarine.get(
        dataset_id=cfg["bathymetry_dataset_id"],
        filter="*bathy*",
        output_directory=cfg["output_dir"],
        overwrite=True,
    )

    nc_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(cfg["output_dir"])
        for f in files
        if "bathy" in f.lower() and f.endswith(".nc")
    ]

    if not nc_files:
        raise FileNotFoundError(
            "No bathymetry/mask file was found after download. "
            "Check that 'bathymetry_dataset_id' is correct for this product."
        )

    return xr.open_dataset(nc_files[0])


def extract_bottom_layer(ds, mask_ds, variables):
    """Regrid the bathymetry mask onto the data grid and extract the
    deepest valid (non-NaN) value along the depth dimension for each
    requested variable."""
    print("\nExtracting bottom-layer values...")
    start = time.time()

    mask_ds = mask_ds.sel(
        latitude=ds.latitude, longitude=ds.longitude, method="nearest"
    )
    mask_ds = mask_ds.interp(latitude=ds.latitude, longitude=ds.longitude)

    merged = ds.merge(mask_ds[["deptho", "mask"]])

    # Forward-fill along depth then take the last level: a robust way to
    # get the deepest non-NaN value (i.e. the seabed) at each grid cell.
    bottom = merged[variables].ffill(dim="depth").isel(depth=-1)

    elapsed_min = int((time.time() - start) // 60)
    print(f"Done in {elapsed_min} min.")
    return bottom


def build_output_filename(cfg):
    var_str = "-".join(cfg["variables"])
    period_str = f"{cfg['start_date']}_{cfg['end_date']}"
    return f"bottom_{var_str}_{period_str}.nc"


# ============================================================
# MAIN
# ============================================================

def main(cfg=CONFIG):
    setup_output_dir(cfg["output_dir"])

    ds = download_variable_dataset(cfg)
    mask_ds = download_bathymetry_mask(cfg)
    bottom_var = extract_bottom_layer(ds, mask_ds, cfg["variables"])

    output_path = os.path.join(cfg["output_dir"], build_output_filename(cfg))
    bottom_var.to_netcdf(output_path)

    print(f"\nNetCDF saved to: {output_path}")
    print("Process completed successfully.")


if __name__ == "__main__":
    main()
