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
    processed_data_dir = archive_root.joinpath("Processed", "Fiveband")
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
        data_proc_df['DATETIME'] = pd.to_datetime(data_proc_df['DATETIME'])

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

        # Find duration of fire, as measured by how long frp > 1000
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
        print("Processed data saved to: ", proc_data_path)

        fig, axs = plt.subplots(4, 1, figsize=(8, 12))
        axs[0].plot(data_proc_df['DATETIME'], data_proc_df['LW_FRP'], label='LW')
        axs[0].plot(data_proc_df['DATETIME'], data_proc_df['MW_FRP'], label='MW')
        axs[0].set_ylabel('FRP [W/m^2]')
        axs[0].legend()

        axs[1].plot(data_proc_df['DATETIME'], data_proc_df['LW_eA'], label='LW')
        axs[1].plot(data_proc_df['DATETIME'], data_proc_df['MW_eA'], label='MW')
        axs[1].set_ylabel('emissivity-Area product')
        axs[1].legend()

        axs[2].plot(data_proc_df['DATETIME'], data_proc_df['T'], label='Target Temperature')
        axs[2].plot(data_proc_df['DATETIME'], data_proc_df['TD'], label='Device Temperature')
        axs[2].set_ylabel('Temperature [K]')
        axs[2].legend()

        axs[3].plot(data_proc_df['DATETIME'], data_proc_df['LW'], label='LW')
        axs[3].plot(data_proc_df['DATETIME'], data_proc_df['MW'], label='MW')
        axs[3].set_ylabel('Raw Sensor Readings')
        axs[3].set_xlabel('Time')
        axs[3].legend()
        plt.tight_layout()
        plt.savefig(processed_data_dir / row['DATAFILE'].replace(".csv", ".png"))

    fiveband_gdf["max_FRP_index"] = max_FRP_indices
    fiveband_gdf["max_FRP_datetime"] = max_FRP_datetimes
    fiveband_gdf["max_FRP"] = max_FRPs
    fiveband_gdf["mean_FRP"] = mean_FRPs
    fiveband_gdf["var_FRP"] = var_FRPs
    fiveband_gdf["MW_FRE"] = MW_FREs
    fiveband_gdf["LW_FRE"] = LW_FREs
    fiveband_gdf["fire_duration"] = fire_durations
    fiveband_gdf["pstart_ind"] = pstart_indices
    fiveband_gdf["pend_ind"] = pend_indices
    fiveband_gdf["fire_start"] = time_starts
    fiveband_gdf["fire_end"] = time_stops
    fiveband_gdf["over_1000FRP_duration"] = over_1000FRP_durations
    fiveband_gdf["PROCESSING_LEVEL"] = processing_levels

    #fiveband_gdf = cu.associate_data2burnplot(fiveband_gdf, bu_gdf)

    fiveband_gdf.to_file(archive_root.joinpath("Fiveband_processed_metadata_raw_location.geojson"), driver='GeoJSON')
    fiveband_gdf.to_csv(archive_root.joinpath("Fiveband_processed_metadata_raw_location.csv"), index=False)

    if "fuel_plots" in data_processing_params:
        # Overwrites the radiometer location with the matching fuel plot location (assume that the fuel plot location is more accurate)
        fuel_plots_file = Path(data_processing_params["fuel_plots"])
        if fuel_plots_file.is_file() and fuel_plots_file.suffix == ".geojson":
            fp_gdf = gpd.read_file(fuel_plots_file, driver='GeoJSON')
        elif fuel_plots_file.is_file() and fuel_plots_file.suffix == ".csv":
            fp_df = pd.read_csv(fuel_plots_file)
            fp_gdf = gpd.GeoDataFrame(fp_df, geometry=gpd.points_from_xy(fp_df.Longitude, fp_df.Latitude), crs="EPSG:4326")
        else:
            raise ValueError(f"Could not read fuel plot data from {fuel_plots_file}")
        fb_assoc_gdf, fb_unassoc_gdf = cu.associate_data2fuelplot(fiveband_gdf, fp_gdf)
        if len(fb_unassoc_gdf) > 0:
            print("Warning! Unable to associate these radiometers with a fuel plot:", fb_unassoc_gdf)
            print(f'{len(fb_unassoc_gdf)} / {len(fb_assoc_gdf)} radiometers did not match with a fuel plot')
        fb_assoc_gdf.to_file(archive_root.joinpath("Fiveband_processed_metadata.geojson"), driver='GeoJSON')
        fb_assoc_gdf.to_csv(archive_root.joinpath("Fiveband_processed_metadata.csv"), index=False)
