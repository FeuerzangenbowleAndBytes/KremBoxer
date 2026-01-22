import csv
from pathlib import Path
import kremboxer.utils.common_utils as kucu


def is_dualband_file(file: Path) -> bool:
    csvreader = csv.reader(open(file, 'r'))
    row1 = next(csvreader, None)
    row2 = next(csvreader, None)
    row3 = next(csvreader, None)
    if row1[0] == "DAY" and row1[6] == "SAMPLE-RATE(Hz)" and row3[1] == "LW-A":
        return True
    return False


def construct_dualband_header_dict(header_titles, header_values):
    header_dict = {}
    header_dict['DAY'] = int(header_values[0])
    header_dict['MONTH'] = int(header_values[1])
    header_dict['YEAR'] = int(header_values[2])
    header_dict['HOURS(UTC)'] = int(header_values[3])
    header_dict['MINUTES'] = int(header_values[4])
    header_dict['SECONDS'] = int(header_values[5])
    header_dict['SAMPLE-RATE(Hz)'] = float(header_values[6])
    header_dict['LATITUDE'] = float(header_values[7]) / 1000000
    header_dict['LONGITUDE'] = float(header_values[8]) / 1000000
    header_dict['GPS-TYPE'] = str(header_values[9])
    header_dict["DATETIME_START"] = kucu.construct_datetime(header_dict["YEAR"],
                                                            header_dict["MONTH"],
                                                            header_dict["DAY"],
                                                            header_dict["HOURS(UTC)"],
                                                            header_dict["MINUTES"],
                                                            header_dict["SECONDS"])
    return header_dict
