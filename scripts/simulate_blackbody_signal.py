import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import scipy.optimize as so
import kremboxer.utils.greybody_utils as gbu

bandpass_dir = Path().home().joinpath("code", "KremBoxer", "calibration_data", "calibration_input", "fiveband", "bandpasses", "interpolated")
bandpass_files = {
    "MW": "DC-6216_u1_Saph_longwave.csv",
    "LW": "DC-6073_W1_8-14Si.csv",
    "3.95": "DC-6725_1095CWL.csv",
    "10.95": "DC-6726_R4_395CWL.csv",
    "WIDE": "DC-6169_KRS5.csv",
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
T_blackbody = np.arange(300, 800, 100)

fig, axs = plt.subplots(2, 2, figsize=(8, 8))
for name, data in bandpass_data.items():
    axs[0, 0].plot(data['f'][:, 0], data['f'][:, 1], label=name)
    (A, N, wd) = gbu.fit_received_bandpass_energy(data['f'], T_blackbody)
    axs[0, 1].scatter(T_blackbody, wd, label=name)
    axs[0, 1].plot(T_blackbody, gbu.planck_model(T_blackbody, A, N))

for T in T_blackbody:
    axs[1, 0].plot(lams, gbu.GB_lambda(lams*10**-6, T), label=f'{T}')

axs[0, 0].legend()
axs[1, 0].legend()
axs[0, 1].legend()

axs[0, 0].set_title("Bandpasses")
axs[1, 0].set_title("Planck Curves")
axs[0, 1].set_title("Received Radiance")

axs[0, 0].set_ylabel("Transmittance")
axs[0, 1].set_ylabel("Irradiance [W/m^2]")
axs[1, 0].set_ylabel("Radiance [W/m^2*um]")

axs[0, 0].set_xlabel("Wavelength [um]")
axs[0, 1].set_xlabel("Blackbody Temperature [K]")
axs[1, 0].set_xlabel("Wavelength [um]")

axs[0, 0].set_xlim([0, 20])
axs[1, 0].set_xlim([0, 20])

plt.tight_layout()
plt.savefig(Path.home().joinpath("code", "KremBoxer", "plots", "blackbody_simulation.png"))
plt.show()
