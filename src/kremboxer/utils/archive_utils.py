from pathlib import Path
import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
import scipy
import kremboxer.dualband.dualband_utils as db_utils
import kremboxer.dualband.dualband_clean as db_clean
import kremboxer.ufm.ufm_utils as ufm_utils
import kremboxer.ufm.ufm_clean as ufm_clean
import kremboxer.fiveband.fiveband_utils as fb_utils


def id_sensor_from_raw_file(file: Path) -> str:
    if db_utils.is_dualband_file(file):
        return "Dualband"
    elif ufm_utils.is_ufm_file(file):
        return "UFM"
    elif fb_utils.is_fiveband_file(file):
        return "Fiveband"
    else:
        return "UNKNOWN"


def extract_datasets_from_raw_file(file: Path, sensor: str):
    if sensor == "Dualband":
        header_dicts, data_dfs = db_clean.extract_dualband_datasets_from_raw_file(file)
        return header_dicts, data_dfs
    elif sensor == "Fiveband":
        pass
    elif sensor == "UFM":
        header_dicts, data_dfs, ir_image_cubes = ufm_clean.extract_ufm_datasets_from_raw_file(file)
        return header_dicts, data_dfs, ir_image_cubes
    else:
        print("Unknown sensor: ", sensor)
        exit(1)


def create_dataset_archive(params: dict):
    print("Creating dataset archive")
    archive_dir = Path(params["archive_dir"])
    data_source_directories = params["data_source_directories"]
    processing_level = "Raw"

    unknown_sensor_file = []
    metadatas = {
        "Dualband": [],
        "UFM": [],
        "Fiveband": []
    }
    for data_source_directory in data_source_directories:
        print(f"Processing directory: {data_source_directory}")
        data_source_directory = Path(data_source_directory)
        for file in data_source_directory.glob('**/*.CSV'):
            sensor = id_sensor_from_raw_file(file)
            print(f'{file} -> {sensor}')
            if sensor == "UNKNOWN":
                print("Unknown sensor type for file: ", file)
                unknown_sensor_file.append(file)
                continue
            if sensor == "Dualband":
                header_dicts, data_dfs = extract_datasets_from_raw_file(file, sensor)
                db_output_dir = archive_dir.joinpath(processing_level).joinpath(sensor)
                db_output_dir.mkdir(exist_ok=True, parents=True)
                datafiles = []
                for i, (header_dict, data_df) in enumerate(zip(header_dicts, data_dfs)):
                    unit = header_dict['UNIT']
                    dt = header_dict['DATETIME_START'].isoformat() #.replace(":", "-")
                    output_file = db_output_dir.joinpath(f'{sensor}_{unit}_{dt.replace(":", "-")}.csv') # Replace : with - in time string for windows
                    data_df.to_csv(output_file, index=False)
                    metadatas[sensor].append(header_dict)
                    metadatas[sensor][-1]['PROCESSING_LEVEL'] = processing_level
                    metadatas[sensor][-1]['SENSOR'] = sensor
                    metadatas[sensor][-1]['DATAFILE'] = output_file.name
                    metadatas[sensor][-1]['DURATION'] = len(data_df) / header_dict['SAMPLE-RATE(Hz)']
                #print(header_dicts)
            elif sensor == "UFM":
                header_dicts, data_dfs, ir_image_cubes = extract_datasets_from_raw_file(file, sensor)
                ufm_output_dir = archive_dir.joinpath(processing_level).joinpath(sensor)
                ufm_output_dir.mkdir(exist_ok=True, parents=True)
                datafiles = []
                for i, (header_dict, data_df, ir_image_cube) in enumerate(zip(header_dicts, data_dfs, ir_image_cubes)):
                    unit = header_dict['UNIT']
                    dt = header_dict['DATETIME_START'].isoformat()#.replace(":", "-")
                    output_file = ufm_output_dir.joinpath(f'{sensor}_{unit}_{dt.replace(":", "-")}.csv')
                    data_df.to_csv(output_file, index=False)
                    metadatas[sensor].append(header_dict)
                    metadatas[sensor][-1]['PROCESSING_LEVEL'] = "Raw"
                    metadatas[sensor][-1]['SENSOR'] = sensor
                    metadatas[sensor][-1]['DATAFILE'] = output_file.name
                    metadatas[sensor][-1]['DURATION'] = len(data_df) / header_dict['SAMPLE-RATE(Hz)']

                    numpy_output_file = ufm_output_dir.joinpath(f'{sensor}_{unit}_{dt.replace(":", "-")}_ir_images.npy')
                    matlab_output_file = ufm_output_dir.joinpath(f'{sensor}_{unit}_{dt.replace(":", "-")}_ir_images.mat')
                    np.save(numpy_output_file, ir_image_cube)
                    scipy.io.savemat(matlab_output_file, {'ir_images': ir_image_cube})
                    metadatas[sensor][-1]['IR_IMAGE_NUMPY'] = numpy_output_file.name
                    metadatas[sensor][-1]['IR_IMAGE_MATLAB'] = matlab_output_file.name

                #print(header_dicts)
            elif sensor == "Fiveband":
                pass

    for key, metadata in metadatas.items():
        #print(key)
        df = pd.DataFrame(metadata)
        # Filter duplicates by datetime start and unit, can happen if the same radiometer is used to collect
        # data on different days, but the memory card is not wiped in between
        df.drop_duplicates(subset=['UNIT', 'DATETIME_START'], inplace=True)

        # Write out to CSV
        df.to_csv(archive_dir.joinpath(f'{key}_raw_metadata.csv'), index=False)

        # print(len(df))
        # print(df[df['UNIT']=='5'])
        # print(df['UNIT'])
        # Write out to geojson
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE), crs="EPSG:4326")
            gdf['DATETIME_START'] = gdf['DATETIME_START'].map(lambda x: x.isoformat(sep='T'))
            gdf.to_file(archive_dir.joinpath(f'{key}_raw_metadata.geojson'), driver='GeoJSON', index=False)

    return 0
