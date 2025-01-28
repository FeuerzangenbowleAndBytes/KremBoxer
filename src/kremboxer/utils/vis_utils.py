import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_FRP_traces_by_burn_unit(gdf: gpd.GeoDataFrame, root_dir: Path, time_window_map):
    print(gdf.head())
    burn_units = gdf['burn_unit'].unique()
    print(burn_units)

    for burn_unit in burn_units:
        fig, axs = plt.subplots(1, 1, figsize=(8,8))

        burn_unit_gdf = gdf[gdf['burn_unit'] == burn_unit]
        for i, row in burn_unit_gdf.iterrows():
            print(i, row)
            datafile = root_dir.joinpath(row['PROCESSING_LEVEL'], row['SENSOR'], row['DATAFILE'])
            start_dt = datetime.datetime.fromisoformat(str(row['fire_start']))
            end_dt = datetime.datetime.fromisoformat(str(row['fire_end']))

            print(datafile)
            df = pd.read_csv(datafile)
            datetimes = pd.to_datetime(df['DATETIME'])
            print(datetimes)
            print(start_dt, end_dt)
            mask = (datetimes >= start_dt) & (datetimes <= end_dt)
            print(len(df['MW_FRP']), len(df[mask]['MW_FRP']))
            axs.plot(datetimes[mask], df[mask]['MW_FRP'], label=row['UNIT'])

        axs.legend()
        axs.set_title(f'FRP vs Datetime, Burn Unit: {burn_unit}')
        axs.set_xlim([time_window_map[burn_unit]['t_start'], time_window_map[burn_unit]['t_end'] ])
        axs.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        axs.xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
        axs.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        axs.set_xlabel('Time (UTC)')
        axs.set_ylabel('FRP (W/m^2)')
        plt.savefig(root_dir.joinpath(f'FRP_Burn_Unit_{burn_unit}.png'))


if __name__ == "__main__":
    root_dir = Path("/home/jepaki/Projects/Objects/Eglin_2023/FireBehaviorDatasets/")
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
    plot_FRP_traces_by_burn_unit(gdf, root_dir, time_window_map)