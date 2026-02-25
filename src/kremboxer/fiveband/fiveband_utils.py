import csv
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def is_fiveband_file(file: Path) -> bool:
    csvreader = csv.reader(open(file, 'r'))
    row1 = next(csvreader, None)
    if row1[0] == "TIME" and row1[7] == "COURSE" and row1[10] == "3.95":
        return True
    return False

def plot_fb_df(fb_df: pd.DataFrame, plot_title: str, output_dir: Path):
    plot_cols = ['TIME', 'LAT', 'LONG', 'TH1', '3.95', '10.95', 'TH2', 'MW', 'LW', 'WIDE']
    num_cols=2
    num_rows=int(np.ceil(len(plot_cols) / num_cols))
    fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(12, 8))
    for i, plot_col in enumerate(plot_cols):
        axs[int(i/num_cols), i%num_cols].plot(fb_df['DATETIME'], fb_df[plot_col], label=plot_col)
        axs[int(i/num_cols), i%num_cols].set_ylabel(plot_col)
        axs[int(i/num_cols), i%num_cols].tick_params(axis='x', rotation=45)
    plt.suptitle(plot_title)
    plt.tight_layout()
    plt.savefig(output_dir / f'{plot_title}_raw_data.png')
