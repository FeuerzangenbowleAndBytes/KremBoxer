import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from kremboxer.utils import greybody_utils


def find_nearest(array, value):
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        return array[idx-1]
    else:
        return array[idx]


def interpolate_bandpass_data(lambdas: np.array, trans: np.array, dl: float, l_min: float, l_max: float):
    lambdas_interp = np.arange(l_min, l_max, dl, dtype=float)
    trans_interp = np.zeros_like(lambdas_interp)

    # Clean up small noisy negative transmission measurements
    trans[trans < 0] = 0
    for i in range(0, len(lambdas_interp)):
        # If trying to interpolate outside the range of the original bandpass data, set transmission to 0
        if lambdas_interp[i] < lambdas[0] or lambdas_interp[i] > lambdas[-1]:
            trans_interp[i] = 0
        else:
            idx = np.searchsorted(lambdas, lambdas_interp[i], side="left")
            trans_interp[i] = trans[idx]

    return lambdas_interp, trans_interp


def interpolate_bandpass_files(input_dir: Path, bandpass_files, output_dir: Path,
                               dl: float, l_min: float, l_max: float):

    output_dir.mkdir(exist_ok=True, parents=False)
    fig, axs = plt.subplots(2, 1, figsize=(8, 12))

    for bandpass_file in bandpass_files:
        bandpass_path = input_dir.joinpath(bandpass_file)
        bandpass_df = pd.read_csv(bandpass_path)
        axs[0].plot(bandpass_df['Lambda[um]'], bandpass_df['T'], label=bandpass_path.stem)

        lam_interp, trans_interp = interpolate_bandpass_data(bandpass_df['Lambda[um]'].to_numpy(), bandpass_df['T'].to_numpy(), dl, l_min, l_max)
        axs[1].plot(lam_interp, trans_interp, label=bandpass_path.stem)

        bandpass_interp_df = pd.DataFrame(data={'Lambda[um]': lam_interp, 'T': trans_interp})
        bandpass_interp_df.to_csv(output_dir.joinpath(bandpass_file), index=False)

    # Add an example scaled blackbody radiance curve for comparison with bandpasses
    T = 2000
    lams_um = np.arange(l_min, l_max, dl)
    lams = lams_um*10**-6
    radiance = greybody_utils.GB_lambda(lams, T)
    radiance = radiance / np.max(radiance)
    axs[0].plot(lams_um, radiance, ls='--', label=f'Blackbody T={T}K')
    axs[1].plot(lams_um, radiance, ls='--', label=f'Blackbody T={T}K')

    axs[0].set_title("Original Bandpasses")
    axs[1].set_title("Interpolated Bandpasses")
    axs[0].legend()
    axs[1].legend()
    #axs[0].set_xlim([3.5, 4.5])
    #axs[1].set_xlim([3.5, 4.5])
    plt.savefig(bandpass_output_dir.joinpath("bandpass_interpolation_results.png"))
    plt.show()


if __name__ == "__main__":
    bandpass_input_dir = Path().home().joinpath("code", "KremBoxer", "calibration_data",
                                                "calibration_input", "fiveband", "bandpasses", "reduced")
    bandpass_output_dir = Path().home().joinpath("code", "KremBoxer", "calibration_data",
                                                 "calibration_input", "fiveband", "bandpasses", "interpolated")

    bandpass_files = ["DC-6073_W1_8-14Si.csv", "DC-6169_KRS5.csv",
                  "DC-6725_1095CWL.csv", "DC-6726_R4_395CWL.csv", "DC-6216_u1_Saph_longwave.csv"]

    interpolate_bandpass_files(bandpass_input_dir, bandpass_files, bandpass_output_dir, dl=0.01, l_min=0.1, l_max=20)
