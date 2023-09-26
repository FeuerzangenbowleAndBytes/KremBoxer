import getopt
import sys
import json
import kremboxer.krembox_dualband_calibrate as kd_calibrate
import kremboxer.krembox_dualband_cleaner as kd_clean
import kremboxer.krembox_dualband_frp as kd_frp
import kremboxer.krembox_dualband_vis as kd_vis


def main(argv):
    """
    Main user entry point for the Kremboxer code.  All parts of the dualband calibration and FRP computation
    can be launched by providing this script with a JSON parameter file as a command line argument

    Ex. python -m kremboxer.kremboxer -p paramfiles/example_paramfile.json

    :param argv: Command line parameters passed from the system.  Will be parsed to extract the parameter file.
    :return:
    :group: kremboxer
    """

    print("Starting Kremboxer, a code for computing FRP from 2 band radiometer data")
    print("Reading parameter file...")

    paramfile = ''
    try:
        opts, args = getopt.getopt(argv, "hp:", ["paramfile"])
    except:
        print('Usage: krembox_driver.py -p <paramfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage: krembox_driver.py -p <paramfile>')
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

    # Run visualizer to make FRP plots, animations, and burn plot maps
    if params["run_visualizer"]:
        print("Running visualizer")
        kd_vis.run_krembox_dualband_vis(params["vis_parameters"])


if __name__ == "__main__":
    main(sys.argv[1:])
