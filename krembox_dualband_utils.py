import datetime
import pandas as pd
import geopandas as gpd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def parse_header(fields, header):
    dt = datetime.datetime(year=int(header[fields.index('YEAR')]),
                           month=int(header[fields.index('MONTH')]),
                           day=int(header[fields.index('DAY')]),
                           hour=int(header[fields.index('HOURS(UTC)')]),
                           minute=int(header[fields.index('MINUTES')]),
                           second=int(header[fields.index('SECONDS')]),
                           tzinfo=datetime.timezone.utc)
    lat, lon = int(header[fields.index('LATITUDE(deg/100000)')]) / 1000000, \
               int(header[fields.index('LONGITUDE(deg/100000)')]) / 1000000

    sample_freq = float(header[fields.index('SAMPLE-RATE(Hz)')])
    return dt, lat, lon, sample_freq


def associate_data2burnplot(rad_data_gdf: gpd.GeoDataFrame, burn_plot_gdf: gpd.GeoDataFrame):
    burn_plot_ids = []
    for i, rad_data_row in rad_data_gdf.iterrows():
        for j, burn_plot_row in burn_plot_gdf.iterrows():
            if burn_plot_row.geometry.contains(rad_data_row.geometry):
                burn_plot_ids.append(burn_plot_row.Id)

    rad_data_gdf["burn_unit"] = burn_plot_ids

    print(rad_data_gdf.head())
    return rad_data_gdf


def plot_processed_dualband_data(rad_df: pd.DataFrame, plot_outfile: str, show_plot: bool, zoom2fire: bool, sup_title: str):
    fig, axs = plt.subplots(3, 2, figsize=(8,8))
    print(rad_df)
    rad_df['datetime'] = pd.to_datetime(rad_df['datetime'])
    if zoom2fire:
        max_frp_index = rad_df['LW_FRP'].argmax()
        max_frp_datetime = rad_df['datetime'][max_frp_index]
        min_datetime = max_frp_datetime - datetime.timedelta(minutes=10)
        max_datetime = max_frp_datetime + datetime.timedelta(minutes=10)
        rad_df = rad_df[(rad_df['datetime'] > min_datetime) & (rad_df['datetime'] < max_datetime)]

    datetimes = rad_df["datetime"]
    mdatetimes = mdates.date2num(datetimes)

    axs[0, 0].plot(mdatetimes, rad_df["TH"])
    axs[0,0].set_ylabel("TH [mV]")

    axs[0, 1].plot(mdatetimes, rad_df["LW-A"], label="LW-A")
    axs[0, 1].plot(mdatetimes, rad_df["MW-B"], label="MW-B")
    axs[0, 1].set_ylabel("Sensor [mV]")
    axs[0, 1].legend()

    axs[1, 0].plot(mdatetimes, rad_df["TD"], label="Detector")
    axs[1, 0].plot(mdatetimes, rad_df["T"], label="Fire")
    axs[1, 0].set_ylabel("Temperature [K]")
    axs[1, 0].legend()

    axs[1, 1].plot(mdatetimes, rad_df["LW_W"], label="LW_W")
    axs[1, 1].plot(mdatetimes, rad_df["MW_W"], label="MW_W")
    axs[1, 1].set_ylabel("Detected W [W/m2]")
    axs[1, 1].legend()

    axs[2, 0].plot(mdatetimes, rad_df["LW_eA"], label="LW_eA")
    axs[2, 0].plot(mdatetimes, rad_df["MW_eA"], label="MW_eA")
    axs[2, 0].set_ylabel("eA")
    axs[2, 0].legend()

    axs[2, 1].plot(mdatetimes, rad_df["LW_FRP"], label="LW_FRP")
    axs[2, 1].plot(mdatetimes, rad_df["MW_FRP"], label="MW_FRP")
    axs[2, 1].set_ylabel("FRP [W/m2]")
    axs[2, 1].legend()

    for i in range(0,3):
        for j in range(0,2):
            axs[i, j].xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            axs[i, j].xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
            axs[i,j].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    print(rad_df["datetime"].iloc[0], rad_df["datetime"].iloc[-1])

    plt.suptitle(sup_title)
    plt.tight_layout()
    plt.savefig(plot_outfile)
    if show_plot:
        plt.show()


def plot_osceola_statistics(gdf: gpd.GeoDataFrame, plot_output_dir: str):
    """
    Makes a plot with statistics computed from all the Osceola FRP datasets at Osceola, ex: fire duration, max FRP, vs treatment
    Note that this only works for the Osceola datasets, because of the special association between treatments and burn units
    :param rad_data_gdf:
    :param plot_output_dir:
    :return:
    """

    fire_durations = gdf["fire_duration"]
    max_frps = gdf["max_FRP"]
    fres = gdf["LW_FRE"]
    burn_units = gdf['burn_unit']
    bus = [int(x[1]) for x in burn_units]
    bu_letters = [x[0] for x in burn_units]

    colors = {'A': 'red', 'B': 'green', 'C': 'blue', 'D': 'violet', 'E': 'orange'}
    scatter_colors = [colors[x] for x in bu_letters]

    fig, axs = plt.subplots(5, 1, figsize=(6, 10))
    axs[0].scatter(bus, fire_durations, c=scatter_colors)
    axs[0].set_ylabel("Fire Len [minutes]")
    axs[0].set_title("Fire Duration vs Burn Frequency at Osceola")
    axs[0].set_ylim([0, 25])

    axs[1].scatter(bus, max_frps, c=scatter_colors)
    axs[1].set_ylabel("max FRP [W/m2]")
    axs[1].set_title("max FRP vs Burn Frequency at Osceola")

    axs[2].scatter(bus, gdf["mean_FRP"], c=scatter_colors)
    axs[2].set_ylabel("mean FRP [W/m2]")
    axs[2].set_title("mean FRP vs Burn Frequency at Osceola")

    axs[3].scatter(bus, gdf["var_FRP"], c=scatter_colors)
    axs[3].set_ylabel("var FRP [W/m2]")
    axs[3].set_title("var FRP vs Burn Frequency at Osceola")

    axs[4].scatter(bus, fres, c=scatter_colors)
    axs[4].set_xlabel("#Years between burns")
    axs[4].set_ylabel("FRE [J/m2]")
    axs[4].set_title("FRE vs Burn Frequency at Osceola")
    plt.tight_layout()

    if not os.path.exists(plot_output_dir):
        os.mkdir(plot_output_dir)
    plt.savefig(os.path.join(plot_output_dir, "fre_vs_burnfreq.png"))
    plt.show()


if __name__ == "__main__":
    params = {
        "rad_data_dataframe": "dataframes/example_processed_dataframe.geojson",
        "burn_plot_dataframe": "dataframes/osceola_burn_plots.geojson"
    }

    rad_data_gdf = gpd.read_file(params["rad_data_dataframe"])
    burn_plot_gdf = gpd.read_file(params["burn_plot_dataframe"])

    gdf = associate_data2burnplot(rad_data_gdf, burn_plot_gdf)

    df_file = os.path.join(gdf.iloc[0]["data_directory"], gdf.iloc[0]["processed_file"])
    print(df_file)
    df = pd.read_csv(df_file)
    plot_name = gdf.iloc[0]["dataset"]+".png"
    sup_title = gdf.iloc[0]["dataset"]+", Burn Unit "+gdf.iloc[0]["burn_unit"]
    plot_processed_dualband_data(df, os.path.join("plots", plot_name), True, True, sup_title)

    burn_units = gdf['burn_unit'].unique()
    for burn_unit in burn_units:
        gdf_temp = gdf[gdf['burn_unit'] == burn_unit]
        df_file = os.path.join(gdf_temp.iloc[0]["data_directory"], gdf_temp.iloc[0]["processed_file"])
        print(df_file)
        df = pd.read_csv(df_file)
        plot_name = gdf_temp.iloc[0]["dataset"] + ".png"
        sup_title = gdf_temp.iloc[0]["dataset"] + ", Burn Unit " + gdf_temp.iloc[0]["burn_unit"]
        plot_processed_dualband_data(df, os.path.join("plots", plot_name), True, True, sup_title)

    fire_durations = gdf["fire_duration"]
    max_frps = gdf["max_FRP"]
    fres = gdf["LW_FRE"]
    burn_units = gdf['burn_unit']
    bus = [int(x[1]) for x in burn_units]
    bu_letters = [x[0] for x in burn_units]
    print(fres)
    print(burn_units)
    colors = {'A': 'red', 'B': 'green', 'C': 'blue', 'D': 'violet', 'E': 'orange'}
    scatter_colors = [colors[x] for x in bu_letters]

    fig, axs = plt.subplots(5, 1, figsize=(6, 10))
    axs[0].scatter(bus, fire_durations, c=scatter_colors)
    axs[0].set_ylabel("Fire Len [minutes]")
    axs[0].set_title("Fire Duration vs Burn Frequency at Osceola")
    axs[0].set_ylim([0, 25])

    axs[1].scatter(bus, max_frps, c=scatter_colors)
    axs[1].set_ylabel("max FRP [W/m2]")
    axs[1].set_title("max FRP vs Burn Frequency at Osceola")

    axs[2].scatter(bus, gdf["mean_FRP"], c=scatter_colors)
    axs[2].set_ylabel("mean FRP [W/m2]")
    axs[2].set_title("mean FRP vs Burn Frequency at Osceola")

    axs[3].scatter(bus, gdf["var_FRP"], c=scatter_colors)
    axs[3].set_ylabel("var FRP [W/m2]")
    axs[3].set_title("var FRP vs Burn Frequency at Osceola")

    axs[4].scatter(bus, fres, c=scatter_colors)
    axs[4].set_xlabel("#Years between burns")
    axs[4].set_ylabel("FRE [J/m2]")
    axs[4].set_title("FRE vs Burn Frequency at Osceola")
    plt.tight_layout()
    plt.savefig("plots/fre_vs_burnfreq.png")
    plt.show()

