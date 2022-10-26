import csv
import os.path
from pathlib import Path
import numpy as np
import datetime
import pandas as pd
import geopandas as gpd
import krembox_dualband_utils as kdb_utils


def process_data_series(data_series, target_dates, file, data_directory, clean_file_list):
    valid_data = False
    metadata = {}
    clean_directory = os.path.join(data_directory, "Clean")

    if len(data_series) > 3:
        if data_series[1][data_series[0].index('GPS-TYPE')] == "LOCKED":
            fields = data_series[0]
            header = data_series[1]
            dt, lat, lon, sample_freq = kdb_utils.parse_header(fields, header)

            # Only clean datasets from the dates we're interested in
            if dt.date() in target_dates:
                dataset = file.split(".CSV")[0] + "_" +dt.isoformat()
                clean_file = dataset + ".csv"
                clean_file = os.path.join("Clean", clean_file)

                # Only keep this dataset if we have not already processed it
                # For example, raw data files from a second day of data collection may
                # still contain datasets from the previous day
                if clean_file not in clean_file_list:
                    clean_file_path = os.path.join(data_directory, clean_file)
                    clean_header = '#'+','.join(data_series[0]) + "\n#" + ','.join(data_series[1]) + "\ndatetime," + ",".join(data_series[2]) + "\n"

                    # Write the cleaned up data file
                    with open(clean_file_path, 'w') as csvcleanfile:
                        csvcleanfile.write(clean_header)
                        dt_data = dt
                        for i in range(3, len(data_series)):
                            data_row = dt_data.isoformat()+", "+', '.join(data_series[i]) + "\n"
                            csvcleanfile.write(data_row)
                            dt_data+= datetime.timedelta(seconds=1)

                    valid_data = True
                    metadata["dt"] = dt
                    metadata["dataset"] = dataset
                    metadata["data_directory"] = data_directory
                    metadata["clean_file"] = clean_file
                    metadata['lat'] = lat
                    metadata['lon'] = lon
                    metadata['rad'] = clean_file.split("_")[-2]
                    metadata['N'] = len(data_series)-3
                    metadata['sample_freq'] = sample_freq
    return valid_data, metadata


def run_krembox_dualband_cleaner(params: dict):
    """
    Cleans the raw datafiles from raw krembox data stored in specified directories.  Only keeps data from the
    specified target dates

    :param params:
    :return:
    """

    # Sort the target dates for convenience
    target_dates = params["target_dates"]
    target_dates = [datetime.datetime.fromisoformat(x).date() for x in target_dates]
    target_dates.sort()

    # Data dictionary to keep track of cleaned datasets, turned into Pandas dataframe at end
    metadata_list = []
    clean_file_list = []

    # Loop through data directories to find all the raw data, create directories to store cleaned data
    for data_directory in params["data_directories"]:
        raw_directory = data_directory+"/Raw/"
        clean_directory = data_directory+"/Clean/"
        if not os.path.exists(raw_directory):
            raise RuntimeError("Specified raw directory "+raw_directory+" does not exist!")
        if not os.path.exists(clean_directory):
            os.mkdir(clean_directory)

        # Loop through the raw data files
        print(f"Cleaning data in {raw_directory}")
        raw_files = os.listdir(raw_directory)
        for file in raw_files:
            # Skip hidden or lock files
            if file[0] == '.':
                continue

            raw_data_file = os.path.join(raw_directory, file)
            with open(raw_data_file, 'r') as csvfile:
                csvreader = csv.reader(csvfile)
                data_series = []

                # Find first header in datafile
                row = next(csvreader, None)
                while not 'DAY' == row[0]:
                    row = next(csvreader, None)

                # Loop through valid datasets by looking for headers
                data_series.append(row)
                while row is not None:
                    row = next(csvreader, None)
                    if row is None or 'DAY' == row[0]:
                        (valid_data, metadata) = process_data_series(data_series, target_dates, file, data_directory, clean_file_list)
                        if valid_data:
                            print(metadata)
                            clean_file_list.append(metadata["clean_file"])
                            metadata_list.append(metadata)
                        data_series.clear()
                    data_series.append(row)

    # Create a pandas dataframe to record the metadata, and then convert into a geopands dataframe with gps info
    df = pd.DataFrame(metadata_list)
    print(df)
    print("Found ", len(clean_file_list), " valid datasets")
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat, crs="EPSG:4326"))

    # Convert to the desired projection
    gdf = gdf.to_crs(params["projection"])

    # Figure out which burn unit each dataset was recorded in, if we have burn unit polygons
    # The burn unit Id will be added as a column in the dataframe
    if "burn_plot_dataframe_input" in params.keys():
        burn_plot_gdf = gpd.read_file(params["burn_plot_dataframe_input"])
        burn_plot_gdf = burn_plot_gdf.to_crs(params["projection"])
        gdf = kdb_utils.associate_data2burnplot(gdf, burn_plot_gdf)

    print("Saving clean dataframe in CSV format: ",  params["clean_dataframe_output"]+".csv")
    gdf.to_csv(params["clean_dataframe_output"]+".csv")
    print("Saving clean dataframe in GeoJSON format: ", params["clean_dataframe_output"]+".geojson")
    gdf.to_file(params["clean_dataframe_output"]+".geojson", driver='GeoJSON')
    return gdf


if __name__ == '__main__':
    """
    Example of running the dual band data cleaner, mostly used for development 
    """

    params = {
        "data_directories": ["/home/jepaki/Projects/Osceola/020322_Osceola_Radiometers_DualBand/", "/home/jepaki/Projects/Osceola/020422_Osceola_Radiometers_DualBand/"],
        #"target_dates": [datetime.date(year=2022, month=2, day=4), datetime.date(year=2022, month=2, day=3)],
        "target_dates": ["2022-02-04", "2022-02-03"],
        "clean_dataframe_output": "dataframes/example_cleaned_dataframe",
        "burn_plot_dataframe_input": "dataframes/osceola_burn_plots.geojson"
    }
    print("Running cleaner with params = ", params)
    cleaned_gdf = run_krembox_dualband_cleaner(params)
