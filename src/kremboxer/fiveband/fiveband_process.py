from pathlib import Path
import numpy as np
import json
import datetime
import pandas as pd
import geopandas as gpd
import scipy.optimize as so
import scipy.constants as sc
from matplotlib import pyplot as plt

import kremboxer.utils.greybody_utils as gbu
import kremboxer.utils.common_utils as cu


def compute_fiveband_FRP(rad_data: pd.DataFrame, F_MW, F_LW, F_395, F_1095, F_WIDE, model_params: dict, detect_temp_cal_data: dict):
    # Load raw temperature sensor data and convert it into actual temperature readings
    # TODO: Use both TH1 and TH2 for the different sensors
    THs = rad_data['TH1']
    vtop = detect_temp_cal_data['v_top']  # voltage at top of divided in mV
    rtop = detect_temp_cal_data['r_top']  # 100K Ohm resistor in voltage divider
    TRs = THs * rtop / (vtop - THs)  # Convert mV reading of temperature sensor into resistance
    TDs = gbu.detector_temperature_lookup(R=TRs, temp_cal_data=detect_temp_cal_data['lookup'])

    # Load the raw mV data from the sensors
    V_LW = rad_data['LW']
    V_MW = rad_data['MW']
    V_395 = rad_data['3.95']
    V_1095 = rad_data['10.95']
    V_WIDE = rad_data['WIDE']

    # Invert the detector model to get the incident flux
    W_GB_LW = V_LW / model_params["LW"]["G"] + model_params["LW"]["AL"] * TDs ** model_params["LW"]["N"]
    W_GB_MW = V_MW / model_params["MW"]["G"] + model_params["MW"]["AL"] * TDs ** model_params["MW"]["N"]
    W_GB_395 = V_MW / model_params["3.95"]["G"] + model_params["3.95"]["AL"] * TDs ** model_params["3.95"]["N"]
    W_GB_1095 = V_MW / model_params["10.95"]["G"] + model_params["10.95"]["AL"] * TDs ** model_params["10.95"]["N"]
    W_GB_WIDE = V_WIDE / model_params["WIDE"]["G"] + model_params["WIDE"]["AL"] * TDs ** model_params["WIDE"]["N"]

    # Compute the target temperature from the ratio of the fluxes from the two bands
    print("Trying to find T_predict")
    ratios = W_GB_MW / W_GB_LW
    ratios_narrow = W_GB_395 / W_GB_1095
    fig, axs = plt.subplots(3, 2)
    axs[0,0].plot(W_GB_LW, label="LW")
    axs[0,1].plot(W_GB_1095, label="10.95")
    axs[0,0].plot(W_GB_MW, label="MW")
    axs[0,1].plot(W_GB_395, label="3.95")
    axs[1,0].plot(ratios)
    axs[1,1].plot(ratios_narrow)
    axs[0,0].legend()
    axs[0,1].legend()
    cand_T = np.arange(200, 2000, 100)
    cand_ratios = [gbu.GB_ratio_BP(x, F_MW, F_LW) for x in cand_T]
    cand_ratios_narrow = [gbu.GB_ratio_BP(x, F_395, F_1095) for x in cand_T]
    axs[2,0].plot(cand_T, cand_ratios)
    axs[2,1].plot(cand_T, cand_ratios_narrow)
    plt.show()

    T_predict = np.zeros_like(W_GB_MW)
    T_predict_narrow = np.zeros_like(W_GB_395)
    for i in range(0, len(T_predict)):
        if V_LW[i] > 0 and V_MW[i] > 0:
            T_predict[i] = so.brentq(lambda Ts: gbu.GB_ratio_BP(Ts, F_MW, F_LW) - ratios[i], 200, 2000)
        if W_GB_395[i] > 0 and W_GB_1095[i] > 0:
            try:
                T_predict_narrow[i] = so.brentq(lambda Ts: gbu.GB_ratio_BP(Ts, F_395, F_1095) - ratios_narrow[i], 200, 2000)
            except:
                print(f"Unable to compute target temperature for 3.95/10.95 ratio: {ratios_narrow[i]}")
    print("Done")
    fig, axs = plt.subplots(1,1)
    axs.plot(T_predict, label="MW/LW")
    axs.plot(T_predict_narrow, label="3.95/10.95")
    axs.legend()
    plt.show()
    exit()

    # Compute emissivity * Area fraction product, fill in zero where the sensors did not detect radiation
    eA_LW = W_GB_LW / gbu.planck_model(T_predict, model_params["LW"]["A"], model_params["LW"]["N"])  # WD_LW
    eA_MW = W_GB_MW / gbu.planck_model(T_predict, model_params["MW"]["A"], model_params["MW"]["N"])  # WD_MW
    eA_LW[eA_LW == np.inf] = 0
    eA_MW[eA_MW == np.inf] = 0

    # Compute fire radiative power, two bands should agree
    FRP_LW = eA_LW * sc.Stefan_Boltzmann * T_predict ** 4
    FRP_MW = eA_MW * sc.Stefan_Boltzmann * T_predict ** 4
    FRP_WIDE = W_GB_WIDE / model_params["WIDE"]["BandpassFraction"]

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

    rad_data_proc["WIDE_FRP"] = FRP_WIDE

    return rad_data_proc


def load_fiveband_calibration_data(fiveband_calibration_path: Path):
    """
    Loads the calibration data needed to process the raw KremBox data, including bandpasses, detector model parameters,
    and temperature sensor look up table

    Parameters
    ----------
    fiveband_calibration_path: Path
        Location of json format calibration data

    Returns
    -------
    model_params, detect_temp_cal_data, F_MW, F_LW: dictionaries of calibration model parameters and bandpasses
    """

    print(fiveband_calibration_path)
    with open(fiveband_calibration_path) as json_data_file:
        cal_params = json.load(json_data_file)

    cal_dir = fiveband_calibration_path.parent
    detect_temp_cal_file = cal_dir.joinpath(cal_params["temp_cal_input"])
    detect_temp_cal_data = {
        'r_top': cal_params['r_top'],
        'v_top': cal_params['v_top'],
        'lookup': np.flip(np.loadtxt(detect_temp_cal_file, skiprows=1, delimiter=',', usecols=[0, 1, 2]), 0)
    }

    bp_lw_file = cal_dir.joinpath(cal_params["bands"]["LW"]["bandpass"])
    bp_mw_file = cal_dir.joinpath(cal_params["bands"]["MW"]["bandpass"])
    bp_395_file = cal_dir.joinpath(cal_params["bands"]["3.95"]["bandpass"])
    bp_1095_file = cal_dir.joinpath(cal_params["bands"]["10.95"]["bandpass"])
    bp_wide_file = cal_dir.joinpath(cal_params["bands"]["WIDE"]["bandpass"])
    F_LW = np.loadtxt(bp_lw_file, delimiter=',', skiprows=1, usecols=[0, 1])
    F_MW = np.loadtxt(bp_mw_file, delimiter=',', skiprows=1, usecols=[0, 1])
    F_395 = np.loadtxt(bp_395_file, delimiter=',', skiprows=1, usecols=[0, 1])
    F_1095 = np.loadtxt(bp_1095_file, delimiter=',', skiprows=1, usecols=[0, 1])
    F_WIDE = np.loadtxt(bp_wide_file, delimiter=',', skiprows=1, usecols=[0, 1])

    model_params = {
        "LW": cal_params["bands"]["LW"],
        "MW": cal_params["bands"]["MW"],
        "3.95": cal_params["bands"]["3.95"],
        "10.95": cal_params["bands"]["10.95"],
        "WIDE": cal_params["bands"]["WIDE"]
    }
    return model_params, detect_temp_cal_data, F_MW, F_LW, F_395, F_1095, F_WIDE

def process_fiveband_datasets(fiveband_raw_metadata: Path, data_processing_params: dict):
    """
    Iterates through the raw UFM datasets and computes FRP traces

    Parameters
    ----------
    fiveband_raw_metadata : path to a GeoJSON file containing the metadata for the raw fiveband datasets
    data_processing_params :

    Returns
    -------

    """
    # Read metadata for dualband datasets, return immediately if there are none
    fiveband_gdf = gpd.read_file(fiveband_raw_metadata, engine="fiona")

    if len(fiveband_gdf) == 0:
        print("No dualband datasets to process")
        return

    # Load dataframe of burn units
    #bu_gdf = gpd.read_file(Path(data_processing_params['burn_units']), engine="fiona")
    #bu_gdf.to_crs(fiveband_gdf.crs, inplace=True)

    # Load calibration parameters
    fiveband_calibration_path = Path(data_processing_params["fiveband_calibration_file"])
    model_params, detect_temp_cal_data, F_MW, F_LW, F_395, F_1095, F_WIDE = load_fiveband_calibration_data(fiveband_calibration_path)

    print(model_params)

    # Filter the datasets to the dates of interest and that are longer than specified cutoff.
    # Used to eliminate spurious datasets from someone turning the device on and off quickly
    initial_num_fiveband_datasets = len(fiveband_gdf)
    target_dates = [datetime.datetime.fromisoformat(x).date() for x in data_processing_params['burn_dates']]
    mask = []
    for i, row in fiveband_gdf.iterrows():
        record_date = datetime.datetime.fromisoformat(str(row['DATETIME_START']))
        if record_date.date() in target_dates and row['DURATION'] > data_processing_params['duration_cutoff']:
            mask.append(True)
        else:
            mask.append(False)
    fiveband_gdf = fiveband_gdf[mask].copy(deep=True)
    filtered_num_fiveband_datasets = len(fiveband_gdf)
    print(f'Removed {initial_num_fiveband_datasets-filtered_num_fiveband_datasets} out of {initial_num_fiveband_datasets} fiveband datasets due to being on the wrong date or less than {data_processing_params["duration_cutoff"]} seconds long')

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
    WIDE_FREs = []
    fire_durations = []
    over_1000FRP_durations = []
    processing_levels = []
    burn_units = []
    for i, row in fiveband_gdf.iterrows():
        print(i, row['DATAFILE'])
        data_path = archive_root.joinpath(row['PROCESSING_LEVEL'], row['SENSOR'], row['DATAFILE'])
        data_df = pd.read_csv(data_path)
        data_proc_df = compute_fiveband_FRP(data_df, F_MW, F_LW, F_395, F_1095, F_WIDE, model_params, detect_temp_cal_data)

        #data_proc_df['DATETIME'] = pd.to_datetime(data_proc_df['DATETIME'])