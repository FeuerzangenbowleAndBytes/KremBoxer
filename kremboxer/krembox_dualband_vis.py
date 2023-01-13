from pathlib import Path
import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
#from shapely.geometry import Point  # Need to comment this out when building sphinx documentation with phinx-immaterial theme, who knows why
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import cm
from celluloid import Camera
import kremboxer.krembox_dualband_utils as kdu


def animate_burn_unit(rad_data_gdf: gpd.GeoDataFrame, burn_plot_gdf: gpd.GeoDataFrame, burn_unit, plot_output_dir: Path, plot_title_prefix=""):
    """
    Animate the time traces of the FRP measurements from each radiometer in the burn unit
    :param rad_data_gdf:
    :param burn_plot_gdf:
    :param burn_unit:
    :param plot_output_dir:
    :param plot_title_prefix:
    :return:
    :group: krembox_dualband_vis
    """

    # Filter to the datasets from the burn unit we care about
    rad_data_gdf = rad_data_gdf[rad_data_gdf["burn_unit"] == burn_unit]
    burn_plot_gdf = burn_plot_gdf[burn_plot_gdf["Id"] == burn_unit]

    if len(rad_data_gdf) == 0:
        print("No datasets from burn unit ", burn_unit, " found.")
        return

    if len(burn_plot_gdf) == 0:
        print("No burn units named ", burn_unit, " found.")
        return

    # Make a color map for the radiometer numbers
    rad_nums = rad_data_gdf["rad"].unique()
    cmap = cm.get_cmap('tab20', len(rad_nums))
    rad_colors = dict(zip(rad_nums, cmap.colors))
    rad_dict = {}
    maximum_frp_in_unit = 0

    # Make a plot of the FRP traces of each radiometer in the burn unit
    print("Animating burn unit", burn_unit, ", ", len(rad_data_gdf), "datasets")
    frp_dfs = {}
    for i, row in rad_data_gdf.iterrows():
        # Load each dataset into a pandas dataframe
        proc_data_filepath = Path(row["data_directory"]).joinpath(row["processed_file"])
        rad_num = row["rad"]
        rad_dict[rad_num] = {"loc": row["geometry"],
                             "max_frp_index": row["max_FRP_index"],
                             "max_frp_datetime": datetime.datetime.fromisoformat(row["max_FRP_datetime"])}
        dataset_name = row["dataset"]
        rad_df = pd.read_csv(proc_data_filepath)
        rad_df['datetime'] = pd.to_datetime(rad_df['datetime'])

        if row["max_FRP"] > maximum_frp_in_unit:
            maximum_frp_in_unit = row["max_FRP"]

        # Figure out where the max FRP occurs and only plot data in a time window around it (reduces time to render plot)
        #max_frp_index = rad_df['LW_FRP'].argmax()
        max_frp_datetime = rad_dict[rad_num]["max_frp_datetime"]
        min_datetime = max_frp_datetime - datetime.timedelta(minutes=10)
        max_datetime = max_frp_datetime + datetime.timedelta(minutes=10)
        rad_df = rad_df[(rad_df['datetime'] > min_datetime) & (rad_df['datetime'] < max_datetime)]
        rad_df = rad_df.set_index("datetime", drop=False)
        frp_dfs[rad_num] = rad_df

    # Figure out the start and end times of the animation
    dt_start = frp_dfs[rad_nums[0]]["datetime"].min()
    dt_end = frp_dfs[rad_nums[0]]["datetime"].max()
    for rn, df in frp_dfs.items():
        if df["datetime"].min() < dt_start:
            dt_start = df["datetime"].min()
        if df["datetime"].max() > dt_end:
            dt_end = df["datetime"].max()

    # Make frames of animation
    fig, axs = plt.subplots(2, 1, figsize=(7,9))
    camera = Camera(fig)

    dt = dt_start
    while dt < dt_end:
        burn_plot_gdf.plot(ax=axs[0], facecolor="none", edgecolor='black')

        for index, row in rad_data_gdf.iterrows():
            point: Point = row["geometry"]
            axs[0].scatter([point.x], [point.y], color=rad_colors[row["rad"]], label=row["rad"])
        axs[0].set_title(plot_title_prefix + "Dualband locations for burn unit " + burn_unit, y=1.04)

        for rad_num, rdf in frp_dfs.items():
            max_frp_datetime = rad_dict[rad_num]["max_frp_datetime"]
            axs[1].plot(rdf["datetime"], rdf["LW_FRP"], color=rad_colors[rad_num], label="Rad " + str(rad_num))
            axs[1].axvline(x=max_frp_datetime, color='grey', linewidth=1, alpha=0.2)

            try:
                frp = rdf.loc[dt]["LW_FRP"]
                radius = 0
                if frp > 0:
                    radius = max(0, 1 * np.log(frp))
                    #radius = 10* frp / maximum_frp_in_unit
                    #print(radius, maximum_frp_in_unit)
                axs[0].add_patch(
                    plt.Circle((rad_dict[rad_num]["loc"].x, rad_dict[rad_num]["loc"].y), radius=radius, alpha=0.5,
                               color=rad_colors[rad_num]))
            except KeyError:
                continue

        axs[1].axvline(x=dt, color='black', linewidth=1, alpha=0.9)
        axs[1].set_ylim([0, None])
        axs[1].xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        axs[1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
        axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        axs[1].set_ylabel("FRP [W/m2]")
        axs[1].set_xlabel("UTC Time")
        axs[1].set_title(plot_title_prefix+"Dualband FRP for burn unit "+burn_unit)

        camera.snap()

        dt += datetime.timedelta(minutes=1)

    # Create animation from saved snapshots and write to file
    print("Creating gif / mp4")
    animation = camera.animate()
    gif_output_filename = str(burn_unit)+"_animation.gif"
    mp4_output_filename = str(burn_unit)+"_animation.mp4"
    if not plot_output_dir.exists():
        plot_output_dir.mkdir()
    animation.save(plot_output_dir.joinpath(gif_output_filename), writer='imagemagick')
    animation.save(plot_output_dir.joinpath(mp4_output_filename), writer='imagemagick')
    print("Animations saved to ", plot_output_dir.joinpath(gif_output_filename))


def plot_burn_unit(rad_data_gdf: gpd.GeoDataFrame, burn_plot_gdf: gpd.GeoDataFrame, burn_unit, plot_output_dir: Path, plot_title_prefix=""):
    """
    Plots data associated with a given burn unit
    :param rad_data_gdf:
    :param burn_plot_gdf:
    :param burn_unit:
    :param plot_output_dir:
    :return:
    :group: krembox_dualband_vis
    """

    # Filter to the datasets from the burn unit we care about
    rad_data_gdf = rad_data_gdf[rad_data_gdf["burn_unit"] == burn_unit]
    burn_plot_gdf = burn_plot_gdf[burn_plot_gdf["Id"] == burn_unit]

    if len(rad_data_gdf) == 0:
        print("No datasets from burn unit ", burn_unit, " found.")
        return

    if len(burn_plot_gdf) == 0:
        print("No burn units named ", burn_unit, " found.")
        return

    # Make a color map for the radiometer numbers
    rad_nums = rad_data_gdf["rad"].unique()
    cmap = cm.get_cmap('tab20', len(rad_nums))
    rad_colors = dict(zip(rad_nums, cmap.colors))
    print(rad_data_gdf.head())

    # Make a plot of the FRP traces of each radiometer in the burn unit
    print("Plotting burn unit", burn_unit, ", ", len(rad_data_gdf), "datasets")
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    for i, row in rad_data_gdf.iterrows():
        # Load each dataset into a pandas dataframe
        proc_data_filepath = Path(row["data_directory"]).joinpath(row["processed_file"])
        rad_num = row["rad"]
        dataset_name = row["dataset"]
        print(dataset_name, proc_data_filepath)
        rad_df = pd.read_csv(proc_data_filepath)
        rad_df['datetime'] = pd.to_datetime(rad_df['datetime'])

        # Figure out where the max FRP occurs and only plot data in a time window around it (reduces time to render plot)
        max_frp_index = rad_df['LW_FRP'].argmax()
        max_frp_datetime = rad_df['datetime'][max_frp_index]
        #min_datetime = max_frp_datetime - datetime.timedelta(minutes=20)
        #max_datetime = max_frp_datetime + datetime.timedelta(minutes=20)
        min_datetime = rad_df['datetime'].iloc[row['pstart_ind']] - datetime.timedelta(minutes=10)
        max_datetime = rad_df['datetime'].iloc[row['pend_ind']] + datetime.timedelta(minutes=10)
        rad_df = rad_df[(rad_df['datetime'] > min_datetime) & (rad_df['datetime'] < max_datetime)]

        ax.plot(rad_df["datetime"], rad_df["LW_FRP"], color=rad_colors[rad_num], label="Rad "+str(rad_num))
        ax.axvline(x=max_frp_datetime, color='grey', linewidth=1, alpha=0.2)

    ax.set_ylim([0, None])
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(axis='x', labelrotation=45)
    ax.set_ylabel("FRP [W/m2]")
    ax.set_xlabel("UTC Time")
    ax.set_title(plot_title_prefix+"Dualband FRP for burn unit "+burn_unit, y=1.04)
    ax.legend()
    plot_filename = "Dualband_FRP_BurnUnit_"+str(burn_unit)+".png"

    if not plot_output_dir.exists():
        plot_output_dir.mkdir()
    plt.savefig(plot_output_dir.joinpath(plot_filename))
    fig.show()

    # Make a spatial plot of the locations of the radiometers
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    burn_plot_gdf.plot(ax=ax, facecolor="none", edgecolor='black')
    for ctype, data in rad_data_gdf.groupby("rad"):
        data.plot(ax=ax, color=rad_colors[ctype], label=ctype, legend=True)
    ax.set_title(plot_title_prefix + "Dualband locations for burn unit " + burn_unit, y=1.04)
    ax.legend()
    plot_filename = "Dualband_Locations_BurnUnit_" + str(burn_unit) + ".png"
    plt.savefig(plot_output_dir.joinpath(plot_filename))
    fig.show()

    # Make detailed plots of each radiometer dataset
    for i, row in rad_data_gdf.iterrows():
        proc_data_filepath = Path(row["data_directory"]).joinpath(row["processed_file"])
        rad_df = pd.read_csv(proc_data_filepath)
        plot_name = row["dataset"] + ".png"
        sup_title = row["dataset"] + ", Burn Unit " + burn_unit
        min_datetime = datetime.datetime.fromisoformat(rad_df['datetime'].iloc[row['pstart_ind']]) - datetime.timedelta(minutes=10)
        max_datetime = datetime.datetime.fromisoformat(rad_df['datetime'].iloc[row['pend_ind']]) + datetime.timedelta(minutes=10)
        kdu.plot_processed_dualband_data(rad_df, plot_output_dir.joinpath(plot_name), True, min_datetime, max_datetime, sup_title)


def plot_burn_unit_map(burn_plot_gdf: gpd.GeoDataFrame, plot_output_dir: Path, color_column: str, plot_title_prefix="", rad_data_df = None):
    """
    Makes a simple plot of all the burn units
    :param burn_plot_gdf:
    :param plot_output_dir:
    :param plot_title_prefix:
    :return:
    :group: krembox_dualband_vis
    """

    fig, ax = plt.subplots(1, 1, figsize=(6, 8))
    burn_plot_gdf.plot(column=color_column, ax=ax, legend=False, alpha=0.5)
    burn_plot_gdf.apply(lambda x: ax.annotate(text=x['Id'], size=10, xy=x.geometry.centroid.coords[0], ha='center'), axis=1)

    if rad_data_df is not None:
        dates = rad_data_df["dt"]
        rad_data_df["date"] = dates.apply(lambda x: datetime.datetime.fromisoformat(x).date())
        rad_data_df.plot(ax=ax, alpha=1, markersize=5, column="date", legend=True)

    ax.set_title(plot_title_prefix + "Burn Unit Map", y=1.04)
    ax.set_aspect('equal')
    plt.tight_layout()
    plot_filename = "BurnUnitMap" + ".png"
    plt.savefig(plot_output_dir.joinpath(plot_filename))
    fig.show()


def run_krembox_dualband_vis(vis_params: dict):
    """
    Runs visualizer
    :param vis_params:
    :return:
    :group: krembox_dualband_vis
    """

    print("Running visualizer")

    # Load processed dataframe and burn plots dataframe
    rad_data_gdf = gpd.read_file(vis_params["rad_data_dataframe"])
    burn_plot_gdf = gpd.read_file(vis_params["burn_plot_dataframe"])

    print("Reprojecting from burn plots from ", burn_plot_gdf.crs, " to ", vis_params["projection"])
    burn_plot_gdf = burn_plot_gdf.to_crs(vis_params["projection"])
    print("Reprojecting from rad data from ", rad_data_gdf.crs, " to ", vis_params["projection"])
    rad_data_gdf = rad_data_gdf.to_crs(vis_params["projection"])
    plot_title_prefix = vis_params["plot_title_prefix"] + ", " + vis_params["projection"] + ", "

    # Figure out which burn units to plot (default to all of them)
    if "burn_units" in vis_params.keys():
        burn_units = params["burn_units"]
    else:
        burn_units = burn_plot_gdf["Id"].unique()

    # Check if the processed data has already been matched with burn unit
    if "burn_unit" not in rad_data_gdf.keys():
        print("Associating datasets with burn units")
        rad_data_gdf = kdu.associate_data2burnplot(rad_data_gdf, burn_plot_gdf)

    rad_data_gdf = rad_data_gdf[rad_data_gdf["burn_unit"] != "unknown"]

    # Make plot of all burn units
    color_column = "Id"
    if vis_params["campaign"] == "Osceola":
        color_column = "BurnYear"
    plot_burn_unit_map(burn_plot_gdf, Path(vis_params["plot_output_dir"]), color_column, plot_title_prefix, rad_data_gdf)

    # Loop through burn units of interest and plot data
    for burn_unit in burn_units:
        burn_unit_plot_output_dir = Path(vis_params["plot_output_dir"]).joinpath(burn_unit)
        plot_burn_unit(rad_data_gdf, burn_plot_gdf, burn_unit, burn_unit_plot_output_dir, plot_title_prefix)
        if vis_params["animations"]:
            animate_burn_unit(rad_data_gdf, burn_plot_gdf, burn_unit, burn_unit_plot_output_dir, vis_params["plot_title_prefix"])

    # Make graphs associated with particular burn campaigns
    if vis_params["campaign"] == "Osceola":
        kdu.plot_osceola_statistics(rad_data_gdf, vis_params["plot_output_dir"])

    print("Finished vis!")
    return 1


if __name__ == "__main__":
    params = {
        "rad_data_dataframe": "dataframes/osceola_processed_dataframe.geojson",
        "burn_plot_dataframe": "dataframes/osceola_burn_plots.geojson",
        "plot_output_dir": "plots/",
        "plot_title_prefix": "Osceola 02/22",
        "projection": "EPSG:32617",
        "campaign": "Osceola",
        "animations": False
    }

    result = run_krembox_dualband_vis(params)
