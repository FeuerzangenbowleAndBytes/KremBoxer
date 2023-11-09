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
        firegdf = gpd.GeoDataFrame(latlongdf, georeference=georeference, crs='EPSG:4326') #assuming standard WGS 84

        # Export the geodataframe to a shapefile
        firegdf.tofile(output_shapefile)
    else:
        raise ValueError('Lat and long values not found in Excel file')


    #Inputs
#from sumbiomass_updated import output_file
#input_file = output_file
latlongs = "C://Users//dnvanhui.MTRI//Desktop//Test Projects//Kremboxer//ft_stewart_2022_lat_long.xlsx"
output_shapefile = "C://Users//dnvanhui.MTRI//Desktop//Test Projects//Kremboxer//ftstewartbiomass.shp"

creatingbiomass_shapefile(latlongs, output_shapefile)