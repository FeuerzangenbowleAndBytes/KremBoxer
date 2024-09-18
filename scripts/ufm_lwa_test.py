import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

root_dir = Path("/home/jepaki/Projects/Objects/FortStewart2024/FireBehaviorDatasets/Raw/UFM")

ufms = []
lw_maxs = []
mw_maxs = []
wide_maxs = []
flow_maxs = []
for file in root_dir.glob('*.csv'):
    ufm = file.stem.split('_')[1]
    df = pd.read_csv(file)
    lw_max = df["LW-A"].max()
    print(f'File: {file}, UFM: {ufm}, LW-A Max: {lw_max}')
    ufms.append(ufm)
    lw_maxs.append(df["LW-A"].max())
    mw_maxs.append(df["MW-B"].max())
    wide_maxs.append(df["WIDE"].max())
    flow_maxs.append(df["Flow"].max())

fig, axs = plt.subplots(2, 2, figsize=(8,8))
axs[0,0].scatter(ufms, lw_maxs)
axs[0,1].scatter(ufms, mw_maxs)
axs[1,0].scatter(ufms, wide_maxs)
axs[1,1].scatter(ufms, flow_maxs)

axs[0,0].set_title("LW-A Max")
axs[0,1].set_title("MW-A Max")
axs[1,0].set_title("WIDE Max")
axs[1,1].set_title("Flow Max")

plt.tight_layout()
plt.savefig(root_dir.joinpath("ufm_channel_maxima.png"))
plt.show()
