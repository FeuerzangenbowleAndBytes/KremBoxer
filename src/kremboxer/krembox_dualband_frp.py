from pathlib import Path
import numpy as np
import json
import pandas as pd
import geopandas as gpd
import scipy.optimize as so
import scipy.constants as sc
import kremboxer.greybody_utils as gbu
import krembox_utils as kbu


def load_calibration_data(cal_params):
    """
    Loads the calibration data needed to process the raw KremBox data, including bandpasses, detector model parameters,
    and temperature sensor look up table

    :param cal_params: dictionary of calibration parameters
    :return: model_params, detect_temp_cal_data, F_MW, F_LW
    :group: krembox_dualband_frp
    """

    detect_temp_cal_file = cal_params["temp_cal_input"]
    detect_temp_cal_data = {
        'r_top': cal_params['r_top'],
        'v_top': cal_params['v_top'],
        'lookup': np.flip(np.loadtxt(detect_temp_cal_file, skiprows=1, delimiter=',', usecols=[0, 1, 2]), 0)
    }

    bp_lw_file = cal_params["LW_bandpass"]
    bp_mw_file = cal_params["MW_bandpass"]
    F_LW = np.loadtxt(bp_lw_file, delimiter=',', skiprows=1, usecols=[0, 1])
    F_MW = np.loadtxt(bp_mw_file, delimiter=',', skiprows=1, usecols=[0, 1])

    model_params = {
        "LW": cal_params["LW"],
        "MW": cal_params["MW"]
    }
    return model_params, detect_temp_cal_data, F_MW, F_LW


def compute_FRP(rad_data: pd.DataFrame, F_MW, F_LW, model_params: dict, detect_temp_cal_data: dict):
    """
    Use the dualband data to compute the target temperature, emissivity Area product, and FRP of the fire
    passing under the krembox
    :param rad_data:
    :param F_MW:
    :param F_LW:
    :param model_params:
    :param detect_temp_cal_data:
    :return:
    :group: krembox_dualband_frp
    """

    # Load raw temperature sensor data and convert it into actual temperature readings
    THs = rad_data['TH']
    vtop = detect_temp_cal_data['v_top']  # voltage at top of divided in mV
    rtop = detect_temp_cal_data['r_top']  # 100K Ohm resistor in voltage divider
    TRs = THs * rtop / (vtop - THs)  # Convert mV reading of temperature sensor into resistance
    TDs = gbu.detector_temperature_lookup(R=TRs, temp_cal_data=detect_temp_cal_data['lookup'])

    # Load the raw mV data from the dualband sensors
    V_LW = rad_data['LW-A']
    V_MW = rad_data['MW-B']

    # Invert the detector model to get the incident flux
    W_GB_LW = V_LW / model_params["LW"]["G"] + model_params["LW"]["AL"] * TDs ** model_params["LW"]["N"]
    W_GB_MW = V_MW / model_params["MW"]["G"] + model_params["MW"]["AL"] * TDs ** model_params["MW"]["N"]

    # Compute the target temperature from the ratio of the fluxes from the two bands
    ratios = W_GB_MW / W_GB_LW
    T_predict = np.zeros_like(W_GB_MW)
    for i in range(0, len(T_predict)):
        if V_LW[i] > 0 and V_MW[i] > 0:
            T_predict[i] = so.brentq(lambda Ts: gbu.GB_ratio_BP(Ts, F_MW, F_LW) - ratios[i], 200, 2000)

    # Compute emissivity * Area fraction product, fill in zero where the sensors did not detect radiation
    eA_LW = W_GB_LW / gbu.planck_model(T_predict, model_params["LW"]["A"], model_params["LW"]["N"])  # WD_LW
    eA_MW = W_GB_MW / gbu.planck_model(T_predict, model_params["MW"]["A"], model_params["MW"]["N"])  # WD_MW
    eA_LW[eA_LW == np.inf] = 0
    eA_MW[eA_MW == np.inf] = 0

    # Compute fire radiative power, two bands should agree
    FRP_LW = eA_LW * sc.Stefan_Boltzmann * T_predict ** 4
    FRP_MW = eA_MW * sc.Stefan_Boltzmann * T_predict ** 4

    # Create a copy of the radiometer dataframe and add the new data products
    rad_data_proc = rad_data.copy(deep=True)
    rad_data_proc["T"] = T_predict
    rad_data_proc["TD"] = TDs

    rad_data_proc["MW_eA"] = eA_MW
    rad_data_proc["MW_FRP"] = FRP_MW
    rad_data_proc["MW_W"] = W_GB_MW
    rad_data_proc["MW_V"] = V_MW

    rad_data_proc["LW_eA"] = eA_LW
    rad_data_proc["LW_FRP"] = FRP_LW
    rad_data_proc["LW_W"] = W_GB_LW
    rad_data_proc["LW_V"] = V_LW

    return rad_data_proc


def run_krembox_dualband_frp(params: dict):
    """

    :param params:
    :return:
    :group: krembox_dualband_frp
    """

    # Get the output root directory
    burn_name = params["burn_name"]
    output_root = Path(params["output_root"])
    dataframes_dir = output_root.joinpath("dataframes_" + burn_name)
    clean_dataframe_input = dataframes_dir.joinpath("cleaned_dataframe_"+burn_name+".geojson")

    # Load calibration data
    print("Loading calibration data...")
    with open(params["cal_input"], "r") as fp:
        cal_params = json.load(fp)
    (model_params, detect_temp_cal_data, F_MW, F_LW) = load_calibration_data(cal_params)
    print(model_params)

    # Load clean dataframe that tells us where the data is and some metadata
    print("Reading clean dataframe")
    gdf = gpd.read_file(clean_dataframe_input)

    # Loop through the clean datasets and compute FRP, record some new metadata
    print("Iterating through clean datasets")
    pstart_indices = []
    pend_indices = []
    time_starts = []
    time_stops = []
    max_FRP_indices = []
    max_FRPs = []
    max_FRP_datetimes = []
    mean_FRPs = []
    var_FRPs = []
    LW_FREs = []
    MW_FREs = []
    proc_files = []
    fire_durations = []
    over_1000FRP_durations = []
    for i, row in gdf.iterrows():
        clean_file_path = Path(row["data_directory"]).joinpath(row["clean_file"])
        print(i, clean_file_path)
        rad_data = pd.read_csv(clean_file_path, skiprows=2, index_col=False, usecols=[0, 1, 2, 3])
        rad_data_proc = compute_FRP(rad_data, F_MW, F_LW, model_params, detect_temp_cal_data)
        rad_data_proc['datetime'] = pd.to_datetime(rad_data_proc['datetime'])

        # Compute when the max FRP occurs
        max_FRP_index = rad_data_proc["MW_FRP"].argmax()
        max_FRP = rad_data_proc["MW_FRP"][max_FRP_index]
        max_FRP_datetime = rad_data_proc["datetime"][max_FRP_index]

        # Compute the FRE as the integral of the FRP over the entire dataset duration
        lw_fre = rad_data_proc["LW_FRP"].sum() * (1./ row['sample_freq'])
        mw_fre = rad_data_proc["MW_FRP"].sum() * (1. / row['sample_freq'])
        print("\tMax FRP: ", max_FRP_index, max_FRP_datetime, max_FRP, "W/m**2")
        print("\t MW FRE:", mw_fre, ', LW FRE:', lw_fre)
        max_FRP_indices.append(max_FRP_index)
        max_FRPs.append(max_FRP)
        max_FRP_datetimes.append(max_FRP_datetime)
        MW_FREs.append(mw_fre)
        LW_FREs.append(lw_fre)

        # Find time bounds for the middle 90% of the integrated FRP signal
        ind_start, ind_end = kbu.get_signal_bounds(rad_data_proc["LW_FRP"].to_numpy(), 0.05, 0.95)
        dt_start = rad_data_proc["datetime"].iloc[ind_start]
        dt_end = rad_data_proc["datetime"].iloc[ind_end]
        dt_dur = (dt_end - dt_start).seconds / 60
        print("\tDuration: {:.2f} minutes".format(dt_dur))
        pstart_indices.append(ind_start)
        pend_indices.append(ind_end)
        time_starts.append(dt_start)
        time_stops.append(dt_end)
        fire_durations.append(dt_dur)

        # Find duration of fire, as measured by how long frp > 0
        df_temp = rad_data_proc[rad_data_proc["LW_FRP"] > 1000]
        if df_temp.empty:
            duration = 0
            mean_FRPs.append(0)
            var_FRPs.append(0)
        else:
            duration = (df_temp['datetime'].iloc[-1] - df_temp['datetime'].iloc[0]).seconds / 60
            mean_FRPs.append(df_temp["LW_FRP"].mean())
            var_FRPs.append(df_temp["LW_FRP"].var())
        over_1000FRP_durations.append(duration)

        # Save the processed data to a new csv file
        proc_directory = Path(row["data_directory"]).joinpath("Processed")
        if not proc_directory.exists():
            proc_directory.mkdir()
        proc_file = Path("Processed").joinpath(Path(row["clean_file"]).stem)
        proc_files.append(str(proc_file))
        proc_file_path = Path(row["data_directory"]).joinpath(proc_file)
        rad_data_proc.to_csv(proc_file_path)

    gdf["max_FRP_index"] = max_FRP_indices
    gdf["max_FRP_datetime"] = max_FRP_datetimes
    gdf["max_FRP"] = max_FRPs
    gdf["mean_FRP"] = mean_FRPs
    gdf["var_FRP"] = var_FRPs
    gdf["MW_FRE"] = MW_FREs
    gdf["LW_FRE"] = LW_FREs
    gdf["processed_file"] = proc_files
    gdf["fire_duration"] = fire_durations
    gdf["pstart_ind"] = pstart_indices
    gdf["pend_ind"] = pend_indices
    gdf["fire_start"] = time_starts
    gdf["fire_end"] = time_stops
    gdf["over_1000FRP_duration"] = over_1000FRP_durations
    print("Saving processed dataframe in GeoJSON format: ", dataframes_dir.joinpath("processed_dataframe_"+burn_name+".geojson"))
    gdf.to_file(dataframes_dir.joinpath("processed_dataframe_"+burn_name+".geojson"), driver='GeoJSON')
    gdf.to_csv(dataframes_dir.joinpath("processed_dataframe_"+burn_name+".csv"))
    return gdf


if __name__ == '__main__':
    """
    Example of running the dual band FRP computation, mostly used for development 
    """

    params = {
        "clean_dataframe_input": "dataframes/example_cleaned_dataframe.geojson",
        "cal_input": "calibrations/example_calibration.json",
        "processed_dataframe_output": "dataframes/example_processed_dataframe"
    }

    gdf = run_krembox_dualband_frp(params)
