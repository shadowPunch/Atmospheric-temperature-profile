# Atmospheric Profile Analysis — New York Station

A seasonal atmospheric physics analysis pipeline combining **radiosonde balloon data** with **ERA5 satellite reanalysis** to study vertical temperature structure, thermodynamic instability indices, and pressure-height relationships across all four seasons.

---

## Overview

This project performs a comprehensive multi-source atmospheric study for New York (Station 72501), covering:

- Skew-T Log-P diagrams with parcel theory overlays
- Thermodynamic indices: CAPE, CIN, LCL, LFC, EL, Wet Bulb
- Environmental Lapse Rate (ELR) and atmospheric stability classification
- Scale-height pressure profiles compared against isothermal theory
- Vertical temperature profiles merging balloon and ERA5 satellite data

---

## Project Structure

    ├── analysis.py                    # Per-season Skew-T, ELR, scale-height analysis
    ├── comparison.py                  # ERA5 vs radiosonde vertical profile comparison
    ├── weather_ny_jan15.xlsx          # Winter radiosonde data
    ├── weather_ny_may15.xlsx          # Spring radiosonde data
    ├── weather_ny_aug15.xlsx          # Summer radiosonde data
    ├── weather_ny_nov15.xlsx          # Autumn radiosonde data
    ├── temperature_0_daily-mean.nc    # ERA5 temperature reanalysis (NetCDF)
    ├── geopotential_stream-oper_daily-mean.nc   # ERA5 geopotential (NetCDF)
    └── output/
        ├── analysis_winter.png
        ├── analysis_spring.png
        ├── analysis_summer.png
        ├── analysis_autumn.png
        └── Comparison_YYYY-MM-DD.png  # One per season

---

## Dependencies

    pip install pandas matplotlib metpy numpy scipy xarray openpyxl

| Package      | Purpose                                     |
|--------------|---------------------------------------------|
| pandas       | Excel/tabular data loading                  |
| matplotlib   | Plotting and figure layout                  |
| metpy        | Skew-T diagrams, thermodynamic calculations |
| numpy        | Numerical operations                        |
| scipy        | Pressure/height interpolation               |
| xarray       | NetCDF ERA5 satellite data handling         |
| openpyxl     | Excel file reading backend                  |

---

## Usage

### 1. Seasonal Skew-T and Thermodynamic Analysis

Processes all four seasons from radiosonde Excel files and generates a 3-panel figure per season:

    python analysis.py

**Output per season:**

- Panel 1 — Skew-T Log-P with parcel path, CAPE/CIN shading, LFC marker
- Panel 2 — Temperature vs. Height profile with tropopause detection
- Panel 3 — Pressure profile: isothermal scale-height theory vs. observations

Console summary printed per season:

    ─────────────────────────────────────────────
      WINTER  ·  New York (72501)
    ─────────────────────────────────────────────
      Surface Temp          : -5.4 °C
      Surface Wet Bulb      : ...
      LCL Pressure          : ...
      CAPE                  : ...
      ELR (lower 5 km)      : 6.1 °C/km
      Stability             : Conditionally Unstable
      Tropopause            : 11.2 km  (-57.3 °C)
      Isothermal Scale Ht   : 7.63 km
    ─────────────────────────────────────────────

---

### 2. ERA5 Satellite vs. Radiosonde Comparison

Merges balloon observations (bottom-up) with ERA5 reanalysis (top-down) at the balloon burst altitude handoff point:

    python comparison.py

**Output:** One temperature profile plot per date showing:

- Balloon profile (solid red) up to burst altitude
- ERA5 satellite profile (dashed blue) over full atmospheric column
- Handoff marker at balloon burst height

---

## Physics Background

**Scale Height (H)**

    H = RT / Mg

Where R = 8.314 J/(mol·K), M = 0.02897 kg/mol, g = 9.81 m/s²

**Hypsometric / Barometric equation**

    p(z) = p0 · exp(−z / H)

Two models are compared:
- Isothermal: constant H computed from surface temperature
- Variable: H recalculated layer-by-layer from observed temperatures

**Stability Classification (ELR)**

| ELR (°C/km) | Stability              |
|-------------|------------------------|
| > 9.8       | Absolutely Unstable    |
| 6.5 – 9.8   | Conditionally Unstable |
| < 6.5       | Stable                 |

**Thermodynamic Indices**

| Index | Description                                      |
|-------|--------------------------------------------------|
| LCL   | Lifting Condensation Level — cloud base estimate |
| LFC   | Level of Free Convection — onset of instability  |
| EL    | Equilibrium Level — storm top estimate           |
| CAPE  | Convective Available Potential Energy (J/kg)     |
| CIN   | Convective Inhibition (J/kg)                     |
| ELR   | Environmental Lapse Rate                         |
| Tw    | Wet Bulb Temperature                             |

---

## Data Sources

| Source    | Description                          | Format  |
|-----------|--------------------------------------|---------|
| Radiosonde | University of Wyoming sounding data | .xlsx   |
| ERA5      | ECMWF reanalysis, pressure levels    | .nc     |

---

## Seasons Analyzed

| Season | Date       | File                    |
|--------|------------|-------------------------|
| Winter | 2025-01-15 | weather_ny_jan15.xlsx   |
| Spring | 2025-05-15 | weather_ny_may15.xlsx   |
| Summer | 2025-08-15 | weather_ny_aug15.xlsx   |
| Autumn | 2025-10-15 | weather_ny_nov15.xlsx   |

---

## Station

**New York — WMO Station 72501**
Coordinates: 40.65°N, 73.80°W
