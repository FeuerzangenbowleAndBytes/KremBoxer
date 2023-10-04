import datetime
import getopt
import sys
import json
import shutil
from pathlib import Path
import pandas as pd
import geopandas as gpd
import kremboxer.krembox_dualband_utils as kdu


def main(argv):
    """
    User entry point for the Kremboxer filtering code.  This script will filter previously processed dualband
    data based on parameters provided within a JSON parameter file as a command line argument

    Ex. python -m kremboxer.krembox_filter -p paramfiles/example_paramfile.json

    :param argv: Command line parameters passed from the system.  Will be parsed to extract the parameter file.
    :return:
    :group: kremboxer
    """

    print("Starting Krembox Filter, a code for filtering dualband radiometer datasets")
    print("Reading parameter file...")

    paramfile = ''
    try:
        opts, args = getopt.getopt(argv, "hp:", ["paramfile"])
    except:
        print('Usage: krembox_filter.py -p <paramfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage: krembox_filter.py -p <paramfile>')
            sys.exit()
        elif opt in ("-p", "--paramfile"):
            paramfile = arg

    # Load parameters
    print("Parameter file = ", paramfile)
    with open(paramfile) as json_data_file:
        params = json.load(json_data_file)
    print("Input params: ", params)

    # Check if the specified output directory already exists and warn the user
    output_root = Path(params["output_dir"])
    if output_root.exists() and not params["overwrite"]:
        print("Warning! Output directory already exists: ", output_root)
        print("Should we continue? (y/n)")
        response = input()
        if response != "y":
            print("Exiting...")
            sys.exit(0)
    else:
        output_root.mkdir(parents=True, exist_ok=True)

    # Copy the filter parameters to the output directory
    shutil.copy(paramfile, output_root.joinpath("filter_params.json"))

    # Read in dataframe to be filtered
    frp_df = gpd.read_file(params["input_frp_dataframe"])
    print(frp_df.head())

    # Filter dataframe by burn unit and date
    filter_criteria = params["filter_criteria"]
    print(filter_criteria)
    filter_df = frp_df[frp_df["burn_unit"] == filter_criteria["burn_unit"]]
    filter_date = datetime.datetime.fromisoformat(filter_criteria["date"]).date()
    filter_df = filter_df[filter_df['dt'].apply(lambda x: x.date() == filter_date)]
    print(filter_df)

    # Filter dataframe by polygon if requested, "feature_name" is the name of the polygon to filter by
    # from the input vector layer "polygon_layer"
    if "polygon_layer" in filter_criteria.keys():
        shutil.copy(filter_criteria["polygon_layer"], output_root)
        poly_gdf = gpd.read_file(filter_criteria["polygon_layer"])
        poly_gdf.to_crs(filter_df.crs, inplace=True)
        feature_name = filter_criteria["feature_name"]
        poly_gdf = poly_gdf[poly_gdf["name"] == feature_name]
        poly_geom = poly_gdf["geometry"].iloc[0]

        # Figure out which dataframe records are within the polygon
        pip = filter_df.within(poly_gdf.loc[0, 'geometry'])

        # Create a new geoDataFrame with only the radiometers within the polygon
        filter_df = filter_df.loc[pip].copy()

    # Create folders to save data and plots
    data_dir = output_root.joinpath("data")
    plot_dir = output_root.joinpath("plots")
    data_dir.mkdir(parents=False, exist_ok=True)
    plot_dir.mkdir(parents=False, exist_ok=True)

    # Iterate through remaining records, copy data to output directory, and make plots of the radiometer data
    filter_data_dirs = []
    filter_data_files = []
    plot_paths = []
    for i, row in filter_df.iterrows():
        print(i, row)
        # Change the paths to the data files if requested, useful if you are running on a different computer
        # from the one that generated the input dataframe
        if "replace_data_dir" in params.keys():
            frp_datafile = Path(params["replace_data_dir"]).joinpath(row["processed_file"])
        else:
            frp_datafile = Path(row["data_directory"]).joinpath(row["processed_file"])
        print(frp_datafile)

        # Copy the radiometer data to the output dir
        dest_file = Path("data").joinpath(frp_datafile.name)
        dest_path = output_root.joinpath(dest_file)
        shutil.copy(frp_datafile, dest_path)

        filter_data_dirs.append(str(output_root))
        filter_data_files.append(str(dest_file))

        # Create plots of each radiometer dataset
        rad_df = pd.read_csv(dest_path)
        plot_name = row["dataset"] + ".png"
        sup_title = row["dataset"]
        min_datetime = datetime.datetime.fromisoformat(rad_df['datetime'].iloc[row['pstart_ind']]) - datetime.timedelta(
            minutes=10)
        max_datetime = datetime.datetime.fromisoformat(rad_df['datetime'].iloc[row['pend_ind']]) + datetime.timedelta(
            minutes=10)

        plot_path = plot_dir.joinpath(plot_name)
        if not plot_path.exists() and params["make_plots"]:
            kdu.plot_processed_dualband_data(rad_df, plot_path, False, min_datetime,
                                             max_datetime, sup_title)
        plot_paths.append(str(plot_path))

    # Save the filtered dataframe
    filter_df["data_directory"] = filter_data_dirs
    filter_df["processed_file"] = filter_data_files
    filter_df.to_file(output_root.joinpath("filtered_frp_dataframe.geojson"), driver='GeoJSON')


if __name__ == "__main__":
    main(sys.argv[1:])
