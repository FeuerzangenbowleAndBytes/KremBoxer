import pandas as pd
import geopandas as gpd
from pathlib import Path

input_csv = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/FortStewart_Mar22/firecam_locations.csv")
output_geojson = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/FortStewart_Mar22/firecam_locations.geojson")

df = pd.read_csv(input_csv)
print(df)
gdf = gpd.GeoDataFrame(
    df, geometry=gpd.points_from_xy(df.lon, df.lat)
)
gdf.set_crs('EPSG:4326', inplace=True)
print(gdf)
print(gdf.crs)
gdf.to_file(output_geojson)
