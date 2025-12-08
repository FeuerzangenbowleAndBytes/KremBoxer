import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

pd.set_option('display.max_columns', None)


def compute_clip_plot_products(biomass_input_file: Path, biomass_data_dir: Path):
    biomass_df = pd.read_csv(biomass_input_file)

    clip_plot_ids = biomass_df["ClipPlot"].unique()
    print(clip_plot_ids)

    # Get the names of columns containing different fuel categories
    fuel_categories = list(set(biomass_df.columns) - {"Burn Unit", "ClipPlot", "Ecotype", "BurnStatus", "Stratum", "Voxel"})

    voxel_sum_data = []
    for clip_plot in clip_plot_ids:
        for burn_status in ["Post", "Pre"]:
            clip_plot_df = biomass_df[(biomass_df["ClipPlot"] == clip_plot) & (biomass_df["BurnStatus"] == burn_status)]
            ecotype = clip_plot_df["Ecotype"].unique()[0]
            burn_unit = clip_plot_df["Burn Unit"].unique()[0]
            clip_plot_biomasses = clip_plot_df[fuel_categories].sum(axis=0)
            voxel_sum_dict = {
                "ClipPlot": clip_plot,
                "BurnUnit": burn_unit,
                "Ecotype": ecotype,
                "BurnStatus": burn_status
            }
            for fuel_cat in fuel_categories:
                voxel_sum_dict[fuel_cat] = float(clip_plot_biomasses[fuel_cat])
            voxel_sum_data.append(voxel_sum_dict)
    biomass_voxel_sum_df = pd.DataFrame(voxel_sum_data)
    biomass_voxel_sum_df.to_csv(biomass_data_dir / f"{biomass_input_file.stem}_voxel_sum.csv", index=False)

    consumption_data = []
    for clip_plot in clip_plot_ids:
        try:
            clip_plot_pre = biomass_voxel_sum_df[(biomass_voxel_sum_df["ClipPlot"] == clip_plot) & (biomass_voxel_sum_df["BurnStatus"] == "Pre")].iloc[0]
            clip_plot_post = biomass_voxel_sum_df[(biomass_voxel_sum_df["ClipPlot"] == clip_plot) & (biomass_voxel_sum_df["BurnStatus"] == "Post")].iloc[0]
        except KeyError:
            print(clip_plot)

        # print(clip_plot_pre)
        # print(clip_plot_post)
        # exit()
        consumption_dict = {
            "ClipPlot": clip_plot_pre["ClipPlot"],
            "BurnUnit": clip_plot_pre["BurnUnit"],
            "Ecotype": clip_plot_pre["Ecotype"]
        }
        for fuel_cat in fuel_categories:
            consumption_dict[fuel_cat] = float(clip_plot_pre[fuel_cat]) - float(clip_plot_post[fuel_cat])
        consumption_data.append(consumption_dict)

    biomass_consumption_df = pd.DataFrame(consumption_data)
    biomass_consumption_df.to_csv(biomass_data_dir / f"{biomass_input_file.stem}_consumption.csv", index=False)

    # Now convert everything to kg, multiply by 4 to get the biomass per square meter (original clip plots are 0.5m x 0.5m), and estimate consumption energy and FRE
    for fuel_cat in fuel_categories:
        biomass_consumption_df[fuel_cat] = biomass_consumption_df[fuel_cat].mul(4).div(1000)

    biomass_sums = {
        "AllFuels": fuel_categories,
        "LitterPlus1hr": list(set(fuel_categories) - {"1000hr", "100hr", "10hr"}),
        "Litter": list(set(fuel_categories) - {"1000hr", "100hr", "10hr", "1hr"})
    }

    for fuel_group_name, fuel_cats in biomass_sums.items():
        print(fuel_group_name, fuel_cats)
        biomass_consumption_df[f'Consumption_{fuel_group_name}'] = biomass_consumption_df[fuel_cats].sum(axis=1)


    biomass_consumption_df.to_csv(biomass_data_dir / f"{biomass_input_file.stem}_kg_1m2_energy.csv", index=False)


if __name__ == '__main__':
    biomass_data_dir = Path("/ws3/gis_lab/project/SERDP_Objects-IRProcessing/FuelsData/Eglin_2023")
    biomass_input_file = biomass_data_dir / 'EAB2023BiomassData.xlsx'

    if biomass_input_file.suffix == '.xlsx':
        print("Converting clip plot data from Excel to CSV")
        biomass_df = pd.read_excel(biomass_input_file, sheet_name='EAB 2023 Biomass Data')
        biomass_csv_file = Path(biomass_data_dir) / f'{biomass_input_file.stem}.csv'
        biomass_df.to_csv(biomass_csv_file, index=False)
        biomass_input_file = biomass_csv_file
        print("CSV version saved as: {}".format(biomass_csv_file))

    compute_clip_plot_products(biomass_input_file, biomass_data_dir)