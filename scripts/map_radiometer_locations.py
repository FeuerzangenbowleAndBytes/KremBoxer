import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gdp
from pathlib import Path

output_folder = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/Eglin_Mar23/RadiometerMaps/G25W")
burn_unt_id = 'G-25W'
crs = 'EPSG:32616'

plot_rad_record = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/Eglin_Mar23/RadiometerMaps/radiometer_locations_G25W.csv")
rad_df = pd.read_csv(plot_rad_record)
print(rad_df.head())

fuel_plots_shp = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/Eglin_Mar23/GIS Shapefiles/Fuel_Plot_Locations/G25_Eglin_Fuels_PlotCenter.shp")
plot_gdf = gdp.read_file(fuel_plots_shp)
plot_gdf.set_index("Macroplot_", inplace=True)
plot_gdf.to_crs(crs, inplace=True)
print(plot_gdf.head())
print(plot_gdf.crs)

burn_units_shp = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/Eglin_Mar23/RadiometerMaps/G25W/G25.geojson")
burn_unit_gdf = gdp.read_file(burn_units_shp)
burn_unit_gdf.to_crs(crs, inplace=True)
print(burn_unit_gdf.head())

geometry = []
for i, row in rad_df.iterrows():
    fuel_plot = row['Plot #']
    geometry.append(plot_gdf.loc[fuel_plot]['geometry'])

rad_gdf = gdp.GeoDataFrame(rad_df, geometry=geometry)
rad_gdf.set_crs(crs, inplace=True)
print(rad_gdf)
rad_gdf.to_file(output_folder.joinpath("radiometer_map.geojson"), driver='GeoJSON')

dualband_gdf = rad_gdf[rad_gdf["Dualband"].notna()]
fiveband_gdf = rad_gdf[rad_gdf["Fiveband"].notna()]
firecam_gdf = rad_gdf[rad_gdf["Firecam"].notna()]
dualband_gdf.to_file(output_folder.joinpath("dualband_map.geojson"), driver='GeoJSON')
fiveband_gdf.to_file(output_folder.joinpath("fiveband_map.geojson"), driver='GeoJSON')
firecam_gdf.to_file(output_folder.joinpath("firecam_map.geojson"), driver='GeoJSON')

fig, axs = plt.subplots(1, 1, figsize=(10, 10))
burn_unit = burn_unit_gdf[burn_unit_gdf['Id'] == burn_unt_id]
burn_unit.boundary.plot(ax=axs)

plots_in_burn_unit = gdp.sjoin(plot_gdf, burn_unit, how='inner', predicate='within')
plots_in_burn_unit.plot(ax=axs, color='Gray', markersize=5)

for x, y, label in zip(plots_in_burn_unit.geometry.x, plots_in_burn_unit.geometry.y, plots_in_burn_unit.index):
    axs.annotate(label, xy=(x, y), xytext=(2, 2), textcoords="offset points", size=6)

firecam_gdf.plot(ax=axs, color='Red', markersize=50, marker='o')
fiveband_gdf.plot(ax=axs, color='aqua', markersize=30, marker='*')
dualband_gdf.plot(ax=axs, color='Green', markersize=30, marker='o')

plt.tight_layout()
plt.savefig(output_folder.joinpath("radiometer_map.png"))
plt.show()
