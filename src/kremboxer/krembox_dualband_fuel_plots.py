import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import json
from pathlib import Path
import matplotlib.pyplot as plt


def run_krembox_dualband_fuel_plot_association(params):
    """
    Associate the dualband FRP data with the fuel plots. This is done by finding the closest fuel plot to each FRP
    measurement and adding the fuel plot information to the FRP dataframe.  It outputs a new dataframe with the
    combined FRP and fuel plot information, and uses the fuel plot locations as the geometry of the dataframe.

    :param params: dictionary of parameters
    """

    # Get the output root directory and the path of the processed FRP dataframe
    burn_name = params["burn_name"]
    output_root = Path(params["output_root"])
    dataframes_dir = output_root.joinpath("dataframes_" + burn_name)
    processed_df = gpd.read_file(dataframes_dir.joinpath("processed_dataframe_" + burn_name + ".geojson"))

    # Read in the fuel plot dataframe and convert it to the same CRS as the processed FRP dataframe.  Also save
    # the fuel plot geometry in a new column called "fuel_plot_location", which we will use as the geometry of the
    # new dataframe after the below spatial join.
    fuel_plot_df = gpd.read_file(params["fuel_plot_dataframe_input"])
    fuel_plot_df.to_crs(processed_df.crs, inplace=True)
    fuel_plot_df['fuel_plot_location'] = fuel_plot_df.geometry

    # Perform a spatial join to figure out which fuel plot is closest to each FRP GPS location.  We assume that the closest
    # fuel plot is the one where the radiometer was actually located, but this could be incorrect if the fuel plots are close together.
    plot_associated_df = processed_df.sjoin_nearest(fuel_plot_df, how="left", distance_col="rad_fuel_plot_separation", max_distance=100)

    # Look at which radiometers were not associated with fuel plots
    unassociated_df = plot_associated_df[plot_associated_df["rad_fuel_plot_separation"].isna()].copy(deep=True)
    print(unassociated_df)
    unassociated_df.drop(columns=["fuel_plot_location"], inplace=True)

    # Use the geometry of the fuel plots as the location in the new FRP dataframe.  Drop the old FRP GPS location column.
    plot_associated_df.set_geometry("fuel_plot_location", inplace=True)
    plot_associated_df.drop(columns=["geometry"], inplace=True)

    print("Saving fuel plot associated dataframe in GeoJSON format: ",
          dataframes_dir.joinpath("frp_fuel_plot_dataframe_" + burn_name + ".geojson"))
    plot_associated_df.to_file(dataframes_dir.joinpath("frp_fuel_plot_dataframe_" + burn_name + ".geojson"), driver='GeoJSON')
    unassociated_df.to_file(dataframes_dir.joinpath("unassociated_frp_fuel_plot_dataframe_" + burn_name + ".geojson"), driver='GeoJSON')

    # Plot the GPS errors
    fig, axs = plt.subplots(1, 1, figsize=(10, 10))
    plot_associated_df.hist(column="rad_fuel_plot_separation", bins=10, ax=axs)
    axs.set_title("GPS Errors from "+burn_name)
    axs.set_xlabel("Diff Rad GPS and Fuel Plot GPS (m)")
    axs.set_ylabel("Count")
    plt.savefig(output_root.joinpath("plots_dualband_"+burn_name).joinpath("gps_errors.png"))
    plt.close()
