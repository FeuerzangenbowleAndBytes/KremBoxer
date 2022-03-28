import numpy as np
import scipy.optimize as so
import scipy.constants as sc
import json
import matplotlib.pyplot as plt
import greybody_utils as gbu


def fit_received_bandpass_energy(f, ts):
    lams = f[:,0]*10**(-6)
    dlam = lams[1] - lams[0]
    wd = np.zeros_like(ts)

    for i in range(0, len(ts)):
        w_lam = gbu.GB_lambda(lams, ts[i])
        wd[i] = np.sum(w_lam*f[:,1])*dlam

    (A, N), pcov = so.curve_fit(gbu.planck_model, ts, wd)
    return (A, N, wd)


def run_krembox_dualband_calibration(cal_params: dict):
    """
    Runs the calibration procedure for the dualband kremboxes, outputs detector model parameters and a plot of
    calibration steps
    """

    # Load the bandpass functions for the two sensors
    f_mw = np.loadtxt(cal_params["MW_bandpass"], delimiter=',', skiprows=1, usecols=[0, 1])
    f_lw = np.loadtxt(cal_params["LW_bandpass"], delimiter=',', skiprows=1, usecols=[0, 1])

    # Load the blackbody calibration data
    blackbody_cal_data = np.loadtxt(cal_params["cal_input"], delimiter=",", skiprows=1)

    # Convert the temperature sensor mV data into resistance, using known voltage divider characteristics
    t_mV = blackbody_cal_data[:, 1]
    v_top = cal_params["v_top"]                                # voltage at the top of divider in mV
    r_top = cal_params["r_top"]                              # 100kOhm resistor in voltage divider
    t_resist = t_mV * r_top / (v_top - t_mV)    # Convert mV reading into resistance of temperature sensor

    # Load actual temperaures and detector signals from calibration data
    t_actual = blackbody_cal_data[:, 0]
    v_lw = blackbody_cal_data[:, 2]
    v_mw = blackbody_cal_data[:, 3]

    # Compute the temperature of the detector from its resistance
    t_cal_data = np.loadtxt(cal_params["temp_cal_input"], skiprows=1, delimiter=",", usecols=[0,1,2])
    t_cal_data = np.flip(t_cal_data, 0)
    t_temp = gbu.detector_temperature_lookup(R=t_resist, temp_cal_data=t_cal_data)

    # Fit a polynomial for the blackbody energy received by each sensor, W~A*T**N
    # LW
    (A_MW, N_MW, wd_mw) = fit_received_bandpass_energy(f_mw, t_actual)
    (A_LW, N_LW, wd_lw) = fit_received_bandpass_energy(f_lw, t_actual)

    # Now fit the detector model with the calibration data to get G and AL
    # Note that since the detector temp barely changes during calibration, we set it to a constant 300 K during this fit
    (G_LW, AL_LW), pcov_LW = so.curve_fit(lambda T, G, AL: gbu.detector_model(T, G, AL, 300, A_LW, N_LW),
                                          t_actual, v_lw)
    # TODO: Left out the 0 at the beginning of MW data, caused optimizer to crash, handle better
    (G_MW, AL_MW), pcov_MW = so.curve_fit(lambda T, G, AL: gbu.detector_model(T, G, AL, 300, A_MW, N_MW),
                                          t_actual[1:], v_mw[1:], maxfev=1000)
    print("Calibration values:")
    print("LW: N_LW=", N_LW, ", A_LW=", A_LW, ", G_LW=", G_LW, ", AL_LW=", AL_LW)
    print("MW: N_MW=", N_MW, ", A_MW=", A_MW, ", G_MW=", G_MW, ", AL_MW=", AL_MW)

    ###############################################
    # End of calibration, now see how well the
    # computation of target temp reproduces the
    # known calibration data
    ###############################################

    # Compute the temperature of the target from the ratio of the incident power
    W_GB_LW = v_lw / G_LW + AL_LW * t_temp ** N_LW
    W_GB_MW = v_mw / G_MW + AL_MW * t_temp ** N_MW
    ratios = W_GB_MW / W_GB_LW
    t_predict = np.zeros_like(t_actual)
    for i in range(0, len(t_actual)):
        if v_lw[i] > 0 and v_mw[i] > 0:
            t_predict[i] = so.brentq(lambda Ts: gbu.GB_ratio_BP(Ts, f_mw, f_lw) - ratios[i], 200, 2000)

    # Compute eA from actual and predicted blackbody power
    eA_LW = W_GB_LW / gbu.planck_model(t_predict, A_LW, N_LW)  # WD_LW
    eA_MW = W_GB_MW / gbu.planck_model(t_predict, A_MW, N_MW)  # WD_MW
    eA_LW[eA_LW == np.inf] = 0
    eA_MW[eA_MW == np.inf] = 0

    # Compute FRP from eA and T
    FRP_LW = eA_LW * sc.Stefan_Boltzmann * t_predict ** 4
    FRP_MW = eA_MW * sc.Stefan_Boltzmann * t_predict ** 4

    #################################
    # Save the calibration data
    #################################

    cal_dict = {
        "cal_input": cal_params["cal_input"],
        "temp_cal_input": cal_params["temp_cal_input"],
        "plot_output": cal_params["plot_output"],
        "LW_bandpass": cal_params["LW_bandpass"],
        "MW_bandpass": cal_params["MW_bandpass"],
        "r_top": cal_params["r_top"],
        "v_top": cal_params["v_top"],
        "LW": {
            "N": N_LW,
            "A": A_LW,
            "G": G_LW,
            "AL": AL_LW
        },
        "MW": {
            "N": N_MW,
            "A": A_MW,
            "G": G_MW,
            "AL": AL_MW
        }
        # "N_LW": N_LW,
        # "A_LW": A_LW,
        # "G_LW": G_LW,
        # "AL_LW": AL_LW,
        # "N_MW": N_MW,
        # "A_MW": A_MW,
        # "G_MW": G_MW,
        # "AL_MW": AL_MW
    }

    with open(cal_params["cal_output"], 'w') as file:
        json.dump(cal_dict, file, indent=0)
    print("Saved calibration data to: ", cal_params["cal_output"])

    ############################################
    # Move on to plotting
    ############################################

    # Plot calibration data and save to file
    fig, axs = plt.subplots(5, 2, figsize=(8, 10))

    # Plot the bandpasses
    axs[0,0].plot(f_lw[:,0], f_lw[:,1], label="F_LW")
    axs[0,0].plot(f_mw[:,0], f_mw[:,1], label="F_MW")
    axs[0, 0].legend()
    axs[0, 0].set_xlim(0, 20)
    axs[0, 0].set_xlabel("Wavelength [um]")
    axs[0, 0].set_ylabel("Transmission [%]")
    axs[0, 0].set_title("Bandpass Functions for 2 Band Radiometers")

    # Plot the blackbody curves for the calibration target temperatures
    wavelengths = f_lw[:, 0] * 10 ** (-6)
    for T in t_actual:
        axs[1, 0].plot(wavelengths, gbu.GB_lambda(wavelengths, T), label="T=" + str(T))
    axs[1, 0].axvline(x=0.1e-6, lw=1, color='black')
    axs[1, 0].axvline(x=5.5e-6, lw=1, color='black')
    axs[1, 0].axvline(x=8e-6, lw=1, color='black')
    axs[1, 0].axvline(x=14e-6, lw=1, color='black')
    axs[1, 0].set_xlabel("Wavelength [m]")
    axs[1, 0].set_xlim(0, 20 * 10 ** (-6))
    axs[1, 0].set_ylabel("Planck [W/m^3]")

    # Plot received energy fit
    axs[2, 0].plot(t_actual, wd_lw, '.', label="W_LW")
    axs[2, 0].plot(t_actual, wd_mw, '.', label="W_MW")
    axs[2, 0].plot(t_actual, gbu.planck_model(t_actual, A_LW, N_LW), '--',
                   label="fit LW: A={:.2E}, N={:.2f}".format(A_LW, N_LW))
    axs[2, 0].plot(t_actual, gbu.planck_model(t_actual, A_MW, N_MW), '--',
                   label="fit MW: A={:.2E}, N={:.2f}".format(A_MW, N_MW))
    axs[2, 0].set_xlabel("Temperature [K]")
    axs[2, 0].set_ylabel("Received Power [W/m^2]")
    axs[2, 0].legend()

    # Plot detector temperature
    axs[0, 1].plot(t_actual, t_temp, label="TD")
    axs[0, 1].set_xlabel("Temperature [K]")
    axs[0, 1].set_ylabel("TD [K]")
    axs[0, 1].set_title("Detector Temp")
    axs[0, 1].legend()

    # Plot LW, MW raw data and fits
    axs[3, 0].plot(t_actual, v_lw, '.', label="V_LW")
    axs[3, 0].plot(t_actual, v_mw, '.', label="V_MW")
    axs[3, 0].set_xlabel("Temperature [K]")
    axs[3, 0].set_ylabel("V sensor")
    axs[3, 0].plot(t_actual, gbu.detector_model(t_actual, G_LW, AL_LW, 300, A_LW, N_LW), '--', label="LW fit")
    axs[3, 0].plot(t_actual, gbu.detector_model(t_actual, G_MW, AL_MW, 300, A_MW, N_MW), '--', label="MW fit")
    axs[3, 0].legend()

    # Compute and plot energy from targets based on the calibrated model (sanity check)
    axs[1, 1].plot(t_actual, W_GB_LW, label="W_GB_LW")
    axs[1, 1].plot(t_actual, W_GB_MW, label="W_GB_MW")
    axs[1, 1].set_xlabel("Temperature [K]")
    axs[1, 1].set_ylabel("W_GB [W/m^2]")
    axs[1, 1].legend()

    # Compare predicted and measured ratios (computed Ratios Theory in two slightly different ways as sanity check)
    axs[2, 1].plot(t_actual, wd_mw / wd_lw, '--', label="Ratios Theory")
    ratio_predicted = []
    for T in t_actual:
        ratio_predicted.append(gbu.GB_ratio_BP(T, f_mw, f_lw))
    axs[2, 1].plot(t_actual, ratio_predicted, '-*', label="Ratios Theory")
    axs[2, 1].plot(t_actual, W_GB_MW / W_GB_LW, label="Ratios Actual")
    axs[2, 1].legend()

    axs[3, 1].plot(t_actual, t_actual, label="T Actual")
    axs[3, 1].plot(t_actual, t_predict, label="T Pred")
    axs[3, 1].set_xlabel("T actual")
    axs[3, 1].set_ylabel("T predict")
    axs[3, 1].set_title("Source Temp [K]")
    axs[3, 1].legend()

    axs[4, 0].plot(t_actual, eA_LW, label="LW")
    axs[4, 0].plot(t_actual, eA_MW, label="MW")
    axs[4, 0].set_title("eA")
    axs[4, 0].set_xlabel("T actual [K]")
    axs[4, 0].set_ylabel("eA")
    axs[4, 0].legend()

    axs[4, 1].plot(t_actual, FRP_LW, label="LW")
    axs[4, 1].plot(t_actual, FRP_MW, label="MW")
    axs[4, 1].set_xlabel("T actual [K]")
    axs[4, 1].set_ylabel("FRP [W/m**2]")
    axs[4, 1].set_title("FRP")
    axs[4, 1].legend()

    fig.suptitle("Radiometer Calibration")
    plt.tight_layout()
    plt.savefig(cal_params["plot_output"])
    print("Saved calibration plot to: ", cal_params["plot_output"])

    if cal_params["show_plot"]:
        plt.show()

    return cal_dict


if __name__ == '__main__':
    """
    Example of running the dual band calibration, primarily used for development testing
    """

    Cal_params_outfile = "calibrations/example_calibration.json"
    F_LW_file = "/home/jepaki/PycharmProjects/OsceolaAnalysis/data/clean/DC-6073_W1_8-14Si.csv"
    F_MW_file = "/home/jepaki/PycharmProjects/OsceolaAnalysis/data/clean/DC-6216_u1_Saph_longwave.csv"
    cal_data_file = "/home/jepaki/PycharmProjects/OsceolaAnalysis/data/clean/unit11_calibration_data.csv"
    detect_temp_cal_file = "/home/jepaki/PycharmProjects/OsceolaAnalysis/data/clean/temperature_sensor_calibration.csv"
    show_plots = True
    plot_output = "plots/example_calibration_plot.png"

    cal_params = {
        "cal_output": Cal_params_outfile,
        "LW_bandpass": F_LW_file,
        "MW_bandpass": F_MW_file,
        "cal_input": cal_data_file,
        "temp_cal_input": detect_temp_cal_file,
        "show_plot": show_plots,
        "plot_output": plot_output,
        "v_top": 3300,  # voltage at the top of divider in mV
        "r_top": 100000  # 100kOhm resistor in voltage divider
    }

    cal_dict = run_krembox_dualband_calibration(cal_params)
