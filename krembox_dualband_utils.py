import datetime
import geopandas as gpd


def parse_header(fields, header):
    dt = datetime.datetime(year=int(header[fields.index('YEAR')]),
                           month=int(header[fields.index('MONTH')]),
                           day=int(header[fields.index('DAY')]),
                           hour=int(header[fields.index('HOURS(UTC)')]),
                           minute=int(header[fields.index('MINUTES')]),
                           second=int(header[fields.index('SECONDS')]),
                           tzinfo=datetime.timezone.utc)
    lat, lon = int(header[fields.index('LATITUDE(deg/100000)')]) / 1000000, \
               int(header[fields.index('LONGITUDE(deg/100000)')]) / 1000000

    sample_freq = float(header[fields.index('SAMPLE-RATE(Hz)')])
    return dt, lat, lon, sample_freq

def associate_data2burnplot(rad_data_gdf: gpd.GeoDataFrame, burn_plot_gdf: gpd.GeoDataFrame):
    burn_plot_ids = []
    for i, rad_data_row in rad_data_gdf.iterrows():
        for j, burn_plot_row in burn_plot_gdf.iterrows():
            if burn_plot_row.geometry.contains(rad_data_row.geometry):
                burn_plot_ids.append(burn_plot_row.Id)

    rad_data_gdf["burn_plot"] = burn_plot_ids

    print(rad_data_gdf.head())
    return rad_data_gdf


if __name__=="__main__":
    params = {
        "rad_data_dataframe": "dataframes/example_processed_dataframe.geojson",
        "burn_plot_dataframe": "dataframes/osceola_burn_plots.geojson"
    }

    rad_data_gdf = gpd.read_file(params["rad_data_dataframe"])
    burn_plot_gdf = gpd.read_file(params["burn_plot_dataframe"])

    gdf = associate_data2burnplot(rad_data_gdf, burn_plot_gdf)