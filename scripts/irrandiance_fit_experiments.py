import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import kremboxer.utils.common_utils as kbc_utils
import kremboxer.utils.greybody_utils as kbg_utils

bandpasses = {
    "MW": {
        "path": Path("/home/oryx/PycharmProjects/KremBoxer/calibration_data/calibration_input/fiveband/bandpasses/interpolated/DC-6216_u1_Saph_longwave.csv"),
        "group": 1,
    },
    "LW": {
        "path": Path("/home/oryx/PycharmProjects/KremBoxer/calibration_data/calibration_input/fiveband/bandpasses/interpolated/DC-6073_W1_8-14Si.csv"),
        "group": 1,
    },
    "3.95": {
        "path": Path("/home/oryx/PycharmProjects/KremBoxer/calibration_data/calibration_input/fiveband/bandpasses/interpolated/DC-6726_R4_395CWL.csv"),
        "group": 2,
    },
    "10.95": {
        "path": Path("/home/oryx/PycharmProjects/KremBoxer/calibration_data/calibration_input/fiveband/bandpasses/interpolated/DC-6725_1095CWL.csv"),
        "group": 2,
    },
    "WIDE": {
        "path": Path("/home/oryx/PycharmProjects/KremBoxer/calibration_data/calibration_input/fiveband/bandpasses/interpolated/DC-6169_KRS5.csv"),
        "group": 1,
    }
}
output_dir = Path.home().joinpath("PycharmProjects", "KremBoxer", "calibration_data", "calibration_output", "fiveband_experiments")
output_dir.mkdir(exist_ok=True, parents=True)

bb_temps = np.arange(400, 800, 50)
bb_temps = np.array([373, 423, 473, 523, 573, 623, 673, 723, 773])

subplot_titles = ['Bandpasses', "Broad", "Narrow"]
fig = make_subplots(rows=3, cols=1, subplot_titles=subplot_titles)
for i, (band, bandpass_data) in enumerate(bandpasses.items()):
    bandpass_file = bandpass_data["path"]
    group = bandpass_data["group"]
    f = np.loadtxt(bandpass_file, delimiter=',', skiprows=1, usecols=[0, 1])
    fig.add_trace(go.Scatter(x=f[:,0], y=f[:,1], mode='lines', name=f'{band}'), row=1, col=1)

    (A, N, wd) = kbg_utils.fit_received_bandpass_energy(f, bb_temps)
    fig.add_trace(go.Scatter(x=bb_temps, y=wd, mode='lines+markers', name=f'{band}'), row=1+group, col=1)
    fig.add_trace(go.Scatter(x=bb_temps, y=A*bb_temps**N, mode='lines', line=dict(dash='dash', color='red', width=2), name=f'{band}'), row=1+group, col=1)

    print(f'band: {band}, A={A}, N={N}')

# Check how cutting off the 3.95um bandpass changes fit values
banddata_395 = bandpasses["3.95"]
group = banddata_395["group"]
f_temp = np.loadtxt(banddata_395["path"], delimiter=',', skiprows=1, usecols=[0, 1])
mask = f_temp[:,0] < 7
f = f_temp[mask,:]

fig.add_trace(go.Scatter(x=f[:,0], y=f[:,1], mode='lines', name=f'{band}'), row=1, col=1)

(A, N, wd) = kbg_utils.fit_received_bandpass_energy(f, bb_temps)
fig.add_trace(go.Scatter(x=bb_temps, y=wd, mode='lines+markers', name=f'{band}'), row=1+group, col=1)
fig.add_trace(go.Scatter(x=bb_temps, y=A*bb_temps**N, mode='lines', line=dict(dash='dash', color='red', width=2), name=f'{band}'), row=1+group, col=1)
print(f'band: {3.95} cutoff, A={A}, N={N}')

fig.update_layout(hovermode="x")
fig.update_layout(title_text="Fiveband Irradiance Fits")
fig.write_html(output_dir.joinpath("fiveband_irradiance_fits.html"))

