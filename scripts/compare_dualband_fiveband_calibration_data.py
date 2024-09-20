import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

dualband_csv = Path("/home/jepaki/code/KremBoxer/calibration_data/calibration_output/FortStewart2024/unit11_calibration_data.csv")
fiveband_csv = Path("/home/jepaki/code/KremBoxer/calibration_data/calibration_output/FortStewart2024/fiveband/fb1_calibration_data.csv")

db_df = pd.read_csv(dualband_csv)
fb_df = pd.read_csv(fiveband_csv)

fig, axs = plt.subplots(3, 1, figsize=(8, 12))
axs[0].plot(db_df["Target T"], db_df["MW-B"], label="Dualband")
axs[0].plot(fb_df["Target T [K]"], fb_df["MW"], label="Fiveband")
axs[1].plot(db_df["Target T"], db_df["LW-A"], label="Dualband")
axs[1].plot(fb_df["Target T [K]"], fb_df["LW"], label="Fiveband")
axs[2].plot(db_df["Target T"], db_df["TH"], label="Dualband, TH2")
axs[2].plot(fb_df["Target T [K]"], fb_df["TH1"], label="Fiveband, TH1")
axs[2].plot(fb_df["Target T [K]"], fb_df["TH2"], label="Fiveband, TH2")
axs[0].set_title("MW Sensor Calibration Data")
axs[1].set_title("LW Sensor Calibration Data")
axs[1].set_title("Temp Sensor Calibration Data")
axs[2].set_xlabel("Blackbody T [K]")
axs[0].set_ylabel("Sensor Voltage [mV]")
axs[1].set_ylabel("Sensor Voltage [mV]")
axs[0].legend()
axs[2].legend()
plt.savefig("/home/jepaki/code/KremBoxer/calibration_data/calibration_input/db_fb_calibration_data_compare.png")
plt.show()
