import getopt
import json
import sys
from pathlib import Path
import kremboxer.utils.archive_utils
import kremboxer.utils.process_utils
import kremboxer.dualband.dualband_process


def main(argv):
    print("Starting Kremboxer, a code for processing fire behavior data recorded by the Krembox family of instruments")
    print("Reading parameter file...")

    paramfile = ''
    try:
        opts, args = getopt.getopt(argv, "hp:", ["paramfile"])
    except:
        print('Usage: kremboxer_driver.py -p <paramfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage: kremboxer_driver.py -p <paramfile>')
            sys.exit()
        elif opt in ("-p", "--paramfile"):
            paramfile = arg

    # Load parameters
    print("Parameter file = ", paramfile)
    with open(paramfile) as json_data_file:
        params = json.load(json_data_file)
    print("Input params: ", params)

    # Check if the specified output directory already exists and warn the user
    archive_root = Path(params["archive_dir"])
    burn_name = params["burn_name"]
    if archive_root.exists() and not params["overwrite"]:
        print("Warning! Archive directory already exists: ", archive_root)
        print("Should we continue? (y/n)")
        response = input()
        if response != "y":
            print("Exiting...")
            sys.exit(0)
    else:
        archive_root.mkdir(parents=True, exist_ok=True)

    # Create the dataset archive if requested
    if params["run_create_dataset_archive"]:
        print("Creating dataset archive")
        archive_params = params["create_dataset_archive_params"]
        archive_params["archive_dir"] = archive_root
        archive_params["burn_name"] = burn_name
        kremboxer.utils.archive_utils.create_dataset_archive(archive_params)

    # Process each dataset
    if params["run_data_processing"]:
        print("Processing raw radiometer data")
        process_params = params["data_processing_params"]
        process_params["archive_dir"] = archive_root
        process_params["burn_dates"] = params["burn_dates"]
        kremboxer.utils.process_utils.run_data_processing(process_params)

    print("Done!")
    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
