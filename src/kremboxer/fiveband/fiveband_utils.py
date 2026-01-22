import csv
from pathlib import Path


def is_fiveband_file(file: Path) -> bool:
    csvreader = csv.reader(open(file, 'r'))
    row1 = next(csvreader, None)
    if row1[0] == "TIME" and row1[7] == "COURSE" and row1[10] == "3.95":
        return True
    return False
