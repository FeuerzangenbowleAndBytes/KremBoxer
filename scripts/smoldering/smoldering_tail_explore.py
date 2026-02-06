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

print(db_gdf.describe())
print(f"Number dualband datasets: {len(db_gdf)}")

fig = make_subplots(rows=1, cols=1)
for i, row in db_gdf.iterrows():
    db_datafile = rad_data_dir / row["PROCESSING_LEVEL"] / row["SENSOR"] / row["DATAFILE"]
    print(db_datafile)
    db_df = gpd.read_file(db_datafile)
    db_df["DATETIME"] = pd.to_datetime(db_df["DATETIME"])
    db_df = db_df[db_df["DATETIME"] >= row["fire_start"]]
    db_df = db_df[db_df["DATETIME"] <= row["fire_end"]]
    frp = db_df["MW_FRP"].astype("float")
    fig.add_trace(go.Scatter(x=db_df["DATETIME"], y=frp, mode='lines', name=f'DB {row["UNIT"]}'), row=1, col=1)

fig.write_html(plot_dir / "frp_traces.html")
