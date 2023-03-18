import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import datetime
import time
import scipy.spatial
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import voronoi_diagram

burn_unt_id = 'G-25W'
crs = "EPSG:32616"

burn_unit_geojson = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/Eglin_Mar23/RadiometerMaps/G25W/G25_split.geojson")
bu_gdf = gpd.read_file(burn_unit_geojson)
bu_gdf = bu_gdf[bu_gdf["Id"] == burn_unt_id]

frp_dataframe = Path(r"/home/jepaki/PycharmProjects/KremBoxer/dataframes/eglin_processed_dataframe.geojson")
frp_gdf = gpd.read_file(frp_dataframe)
frp_gdf = frp_gdf[frp_gdf["burn_unit"] == burn_unt_id]

bu_gdf.to_crs(crs, inplace=True)
frp_gdf.to_crs(crs, inplace=True)

fig, axs = plt.subplots(1, 1, figsize=(6, 8))
bu_gdf.boundary.plot(ax=axs)
frp_gdf.plot(ax=axs)
plt.show()

print(frp_gdf)
print(frp_gdf.keys())

xs = frp_gdf.geometry.x.to_numpy()
ys = frp_gdf.geometry.y.to_numpy()
xys = np.zeros(shape=(len(xs), 2), dtype=float)
for i, (x, y) in enumerate(zip(xs, ys)):
    xys[i, 0] = x
    xys[i, 1] = y

dts = frp_gdf["max_FRP_datetime"]
dts_unix = []
for dt in dts:
    dt_ = datetime.datetime.fromisoformat(dt)
    print(dt_)
    dt_unix = time.mktime(dt_.timetuple())
    print(dt_unix)
    dts_unix.append(dt_unix)

print(xys)

points = MultiPoint(frp_gdf.geometry)
env_poly = Polygon(bu_gdf.iloc[0].geometry[0])
print("env_poly=", env_poly)
print(env_poly.boundary)

env_poly = Polygon([(xy[0], xy[1]) for xy in env_poly.exterior.coords])

v_results = voronoi_diagram(points, envelope=env_poly)
v_results = voronoi_diagram(points)
v_gsr = gpd.GeoSeries(v_results)
print(v_results)

d = {'rad': frp_gdf.rad, 'dt': dts_unix, 'geometry': v_results}
vor_gdf = gpd.GeoDataFrame(d, crs=crs)
vor_gdf = gpd.clip(vor_gdf, bu_gdf)
print(vor_gdf.head())

fig, axs = plt.subplots(1, 1, figsize=(6, 8))

vor_gdf.boundary.plot(ax=axs)
frp_gdf.plot(ax=axs, color="Red")
plt.show()


