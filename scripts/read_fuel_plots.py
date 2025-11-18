import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
import kremboxer.utils.common_utils

pd.set_option('display.max_columns', None)

fuel_plots_csv = Path("/home/jepaki/code/KremBoxer/fuel_plots/fort_stewart_2025_fuel_plots.csv")
db_meta_geojson = Path("/home/jepaki/Projects/Objects/FortStewart2025/FireBehaviorDatasets/Dualband_processed_metadata_raw_location.geojson")
fp_df = pd.read_csv(fuel_plots_csv)
fp_gdf = gpd.GeoDataFrame(fp_df, geometry=gpd.points_from_xy(fp_df.Longitude, fp_df.Latitude), crs="EPSG:4326")
db_gdf = gpd.read_file(db_meta_geojson)

print("Fuel Plots: ", fp_gdf.head())
print("Dualband Meta: ", db_gdf.head())

plot_associated_df, unassociated_df = kremboxer.utils.common_utils.associate_data2fuelplot(db_gdf, fp_gdf)
print("# radiometers:", len(db_gdf))
print("# unassociated radiometers:", len(unassociated_df))
print("# associated radiometers:", len(plot_associated_df))
print(plot_associated_df)