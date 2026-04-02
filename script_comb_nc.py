import xarray as xr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# --- FILE CONFIGURATION ---
temp_nc = 'temperature_0_daily-mean.nc'
geo_nc = 'geopotential_stream-oper_daily-mean.nc'

seasons_map = {
    '2025-01-15': 'weather_ny_jan15.xlsx',
    '2025-05-15': 'weather_ny_may15.xlsx',
    '2025-08-15': 'weather_ny_aug15.xlsx',
    '2025-10-15': 'weather_ny_nov15.xlsx'
}

def generate_comparison_plots():
    ds_t = xr.open_dataset(temp_nc, engine='netcdf4')
    ds_z = xr.open_dataset(geo_nc, engine='netcdf4')

    for date, excel_file in seasons_map.items():
        # ✅ Each iteration creates its own independent figure
        fig, ax = plt.subplots(figsize=(10, 12))

        print(f"Processing {date} using {excel_file}...")

        # --- Extract Satellite Data ---
        try:
            t_slice = ds_t['t'].sel(valid_time=date, method='nearest').isel(latitude=2, longitude=2)
            z_slice = ds_z['z'].sel(valid_time=date, method='nearest').isel(latitude=2, longitude=2)
        except Exception as e:
            ax.set_title(f"Error extracting {date}: {e}")
            plt.savefig(f"Comparison_{date}.png", dpi=300)
            plt.close(fig)
            continue

        sat_df = pd.DataFrame({
            'PRES': t_slice.pressure_level.values,
            'TEMP': t_slice.values - 273.15,        # Kelvin → Celsius
            'HGHT': z_slice.values / 9.80665         # Geopotential → Height (m)
        }).sort_values('HGHT')

        # --- Load Excel Balloon Data ---
        if os.path.exists(excel_file):
            ball_df = pd.read_excel(excel_file).dropna(subset=['HGHT (m)', 'TEMP (C)'])
            burst_h = ball_df['HGHT (m)'].max()

            # ── Complementary merge: balloon below burst, satellite above ──
            sat_above = sat_df[sat_df['HGHT'] > burst_h]

            # Plot balloon data (solid red) for its full range
            ax.plot(ball_df['TEMP (C)'], ball_df['HGHT (m)'],
                    'r-', linewidth=2, label='Balloon Observation')

            # Plot satellite data only above balloon burst height (dashed blue)
            ax.plot(sat_df['TEMP'], sat_df['HGHT'],
                    'b--', linewidth=1.5, label='Satellite ERA5 (full range)')

            # Mark the handoff point
            ax.axhline(y=burst_h, color='gray', linestyle=':',
                       alpha=0.7, label=f'Burst / Handoff: {burst_h/1000:.1f} km')
        else:
            print(f"Warning: Excel file {excel_file} not found.")
            # Fall back to satellite-only
            ax.plot(sat_df['TEMP'], sat_df['HGHT'],
                    'b--', linewidth=1.5, label='Satellite ERA5 (full range)')

        # --- Formatting ---
        ax.set_title(f"Vertical Temperature Profile: {date}", fontsize=15, fontweight='bold')
        ax.set_xlabel("Temperature (°C)", fontsize=12)
        ax.set_ylabel("Height (m)", fontsize=12)
        ax.grid(True, linestyle=':', alpha=0.7)
        ax.legend(loc='lower left', fontsize=10)
        ax.set_ylim(0, 50000)

        plt.tight_layout()

        # ✅ Save each figure with a unique filename
        out_name = f"Comparison_{date}.png"
        plt.savefig(out_name, dpi=300)
        print(f"Saved: {out_name}")

        plt.show()
        plt.close(fig)  # ✅ Free memory before next iteration

    ds_t.close()
    ds_z.close()

if __name__ == "__main__":
    generate_comparison_plots()
