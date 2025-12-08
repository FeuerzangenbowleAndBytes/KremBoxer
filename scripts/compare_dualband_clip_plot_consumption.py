import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

pd.set_option('display.max_columns', None)

rad_file = Path("/home/jepaki/Projects/Objects/Eglin_2023/FireBehaviorDatasets/Dualband_processed_metadata.geojson")
biomass_file = Path("/ws3/gis_lab/project/SERDP_Objects-IRProcessing/FuelsData/Eglin_2023/EAB2023BiomassData_kg_1m2_energy.csv")

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

fig, axs = plt.subplots(1, 1)
axs.scatter(rad_cons_gdf["Consumption_Litter"], rad_cons_gdf["Consumption_Radiometer"])
axs.set_aspect('equal', 'box')
plt.show()