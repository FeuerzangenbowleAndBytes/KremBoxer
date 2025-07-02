from pathlib import Path
import numpy as np
import json
import datetime
import pandas as pd
import geopandas as gpd
import scipy.optimize as so
import scipy.constants as sc
import kremboxer.utils.greybody_utils as gbu
import kremboxer.utils.common_utils as cu


def load_dualband_calibration_data(dualband_calibration_path: Path):
    """
    Loads the calibration data needed to process the raw KremBox data, including bandpasses, detector model parameters,
    and temperature sensor look up table

    Parameters
    ----------
    dualband_calibration_path: Path
        Location of json format calibration data

    Returns
    -------
    model_params, detect_temp_cal_data, F_MW, F_LW: dictionaries of calibration model parameters and bandpasses
    """

    with open(dualband_calibration_path) as json_data_file:
        cal_params = json.load(json_data_file)

    cal_dir = dualband_calibration_path.parent
    detect_temp_cal_file = cal_dir.joinpath(cal_params["temp_cal_input"])
    detect_temp_cal_data = {
        'r_top': cal_params['r_top'],
        'v_top': cal_params['v_top'],
        'lookup': np.flip(np.loadtxt(detect_temp_cal_file, skiprows=1, delimiter=',', usecols=[0, 1, 2]), 0)
    }

    bp_lw_file = cal_dir.joinpath(cal_params["LW_bandpass"])
    bp_mw_file = cal_dir.joinpath(cal_params["MW_bandpass"])
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


def process_dualband_datasets(dualband_raw_metadata: Path, data_processing_params: dict):

    # Read metadata for dualband datasets, return immediately if there are none
    db_gdf = gpd.read_file(dualband_raw_metadata, engine="fiona")
    print(dualband_raw_metadata)

    if len(db_gdf) == 0:
        print("No dualband datasets to process")
        return

    # Load dataframe of burn units
    bu_gdf = gpd.read_file(Path(data_processing_params['burn_units']), engine="fiona")
    bu_gdf.to_crs(db_gdf.crs, inplace=True)

    # Load calibration parameters
    dualband_calibration_path = Path(data_processing_params["dualband_calibration_file"])
    (model_params, detect_temp_cal_data, F_MW, F_LW) = load_dualband_calibration_data(dualband_calibration_path)

    # Filter the datasets to the dates of interest and that are longer than specified cutoff.
    # Used to eliminate spurious datasets from someone turning the device on and off quickly
    target_dates = [datetime.datetime.fromisoformat(x).date() for x in data_processing_params['burn_dates']]
    mask = []
    for i, row in db_gdf.iterrows():
        record_date = datetime.datetime.fromisoformat(str(row['DATETIME_START']))
        if record_date.date() in target_dates and row['DURATION'] > data_processing_params['duration_cutoff']:
            mask.append(True)
        else:
            mask.append(False)
    db_gdf = db_gdf[mask].copy(deep=True)

    # Apply calibration to each dataset to compute FRP and other derived parameters
    archive_root = Path(data_processing_params["archive_dir"])
    processed_data_dir = archive_root.joinpath("Processed", "Dualband")
    processed_data_dir.mkdir(exist_ok=True, parents=True)
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
    fire_durations = []
    over_1000FRP_durations = []
    processing_levels = []
    burn_units = []
    for i, row in db_gdf.iterrows():
        data_path = archive_root.joinpath(row['PROCESSING_LEVEL'], row['SENSOR'], row['DATAFILE'])
        data_df = pd.read_csv(data_path)
        data_proc_df = compute_FRP(data_df, F_MW, F_LW, model_params, detect_temp_cal_data)
        data_proc_df['DATETIME'] = pd.to_datetime(data_proc_df['DATETIME'])
        print(data_df.keys(), len(data_df))
        print(data_proc_df.keys(), len(data_proc_df))

        # Compute when the max FRP occurs
        max_FRP_index = data_proc_df["MW_FRP"].argmax()
        max_FRP = data_proc_df["MW_FRP"][max_FRP_index]
        max_FRP_datetime = data_proc_df['DATETIME'][max_FRP_index]

        # Compute the FRE as the integral of the FRP over the entire dataset duration
        lw_fre = data_proc_df["LW_FRP"].sum() * (1. / row['SAMPLE-RATE(Hz)'])
        mw_fre = data_proc_df["MW_FRP"].sum() * (1. / row['SAMPLE-RATE(Hz)'])
        print("\tMax FRP: ", max_FRP_index, max_FRP_datetime, max_FRP, "W/m**2")
        print("\t MW FRE:", mw_fre, ', LW FRE:', lw_fre)
        max_FRP_indices.append(max_FRP_index)
        max_FRPs.append(max_FRP)
        max_FRP_datetimes.append(max_FRP_datetime)
        MW_FREs.append(mw_fre)
        LW_FREs.append(lw_fre)

        # Find time bounds for the middle 90% of the integrated FRP signal
        ind_start, ind_end = cu.get_signal_bounds(data_proc_df["LW_FRP"].to_numpy(), 0.05, 0.95)
        dt_start = data_proc_df['DATETIME'].iloc[ind_start]
        dt_end = data_proc_df['DATETIME'].iloc[ind_end]
        dt_dur = (dt_end - dt_start).seconds / 60
        print("\tDuration: {:.2f} minutes".format(dt_dur))
        pstart_indices.append(ind_start)
        pend_indices.append(ind_end)
        time_starts.append(dt_start)
        time_stops.append(dt_end)
        fire_durations.append(dt_dur)

        # Find duration of fire, as measured by how long frp > 0
        df_temp = data_proc_df[data_proc_df["LW_FRP"] > 1000]
        if df_temp.empty:
            duration = 0
            mean_FRPs.append(0)
            var_FRPs.append(0)
        else:
            duration = (df_temp['DATETIME'].iloc[-1] - df_temp['DATETIME'].iloc[0]).seconds / 60
            mean_FRPs.append(df_temp["LW_FRP"].mean())
            var_FRPs.append(df_temp["LW_FRP"].var())
        over_1000FRP_durations.append(duration)

        # Save the processed data to a new csv file
        proc_data_path = processed_data_dir.joinpath(row['DATAFILE'])
        data_proc_df.to_csv(proc_data_path)
        processing_levels.append("Processed")

    db_gdf["max_FRP_index"] = max_FRP_indices
    db_gdf["max_FRP_datetime"] = max_FRP_datetimes
    db_gdf["max_FRP"] = max_FRPs
    db_gdf["mean_FRP"] = mean_FRPs
    db_gdf["var_FRP"] = var_FRPs
    db_gdf["MW_FRE"] = MW_FREs
    db_gdf["LW_FRE"] = LW_FREs
    db_gdf["fire_duration"] = fire_durations
    db_gdf["pstart_ind"] = pstart_indices
    db_gdf["pend_ind"] = pend_indices
    db_gdf["fire_start"] = time_starts
    db_gdf["fire_end"] = time_stops
    db_gdf["over_1000FRP_duration"] = over_1000FRP_durations
    db_gdf["PROCESSING_LEVEL"] = processing_levels

    db_gdf = cu.associate_data2burnplot(db_gdf, bu_gdf)

    db_gdf.to_file(archive_root.joinpath("Dualband_processed_metadata.geojson"), driver='GeoJSON')
    db_gdf.to_csv(archive_root.joinpath("Dualband_processed_metadata.csv"), index=False)
