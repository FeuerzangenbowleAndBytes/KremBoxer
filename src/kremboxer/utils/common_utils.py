import datetime
import numpy as np
import geopandas as gpd
import scipy.optimize as so
import scipy.constants as sc
import kremboxer.utils.greybody_utils as gbu


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
