import openpyxl as openpyxl
import pandas as pd


def sum_rows_by_title(input_file, output_file, title_column, group_column, sum_columns):
    # Read the Excel spreadsheet
    df = pd.read_excel(input_file)

    # Group the rows by the title column and additional group column, and sum the specified columns
    grouped = df.groupby([title_column, group_column])[sum_columns].sum()

    # Create a new DataFrame for the results
    result_df = pd.DataFrame(grouped)

    # Save the results to a new sheet in the same Excel file
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a') as writer:
        result_df.to_excel(writer, sheet_name='Summed Rows', index=True)

    print("Summed rows saved to", output_file)


# Example usage
input_file = '//nas3//data//gis_lab//project//SERDP_Objects-IRProcessing//workingdir//dnvanhui//FS_Biomass_2022_test.xlsx'  # Replace with your input file path
output_file = '//nas3//data//gis_lab//project//SERDP_Objects-IRProcessing//workingdir//dnvanhui//FS_Biomass_2022_test.xlsx'  # Replace with your output file path
title_column = 'Macroplot'  # Replace with your title column name
group_column = 'Plot_Type'  # Replace with your additional group column name
sum_columns = ["WLive", "WLit", "1hr", "10hr", "100hr", "1000hr", "PC", "CL", "PN", "ETE", "FL", "CYLitter",
               "CoarseChar", "FineChar", "ND"]  # Replace with the columns you want to sum

sum_rows_by_title(input_file, output_file, title_column, group_column, sum_columns)
