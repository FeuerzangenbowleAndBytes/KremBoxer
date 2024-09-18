from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

cal_dir = Path("/home/jepaki/Dropbox/Jobs/MTRI/Projects/Wildfire/RadiometerCalibrations/Athens5bandcalibration/")

cal_condensed_csv = cal_dir.joinpath("fb1_calibration_data.csv")
df = pd.read_csv(cal_condensed_csv)
fig, axs = plt.subplots(1, 1, figsize=(8, 8))
axs.plot(df['Target T [K]'], df['TH1'], label="TH1")
axs.plot(df['Target T [K]'], df['TH2'], label="TH2")
axs.plot(df['Target T [K]'], df['3.95'], label="3.95")
axs.plot(df['Target T [K]'], df['10.95'], label="10.95")
axs.plot(df['Target T [K]'], df['MW'], label="MW")
axs.plot(df['Target T [K]'], df['LW'], label="LW")
axs.plot(df['Target T [K]'], df['WIDE'], label="WIDE")
axs.set_xlabel("Target T [K]")
axs.legend()
plt_file = cal_dir.joinpath("fb1_calibration_condensed_data.png")
plt.savefig(plt_file)

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



# fig = px.line(x=df["TIME"].astype('float'), y=df['TH1'])
#
# fig.show()

fig = go.Figure()
fig.add_trace(go.Line(x=df["TIME"].astype('float'), y=df['TH1'].astype('float'), name='TH1'))
fig.add_trace(go.Line(x=df["TIME"].astype('float'), y=df['TH2'].astype('float'), name='TH2'))
fig.add_trace(go.Line(x=df["TIME"].astype('float'), y=df['3.95'].astype('float'), name='3.95'))
fig.add_trace(go.Line(x=df["TIME"].astype('float'), y=df['10.95'].astype('float'), name='10.95'))
fig.add_trace(go.Line(x=df["TIME"].astype('float'), y=df['MW'].astype('float'), name='MW'))
fig.add_trace(go.Line(x=df["TIME"].astype('float'), y=df['LW'].astype('float'), name='LW'))
fig.add_trace(go.Line(x=df["TIME"].astype('float'), y=df['WIDE'].astype('float'), name='WIDE'))
fig.update_layout(hovermode="x")

fig.show()
