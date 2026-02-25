from pathlib import Path
import numpy as np
import json
import pandas as pd
import geopandas as gpd
import scipy.optimize as so
import scipy.constants as sc
import kremboxer.dualband.dualband_process
import kremboxer.ufm.ufm_process
import kremboxer.fiveband.fiveband_process


def run_data_processing(data_processing_params: dict):

    archive_root = Path(data_processing_params["archive_dir"])

    # Process raw dualband data
    dualband_metadata_path = Path(archive_root.joinpath("Dualband_raw_metadata.geojson"))
    if dualband_metadata_path.exists():
        kremboxer.dualband.dualband_process.process_dualband_datasets(dualband_metadata_path,
                                                                          data_processing_params)

    # Process raw UFM data
    ufm_metadata_path = Path(archive_root.joinpath("UFM_raw_metadata.geojson"))
    if ufm_metadata_path.exists():
        kremboxer.ufm.ufm_process.process_ufm_datasets(ufm_metadata_path, data_processing_params)

    # Process raw fiveband data
    fiveband_metadata_path = Path(archive_root.joinpath("Fiveband_raw_metadata.geojson"))
    if fiveband_metadata_path.exists():
        kremboxer.fiveband.fiveband_process.process_fiveband_datasets(fiveband_metadata_path, data_processing_params)

