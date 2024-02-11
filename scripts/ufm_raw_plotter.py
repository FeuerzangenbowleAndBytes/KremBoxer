import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd

ufm_raw_data_csv = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerTesting/datalog5_output/DATLOG5_2024-02-10T13:34:52+00:00.csv")
ufm_raw_data_csv = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerTesting/datalog3_output/DATLOG3_2024-02-10T13:59:25+00:00.csv")
ufm_raw_data_csv = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerTesting/datalog6_output/DATLOG6_2024-02-10T13-43-34+00-00.csv")
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
plt.savefig(ufm_raw_data_csv.parent.joinpath(ufm_raw_data_csv.stem + ".png"))
plt.show()

