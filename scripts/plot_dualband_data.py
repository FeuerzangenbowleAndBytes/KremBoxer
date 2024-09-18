import datetime

import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.dates as mdates

data_dir = Path("/ws3/gis_lab/project/SERDP_Objects-IRProcessing/RadiometerData/FortStewart_2022-03/")
plot_dir = data_dir.joinpath("/ws3/gis_lab/project/SERDP_Objects-IRProcessing/PresentationsandPosters/ForestSAT/Figures/")

burn_plot_geojson = data_dir.joinpath("fort_stewart_burn_plots.geojson")
processed_data_geojson = data_dir.joinpath("fort_stewart_processed_dataframe.geojson")

burn_unit_gdf = gpd.read_file(burn_plot_geojson)
data_gdf = gpd.read_file(processed_data_geojson)

print(burn_unit_gdf.head())
print(data_gdf.head(), data_gdf.keys())

burn_units = burn_unit_gdf['UNITNAME'].unique()
print(burn_units)

for burn_unit in burn_units:
    unit_data_gdf = data_gdf[data_gdf['burn_unit'] == burn_unit]
    print(unit_data_gdf)

    fig, axs = plt.subplots(1, 1, figsize=(8, 8))

    max_frp_time = unit_data_gdf.iloc[0]['max_FRP_datetime']
    for i, row in unit_data_gdf.iterrows():
        print(i, row)
        datafile = data_dir.joinpath(row['data_directory'].split('/')[-1], row['processed_file']+'.csv')
        print(datafile)
        df = pd.read_csv(datafile)
        print(df.head(), df.keys())
        times = pd.to_datetime(df['datetime'])
        frp = df['MW_FRP']

        axs.plot(times, frp, label=str(row['rad']))
        axs.axvline(x=row['max_FRP_datetime'], color='grey', linewidth=1, alpha=0.2)

        if row['max_FRP_datetime'] > max_frp_time:
            max_frp_time = row['max_FRP_datetime']

    axs.set_ylim([0, None])
    axs.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    axs.xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
    axs.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    time_begin = max_frp_time - datetime.timedelta(hours=1, minutes=30)
    time_end = max_frp_time + datetime.timedelta(hours=0, minutes=30)
    axs.set_xlim([time_begin, time_end])
    axs.tick_params(axis='x', labelrotation=45)
    axs.set_ylabel("FRP [W/m2]")
    axs.set_xlabel("UTC Time")
    axs.set_title(f'Fort Stewart, Burn Unit {burn_unit}, {max_frp_time.date()}')
    axs.legend()

    plt.savefig(plot_dir.joinpath(f'FRP_Traces_Unit_{burn_unit}.png'))


