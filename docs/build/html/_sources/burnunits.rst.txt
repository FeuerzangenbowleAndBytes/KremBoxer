Burn Units Data
==================

KremBoxer can use a GeoJSON file that describes the burn units to determine the burn unit for each radiometer dataset.
This GeoJSON file is provided via the optional parameter `data_cleaner_parameters/burn_plot_dataframe_input` in the JSON parameter file for the processing run.
The actual matching of datasets to burn units occurs in the **Cleaning** processing step.

The GeoJSON file must have the following properties:

#. Each burn unit must have a `geometry` attribute that is a Polygon.

#. Each burn unit must have a unique `Id` attribute that is a string.
