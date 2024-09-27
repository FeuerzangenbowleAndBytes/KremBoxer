import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import scipy.optimize as so
import kremboxer.utils.greybody_utils as gbu

bandpass_dir = Path().home().joinpath("code", "KremBoxer", "calibration_data", "calibration_input", "fiveband", "bandpasses", "interpolated")
bandpass_files = {
    #"MW": "DC-6216_u1_Saph_longwave.csv",
    #"LW": "DC-6073_W1_8-14Si.csv",
    "10.95": "DC-6725_1095CWL.csv",
    "3.95": "DC-6726_R4_395CWL.csv",
    #"WIDE": "DC-6169_KRS5.csv",
}

bandpass_data = {}
for key, file in bandpass_files.items():
    print(key, file)
    bandpass_data[key] = {
        'filename': file,
        'path': bandpass_dir.joinpath(file),
        'f': np.loadtxt(bandpass_dir.joinpath(file), delimiter=',', skiprows=1, usecols=[0, 1])
    }

lams = np.arange(0, 20, 0.01)
T_blackbody = np.arange(200, 800, 50)

fig, axs = plt.subplots(2, 2, figsize=(8, 8))
for name, data in bandpass_data.items():
    axs[0, 0].plot(data['f'][:, 0], data['f'][:, 1], label=name)
    (A, N, wd) = gbu.fit_received_bandpass_energy(data['f'], T_blackbody)
    print(name, A, N, wd)
    axs[0, 1].scatter(T_blackbody, wd, label=name)
    axs[0, 1].plot(T_blackbody, gbu.planck_model(T_blackbody, A, N))

for T in T_blackbody:
    axs[1, 0].plot(lams, gbu.GB_lambda(lams*10**-6, T), label=f'{T}')

(A_395, N_395, wd_395) = gbu.fit_received_bandpass_energy(bandpass_data['3.95']['f'], T_blackbody)
(A_1095, N_1095, wd_1095) = gbu.fit_received_bandpass_energy(bandpass_data['10.95']['f'], T_blackbody)
axs[1, 1].plot(T_blackbody, wd_395 / wd_1095)
T_min = T_blackbody[np.argmin(wd_395 / wd_1095)]
axs[1, 1].axvline(x=T_min, ls='--', label=f'T min = {T_min}K')
print("Minimum Ratio Temperature = ", T_min)
axs[1, 1].legend()
axs[1, 1].set_title("3.95 / 10.95 Blackbody Irradiance Ratio")
axs[1, 1].set_xlabel("Blackbody Temperature")
axs[1, 1].set_ylabel("3.95 / 10.95 Ratio")

axs[0, 0].legend()
axs[1, 0].legend()
axs[0, 1].legend()

axs[0, 0].set_title("Bandpasses")
axs[1, 0].set_title("Planck Curves")
axs[0, 1].set_title("Received Irradiance")

axs[0, 0].set_ylabel("Transmittance")
axs[0, 1].set_ylabel("Irradiance [W/m^2]")
axs[1, 0].set_ylabel("Radiance [W/m^2*um]")

axs[0, 0].set_xlabel("Wavelength [um]")
axs[0, 1].set_xlabel("Blackbody Temperature [K]")
axs[1, 0].set_xlabel("Wavelength [um]")

axs[0, 0].set_xlim([0, 20])
axs[1, 0].set_xlim([0, 20])
#axs[0, 1].set_xlim([190, 300])
#axs[0, 1].set_ylim([0, 40])

plt.tight_layout()
plt.savefig(Path.home().joinpath("code", "KremBoxer", "plots", "blackbody_simulation.png"))
plt.show()
