# Kremboxer
This Python 3 code performs calibration and FRP computation with data gathering by the dualband 'krembox' detectors.  More documentation will follow, but for now here is a quick start guide.  

**NOTE**: So far this has only been tested on Ubuntu, but in principle it should work on Windows and Mac too.  We might just need to work through some OS specific file path issues.

**NOTE**:  I still need to add the bandpass, temperature sensor calibration, and blackbody calibration data to this repo in order for users to run the calibration themselves.

## Installation
1. Clone the repo into the directory of your choosing
```
$ cd ~/code
$ git clone https://github.com/FeuerzangenbowleAndBytes/KremBoxer.git
```
2. Setup a Python virtual environment to run the code.
```
$ python3 -m venv ~/python_venvs/kremboxer
```
4. Activate virtual environment and install Python dependencies 
```
$ source ~/python_venvs/kremboxer/bin/activate
(kremboxer) $ pip install datetime numpy scipy matplotlib pandas geopandas
```

## Download KremBox dualband raw data
I believe Bob has uploaded all the Osceola and Fort Stewart data to the Forest Service Box, but I'll need to confirm that.  Supposing that you find the raw CSV files, you'll need to place them in a simple file structure so that KremBoxer can automate the processing.  First, pick any directory to serve as your `data_directory` - it can have whatever name you want.  Then, place the raw data files in a subfolder called `Raw`.  For example, if your `data_directory` is `~/Osceola`, then place the raw datafiles in `~/Osceola/Raw`.

## Run KremBoxer 
It is easiest to run `KremBoxer` from the command line.  The most import thing for the user to do is to provide a valid JSON parameter file that provides the local paths to the raw data and calibration datasets.  An example of a valid parameter file is located at `paramfiles/example_paramfile.json`, but you would have to modify it to reflect the paths on your computer.

```
$ cd ~/code/kremboxer
$ source ~/python_venvs/kremboxer/bin/activate
$ python kremboxer.py -p paramfiles/example_paramfile.json
```

## Parameter File
KremBoxer requires a user defined JSON parameter file to run. This file specifies things like which processing steps to run (i.e. calibration, cleaning, FRP computation) and all of the parameters needed for those steps.  There is an example parameter file demonstrating all of the possible parameters in `paramfiles/example_paramfile.json`.  Here is a description of the parameters:

* run_calibration (bool) - 
* run_data_cleaner (bool) - 
* run_frp_computation (bool) - 
* calibration_parameters
  * cal_output (string) - 
  * LW_bandpass (string) - 
  * MW_bandpass (string) - 
  * cal_input (string) - 
  * temp_cal_input (string) - 
  * show_plot (bool)
  * plot_output (string) - 
  * v_top (float) - 
  * r_top (float) - 
* data_cleaner_parameters 
  * data_directories (list[string]) - 
  * target_dates (list[date strings]) - 
  * clean_datafrom_output (string) - 
  * burn_plot_dataframe_input (string) - 
* frp_parameters
  * clean_dataframe_output (string) - 
  * cal_input (string) - 
  * processed_dataframe_output (string) - 
