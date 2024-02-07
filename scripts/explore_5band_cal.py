from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

cal_dir = Path("/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/RadiometerCalibrations/Athens5bandcalibration/")
cal_csv = cal_dir.joinpath("DATALOG_FB1.CSV")
df = pd.read_csv(cal_csv)
df = df[df["TIME"] != "TIME"]

fig, axs = plt.subplots(1, 2, figsize=(12, 7))
print(df["TIME"])
axs[0].plot(df["TIME"].astype('float'))
axs[0].set_xlabel("Sample number")
axs[0].set_ylabel("Time (s)")

axs[1].plot(df["TH1"].astype('float'), label="TH1")
axs[1].plot(df["3.95"].astype('float'), label="3.95")
axs[1].plot(df["10.95"].astype('float'), label="10.95")
axs[1].plot(df["TH2"].astype('float'), label="TH2")
axs[1].plot(df["MW"].astype('float'), label="MW")
axs[1].plot(df["LW"].astype('float'), label="LW")
axs[1].plot(df["WIDE"].astype('float'), label="WIDE")
axs[1].set_xlabel("Sample number")

axs[1].legend()

plt.suptitle(cal_csv.stem)
plt.tight_layout()

plt_file = cal_dir.joinpath(cal_csv.stem + ".png")
plt.savefig(plt_file)
plt.show()
print(df)
