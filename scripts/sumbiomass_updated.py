import geopandas as gpd
import pandas as pd


def sum_rows_by_title(input_file, output_file, title_column, group_column, sum_columns):
    '''
    This function will first read the data collections for all three 'Stratum' sets of each macroplot, and will create a table
    of summed rows for each fuel type in each macroplot. 'Postburn' and 'preburn' fuel collections will be separated
    into two rows.


    '''

    # Read the Excel spreadsheet
    df = pd.read_excel(input_file, 'Biomass')

    # Group the rows by the title column and additional group column, and sum the specified columns
    grouped = df.groupby([title_column, group_column])[sum_columns].sum()

    # Sum all biomass values
    sumbiomass_df = pd.DataFrame(grouped)
    sumbiomass_df['SumBiomass'] = sumbiomass_df[sum_columns].sum(axis=1)

    # Find the mass difference in grams
    sumbiomass_df['Mass difference in grams'] = sumbiomass_df['SumBiomass'].diff()
    sumbiomass_df['Mass difference in grams'].iloc[::2] = None

    # grams to kg all hours
    sumbiomass_df['Mass difference grams to kg_allhrs'] = sumbiomass_df['Mass difference in grams'].div(1000)

    #FRE all hours
    '''
    FRE is calculated using this equation: Mc = FRE / (Fr*Hc), where Mc is the fuel mass consumed per unit area (summed 
    biomass collections for each AOI), Hc is the heat of combusion of the fuel, and Fr is the fraction of the total 
    energy release (per unit area) that is transported by radiation
    '''
    sumbiomass_df['FRE_allhrs'] = sumbiomass_df['Mass difference grams to kg_allhrs'].mul(.3*20)
        # Radiative fraction = .3, heat of combusion = 20

    '''
    Clip plots were 0.5mx0.5mx and we are converting the units in the denominator to m^2 to compare to radiometer 
    outputs
    '''
    #Adjusted FRE all hours
    sumbiomass_df['FRE_allhrsadjusted'] = sumbiomass_df['FRE_allhrs'].mul(4)

    '''
    Total Energy is found by multiplying biomass difference in kg by heat of combusti
    '''
    #Total Energy all hours
    sumbiomass_df['Total Energy_allhrs'] = sumbiomass_df['Mass difference grams to kg_allhrs'].mul(20)

    #Adjusted Total Energy all hours
    sumbiomass_df['Total Energy_allhrsadjusted'] = sumbiomass_df['Total Energy_allhrs'].mul(4)

    #Sum all biomass values except for 10, 100, 1000hr columns
    sumbiomass_df['SumBiomass_1hr'] = sumbiomass_df[sum_columns1hr].sum(axis=1)

    # Find the mass difference in grams except for 10, 100, 1000hr columns
    sumbiomass_df['Mass difference in grams_1hr'] = sumbiomass_df['SumBiomass_1hr'].diff()
    sumbiomass_df['Mass difference in grams_1hr'].iloc[::2] = None

    # grams to kg 1 hours
    sumbiomass_df['Mass difference grams to kg_1hr'] = sumbiomass_df['Mass difference in grams_1hr'].div(1000)

    # FRE 1 hours
    sumbiomass_df['FRE_1hr'] = sumbiomass_df['Mass difference grams to kg_1hr'].mul(.3 * 20)
    # Radiative fraction = .3, heat of combustion = 20

    # Adjusted FRE 1 hours
    sumbiomass_df['FRE_1hradjusted'] = sumbiomass_df['FRE_1hrs'].mul(4)

    # Total Energy 1 hours
    sumbiomass_df['Total Energy_1hr'] = sumbiomass_df['Mass difference grams to kg_1hr'].mul(20)

    #Adjusted Total Energy 1 hours
    sumbiomass_df['Total Energy_1hradjusted'] = sumbiomass_df['Total Energy_1hr'].mul(4)


    #Sum all biomass values except for 1, 10, 100, 1000hr columns
    sumbiomass_df['SumBiomass_nohrs'] = sumbiomass_df[sum_columnsnohrs].sum(axis=1)

    # Find the mass difference in grams except for 1, 10, 100, 1000hr columns
    sumbiomass_df['Mass difference in grams_nohrs'] = sumbiomass_df['SumBiomass_nohrs'].diff()
    sumbiomass_df['Mass difference in grams_nohrs'].iloc[::2] = None

    # grams to kg no hours
    sumbiomass_df['Mass difference grams to kg_nohrs'] = sumbiomass_df['Mass difference in grams_nohrs'].div(1000)

    # FRE no hours
    sumbiomass_df['FRE_nohrs'] = sumbiomass_df['Mass difference grams to kg_1hr'].mul(.3 * 20)
    # Radiative fraction = .3, heat of combustion = 20

    # Adjusted FRE no hours
    sumbiomass_df['FRE_nohrsadjusted'] = sumbiomass_df['FRE_nohrs'].mul(4)

    # Total Energy no hours
    sumbiomass_df['Total Energy_nohrs'] = sumbiomass_df['Mass difference grams to kg_nohrs'].mul(20)

    # Total Energy no hours adjusted
    sumbiomass_df['Total Energy_nohrsadjusted'] = sumbiomass_df['Total Energy_nohrs'].mul(4)


    # Save the results to a new sheet in the same Excel file
    # with pd.ExcelWriter(
    #         output_file,
    #         mode="a",
    #         engine="openpyxl",
    #         if_sheet_exists="replace"
    # ) as writer:
    #     sumbiomass_df.to_excel(writer, sheet_name='Summed Rows', index=True)
    sumbiomass_df.to_csv(output_file, mode="w")

    print("Summed rows saved to", output_file)


# Inputs
#input_file = 'J://project//SERDP_Objects-IRProcessing//workingdir//dnvanhui//Biomassexcelsheets//testpythoncode//FS_Biomass_2022.xlsx'  # Replace with your input file path
input_file = 'C://Users//dnvanhui.MTRI//Desktop//Test Projects//Kremboxer//FS_Biomass_2022.xlsx'  # Replace with your input file path
#output_file = 'J://project//SERDP_Objects-IRProcessing//workingdir//dnvanhui//Biomassexcelsheets//testpythoncode//FS_Biomass_2022.xlsx'  # Replace with your output file path
output_file = 'C://Users//dnvanhui.MTRI//Desktop//Test Projects//Kremboxer//FS_Biomass_2022.csv'  # Replace with your output file path
title_column = 'Macroplot'  # Replace with your title column name
group_column = 'Plot_Type'  # Replace with your additional group column name
sum_columns = ["WLive", "WLit", "1hr", "10hr", "100hr", "1000hr", "PC", "CL", "PN", "ETE", "FL", "CYLitter",
               "CoarseChar", "FineChar", "ND"]  # Replace with the columns you want to sum
sum_columns1hr = ["WLive", "WLit", "1hr", "PC", "CL", "PN", "ETE", "FL", "CYLitter",
               "CoarseChar", "FineChar", "ND"]
sum_columnsnohrs = ["WLive", "WLit", "PC", "CL", "PN", "ETE", "FL", "CYLitter",
               "CoarseChar", "FineChar", "ND"]

sum_rows_by_title(input_file, output_file, title_column, group_column, sum_columns)