import getopt
import json
import sys
from pathlib import Path
import kremboxer.utils.archive_utils


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


if __name__ == "__main__":
    main(sys.argv[1:])
