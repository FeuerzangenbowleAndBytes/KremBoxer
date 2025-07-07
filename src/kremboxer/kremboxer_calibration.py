import getopt
import json
import sys
from pathlib import Path
import kremboxer.utils.archive_utils
import kremboxer.dualband.dualband_calibration
import kremboxer.fiveband.fiveband_calibration
import kremboxer.ufm.ufm_calibration


def main(argv):
    print("Starting Kremboxer calibration script, this code generates sensor models from calibration data for the various Krembox devices")
    print("Reading parameter file...")

    paramfile = ''
    try:
        opts, args = getopt.getopt(argv, "hp:", ["paramfile"])
    except:
        print('Usage: kremboxer_calibration.py -p <paramfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage: kremboxer_calibration.py -p <paramfile>')
            sys.exit()
        elif opt in ("-p", "--paramfile"):
            paramfile = arg

    # Load parameters
    print("Parameter file = ", paramfile)
    with open(paramfile) as json_data_file:
        params = json.load(json_data_file)
    print("Input params: ", params)

    # Perform calibration for dualband devices
    if 'dualband_calibration_parameters' in params:
        cal_params = params['dualband_calibration_parameters']
        cal_params["calibration_id"] = params["calibration_id"]
        kremboxer.dualband.dualband_calibration.compute_dualband_calibration(cal_params)
    # Perform calibration for fiveband devices
    if 'fiveband_calibration_parameters' in params:
        cal_params = params['fiveband_calibration_parameters']
        cal_params["calibration_id"] = params["calibration_id"]
        kremboxer.fiveband.fiveband_calibration.compute_fiveband_calibration(cal_params)
        # Perform calibration for fiveband devices
    if 'ufm_calibration_parameters' in params:
        cal_params = params['ufm_calibration_parameters']
        cal_params["calibration_id"] = params["calibration_id"]
        kremboxer.ufm.ufm_calibration.compute_ufm_calibration(cal_params)


if __name__ == "__main__":
    main(sys.argv[1:])
