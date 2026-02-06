import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

rad_data_dir = Path.home() / "Projects" / "Objects" / "FortStewart_2022-03" / "FireBehaviorDatasets"
plot_dir = rad_data_dir / "plot"
plot_dir.mkdir(parents=True, exist_ok=True)
db_meta_file = rad_data_dir / "Dualband_processed_metadata.geojson"
db_gdf = gpd.read_file(db_meta_file)
db_gdf["fire_start"] = pd.to_datetime(db_gdf["fire_start"])
db_gdf["fire_end"] = pd.to_datetime(db_gdf["fire_end"])
db_gdf["max_FRP_datetime"] = pd.to_datetime(db_gdf["max_FRP_datetime"])

print(db_gdf.describe())
print(f"Number dualband datasets: {len(db_gdf)}")

row = db_gdf.loc[4]
db_datafile = rad_data_dir / row["PROCESSING_LEVEL"] / row["SENSOR"] / row["DATAFILE"]
db_df = gpd.read_file(db_datafile)
db_df["DATETIME"] = pd.to_datetime(db_df["DATETIME"])

db_df = db_df[db_df["DATETIME"] >= row["fire_start"]]
db_df = db_df[db_df["DATETIME"] <= row["fire_end"]]
frp = db_df["MW_FRP"].astype("float")

max_frp_datetime = row["max_FRP_datetime"]
end_frp_datetime = max_frp_datetime + pd.Timedelta(minutes=5)
max_frp_index = row["max_FRP_index"]
end_frp_index = (db_df["DATETIME"] - end_frp_datetime).abs().idxmin()
max_frp = frp[max_frp_index]
end_frp = frp[end_frp_index]

fig = make_subplots(rows=1, cols=1)
fig.add_trace(go.Scatter(x=db_df["DATETIME"], y=frp, mode='lines', name=f'DB {row["UNIT"]}'), row=1, col=1)
fig.add_trace(go.Scatter(x=[max_frp_datetime], y=[max_frp], mode='markers', name=f'DB {row["UNIT"]}'), row=1, col=1)
fig.add_trace(go.Scatter(x=[end_frp_datetime], y=[end_frp], mode='markers', name=f'DB {row["UNIT"]}'), row=1, col=1)
fig.add_vline(x=max_frp_datetime, line_width=2, line_dash='dash', name="max FRP", row=1, col=1)
fig.add_vline(x=end_frp_datetime, line_width=2, line_dash='dash', name="max FRP", row=1, col=1)
fig.update_layout(
    title_text=f'Fire Radiative Power (W/m^2)',
    showlegend=True
)
fig.write_html(plot_dir / "frp_trace_demo.html")
fig.show()


