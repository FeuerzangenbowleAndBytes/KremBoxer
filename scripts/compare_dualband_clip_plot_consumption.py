import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

#plt.rcParams['text.usetex'] = True
pd.set_option('display.max_columns', None)

fire_name = "Eglin2023"
rad_file = Path("/home/jepaki/Projects/Objects/Eglin_2023/FireBehaviorDatasets/Dualband_processed_metadata.geojson")
biomass_file = Path("/ws3/gis_lab/project/SERDP_Objects-IRProcessing/FuelsData/Eglin_2023/EAB2023BiomassData_kg_1m2_energy.csv")
output_dir = Path("/ws3/gis_lab/project/SERDP_Objects-IRProcessing/FuelsData/Eglin_2023")

rad_df = gpd.read_file(rad_file)
biomass_df = pd.read_csv(biomass_file)

print(rad_df.columns)
print(rad_df["Plot"])
print(biomass_df.columns)
print(biomass_df["ClipPlot"])

num_no_match = 0
for i, rad_data in rad_df.iterrows():
    matching_plots = biomass_df[biomass_df["ClipPlot"] == rad_data["Plot"]]
    if not len(matching_plots) == 1:
        print(f'Not matching plot found for radiometer {rad_data["Plot"]}')
        num_no_match += 1
    #print(rad_data["UNIT"], rad_data["Plot"], biomass_df[biomass_df["ClipPlot"]==rad_data["Plot"]].iloc[0]["ClipPlot"])
print(f"No fuel plot matches for {num_no_match} out of {len(rad_df)} radiometer plots.")

rad_df["ClipPlot"] = rad_df["Plot"].astype(str)
biomass_df["ClipPlot"] = biomass_df["ClipPlot"].astype(str)
print(rad_df["ClipPlot"].dtype, biomass_df["ClipPlot"].dtype)
#rad_cons_gdf = rad_df.join(biomass_df, on="ClipPlot", how="inner")
rad_cons_gdf = rad_df.merge(biomass_df, on="ClipPlot", how="inner")
rad_cons_gdf["Consumption_Radiometer"] = rad_df["MW_FRE"] / 1000000 / 0.3 / 20
print(rad_cons_gdf.head())
print(len(rad_cons_gdf))

fig, axs = plt.subplots(1, 1, figsize = (8, 8))
axs.plot([0, 1], [0, 1], ls='--', lw=1, color='grey')
axs.scatter(rad_cons_gdf["Consumption_Litter"], rad_cons_gdf["Consumption_Radiometer"], label="Litter")
axs.scatter(rad_cons_gdf["Consumption_LitterPlus1hr"], rad_cons_gdf["Consumption_Radiometer"], label="Litter + 1hr")
axs.scatter(rad_cons_gdf["Consumption_AllFuels"], rad_cons_gdf["Consumption_Radiometer"], label="Litter + All Hours")

for i, rad_row in rad_cons_gdf.iterrows():
    axs.plot([rad_cons_gdf["Consumption_Litter"], rad_cons_gdf["Consumption_LitterPlus1hr"], rad_cons_gdf["Consumption_AllFuels"]],
             [rad_cons_gdf["Consumption_Radiometer"], rad_cons_gdf["Consumption_Radiometer"], rad_cons_gdf["Consumption_Radiometer"]], ls='-', lw=0.5, color='grey')

axs.set_xlabel(r'Clip Plot Consumption, $\frac{kg}{m^2}$ (Varying Fuels Subsets)')
axs.set_ylabel(r'Radiometer Consumption, $\frac{kg}{m^2}$ (Dualband, $F_r=0.3$, $H_c=20\frac{MJ}{kg}$)')
axs.set_title(f"{fire_name}, Biomass Consumption, Radiometer vs Clip Plot")
axs.legend()
plt.savefig(output_dir / f"{fire_name}_biomass_consumption_all_fuel_subsets.png")

# Zoomed In
fig, axs = plt.subplots(1, 1, figsize = (8, 8))
axs.plot([0, 1], [0, 1], ls='--', lw=1, color='grey')
axs.scatter(rad_cons_gdf["Consumption_Litter"], rad_cons_gdf["Consumption_Radiometer"], label="Litter")
axs.scatter(rad_cons_gdf["Consumption_LitterPlus1hr"], rad_cons_gdf["Consumption_Radiometer"], label="Litter + 1hr")
axs.scatter(rad_cons_gdf["Consumption_AllFuels"], rad_cons_gdf["Consumption_Radiometer"], label="Litter + All Hours")

for i, rad_row in rad_cons_gdf.iterrows():
    axs.plot([rad_cons_gdf["Consumption_Litter"], rad_cons_gdf["Consumption_LitterPlus1hr"], rad_cons_gdf["Consumption_AllFuels"]],
             [rad_cons_gdf["Consumption_Radiometer"], rad_cons_gdf["Consumption_Radiometer"], rad_cons_gdf["Consumption_Radiometer"]], ls='-', lw=0.5, color='grey')
axs.set_xlim([-0.2,1])
axs.set_ylim([0,1])

axs.set_xlabel(r'Clip Plot Consumption, $\frac{kg}{m^2}$ (Varying Fuels Subsets)')
axs.set_ylabel(r'Radiometer Consumption, $\frac{kg}{m^2}$ (Dualband, $F_r=0.3$, $H_c=20\frac{MJ}{kg}$)')
axs.set_title(f"{fire_name}, Biomass Consumption, Radiometer vs Clip Plot")
axs.legend()
plt.savefig(output_dir / f"{fire_name}_biomass_consumption_all_fuel_subsets_zoom.png")

# Compare ecotypes for just litter consumption
fig, axs = plt.subplots(1, 1, figsize = (8, 8))
axs.plot([0, 1], [0, 1], ls='--', lw=1, color='grey')
ecotypes = rad_cons_gdf["Ecotype"].unique()
for ecotype in ecotypes:
    rad_cons_ecotype_gdf = rad_cons_gdf[rad_cons_gdf["Ecotype"] == ecotype]
    axs.scatter(rad_cons_ecotype_gdf["Consumption_Litter"], rad_cons_ecotype_gdf["Consumption_Radiometer"], label=ecotype)

axs.set_xlim([-0.2,1])
axs.set_ylim([0,1])

axs.set_xlabel(r'Clip Plot Consumption, $\frac{kg}{m^2}$ (Litter / No Hours)')
axs.set_ylabel(r'Radiometer Consumption, $\frac{kg}{m^2}$ (Dualband, $F_r=0.3$, $H_c=20\frac{MJ}{kg}$)')
axs.set_title(f"{fire_name}, Biomass Consumption, Radiometer vs Clip Plot")
axs.legend()
plt.savefig(output_dir / f"{fire_name}_biomass_consumption_litter_ecotypes.png")

# Plot of clip plot consumption across fuels subsets
fuel_categories = ["Litter", "LitterPlus1hr", "AllFuels"]
rad_cons_gdf.sort_values("ClipPlot", inplace=True)

fig, axs = plt.subplots(1, 1, figsize = (12, 8))
for fuel_cat in fuel_categories:
    axs.scatter(rad_cons_gdf["ClipPlot"], rad_cons_gdf[f'Consumption_{fuel_cat}'], label=fuel_cat)
for i, rad_row in rad_cons_gdf.iterrows():
    axs.plot([rad_row["ClipPlot"]]*3, [rad_row["Consumption_Litter"], rad_row["Consumption_LitterPlus1hr"], rad_row["Consumption_AllFuels"]], ls='-', lw=0.5, color='grey')
axs.set_ylabel(r'Clip Plot Consumption, $\frac{kg}{m^2}$ (Varying Fuels Subsets)')
axs.set_xlabel(r'Clip Plot')
axs.set_title(f"{fire_name}, Clip Plot Biomass Consumption vs Clip Plot")
axs.tick_params(axis='x', rotation=60)
axs.set_ylim([-0.1, 1])
axs.legend()
plt.savefig(output_dir / f"{fire_name}_biomass_consumption_vs_plot_and_subset.png")

fig, axs = plt.subplots(1, 1, figsize = (12, 8))
axs.scatter(rad_cons_gdf["ClipPlot"], rad_cons_gdf[f'Consumption_Litter'], label="Litter")
axs.set_ylabel(r'Clip Plot Consumption, $\frac{kg}{m^2}$ (Litter)')
axs.set_xlabel(r'Clip Plot')
axs.set_title(f"{fire_name}, Clip Plot Biomass Consumption vs Clip Plot")
axs.tick_params(axis='x', rotation=60)
axs.set_ylim([-0.1, 1])
axs.legend()
plt.savefig(output_dir / f"{fire_name}_biomass_consumption_vs_plot_litter.png")

print("Consumption Stats, Mean, Std")
for fuel_cat in fuel_categories:
    print(f"{fuel_cat}", rad_cons_gdf[f'Consumption_{fuel_cat}'].mean(), rad_cons_gdf[f'Consumption_{fuel_cat}'].std())

frfs = np.arange(0.2, 1, 0.05)
cons_stder = np.zeros_like(frfs)

for i in range(len(frfs)):
    frf = frfs[i]
    rad_cons = np.array(rad_cons_gdf["MW_FRE"] / 1000000 / frf / 20)
    litter_cons = np.array(rad_cons_gdf["Consumption_Litter"])
    cons_stder[i] = np.sum((rad_cons - litter_cons)**2) / len(rad_cons)

best_frf = frfs[np.argmin(cons_stder)]
print("Best fitting FRF is ", best_frf)

fig, axs = plt.subplots(1,1)
axs.plot(frfs, cons_stder)
axs.axvline(best_frf, ls='--', color='grey')
axs.set_xlabel("Fire Radiative Fraction")
axs.set_ylabel(r"Sum Squared Difference of Biomass Consumption")
axs.set_title("Difference btw Radiometer and Clip Plot Consumption vs FRF")
plt.savefig(output_dir / f"{fire_name}_rad_cons_error_vs_frf.png")







