import numpy as np
import pandas as pd
import geopandas as gpd
import datetime
from pathlib import Path
import pytz
import matplotlib.pyplot as plt


class LoraRecorderDataParser:
    metadata_elements = {
        "Node": {
            "value": None,
            "index": None,
            "type": int
        },
        "Lat": {
            "value": None,
            "index": None,
            "type": float
        },
        "Lon": {
            "value": None,
            "index": None,
            "type": float
        },
        "Year": {
            "value": None,
            "index": None,
            "type": int
        },
        "Month": {
            "value": None,
            "index": None,
            "type": int
        },
        "Day": {
            "value": None,
            "index": None,
            "type": int
        },
        "Hours": {
            "value": None,
            "index": None,
            "type": int
        },
        "Minutes": {
            "value": None,
            "index": None,
            "type": int
        },
        "Seconds": {
            "value": None,
            "index": None,
            "type": int
        },
        "SampleFrameStart": {
            "value": None,
            "index": None,
            "type": int
        },
    }

    sensor_names = ["A0", "A1", "A2"]
    number_of_sensors = len(sensor_names)
    samples_per_frame = 5
    data_elements = {
        "SensorData": {
            "value": None,
            "index": None,
            "type": float
        }
    }

    def __init__(self, record_entries: list):
        self.record_entries = [x.replace("\n","") for x in record_entries]
        for key in self.metadata_elements.keys():
            self.metadata_elements[key]["index"] = self.record_entries.index(key)
        for key in self.data_elements.keys():
            self.data_elements[key]["index"] = self.record_entries.index(key)

    def parse_data_string(self, data_string: str):
        data_string = data_string.replace("\n", "").strip()
        data = [x for x in data_string.split(",")]

        for key in self.metadata_elements.keys():
            self.metadata_elements[key]["value"] = self.metadata_elements[key]["type"](data[self.metadata_elements[key]["index"]])
        for key in self.data_elements.keys():
            start_index = int(self.data_elements[key]["index"])
            end_index = start_index + self.number_of_sensors * self.samples_per_frame
            self.data_elements[key]["value"] = np.array([float(x) for x in data[start_index:end_index]]).reshape((self.samples_per_frame, self.number_of_sensors))

    def get_dataframe(self):
        if(self.metadata_elements["Year"]["value"]==0):
            start_datetime = datetime.datetime(2020, 1, 1, tzinfo=pytz.timezone("UTC"))
        else:
            start_datetime = datetime.datetime(year=self.metadata_elements["Year"]["value"],
                                               month=self.metadata_elements["Month"]["value"],
                                               day=self.metadata_elements["Day"]["value"],
                                               hour=self.metadata_elements["Hours"]["value"],
                                               minute=self.metadata_elements["Minutes"]["value"],
                                               second=self.metadata_elements["Seconds"]["value"],
                                               tzinfo=pytz.timezone("UTC"))
        #print(start_datetime)
        #print(self.metadata_elements["SampleFrameStart"]["value"])
        frame_start_datetime = start_datetime+datetime.timedelta(milliseconds=self.metadata_elements["SampleFrameStart"]["value"])
        #print(frame_start_datetime)
        timestamps = [start_datetime+datetime.timedelta(milliseconds=self.metadata_elements["SampleFrameStart"]["value"]) + i*datetime.timedelta(milliseconds=1000) for i in range(0, self.samples_per_frame)]
        df_data = {
            "Node": [self.metadata_elements["Node"]["value"]] * self.samples_per_frame,
            "Latitude": [self.metadata_elements["Lat"]["value"]] * self.samples_per_frame,
            "Longitude": [self.metadata_elements["Lon"]["value"]] * self.samples_per_frame,
            "Datetime": timestamps
        }
        for i, sensor_name in enumerate(self.sensor_names):
            df_data[sensor_name] = self.data_elements["SensorData"]["value"][:,i]

        df = pd.DataFrame.from_dict(df_data)
        return df


data_file = Path("/home/jepaki/Projects/Objects/LoRaDualbandTesting/LORA__01_2025_03_19.txt")
with open(data_file) as f:
    lines = f.readlines()
    header = lines[0].strip()
    cols = header.split(',')
    parser = LoraRecorderDataParser(cols)

    record = lines[1].strip()
    parser.parse_data_string(record)
    rec_df = parser.get_dataframe()

    for i in range(2, len(lines)):
        if i%100 == 0:
            print(f'{i}/{len(lines)}')
        record = lines[i].strip()
        parser.parse_data_string(record)
        new_rec_df = parser.get_dataframe()
        rec_df = pd.concat([rec_df, new_rec_df])

print(rec_df.head())

fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(10,8))
nodes = rec_df["Node"].unique()

for node in nodes:
    node_df = rec_df[rec_df["Node"] == node]
    for i, name in enumerate(["A0", "A1", "A2"]):
        axs[i].plot(node_df.Datetime, node_df[name], label=f'Node {node}')

for i, name in enumerate(["A0", "A1", "A2"]):
    axs[i].legend()
    axs[i].set_ylabel(name)
axs[0].set_title("Dualband LoRa Datalog")
plt.show()