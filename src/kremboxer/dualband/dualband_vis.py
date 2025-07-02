from pathlib import Path
import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from celluloid import Camera
import kremboxer.utils.greybody_utils as gbu
import kremboxer.utils.common_utils as cu


def plot_dualband_burn_unit_maps(db_gdf: gpd.GeoDataFrame, bu_gdf: gpd.GeoDataFrame, vis_dir: Path, burn_name: str):
    db_burn_units = db_gdf.burn_unit.unique()

    for bu in db_burn_units:
        db_in_bu_gdf = db_gdf[db_gdf.burn_unit == bu]
        single_bu_gdf = bu_gdf[bu_gdf.Id == bu]

        fig, ax = plt.subplots(1, 1, figsize=(8,8))
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="5%", pad=0.3)

        single_bu_gdf.boundary.plot(ax=ax)
        db_in_bu_gdf.plot(ax=ax, alpha=1, markersize=20,
                          column="max_FRP", legend=True,
                          cax=cax,
                          legend_kwds={"label": "Max FRP (W/m2)", "orientation": "horizontal"})
        db_in_bu_gdf.apply(lambda x: ax.annotate(text=x['UNIT'], size=10, xy=x.geometry.centroid.coords[0],
                                                 ha='center', xytext=(0, 8), textcoords='offset points',),
                            axis=1)

        ax.set_title(f'{burn_name}, Unit {bu}, Dualband Radiometers')
        plt.tight_layout()

        plot_filename = f'BurnUnitMap_{bu}_dualband.png'
        plt.savefig(vis_dir / plot_filename)


def plot_dualband_frp(db_gdf: gpd.GeoDataFrame, archive_dir: Path, vis_dir:Path, burn_name: str):
    db_burn_units = db_gdf.burn_unit.unique()
    for bu in db_burn_units:
        db_in_bu_gdf = db_gdf[db_gdf.burn_unit == bu]
        plot_dir = vis_dir / f'{bu}'
        plot_dir.mkdir(parents=True, exist_ok=True)

        for i, row in db_in_bu_gdf.iterrows():
            # Load each dataset into a pandas dataframe
            proc_data_filepath = archive_dir / row["PROCESSING_LEVEL"] / row["SENSOR"] / row["DATAFILE"]
            rad_id = row["UNIT"]
            rad_df = pd.read_csv(proc_data_filepath)
            rad_df['DATETIME'] = pd.to_datetime(rad_df['DATETIME'])

            # Figure out where the max FRP occurs and only plot data in a time window around it (reduces time to render plot)
            max_frp_datetime = row['max_FRP_datetime']
            min_datetime = rad_df['DATETIME'].iloc[row['pstart_ind']] - datetime.timedelta(minutes=10)
            max_datetime = rad_df['DATETIME'].iloc[row['pend_ind']] + datetime.timedelta(minutes=10)
            rad_df = rad_df[(rad_df['DATETIME'] > min_datetime) & (rad_df['DATETIME'] < max_datetime)]

            fig, axs = plt.subplots(1, figsize=(8,8))
            axs.plot(rad_df["DATETIME"], rad_df["LW_FRP"])
            axs.axvline(x=max_frp_datetime, color='grey', linewidth=1, alpha=0.2)
            axs.set_xlabel('Datetime')
            axs.set_ylabel('FRP (W/m2)')
            axs.set_title(f'{burn_name}, Unit {bu}, Dualband {rad_id}, FRP')
            plt.savefig(plot_dir / f'{Path(row["DATAFILE"]).stem}.png')
            plt.close()

def vis_dualband_datasets(dualband_processed_metadata: Path, data_vis_params: dict):
    archive_dir =Path(data_vis_params['archive_dir'])
    vis_dir = archive_dir.joinpath('Visualisation').joinpath('dualband')
    vis_dir.mkdir(parents=True, exist_ok=True)

    db_gdf = gpd.read_file(dualband_processed_metadata)
    db_gdf.to_crs(data_vis_params['projection'], inplace=True)
    bu_gdf = gpd.read_file(data_vis_params['burn_units'])
    bu_gdf.to_crs(data_vis_params['projection'], inplace=True)

    plot_dualband_burn_unit_maps(db_gdf, bu_gdf, vis_dir, vis_params['burn_name'])
    plot_dualband_frp(db_gdf, archive_dir, vis_dir,  vis_params['burn_name'])


if __name__ == "__main__":
    dualband_processed_metadata = Path("/home/jepaki/Projects/Objects/FortStewart2025/FireBehaviorDatasets/Dualband_processed_metadata.geojson")
    vis_params = {
        "burn_units": "/home/jepaki/code/KremBoxer/burn_units/fort_stewart_2025_burn_units.geojson",
        "burn_name": "FortStewart2025",
        "projection": "EPSG:32617",
        "archive_dir": "/home/jepaki/Projects/Objects/FortStewart2025/FireBehaviorDatasets"
    }
    vis_dualband_datasets(dualband_processed_metadata, vis_params)
