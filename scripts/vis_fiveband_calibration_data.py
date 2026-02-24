from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

cal_dir = Path("/home/oryx/Dropbox/Jobs/MTRI/Projects/Wildfire/RadiometerCalibrations/Athens5bandcalibration/")
cal_data = {
    "DATALOG_FB1.CSV": "fb1_meta.csv",
    "DATALOG_FB8.CSV": "fb8_meta.csv"
}
num_cals = len(cal_data.keys())
data_cols = ["TH1", "TH2", "3.95", "10.95", "MW", "LW", "WIDE"]

fig = make_subplots(rows=2, cols=1, subplot_titles=list(cal_data.keys()))
for i, (cal_csv, meta_csv) in enumerate(cal_data.items()):
    cal_path = cal_dir.joinpath(cal_csv)
    meta_path = cal_dir.joinpath(meta_csv)

    cal_df = pd.read_csv(cal_path)
    meta_df = pd.read_csv(meta_path)
    cal_df = cal_df[cal_df["TIME"] != "TIME"]

    for data_col in data_cols:
        cal_df[data_col] = pd.to_numeric(cal_df[data_col])

    print(cal_path, i)
    no_time = pd.isna(cal_df['TIME'].loc[0]) and (len(cal_df['TIME'].unique()) == 1)

    if not no_time and False:
        time_vals = cal_df["TIME"].astype('float')
        time_vals = time_vals - time_vals.min()
    else:
        time_vals = np.arange(0, len(cal_df))

    fig.add_trace(go.Scatter(x=time_vals, y=cal_df['TH1'].astype('float'), name='TH1'),
                  row=i+1, col=1)
    fig.add_trace(go.Scatter(x=time_vals, y=cal_df['TH2'].astype('float'), name='TH2'),
                  row=i + 1, col=1)
    fig.add_trace(go.Scatter(x=time_vals, y=cal_df['3.95'].astype('float'), name='3.95'),
                  row=i + 1, col=1)
    fig.add_trace(go.Scatter(x=time_vals, y=cal_df['10.95'].astype('float'), name='10.95'),
                  row=i + 1, col=1)
    fig.add_trace(go.Scatter(x=time_vals, y=cal_df['MW'].astype('float'), name='MW'),
                  row=i + 1, col=1)
    fig.add_trace(go.Scatter(x=time_vals, y=cal_df['LW'].astype('float'), name='LW'),
                  row=i + 1, col=1)
    fig.add_trace(go.Scatter(x=time_vals, y=cal_df['WIDE'].astype('float'), name='WIDE'),
                  row=i + 1, col=1)

    print(meta_df)
    meta_df["Time Start"] = pd.to_datetime(meta_df["Time Start"])
    min_start_time = meta_df["Time Start"].min()
    meta_df["Time Start"] = (meta_df["Time Start"] - min_start_time).dt.total_seconds()
    meta_df["Time End"] = pd.to_datetime(meta_df["Time End"])
    meta_df["Time End"] = (meta_df["Time End"] - min_start_time).dt.total_seconds()

    lw_max_index = cal_df['LW'].idxmax()
    lw_max_time = time_vals[lw_max_index]
    dt = lw_max_index - meta_df.iloc[-1]["Time Start"]
    print(meta_df.iloc[-1]["Time Start"], lw_max_time, lw_max_index, dt)

    sample_indices = []
    bb_temps = []
    for k, row in meta_df.iterrows():
        fig.add_vline(x=row["Time Start"]+dt, line_dash="dash", annotation_text=f'{row["Temp"]}C<br>{row["Temp"] + 273}K',
                      row=i+1, col=1)
        sample_indices.append(row["Time Start"]+dt)
        bb_temps.append(row["Temp"])

    cal_data_reduced_df = cal_df.loc[sample_indices, data_cols].reset_index(drop=True)
    cal_data_reduced_df["Temp"] = meta_df["Temp"].astype(float)+273
    cal_data_reduced_df.to_csv(cal_dir.joinpath(cal_path.stem+"_cal.csv"), index=False)

fig.update_layout(hovermode="x")
fig.update_yaxes(title_text="Sensor Value (mV)", row=1, col=1)
fig.update_yaxes(title_text="Sensor Value (mV)", row=2, col=1)
fig.update_xaxes(title_text="Time (seconds)", row=1, col=1)
fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
fig.update_layout(title_text="Fiveband Calibration Dataset")
fig.write_html(cal_dir.joinpath("fiveband_calibration_data.html"))


# Make plot comparing the reduced calibration datasets





