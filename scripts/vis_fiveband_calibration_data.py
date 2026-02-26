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
    meta_df["Time Start"] = pd.to_datetime(meta_df["Time Start"], format='%H:%M:%S')
    min_start_time = meta_df["Time Start"].min()
    meta_df["Time Start"] = (meta_df["Time Start"] - min_start_time).dt.total_seconds()
    meta_df["Time End"] = pd.to_datetime(meta_df["Time End"], format='%H:%M:%S')
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
fb1_cal_path = cal_dir.joinpath("DATALOG_FB1_cal.csv")
fb8_cal_path = cal_dir.joinpath("DATALOG_FB8_cal.csv")
kremens_cal_path = Path.home().joinpath("PycharmProjects", "KremBoxer", "calibration_data", "calibration_input", "fiveband", "fiveband_calibration_data_kremens.csv")
db_cal_path =Path.home().joinpath("PycharmProjects", "KremBoxer", "calibration_data",
                                  "calibration_output", "FortStewart2024", "unit11_calibration_data.csv")
fb1_cal_df = pd.read_csv(fb1_cal_path)
fb8_cal_df = pd.read_csv(fb8_cal_path)
db_cal_df = pd.read_csv(db_cal_path)
print(db_cal_df.head())

kremens_cal_df = pd.read_csv(kremens_cal_path)
kremens_ave_cal_df = kremens_cal_df.groupby('Temp').aggregate('mean').reset_index()
kremens_ave_cal_df["Target T [K]"] = kremens_ave_cal_df["Temp"]
kremens_ave_cal_path = Path.home().joinpath("PycharmProjects", "KremBoxer", "calibration_data", "calibration_input", "fiveband", "fiveband_calibration_data_kremens_ave.csv")
kremens_ave_cal_df.to_csv(kremens_ave_cal_path)
print(kremens_ave_cal_df.head())

cal_dfs = {"fb1": fb1_cal_df,
           "fb8": fb8_cal_df,
           "kremens": kremens_cal_df,
           "kremens_ave": kremens_ave_cal_df
           }
colors = ["blue", "green", "red", "orange"]

num_cols = 2
num_rows = int(np.ceil(len(data_cols)/num_cols))
print(num_rows)
fig = make_subplots(rows=num_rows, cols=num_cols, subplot_titles=data_cols, shared_xaxes='all')
for i, (cal_name, cal_df) in enumerate(cal_dfs.items()):
    for j, data_col in enumerate(data_cols):
        fig.add_trace(go.Scatter(x=cal_df["Temp"], y=cal_df[data_col].astype('float'), mode='lines+markers',
                                 marker=dict(color=colors[i], size=10), name=f'{data_col}, {cal_name}'),
                      row=int(np.floor(j/2))+1, col=j%2+1)

# Add dualband calibration data
fig.add_trace(go.Scatter(x=db_cal_df["Target T"],
                         y=db_cal_df['TH'].astype('float'),
                         mode='lines+markers',
                         marker=dict(color='brown', size=10),
                         name=f'TH, dualband'),
              row=1, col=1)

fig.add_trace(go.Scatter(x=db_cal_df["Target T"],
                         y=db_cal_df['LW-A'].astype('float'),
                         mode='lines+markers',
                         marker=dict(color='brown', size=10),
                         name=f'LW-A, dualband'),
              row=3, col=2)

fig.add_trace(go.Scatter(x=db_cal_df["Target T"],
                         y=db_cal_df['MW-B'].astype('float'),
                         mode='lines+markers',
                         marker=dict(color='brown', size=10),
                         name=f'MW-B, dualband'),
              row=3, col=1)

for i in range(num_rows):
    for j in range(num_cols):
        fig.update_yaxes(title_text="Sensor Value (mV)", row=i+1, col=j+1)
        fig.update_xaxes(title_text="Black Body Temp (K)", row=i+1, col=j+1)
fig.update_layout(hovermode="x")
fig.update_layout(title_text="Fiveband Calibration Comparison")
fig.write_html(cal_dir.joinpath("fiveband_calibration_comparison.html"))
fig.write_image(cal_dir.joinpath("fiveband_calibration_comparison.png"), height=800, width=1000, scale=2)

