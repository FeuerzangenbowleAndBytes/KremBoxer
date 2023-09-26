# Burn Units Data
KremBoxer can use a GEOJSON that describes the burn units to determine the burn unit for each radiometer dataset.
This GEOJSON is provided via the optional parameter `data_cleaner_parameters/burn_plot_dataframe_input` in the JSON parameter file for the processing run.
The actual matching of datasets to burn units occurs in the **Cleaning** processing step.

The GEOJSON must have the following properties:
1. Each burn unit must have a `geometry` attribute that is a Polygon.
2. Each burn unit must have a unique `Id` attribute that is a string.
