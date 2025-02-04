import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_FRP_traces_by_burn_unit(gdf: gpd.GeoDataFrame, root_dir: Path, time_window_map, plot_lookup_df: pd.DataFrame):
    print(gdf.head())
    burn_units = gdf['burn_unit'].unique()
    print(burn_units)

    print(plot_lookup_df.head())
    plot_lookup_df["rad"] = plot_lookup_df["rad"].str.lower()

    for burn_unit in burn_units:
        plt.rcParams.update({'font.size': 14})
        plt.rc('legend', fontsize=10)
        fig, axs = plt.subplots(1, 1, figsize=(8,8))

        burn_unit_gdf = gdf[gdf['burn_unit'] == burn_unit]
        for i, row in burn_unit_gdf.iterrows():
            datafile = root_dir.joinpath(row['PROCESSING_LEVEL'], row['SENSOR'], row['DATAFILE'])
            start_dt = datetime.datetime.fromisoformat(str(row['fire_start']))
            end_dt = datetime.datetime.fromisoformat(str(row['fire_end']))

            df = pd.read_csv(datafile)
            datetimes = pd.to_datetime(df['DATETIME'])

            mask = (datetimes >= start_dt) & (datetimes <= end_dt)
            clipplot = plot_lookup_df[(plot_lookup_df.burn_unit == burn_unit) & (plot_lookup_df.rad == row['UNIT'].lower())]

            if len(clipplot) == 0:
                print(f'Unknown clip plot for burn unit: {burn_unit}, sensor: {row["UNIT"]}')
                continue
            if len(clipplot) > 1:
                print(f'Multiple clip plot for burn unit: {burn_unit}, sensor: {row["UNIT"]}')
                print(clipplot)
                print("Using first entry")
            clipplot_name = clipplot.iloc[0]['clipplot']
            print(clipplot_name)
            axs.plot(datetimes[mask], df[mask]['MW_FRP'], label=clipplot_name)

        axs.legend()
        axs.set_title(f'FRP vs Datetime, Burn Unit: {burn_unit}')
        axs.set_xlim([time_window_map[burn_unit]['t_start'], time_window_map[burn_unit]['t_end'] ])
        axs.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        axs.xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
        axs.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        axs.set_xlabel('Time (UTC)')
        axs.set_ylabel('FRP (W/m^2)')
        plt.tight_layout()
        plt.savefig(root_dir.joinpath(f'FRP_Burn_Unit_{burn_unit}.png'))


if __name__ == "__main__":
    root_dir = Path("/home/jepaki/Projects/Objects/Eglin_2023/FireBehaviorDatasets/")
    clipplot_rad_lookup_table = Path("/home/jepaki/Projects/Objects/Eglin_2023/eglin_2023_clipplot_rad_lookuptable.csv")
    plot_lookup_df = pd.read_csv(clipplot_rad_lookup_table)
    dualband_processed_metadatafile = root_dir.joinpath("Dualband_processed_metadata.geojson")
    gdf = gpd.read_file(dualband_processed_metadatafile, engine='fiona')
    time_window_map = {
        'G-20': {
            't_start': datetime.datetime(year=2023, month=3, day=19, hour=15, minute=45, second=0,
                                         tzinfo=datetime.timezone.utc),
            't_end': datetime.datetime(year=2023, month=3, day=19, hour=16, minute=25, second=0,
                                       tzinfo=datetime.timezone.utc)
        },
        'G-25E': {
            't_start': datetime.datetime(year=2023, month=3, day=16, hour=15, minute=50, second=0,
                                         tzinfo=datetime.timezone.utc),
            't_end': datetime.datetime(year=2023, month=3, day=16, hour=16, minute=30, second=0,
                                       tzinfo=datetime.timezone.utc)
        },
        'G-25W': {
            't_start': datetime.datetime(year=2023, month=3, day=11, hour=19, minute=0, second=0,
                                         tzinfo=datetime.timezone.utc),
            't_end': datetime.datetime(year=2023, month=3, day=11, hour=20, minute=5, second=0,
                                       tzinfo=datetime.timezone.utc)
        }
    }
    plot_FRP_traces_by_burn_unit(gdf, root_dir, time_window_map, plot_lookup_df)