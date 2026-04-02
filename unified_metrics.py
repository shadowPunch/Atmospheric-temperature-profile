import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import metpy.calc as mpcalc
from metpy.plots import SkewT
from metpy.units import units
import numpy as np
from scipy.interpolate import interp1d
import warnings
warnings.filterwarnings("ignore")

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
FILES = {
    'Winter':  'weather_ny_jan15.xlsx',
    'Spring':  'weather_ny_may15.xlsx',
    'Summer':  'weather_ny_aug15.xlsx',
    'Autumn':  'weather_ny_nov15.xlsx',
}
STATION = 'New York (72501)'

# Physical constants
R = 8.314       # J/(mol·K)
g = 9.81        # m/s²
M = 0.02897     # kg/mol

# ─── PER-SEASON ANALYSIS ──────────────────────────────────────────────────────
def analyze_season(season, file_path):
    df = pd.read_excel(file_path).dropna(subset=['PRES (hPa)', 'TEMP (C)', 'DWPT (C)', 'HGHT (m)'])

    # Raw arrays
    p_raw  = df['PRES (hPa)'].values
    T_raw  = df['TEMP (C)'].values
    Td_raw = df['DWPT (C)'].values
    z_raw  = df['HGHT (m)'].values
    T_K    = T_raw + 273.15

    # MetPy units
    p_u  = p_raw  * units.hPa
    T_u  = T_raw  * units.degC
    Td_u = Td_raw * units.degC

    # ── Derived metrics ──────────────────────────────────────────────────────
    lcl_p, lcl_t   = mpcalc.lcl(p_u[0], T_u[0], Td_u[0])
    wet_bulb        = mpcalc.wet_bulb_temperature(p_u[0], T_u[0], Td_u[0])
    lfc_p, lfc_t   = mpcalc.lfc(p_u, T_u, Td_u)
    el_p,  el_t    = mpcalc.el(p_u, T_u, Td_u)
    prof            = mpcalc.parcel_profile(p_u, T_u[0], Td_u[0]).to('degC')
    cape, cin       = mpcalc.cape_cin(p_u, T_u, Td_u, prof)

    # ELR (lower 5 km)
    mask = z_raw <= 5000
    if mask.sum() > 2:
        elr = -((T_raw[mask][-1] - T_raw[0]) / ((z_raw[mask][-1] - z_raw[0]) / 1000))
    else:
        elr = 0.0

    stability = ("Absolutely Unstable" if elr > 9.8
                 else "Conditionally Unstable" if elr > 6.5
                 else "Stable")

    inversion = "Yes" if T_raw[1] > T_raw[0] else "No"

    # Tropopause (minimum temperature)
    trop_idx  = np.argmin(T_raw)
    trop_h    = z_raw[trop_idx]
    trop_t    = T_raw[trop_idx]

    # ── Scale-height pressure profiles ──────────────────────────────────────
    z_grid = np.arange(np.floor(z_raw.min() / 100) * 100,
                       np.floor(z_raw.max() / 100) * 100 + 100, 100)
    T_grid = interp1d(z_raw, T_K, kind='linear', fill_value='extrapolate')(z_grid)

    T0     = T_grid[0]
    H_const = (R * T0) / (M * g)
    p_theo  = p_raw[0] * np.exp(-(z_grid - z_grid[0]) / H_const)

    p_var = np.zeros_like(z_grid)
    p_var[0] = p_raw[0]
    for i in range(len(z_grid) - 1):
        H_local   = (R * T_grid[i]) / (M * g)
        p_var[i+1] = p_var[i] * np.exp(-100 / H_local)

    return dict(
        # raw
        p_raw=p_raw, T_raw=T_raw, Td_raw=Td_raw, z_raw=z_raw,
        # metpy units
        p_u=p_u, T_u=T_u, Td_u=Td_u, prof=prof,
        # metrics
        lcl_p=lcl_p, lcl_t=lcl_t, wet_bulb=wet_bulb,
        lfc_p=lfc_p, lfc_t=lfc_t, el_p=el_p, el_t=el_t,
        cape=cape, cin=cin,
        elr=elr, stability=stability, inversion=inversion,
        trop_h=trop_h, trop_t=trop_t,
        # scale height
        z_grid=z_grid, T_grid=T_grid, H_const=H_const,
        p_theo=p_theo, p_var=p_var,
    )

# ─── PLOTTING ─────────────────────────────────────────────────────────────────
def plot_season(season, d):
    """Produces one figure with 3 panels for a single season."""

    # ── Figure layout: 3 columns ─────────────────────────────────────────────
    fig = plt.figure(figsize=(22, 10))
    fig.suptitle(f'{season}  ·  {STATION}', fontsize=17, fontweight='bold', y=1.01)
    gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.35)

    # ── Panel 1: Skew-T Log-P ────────────────────────────────────────────────
    skew = SkewT(fig, rotation=45, subplot=gs[0])
    skew.plot(d['p_u'], d['T_u'],   'r',  linewidth=2,   label='Env Temp')
    skew.plot(d['p_u'], d['Td_u'],  'g',  linewidth=2,   label='Dew Point')
    skew.plot(d['p_u'], d['prof'],  'k--',linewidth=1.5, label='Parcel Path')
    skew.shade_cape(d['p_u'], d['T_u'], d['prof'])
    skew.shade_cin (d['p_u'], d['T_u'], d['prof'])
    if not np.isnan(d['lfc_p'].magnitude):
        skew.ax.plot(d['lfc_t'], d['lfc_p'], '_', color='blue', markersize=20, label='LFC')
    skew.plot_dry_adiabats(alpha=0.4)
    skew.plot_moist_adiabats(alpha=0.4)
    skew.plot_mixing_lines(alpha=0.3)
    skew.ax.set_title('Skew-T Log-P', fontsize=12, pad=8)
    skew.ax.legend(loc='upper right', fontsize=8)

    # ── Panel 2: Temp vs Height  (tropopause + ELR) ──────────────────────────
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(d['T_raw'], d['z_raw'], 'b-', linewidth=2, label='Temp Profile')
    ax2.axhline(d['trop_h'], color='red', linestyle='--', alpha=0.6)
    ax2.text(d['T_raw'].min() + 1, d['trop_h'] + 400,
             f"Tropopause\n{d['trop_h']/1000:.1f} km  {d['trop_t']:.1f}°C",
             color='red', fontsize=8)
    ax2.set_xlabel('Temperature (°C)', fontsize=11)
    ax2.set_ylabel('Height (m)',        fontsize=11)
    ax2.set_title('Temp Profile & Tropopause', fontsize=12)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(fontsize=9)

    # ── Panel 3: Scale-Height Pressure ───────────────────────────────────────
    ax3 = fig.add_subplot(gs[2])
    ax3.plot(d['p_theo'], d['z_grid'], 'r--', linewidth=1.8,
             label=f'Theoretical (isothermal, H={d["H_const"]/1000:.2f} km)')
    ax3.plot(d['p_var'],  d['z_grid'], 'b-',  linewidth=2,
             label='Data-derived (variable H)')
    ax3.scatter(d['p_raw'], d['z_raw'], color='black', s=12, alpha=0.6,
                label='Observations')
    ax3.invert_xaxis()
    ax3.set_xlabel('Pressure (hPa)', fontsize=11)
    ax3.set_ylabel('Height (m)',     fontsize=11)
    ax3.set_title('Pressure: Theoretical vs Observed', fontsize=12)
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(fontsize=8)

    plt.tight_layout()
    out = f"analysis_{season.lower()}.png"
    plt.savefig(out, dpi=200, bbox_inches='tight')
    print(f"  Saved → {out}")
    plt.show()
    plt.close(fig)

# ─── CONSOLE SUMMARY ──────────────────────────────────────────────────────────
def print_summary(season, d):
    sep = "─" * 45
    print(f"\n{sep}")
    print(f"  {season.upper()}  ·  {STATION}")
    print(sep)
    print(f"  Surface Temp          : {d['T_raw'][0]:.1f} °C")
    print(f"  Surface Wet Bulb      : {d['wet_bulb']:.1f}")
    print(f"  LCL Pressure          : {d['lcl_p']:.1f}")
    print(f"  LFC Pressure          : {d['lfc_p'] if not np.isnan(d['lfc_p'].magnitude) else 'None'}")
    print(f"  EL  Pressure          : {d['el_p']  if not np.isnan(d['el_p'].magnitude)  else 'None'}")
    print(f"  CAPE                  : {d['cape']:.2f}")
    print(f"  CIN                   : {d['cin']:.2f}")
    print(f"  ELR (lower 5 km)      : {d['elr']:.2f} °C/km")
    print(f"  Stability             : {d['stability']}")
    print(f"  Surface Inversion     : {d['inversion']}")
    print(f"  Tropopause            : {d['trop_h']/1000:.1f} km  ({d['trop_t']:.1f} °C)")
    print(f"  Isothermal Scale Ht   : {d['H_const']/1000:.2f} km")
    print(sep)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    for season, path in FILES.items():
        print(f"\nProcessing {season} …")
        data = analyze_season(season, path)
        print_summary(season, data)
        plot_season(season, data)
