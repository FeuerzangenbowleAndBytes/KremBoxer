import datetime
import numpy as np
import geopandas as gpd
import scipy.optimize as so
import scipy.constants as sc
import kremboxer.utils.greybody_utils as gbu
from pathlib import Path


def construct_datetime(year, month, day, hours_utc, minutes, seconds):
    if int(year) == 0:
        return datetime.datetime.min
    dt = datetime.datetime(year=int(year),
                           month=int(month),
                           day=int(day),
                           hour=int(hours_utc),
                           minute=int(minutes),
                           second=int(seconds),
                           tzinfo=datetime.timezone.utc)
    return dt


def get_signal_bounds(data: np.array, p_start: float, p_end: float):
    """
    Compute the indices, `ind_start` `ind_end`, containing the specified percentage of the signal's integrated weight.  IE `p_start` of the
    signal occurs before `ind_start`, `p_end` of the signal occurs before `ind_end`.

    :param data: One dimensional signal data
    :param p_start:  Want position in signal where `p_start` of the total weight has occurred
    :param p_end: Want position in signal where `p_end` of the total weight has occurred

    :return: `ind_start`, `ind_end`, integers specifying the indices of the signal between which `p_end` - `p_start` of the signal occurs
    :group: krembox_utils
    """

    N = len(data)
    Itotal = np.sum(data)

    if Itotal <= 0:
        print("get_signal_bounds: given array contains no data")
        return 0, 0

    Imin = Itotal*p_start
    Imax = Itotal*p_end

    w = 0
    i = 0
    while w < Imin and i < N:
        w += data[i]
        i += 1
    ind_start = i
    while w < Imax and i < N:
        w += data[i]
        i += 1
    ind_end = i-1
    return ind_start, ind_end


def associate_data2burnplot(rad_data_gdf: gpd.GeoDataFrame, burn_plot_gdf: gpd.GeoDataFrame):
    """

    :param rad_data_gdf:
    :param burn_plot_gdf:
    :return:
    """
    burn_plot_ids = []
    for i, rad_data_row in rad_data_gdf.iterrows():
        found = False
        for j, burn_plot_row in burn_plot_gdf.iterrows():
            if burn_plot_row.geometry.contains(rad_data_row.geometry):
                burn_plot_ids.append(burn_plot_row.Id)
                found = True
                break
        if not found:
            print("Warning! Dataset ", rad_data_row["DATAFILE"], " not contained in any burn plot!!")
            print("\t(lat,lon)=(", rad_data_row["LATITUDE"], ", ", rad_data_row["LONGITUDE"], ")")
            print("\tSetting burn plot to unknown")
            burn_plot_ids.append("unknown")

    rad_data_gdf["burn_unit"] = burn_plot_ids

    return rad_data_gdf


def fit_detector_model(t_target, t_detector, v_sensor, A, N, p0):
    T_data = np.stack((t_target, t_detector), axis=0)
    (G, AL), pcov = so.curve_fit(
        lambda T, G, AL: gbu.detector_model(T[0], G, AL, T[1], A, N),
        T_data, v_sensor, maxfev=1000, p0=p0)

    return G, AL, pcov


def fit_narrow_detector_model(t_target, t_detector, v_sensor, A, N, p0):
    T_data = np.stack((t_target, t_detector), axis=0)
    (G, AL), pcov = so.curve_fit(
        lambda T, G, AL: G*(A*T[0]**N-AL*T[1]**4),
        T_data, v_sensor, maxfev=1000, p0=p0)

    return G, AL, 4, pcov


def associate_data2fuelplot(rad_data_gdf: gpd.GeoDataFrame, fuel_plot_gdf: gpd.GeoDataFrame):
    """
    Associate the dualband FRP data with the fuel plots. This is done by finding the closest fuel plot to each FRP
    measurement and adding the fuel plot information to the FRP dataframe.  It outputs a new dataframe with the
    combined FRP and fuel plot information, and uses the fuel plot locations as the geometry of the dataframe.

    :param params: dictionary of parameters
    """

    # Read in the fuel plot dataframe and convert it to the same CRS as the processed FRP dataframe.  Also save
    # the fuel plot geometry in a new column called "fuel_plot_location", which we will use as the geometry of the
    # new dataframe after the below spatial join.
    rad_data_gdf.to_crs(crs="epsg:3857", inplace=True)
    fuel_plot_gdf.to_crs(rad_data_gdf.crs, inplace=True)
    fuel_plot_gdf['fuel_plot_location'] = fuel_plot_gdf.geometry

    # Perform a spatial join to figure out which fuel plot is closest to each FRP GPS location.  We assume that the closest
    # fuel plot is the one where the radiometer was actually located, but this could be incorrect if the fuel plots are close together.
    plot_associated_df = rad_data_gdf.sjoin_nearest(fuel_plot_gdf, how="left", distance_col="rad_fuel_plot_separation", max_distance=60)

    # Look at which radiometers were not associated with fuel plots
    unassociated_df = plot_associated_df[plot_associated_df["rad_fuel_plot_separation"].isna()].copy(deep=True)
    unassociated_df.drop(columns=["fuel_plot_location"], inplace=True)

    # Use the geometry of the fuel plots as the location in the new FRP dataframe.  Drop the old FRP GPS location column.
    plot_associated_df.drop(columns=["LATITUDE", "LONGITUDE"], inplace=True)
    associated_mask = plot_associated_df["fuel_plot_location"].notna()
    plot_associated_df.loc[associated_mask, 'geometry'] = plot_associated_df["fuel_plot_location"][associated_mask]
    plot_associated_df.drop(columns=["fuel_plot_location"], inplace=True)
    #plot_associated_df.set_geometry(col="fuel_plot_location", inplace=True, drop=True)

    plot_associated_df.to_crs(crs="epsg:4326", inplace=True)
    unassociated_df.to_crs(crs="epsg:4326", inplace=True)

    return plot_associated_df, unassociated_df

    # print("Saving fuel plot associated dataframe in GeoJSON format: ",
    #       dataframes_dir.joinpath("frp_fuel_plot_dataframe_" + burn_name + ".geojson"))
    # plot_associated_df.to_file(dataframes_dir.joinpath("frp_fuel_plot_dataframe_" + burn_name + ".geojson"), driver='GeoJSON')
    # unassociated_df.to_file(dataframes_dir.joinpath("unassociated_frp_fuel_plot_dataframe_" + burn_name + ".geojson"), driver='GeoJSON')

    # Plot the GPS errors
    # fig, axs = plt.subplots(1, 1, figsize=(10, 10))
    # plot_associated_df.hist(column="rad_fuel_plot_separation", bins=10, ax=axs)
    # axs.set_title("GPS Errors from "+burn_name)
    # axs.set_xlabel("Diff Rad GPS and Fuel Plot GPS (m)")
    # axs.set_ylabel("Count")
    # plt.savefig(output_root.joinpath("plots_dualband_"+burn_name).joinpath("gps_errors.png"))
    # plt.close()
