import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd

ufm_raw_data_csv = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerTesting/datalog5_output/DATLOG5_2024-02-10T13:34:52+00:00.csv")
ufm_raw_data_csv = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerTesting/datalog3_output/DATLOG3_2024-02-10T13:59:25+00:00.csv")
ufm_raw_data_csv = Path("/home/oryx/Projects/Objects/FortStewart2024/RadiometerTesting/datalog6_output/DATLOG6_2024-02-10T13-43-34+00-00.csv")
ufm_df = pd.read_csv(ufm_raw_data_csv)
print(ufm_df.head())
print(ufm_df.columns)

print(ufm_df.iloc[ufm_df["LW-A"].argmax()]["IR_IMAGE"])

fig, axs = plt.subplots(2, 2, figsize=(10, 10))
axs[0,0].plot(ufm_df["LW-A"].astype('float'), label="LW-A")
axs[0,1].plot(ufm_df["MW-B"].astype('float'), label="MW-B")
axs[1,0].plot(ufm_df["WIDE"].astype('float'), label="WIDE")
axs[1,1].plot(ufm_df["Flow"].astype('float'), label="Flow")
axs[0,0].legend()
axs[0,1].legend()
axs[1,0].legend()
axs[1,1].legend()
# xmin=8500
# xmax=9400
# axs[0,0].set_xlim(xmin, xmax)
# axs[0,1].set_xlim(xmin, xmax)
# axs[1,0].set_xlim(xmin, xmax)
# axs[1,1].set_xlim(xmin, xmax)
plt.savefig(ufm_raw_data_csv.parent.joinpath(ufm_raw_data_csv.stem + ".png"))

fig, axs = plt.subplots(2, 1, figsize=(5, 8))
x_peak = np.argmax(ufm_df["WIDE"].astype('float'))
axs[0].plot(ufm_df["WIDE"].astype('float'), label="WIDE")
axs[0].axvline(x_peak, color='r', linestyle='--')
pressure_diff = ufm_df["Flow"].astype('float')
N=10
pressure_diff_ave = np.convolve(pressure_diff , np.ones(N)/N, mode='valid')
axs[1].plot(pressure_diff, label="Flow")
axs[1].plot(pressure_diff_ave, label="10s Average")
axs[1].axvline(x_peak, color='r', linestyle='--')
axs[0].set_title("Wideband Radiometric Signal")
axs[1].set_title("Differential Pressure Signal")
axs[1].legend()
xmin=8800
xmax=9200
axs[0].set_xlim(xmin, xmax)
axs[1].set_xlim(xmin, xmax)
axs[1].set_xlabel("Sample (1 Hz)")
axs[0].set_ylabel("Voltage (mV)")
axs[1].set_ylabel("Voltage (mV)")
plt.savefig(ufm_raw_data_csv.parent.joinpath(ufm_raw_data_csv.stem + "_wide.png"))
plt.show()

plt.show()

