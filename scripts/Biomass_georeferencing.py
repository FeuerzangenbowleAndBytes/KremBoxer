import geopandas as gpd
import pandas as pd

''' 
Reads an excel file and creates a geodataframe with point geometries based on latlong columns
then will eventually join output file from sumbiomass_updated to latlongs
'''
def creatingbiomass_shapefile(latlongs, output_shapefile):

    # read excel file into pandas dataframe
    latlongdf = pd.read_excel(latlongs, sheet_name='Sheet1')

    # create dataframe with latlong values
    if 'latitude' in latlongdf.columns and 'longitude' in latlongdf.columns:
        georeference = gpd.points_from_xy(latlongdf['longitude'], latlongdf['latitude'])
        crs = custom_crs if custom_crs else 'EPSG:4326'
        firegdf = gpd.GeoDataFrame(latlongdf, geometry=georeference, crs=crs) #assuming standard WGS 84

        # Export the geodataframe to a shapefile
        #firegdf.to_file(output_shapefile)
    else:
        raise ValueError('Lat and long values not found in Excel file')

    #now bring in biomass data from sumbiomass.py
    biomass_data = pd.read_csv(input_file)

    #remove preburn data before conducting the join



    merged_biomassdf = pd.merge(firegdf, biomass_data, left_on='plot_clean', right_on='Macroplot', how='left')
    merged_biomassdf.to_file(output_shapefile)

    #Inputs
from sumbiomass_forgeoreferencing import output_file
input_file = output_file
latlongs = "C://Users//dnvanhui.MTRI//Desktop//Test Projects//Kremboxer//ft_stewart_2022_lat_long.xlsx"
output_shapefile = "C://Users//dnvanhui.MTRI//Desktop//Test Projects//Kremboxer//ftstewartbiomass.shp"
custom_crs = 'EPSG:4326' #change to desired projection

creatingbiomass_shapefile(latlongs, output_shapefile)

