import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import datetime
import time
import scipy.spatial
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import voronoi_diagram
from scipy.interpolate import griddata

burn_unt_id = 'G-25W'
crs = "EPSG:32616"
output_dir = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/Eglin_Mar23/RadiometerMaps/G25W")

burn_unit_geojson = Path(r"/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/Eglin_Mar23/RadiometerMaps/G25W/G25_split.geojson")
bu_gdf = gpd.read_file(burn_unit_geojson)
bu_gdf = bu_gdf[bu_gdf["Id"] == burn_unt_id]

frp_dataframe = Path(r"/home/jepaki/PycharmProjects/KremBoxer/dataframes/eglin_processed_dataframe.geojson")
frp_gdf = gpd.read_file(frp_dataframe)
frp_gdf = frp_gdf[frp_gdf["burn_unit"] == burn_unt_id]
frp_gdf = frp_gdf[frp_gdf["max_FRP"] > 100]
frp_gdf.reset_index(inplace=True)


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
dts_unix = np.array(dts_unix)
dts_unix -= np.min(dts_unix)

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

print(xys, dts_unix)
bu_bbox = bu_gdf.bounds.iloc[0]

grid_x, grid_y = np.meshgrid(np.linspace(bu_bbox['minx'], bu_bbox['maxx'], 100),
                             np.linspace(bu_bbox['miny'], bu_bbox['maxy'], 100), indexing='xy')
points = xys
values = np.array(dts_unix)

grid_dt = griddata(points, values, (grid_x, grid_y), method='nearest')
grid_cubic_dt = griddata(points, values, (grid_x, grid_y), method='cubic')


fig, axs = plt.subplots(1, 2, figsize=(10, 8))
im = axs[0].imshow(grid_dt, extent=(bu_bbox['minx'], bu_bbox['maxx'],
                                  bu_bbox['miny'], bu_bbox['maxy']),
                 vmin=np.min(dts_unix), vmax=np.max(dts_unix), origin='lower')

#plt.colorbar(im, ax=axs[0])
axs[0].plot(points[:, 0], points[:, 1], 'k.', color='red')
vor_gdf.boundary.plot(ax=axs[0])

im = axs[1].imshow(grid_cubic_dt, extent=(bu_bbox['minx'], bu_bbox['maxx'],
                                  bu_bbox['miny'], bu_bbox['maxy']),
                 vmin=np.min(dts_unix), vmax=np.max(dts_unix), origin='lower')

plt.colorbar(im, ax=axs[1])
axs[1].plot(points[:, 0], points[:, 1], 'k.', color='red')
vor_gdf.boundary.plot(ax=axs[1])

plt.tight_layout()
plt.savefig(output_dir.joinpath("arrival_time_interp.png"))
plt.show()



