import csv
from pathlib import Path


def is_ufm_file(file: Path) -> bool:
    csvreader = csv.reader(open(file, 'r'))
    row1 = next(csvreader, None)
    row2 = next(csvreader, None)
    row3 = next(csvreader, None)
    if row1[0] == "UNIT" and row3[0] == "SensTH" and row3[4] == "Flow":
        return True
    return False
