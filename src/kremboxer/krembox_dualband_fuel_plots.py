import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import json
from pathlib import Path


def run_krembox_dualband_fuel_plot_association(params):
    # Get the output root directory
    burn_name = params["burn_name"]
    output_root = Path(params["output_root"])
    dataframes_dir = output_root.joinpath("dataframes_" + burn_name)
    clean_dataframe_input = dataframes_dir.joinpath("cleaned_dataframe_" + burn_name + ".geojson")

   