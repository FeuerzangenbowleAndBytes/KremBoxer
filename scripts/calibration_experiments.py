import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import scipy.optimize as so
import kremboxer.utils.greybody_utils as gbu


v_top = 3300
r_top = 100000

cal_dir = Path("C:\\Users\\pakij\\Code\\KremBoxer\\calibration_data\\calibration_output\\FortStewart2024\\fiveband")
temp_cal_input = cal_dir.joinpath("temperature_sensor_calibration.csv")
bandpass_input = cal_dir.joinpath("DC-6216_u1_Saph_longwave.csv")
cal_input_path = cal_dir.joinpath("fb1_calibration_data.csv")

# Load bandpass data
f = np.loadtxt(bandpass_input, delimiter=',', skiprows=1, usecols=[0, 1])

# Load the blackbody calibration data
blackbody_cal_data_df = pd.read_csv(cal_input_path)

# Convert the two temperature sensors' mV data into resistance, using known voltage divider characteristics
t_mV = blackbody_cal_data_df["TH2"].to_numpy()
t_resist = t_mV * r_top / (v_top - t_mV)  # Convert mV reading into resistance of temperature sensor

# Load actual temperatures and detector signals from calibration data
t_actual = blackbody_cal_data_df["Target T [K]"].to_numpy()
v = blackbody_cal_data_df["MW"].to_numpy()

# Compute the temperature of the detector from its resistance
t_cal_data = np.loadtxt(temp_cal_input, skiprows=1, delimiter=",", usecols=[0, 1, 2])
t_cal_data = np.flip(t_cal_data, 0)
t_temp = gbu.detector_temperature_lookup(R=t_resist, temp_cal_data=t_cal_data)

(A, N, wd) = gbu.fit_received_bandpass_energy(f, t_actual)
# (G, AL), pcov_LW = so.curve_fit(
#         lambda T, G, AL: gbu.detector_model(T, G, AL, 290, A, N),
#         t_actual, v)

print(len(t_temp), len(t_actual), len(v))
T_data = np.stack((t_actual, t_temp), axis=0)
print(T_data.shape)
(G, AL), pcov = so.curve_fit(
        lambda T, G, AL: G*(A*T[0]**N-AL*T[1]**N),
        T_data, v, maxfev=1000,
        p0=[1, 1e-10])
        #p0=[0.03932454347554703, 8.163502457789143e-12])

print("t_temp:", t_temp)
print("t_blackbody:", t_actual)
print("N=", N, ", A=", A, ", G=", G, ", AL=", AL)

fig, axs = plt.subplots(1, 2, figsize=(12, 8))
axs[0].plot(f[:, 0], f[:, 1], label="Bandpass")
axs[1].plot(t_actual, v, label='Data')
axs[1].plot(t_actual, gbu.detector_model(t_actual, G, AL, t_temp, A, N),
            ls='--', label='fit')
axs[1].legend()
plt.show()
