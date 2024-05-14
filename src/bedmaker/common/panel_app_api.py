import requests
import sys, os
import pandas as pd

import httpx
import asyncio


def get_panel_app_list():
    """
    Queries the Panel App API to return details on all signed off Panels

    :return: Pandas dataframe, Columns:id, hash_id, name, disease_group, disease_sub_group, status version, version_created, relevant_disorders, types, stats.number_of_genes, stats.number_of_strs, stats.number_of_regions
    :rtype: pandas dataframe
    """
    server = "https://panelapp.genomicsengland.co.uk"

    ext = f"/api/v1/panels/signedoff/"
    r = requests.get(server + ext, headers={"Content-Type": "application/json"})

    # Send informative error message if bad request returned
    if not r.ok:
        r.raise_for_status()
        sys.exit()

    expected_panels = r.json()["count"]

    # df columns: 'Name', 'DiseaseSubGroup', 'DiseaseGroup', 'CurrentVersion', 'CurrentCreated', 'Number_of_Genes',
    # 'Number_of_STRs', 'Number_of_Regions', 'Panel_Id', 'Relevant_disorders', 'Status', 'PanelTypes'
    GEL_panel_app_df = pd.json_normalize(r.json(), record_path=["results"])

    # Reiterate over remaining pages of data
    while r.json()["next"] is not None:

        r = requests.get(r.json()["next"], headers={"Content-Type": "application/json"})
        GEL_panel_app_df = GEL_panel_app_df.append(
            pd.json_normalize(r.json(), record_path=["results"])
        )

    return GEL_panel_app_df


def get_panel_app_genes(panel_id, panel_version, genome_build):

    server = "https://panelapp.genomicsengland.co.uk"

    ext = f"/api/v1/panels/{panel_id}/genes/?version={panel_version}"
    print(f"{server}{ext}")
    r = requests.get(server + ext, headers={"Content-Type": "application/json"})

    # Send informative error message if bad request returned
    if not r.ok:
        r.raise_for_status()
        sys.exit()

    decoded = r.json()
    gene_list = []
    for entry in decoded.get("results"):
        gene_list.append(entry.get("gene_data").get("gene_symbol"))

    return gene_list
