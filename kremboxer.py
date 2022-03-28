import getopt
import sys
import json
import krembox_dualband_calibrate as kd_calibrate
import krembox_dualband_cleaner as kd_clean
import krembox_dualband_frp as kd_frp


def main(argv):
    """
    Main user entry point for the Kremboxer code.  All parts of the dualband calibration and FRP computation
    can be launched by providing this script with a JSON parameter file as a command line argument
    Ex. python kremboxer.py -p paramfiles/example_paramfile.json
    :param argv:
    :return:
    """

    print("Starting Kremboxer, a code for computing FRP from 2 band radiometer data")
    print("Reading parameter file...")

    paramfile = ''
    try:
        opts, args = getopt.getopt(argv, "hp:", ["paramfile"])
    except:
        print('Usage: kremboxer.py -p <paramfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage: kremboxer.py -p <paramfile>')
            sys.exit()
        elif opt in ("-p", "--paramfile"):
            paramfile = arg

    # Load parameters
    print("Parameter file = ", paramfile)
    with open(paramfile) as json_data_file:
        params = json.load(json_data_file)
    print("Input params: ", params)

    # Run detector calibration if requested
    if params["run_calibration"]:
        print("Running dualband calibration")
        kd_calibrate.run_krembox_dualband_calibration(params["calibration_parameters"])

    # Clean data if requested
    if params["run_data_cleaner"]:
        print("Running dualband data cleaner")
        cleaned_gdf = kd_clean.run_krembox_dualband_cleaner(params["data_cleaner_parameters"])

    # Process cleaned data and compute FRP
    if params["run_frp_computation"]:
        print("Running dualband FRP computation")
        processed_gdf = kd_frp.run_krembox_dualband_frp(params["frp_parameters"])


if __name__ == "__main__":
    main(sys.argv[1:])
