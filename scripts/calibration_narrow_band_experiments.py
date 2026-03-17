import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

import kremboxer.utils.greybody_utils as gbu


plot_dir = Path("/home/oryx/PycharmProjects/KremBoxer/plots/")
bandpass_dir = Path("/home/oryx/PycharmProjects/KremBoxer/calibration_data/calibration_output/Kremens_Fiveband/fiveband")
f_395_path = bandpass_dir / "DC-6726_R4_395CWL.csv"
f_1095_path = bandpass_dir / "DC-6725_1095CWL.csv"
f_395 = np.loadtxt(f_395_path, delimiter=',', skiprows=1, usecols=[0, 1])
mask = f_395[:,0] < 7.5
f_395_mod = f_395[mask,:]
f_1095 = np.loadtxt(f_1095_path, delimiter=',', skiprows=1, usecols=[0, 1])

Ts = np.arange(200, 1000, 10.0)
GB_ratios = np.zeros_like(Ts)
GB_ratios_mod = np.zeros_like(Ts)
for i in range(0, len(Ts)):
    GB_ratios[i] = gbu.GB_ratio_BP(Ts[i], f_395, f_1095)
    GB_ratios_mod[i] = gbu.GB_ratio_BP(Ts[i], f_395_mod, f_1095)

fig, axs = plt.subplots(2, 1, figsize=(5,6))
axs[0].plot(f_395[:,0], f_395[:,1], label="3.95um")
axs[0].plot(f_395_mod[:,0], f_395_mod[:,1], '--', label="3.95um mod")
axs[0].plot(f_1095[:,0], f_1095[:,1], label="10.95um")
axs[0].set_xlabel("Wavelength [um]")
axs[0].set_ylabel("Bandpass Transmission")
axs[0].legend()

axs[1].plot(Ts, GB_ratios, label="GB Ratio (3.95 / 10.95)")
axs[1].plot(Ts, GB_ratios_mod, label="GB Ratio (3.95 mod / 10.95)")
axs[1].set_xlabel("Blackbody Temperature [K]")
axs[1].set_ylabel("In-Band Irradiance Ratio")
axs[1].legend()
plt.tight_layout()

plt.savefig(plot_dir / "GB_ratios_narrow.png")
plt.show()


