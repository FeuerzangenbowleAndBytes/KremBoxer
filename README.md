# Kremboxer
This Python 3 code performs calibration and FRP computation with data gathering by the dualband 'krembox' detectors.  More documentation will follow, but for now here is a quick start guide.  

**NOTE**: So far this has only been tested on Ubuntu, but in principle it should work on Windows and Mac too.  We might just need to work through some OS specific file path issues.

The repo includes data for the sensor bandpasses, temperature sensor calibration, and blackbody calibration data for one of Bob's radiometers in `calibration_data`.  This calibration data is valid for the radiometers used during the Osceola and Fort Stewart 2022 prescribed burns.  Note that the calibration from one radiometer (unit 11, in this case) is applied to all the datasets.  We believe that this is adequate because Bob has seen that the sensor have nearly ideentical responses.  However, this shortcut should be checked for any new batch of sensors.

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

* run_calibration (bool) - whether to run the calibration routine, which creates models for the sensor response vs radiance from blackbody calibration data
* run_data_cleaner (bool) - whether to run the cleaning routine, which extracts the datasets from specified days and separates each into its own file
* run_frp_computation (bool) - whether to run the dualband calibration routine to copmute FRP
* calibration_parameters
  * cal_output (string) - path to output the calibration coefficients (as a JSON file)
  * LW_bandpass (string) - path to the bandpass data for the LW sensor (CSV)
  * MW_bandpass (string) - path to the bandpass data for the MW sesnor (CSV)
  * cal_input (string) - blackbody calibration data for one of the sensors. (CSV) Note that the same calibration is used for all datasets - Bob says this should be fine for a given batch of sensors.
  * temp_cal_input (string) - data to match the resistance of the internal temperature sensor to radiometer temperature (CSV)
  * show_plot (bool) - whether to display the steps of the calibration routine
  * plot_output (string) - where to store a plot of the steps in the calibration routine (PNG)
  * v_top (float) - voltage in mV across the internal temperature sensor voltage divider
  * r_top (float) - resistance in Ohms of the resistor that makes up the internal temperature sensor voltage divider
* data_cleaner_parameters 
  * data_directories (list[string]) - list of folders containing data to process
  * target_dates (list[date strings]) - list of dates we are interested in, the cleaner will only extract datasets from these dates (year-month-day format, ex. 2022-02-04 is Feb 4, 2022)
  * clean_datafrom_output (string) - where to store the dataframe of metadata on the cleaned datasets
  * burn_plot_dataframe_input (string) - GIS polygon info on the burn plots (GEOJSON)
* frp_parameters
  * clean_dataframe_output (string) - where the dataframe for the clean data lives (GEOJSON) Typically this is the same as clean_dataframe_output.
  * cal_input (string) - calibration data required for computing FRP (JSON). Typically this is the same as cal_output.
  * processed_dataframe_output (string) - where to store the dataframe of metadata on the processed datasets
