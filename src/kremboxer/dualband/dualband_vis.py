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
from shapely.geometry import Point
from tqdm import tqdm
import kremboxer.utils.greybody_utils as gbu
import kremboxer.utils.common_utils as cu


def animate_burn_units(db_gdf: gpd.GeoDataFrame, bu_gdf: gpd.GeoDataFrame, archive_dir: Path, vis_dir: Path, burn_name: str):
    db_burn_units = db_gdf.burn_unit.unique()

    for bu in db_burn_units:
        db_in_bu_gdf = db_gdf[db_gdf.burn_unit == bu]
        single_bu_gdf = bu_gdf[bu_gdf.Id == bu]
        plot_dir = vis_dir / f'{bu}'
        plot_dir.mkdir(parents=True, exist_ok=True)

        # Make a color map for the radiometer numbers
        rad_nums = db_in_bu_gdf["UNIT"].unique()
        cmap = cm.get_cmap('tab20', len(rad_nums))
        rad_colors = dict(zip(rad_nums, cmap.colors))

        # Collect data from dualband datasets to create animation
        rad_data = {}
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
            rad_df = rad_df.set_index("DATETIME", drop=False)

            rad_data[rad_id] = {
                "df": rad_df,
                "max_FRP": row["max_FRP"],
                "max_FRP_datetime": max_frp_datetime,
                "min_datetime": min_datetime,
                "max_datetime": max_datetime,
                "location": row["geometry"]
            }

        start_time = min([rad_data[key]["min_datetime"] for key in rad_data.keys() if rad_data[key]["max_FRP"] > 10])
        end_time = max([rad_data[key]["max_datetime"] for key in rad_data.keys() if rad_data[key]["max_FRP"] > 10])

        print("Creating animation for burn unit ", bu)
        fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(7, 9))
        camera = Camera(fig)

        # Create range of datetimes for the animation frames
        dt = start_time
        dts = []
        while dt < end_time:
            dts.append(dt)
            dt += datetime.timedelta(minutes=1)

        for dt in tqdm(dts):
            single_bu_gdf.boundary.plot(ax=axs[0])
            for key in rad_data.keys():
                rad_df = rad_data[key]["df"]
                if rad_df["LW_FRP"].max() > 10:
                    axs[1].plot(rad_df["DATETIME"], rad_df["LW_FRP"], color=rad_colors[key], label=key)
                    axs[1].axvline(x=rad_data[key]['max_FRP_datetime'], color='grey', linewidth=1, alpha=0.2)

                x, y = rad_data[key]['location'].x, rad_data[key]['location'].y
                axs[0].scatter([x], [y], color=rad_colors[key], label=key)

                try:
                    frp = rad_df.loc[dt]["LW_FRP"]
                    radius = 0
                    if frp > 0:
                        radius = max(0, 20 * np.log(frp))
                    axs[0].add_patch(
                        plt.Circle((x, y), radius=radius, alpha=0.5,
                                   color=rad_colors[key]))
                except KeyError:
                    continue
            axs[1].axvline(x=dt, color='black', linewidth=1, alpha=0.8)
            axs[1].set_ylim([0, None])
            axs[1].set_xlim([start_time, end_time])
            axs[1].xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            axs[1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
            axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            axs[1].set_ylabel('FRP (W/m2)')
            axs[1].set_xlabel('Datetime')
            axs[0].set_title(f'{burn_name}, Unit {bu}, Dualband FRP')
            camera.snap()

            dt += datetime.timedelta(minutes=1)

        # Create animation from saved snapshots and write to file
        animation = camera.animate()
        gif_output_filename = str(bu) + "_animation.gif"
        mp4_output_filename = str(bu) + "_animation.mp4"
        animation.save(plot_dir.joinpath(gif_output_filename), writer='imagemagick')
        animation.save(plot_dir.joinpath(mp4_output_filename), writer='imagemagick')
        print("Animations saved to ", plot_dir.joinpath(gif_output_filename))


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

        fig_combine, axs_combine = plt.subplots(1, figsize=(8,8))

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
            if rad_df["LW_FRP"].max() > 1000:
                axs_combine.plot(rad_df["DATETIME"], rad_df["LW_FRP"], label=rad_id)
                axs_combine.axvline(x=max_frp_datetime, color='grey', linewidth=1, alpha=0.2)
            axs.set_xlabel('Datetime')
            axs.set_ylabel('FRP (W/m2)')
            axs.set_title(f'{burn_name}, Unit {bu}, Dualband {rad_id}, FRP')
            fig.savefig(plot_dir / f'{Path(row["DATAFILE"]).stem}.png')
            plt.close(fig)

        axs_combine.set_ylabel('FRP (W/m2)')
        axs_combine.set_xlabel('Datetime')
        axs_combine.set_title(f'{burn_name}, Unit {bu}, Dualband FRP')
        axs_combine.legend()
        fig_combine.savefig(plot_dir / f'Dualband_{bu}.png')
        plt.close(fig_combine)

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
    animate_burn_units(db_gdf, bu_gdf, archive_dir,  vis_dir, vis_params['burn_name'])


if __name__ == "__main__":
    dualband_processed_metadata = Path("/home/jepaki/Projects/Objects/FortStewart2025/FireBehaviorDatasets/Dualband_processed_metadata.geojson")
    vis_params = {
        "burn_units": "/home/jepaki/code/KremBoxer/burn_units/fort_stewart_2025_burn_units.geojson",
        "burn_name": "FortStewart2025",
        "projection": "EPSG:32617",
        "archive_dir": "/home/jepaki/Projects/Objects/FortStewart2025/FireBehaviorDatasets"
    }
    vis_dualband_datasets(dualband_processed_metadata, vis_params)
