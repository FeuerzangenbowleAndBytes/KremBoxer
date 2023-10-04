import getopt
import sys
import json
from pathlib import Path
import kremboxer.krembox_dualband_calibrate as kd_calibrate
import kremboxer.krembox_dualband_cleaner as kd_clean
import kremboxer.krembox_dualband_frp as kd_frp
import kremboxer.krembox_dualband_vis as kd_vis
import kremboxer.krembox_dualband_fuel_plots as kd_fuel_plots


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

    # Check if the specified output directory already exists and warn the user
    output_root = Path(params["output_root"])
    burn_name = params["burn_name"]
    if output_root.exists() and not params["overwrite"]:
        print("Warning! Output directory already exists: ", output_root)
        print("Should we continue? (y/n)")
        response = input()
        if response != "y":
            print("Exiting...")
            sys.exit(0)
    else:
        output_root.mkdir(parents=True, exist_ok=True)

    # Run detector calibration if requested
    if params["run_calibration"]:
        print("Running dualband calibration")
        cal_params = params["calibration_parameters"]
        cal_params["output_root"] = output_root
        cal_params["burn_name"] = burn_name
        kd_calibrate.run_krembox_dualband_calibration(params["calibration_parameters"])

    # Clean data if requested
    if params["run_data_cleaner"]:
        print("Running dualband data cleaner")
        cleaner_params = params["data_cleaner_parameters"]
        cleaner_params["output_root"] = output_root
        cleaner_params["burn_name"] = burn_name
        cleaned_gdf = kd_clean.run_krembox_dualband_cleaner(cleaner_params)

    # Process cleaned data and compute FRP
    if params["run_frp_computation"]:
        print("Running dualband FRP computation")
        frp_params = params["frp_parameters"]
        frp_params["output_root"] = output_root
        frp_params["burn_name"] = burn_name
        processed_gdf = kd_frp.run_krembox_dualband_frp(frp_params)

    # Associate dualband data with fuel plots
    if params["run_fuel_plot_association"]:
        print("Running fuel plot association")
        assoc_params = params["fuel_plot_association_parameters"]
        assoc_params["output_root"] = output_root
        assoc_params["burn_name"] = burn_name
        kd_fuel_plots.run_krembox_dualband_fuel_plot_association(assoc_params)

    # Run visualizer to make FRP plots, animations, and burn plot maps
    if params["run_visualizer"]:
        print("Running visualizer")
        vis_params = params["vis_parameters"]
        vis_params["output_root"] = output_root
        vis_params["burn_name"] = burn_name
        kd_vis.run_krembox_dualband_vis(vis_params)


if __name__ == "__main__":
    main(sys.argv[1:])
