import numpy as np
import scipy.constants as sc
import scipy.optimize as so
import math
import matplotlib.pyplot as plt


def planck_model(T, A, N):
    return A*T**N


def detector_model(T, G, AL, TD, A, N):
    return G*(A*T**N-AL*TD**N)


def GB_lambda(lams, T, emissivity=1):
    A = 2*math.pi*emissivity*sc.Planck*sc.c*sc.c
    B = sc.Planck*sc.c/(lams*sc.Boltzmann*T)
    return A/(lams**5*(np.exp(B)-1))


def GB_lambda_window(lam1, lam2, T, emissivity=1):
    dlam = 1e-9
    lams = np.arange(lam1, lam2, dlam) # Integrate with 1nm grid
    rads = GB_lambda(lams, T, emissivity)
    return np.sum(rads)*dlam


def GB_ratio(T, lam1, lam2, lam3, lam4):
    return GB_lambda_window(lam1, lam2, T) / GB_lambda_window(lam3, lam4, T)


def GB_ratio_BP(T, F1, F2):
    lams1 = F1[:,0]*10**(-6)
    dlam1 = lams1[1]-lams1[0]
    W1 = np.sum(GB_lambda(lams1, T) * F1[:, 1])*dlam1

    lams2 = F2[:,0]*10**(-6)
    dlam2 = lams2[1]-lams2[0]
    W2 = np.sum(GB_lambda(lams2, T) * F2[:, 1])*dlam2
    return W1 / W2


def stefan_boltzmann(T, emissivity=1):
    return emissivity*sc.Stefan_Boltzmann*T**4


def detector_temperature_lookup(R, temp_cal_data):
    """
    Converts a resistance reading into a temperature measurement
    :param R: - Resistance of temperature sensor, Ohms
    :param temp_cal_data: - Lookup table that translates Resistance readings to temperature measurements. Columns are [T Celcius, T Kelvin, Resistance]
    :return: Td, the temperature of the sensor
    """

    index = np.searchsorted(temp_cal_data[:,2], R)

    w = (R - temp_cal_data[index - 1, 2]) / (temp_cal_data[index, 2] - temp_cal_data[index - 1, 2])
    Td = (1-w)*temp_cal_data[index-1, 1] + (w)*temp_cal_data[index, 1]
    #print(R, index, temp_cal_data[index-1, 2], temp_cal_data[index,2], temp_cal_data[index-1, 1], temp_cal_data[index,1], w, Td)
    return Td


if __name__ == '__main__':
    """
    This is just some testing code to verify the above functions and test some processing 
    """
    print(sc.c, sc.Planck, sc.Boltzmann, sc.Stefan_Boltzmann)
    Ts = np.arange(300, 1500, 100)
    fig, axs = plt.subplots(4,1,figsize=(5,8))
    axs[0].plot(Ts, stefan_boltzmann(Ts))

    lams = np.linspace(100e-9, 15e-6, 100)
    dlam = lams[1]-lams[0]

    lam1 = 2000e-9
    lam2 = 2700e-9

    for T in [800, 1000, 1200]:
        axs[1].plot(lams, GB_lambda(lams, T), label=str(T)+"K")
        axs[2].scatter([T], [GB_lambda_window(lam1, lam2, T)], label=str(T)+"K")
        print(T, stefan_boltzmann(T), np.sum(GB_lambda(lams, T))*dlam)
    axs[1].axvline(x=lam1, color='black')
    axs[1].axvline(x=lam2, color='black')
    axs[1].legend()
    axs[2].legend(loc=2)

    Ts = np.arange(300, 1500, 100)
    lam1 = 2e-6
    lam2 = 5e-6
    lam3 = 8e-6
    lam4 = 14e-6

    ratios = []
    for T in Ts:
        ratios.append(GB_ratio(T, lam1, lam2, lam3, lam4))

    target_ratio = 3.7
    target_temp = 800
    target_temp = so.brentq(lambda Ts: GB_ratio(Ts, lam1, lam2, lam3, lam4) - target_ratio, 300, 1500)

    axs[3].plot(Ts, ratios)
    axs[3].axhline(y=target_ratio, color='black')
    axs[3].axvline(x=target_temp, color='black')
    print('ratio= ', target_ratio, ', T= ', target_temp)

    plt.tight_layout()


    datafile = "/home/jepaki/Projects/Osceola/020422_Osceola_Radiometers_DualBand/Clean/DATALOG_16_2022-02-04T16:21:39+00:00.csv"

    data = np.loadtxt(datafile, skiprows=3, delimiter=',', usecols=[0,1,2])

    temp_cal_file = "/home/jepaki/PycharmProjects/OsceolaAnalysis/data/clean/temperature_sensor_calibration.csv"
    temp_data = np.loadtxt(temp_cal_file, skiprows=1, delimiter=',', usecols=[0,1,2])
    temp_data = np.flip(temp_data, 0)

    print(detector_temperature_lookup(R=[1200, 1000], temp_cal_data=temp_data))

    F_MW = 1.34e-13
    N_MW = 5.4
    F_LW = 1.34e-4
    N_LW = 2.38

    # LW: [0.37709458 1.25732457]
    # MW: [6.55094622e-13 5.12887734e+00]

    # LW: [1.36073729e-04 2.38240734e+00]
    # MW: [4.31109616e-14 5.53486272e+00]
    F_MW = 4.31109616e-14
    N_MW = 5.53486272e+00
    F_LW = 1.36073729e-04
    N_LW = 2.38240734e+00

    print(data[0:3, :])
    print(temp_data[0:3, :])

    t_min = 6000
    t_max = 7500
    fig, axs = plt.subplots(3, 2, figsize=(6, 6))
    axs[0,0].plot(data[:, 0], label="TH")
    #axs[0].plot(data[:, 1], label="V_1")
    #axs[0].plot(data[:, 2], label="V_2")
    axs[0,0].set_ylabel("Raw Data")
    axs[0,0].set_title("TH [mV]")
    axs[0,0].legend()
    axs[0,0].set_xlim(t_min, t_max)

    axs[0,1].plot(data[:,1], label="LW-A")
    axs[0,1].plot(data[:,2], label="MW-B")
    axs[0,1].set_title("LW-A, MW-B")
    axs[0,1].legend()
    axs[0,1].set_xlim(t_min, t_max)

    T_mV = data[:,0]
    vtop = 3300 # voltage at top of divded in mV
    rtop = 100000 # 100K Ohm resistor in voltage divider
    T_R = T_mV*rtop / (vtop - T_mV)
    print(T_mV)
    print(T_R)
    T_d = detector_temperature_lookup(R=T_R, temp_cal_data=temp_data)

    axs[1,0].plot(T_d, label="T_d")
    axs[1,0].legend()
    axs[1,0].set_title("Detector Temperature")
    axs[1,0].set_ylabel("Processed Data")
    axs[1,0].set_xlim(t_min, t_max)

    ratios = data[:,2] / data[:,1]  # midwave (0.1-5.5 um) over longwave (8-14 um)
    T_t = np.zeros_like(ratios)
    eAs_LW = np.zeros_like(ratios)
    eAs_MW = np.zeros_like(ratios)
    FRPs_LW = np.zeros_like(ratios)
    FRPs_MW = np.zeros_like(ratios)

    print(ratios)

    lam1 = 0.1e-6
    lam2 = 5.5e-6
    lam3 = 8e-6
    lam4 = 14e-6

    for i in range(0, len(T_t)):
        if data[i,1] < 1 or data[i,2] < 1:
            T_t[i] = 0
        else:
            print(ratios[i])
            T_t[i] = so.brentq(lambda Ts: GB_ratio(Ts, lam1, lam2, lam3, lam4) - ratios[i], 200, 2000)
            Vexp_LW = F_LW*(T_t[i]**N_LW - T_d[i]**N_LW)
            Vexp_MW = F_MW*(T_t[i]**N_MW - T_d[i]**N_MW)

            eAs_LW[i] = data[i,1] / Vexp_LW
            eAs_MW[i] = data[i,2] / Vexp_MW

            FRPs_LW[i] = eAs_LW[i] * sc.Stefan_Boltzmann * T_t[i]**4
            FRPs_MW[i] = eAs_MW[i] * sc.Stefan_Boltzmann * T_t[i]**4

    axs[1,1].plot(T_t)
    axs[1,1].set_title("Target Temperature [K]")
    axs[1, 1].set_xlim(t_min, t_max)

    axs[2,0].plot(eAs_LW, label="eA LW")
    axs[2,0].plot(eAs_MW, label="eA MW")
    axs[2,0].legend()
    axs[2, 0].set_xlim(t_min, t_max)
    axs[2,0].set_ylim(-3, 10)
    axs[2,0].set_title("epsilon-Area product")

    axs[2, 1].plot(FRPs_LW, label="FRP LW")
    axs[2, 1].plot(FRPs_MW, label="FRP MW")
    axs[2, 1].set_xlim(t_min, t_max)
    axs[2,1].legend()
    axs[2,1].set_title("FRP [W/m^2]")

    plt.suptitle(datafile.split("/")[-1])
    fig.tight_layout()

    # Check that ratios are computed correctly
    fig, axs = plt.subplots(2,1)

    Ts = np.arange(300, 1500, 100)
    lam1 = 0.1e-6
    lam2 = 5.5e-6
    lam3 = 8e-6
    lam4 = 14e-6

    ratios = []
    for T in Ts:
        ratios.append(GB_ratio(T, lam1, lam2, lam3, lam4))

    T_actual = 873
    W1 = GB_lambda_window(lam1, lam2, T_actual)
    W2 = GB_lambda_window(lam3, lam4, T_actual)
    ratio = W1/W2
    T_found = so.brentq(lambda Ts: GB_ratio(Ts, lam1, lam2, lam3, lam4) - ratio, 200, 2000)

    axs[0].plot(Ts, ratios)
    axs[0].axhline(y=ratio, color='black', label="ratio")
    axs[0].axvline(x=T_actual, color='black', label="T actual")
    axs[0].axvline(x=T_found, color='red', linestyle='--', label="T found")

    axs[0].set_xlabel('T')
    axs[0].set_ylabel('GB ratio')
    axs[0].set_title('lam1='+str(lam1)+", lam2="+str(lam2)+', lam3='+str(lam3)+", lam4="+str(lam4))
    axs[0].legend()

    lambdas = np.arange(lam1, lam4, 100e-9)
    axs[1].plot(lambdas, GB_lambda(lambdas, T_actual))
    axs[1].set_ylabel('W(lam,T) [W/m^3]')
    axs[1].set_xlabel('Lambda [m]')
    axs[1].axvline(x=lam1, color='black')
    axs[1].axvline(x=lam2, color='black')
    axs[1].axvline(x=lam3, color='black')
    axs[1].axvline(x=lam4, color='black')

    plt.show()

