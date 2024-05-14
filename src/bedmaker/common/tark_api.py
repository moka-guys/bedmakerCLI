"""Functions for using the Ensembl TARK API."""

import pandas as pd
from datetime import datetime

from bedmaker.common.models import Transcript, Exon, ManeList, GenomicRange, Utr
from bedmaker.common.exceptions import InvalidTranscriptId
import httpx
import asyncio
from typing import List, Dict, Optional, Union
from pydantic import BaseModel
from dataclasses import dataclass


@dataclass
class SelectedTranscripts:
    """
    Class to hold the returned MANE transcript data.
    While most transcripts will have a single MANE transcript, some will not have a MANE transcript,
    while others will have a MANE transcript and an additional Clinical Plus transcript.
    This class allows for returning a standard object to downstream functions no matter what is
    returned.
    """

    requested_id: str
    mane_transcript: Optional[Transcript]
    clinical_plus_transcript: Optional[Transcript]
    mane_transcript_found: bool = False
    clinical_plus_transcript_found: bool = False
    is_mane_transcript_requested: bool = False
    is_clinical_plus_requested: bool = False
    are_additional_transcripts_requested: bool = False
    all_transcript_version_ids = List[str]
    non_coding_gene: bool = False


class MANETranscriptFetcher:
    """
    This class fetchs transcript data via the TARK (Transcript Archive) API.

    It provides a set of methods for fetching MANE (Matched Annotation from NCBI and EMBL-EBI) transcripts

    MANE transcripts are minimal set of matching RefSeq and Ensembl transcripts of human
    protein-coding genes, where the transcripts from a matched pair are identical
    (5' UTR, coding region and 3' UTR), but retain their respective identifiers.

    The MANE transcript set is classified into two groups or mane_type:

    1) MANE Select: One high-quality representative transcript per protein-coding gene that is well-supported by
    experimental data and represents the biology of the gene.
    2) MANE Plus Clinical: Transcripts chosen to supplement MANE Select when needed for clinical variant reporting.
    Only a small subset of genes have a MANE Plus Clinical transcript.

    If a MANE transcript is available for a gene, it is the recommended transcript to use for variant reporting and
    will be returned by default.  If a user has specified a different version of a transcript, when a MANE transcript
    is available they will be prompted to explicitly override this recommendation.

    The class  provides a warning when either a "MANE SELECT" or "CLINICAL PLUS" transcript has been requested without
    its paired "CLINICAL PLUS" or "MANE SELECT" transcript respectively.

    MANE transcripts are not available for non-coding genes, and a small subset of unpaired coding genes.  If there is a single
    trahnscript version available for the requested transcript that will be returned, if there are multiple versions the user
    will will be prompted ,to supply the version required.
    """

    def __init__(self):
        # Set the server_url to the base URL of the TARK API
        self.server_url = "http://tark.ensembl.org/"
        # Async HTTP client session is initiated here for re-use in multiple requests
        self.client = httpx.AsyncClient()

    def check_id_type(self, stable_id: str) -> str:
        """Check whether the provided ID is an Ensembl or RefSeq ID."""
        if stable_id.startswith("ENST"):
            return "ensembl"
        elif stable_id.startswith(("NM_", "NR_")):
            return "refseq"
        else:
            raise InvalidTranscriptId(
                f"Invalid transcript ID format: {stable_id}. "
                "Transcript ID must start with 'ENST', 'NM_' or 'NR_'"
            )

    def is_id_version_included(self, stable_id: str) -> bool:
        """Check whether the provided ID includes a version number."""
        split_stable_id = stable_id.split(".")
        if len(split_stable_id) == 1:
            return False
        if len(split_stable_id) == 2 and split_stable_id[1].isdigit():
            return True
        raise InvalidTranscriptId(
            f"Invalid transcript ID format: {stable_id}."
            "Transcript ID must have at most one version number."
        )

    def check_if_mane_transcript(self, mane_transcript: Transcript) -> bool:
        """Check whether the provided transcript is a MANE transcript."""
        return mane_transcript.mane_type is None

    async def fetch_mane_list(self) -> pd.DataFrame:
        """
        Fetch a list of all MANE transcripts using an async HTTP client.  The function returns a pandas DataFrame
        containing the stable IDS
        """
        ext = "/api/transcript/manelist/"
        response = await self.client.get(self.server_url + ext)
        if response.status_code != 200:
            raise ValueError("Failed to retrieve data for MANE transcripts.")
        json_data = response.json()

        return json_data

    def parse_mane_list(self, data: dict) -> List[ManeList]:
        """
        Parses the JSON data returned by the TARK API and constructs a list of ManeList objects.
        """
        mane_lists = []  # Initialize an empty list to store the parsed ManeList objects
        current_date = (
            datetime.now()
        )  # Record the current date to include in each ManeList object
        for result in data["results"]:  # Loop over each result in the data
            mane_data = ManeList(
                ens_stable_id=result["ens_stable_id"],
                ens_stable_id_version=result["ens_stable_id_version"],
                refseq_stable_id=result["refseq_stable_id"],
                refseq_stable_id_version=result["refseq_stable_id_version"],
                mane_type=result["mane_type"],
                ens_gene_name=result["ens_gene_name"],
                access_date=current_date,
            )
            mane_lists.append(
                mane_data
            )  # Add each constructed ManeList object to the list
        return mane_lists

    async def fetch_mane_transcript(self, stable_id: str) -> SelectedTranscripts:
        """
        Fetch MANE transcripts for a single stable ID using an async HTTP client.  The function can
        use either the ensembl or RefSeq stable ID for a transcript.

        It returns a ManeTranscripts object which will contain either contain:
        - A single MANE transcript
        - Both a MANE and Clinical Plus transcript
        - No MANE transcript if the gene is non-coding or has no MANE transcript
        """
        ext = f"/api/transcript/?stable_id={stable_id}&assembly_name=GRCh38&expand=transcript%2C%20exons%2C%20genes"
        response = await self.client.get(self.server_url + ext)
        # if response.status_code != 200:
        #     return {
        #         stable_id: {
        #             "error": f"Failed to retrieve data for stable ID {stable_id}."
        #         }
        #     }

        data = response.json()
        result = self.parse_transcript_data(data)
        return result

    async def fetch_multiple_transcripts(
        self, stable_ids: List[str]
    ) -> List[SelectedTranscripts]:
        """
        Fetches multiple transcripts when provided with a list of stable IDs using an async HTTP client.
        """
        # List comprehension to create a list of tasks for fetching each transcript
        tasks = [self.fetch_mane_transcript(stable_id) for stable_id in stable_ids]
        results = await asyncio.gather(*tasks)
        return results

    def parse_transcript_data(self, data: dict) -> list:
        """
        Parses the JSON data returned by the TARK API and constructs a list of SelectedTranscripts objects.
        Each SelectedTranscripts object will represent a separate transcript version.
        """
        transcripts = SelectedTranscripts()

        for result in data.get("results", []):
            if "mane_transcript_type" in result:
                exons = [
                    Exon(
                        exon_id=exon.get("exon_id"),
                        exon_id_version=exon.get("exon_version"),
                        genomic_ranges=GenomicRange(
                            range_id="range_id",
                            loc_start=exon.get("loc_start"),
                            loc_end=exon.get("loc_end"),
                            loc_strand=exon.get("loc_strand"),
                            loc_region=exon.get("loc_region"),
                            loc_checksum=exon.get("loc_checksum"),
                        ),
                        exon_checksum=exon.get("exon_checksum"),
                    )
                    for exon in result.get("exons", [])
                ]

                utrs = [
                    Utr(
                        utr_id=utr.get("exon_id"),
                        ens_stable_id=utr.get("ens_stable_id"),
                        genomic_ranges=GenomicRange(
                            range_id="range_id",
                            loc_start=utr.get("loc_start"),
                            loc_end=utr.get("loc_end"),
                            loc_strand=utr.get("loc_strand"),
                            loc_region=utr.get("loc_region"),
                            loc_checksum=utr.get("loc_checksum"),
                        ),
                    )
                    for utr in result.get("utrs", [])
                ]
                ens_stable_id = None
                ens_stable_id_version = None
                refseq_stable_id = None
                refseq_stable_id_version = None
                if self.check_id_type(result.get("stable_id", "")) == "ensembl":
                    ens_stable_id = result.get("stable_id")
                    ens_stable_id_version = result.get("stable_id_version")
                elif self.check_id_type(result.get("stable_id", "")) == "refseq":
                    refseq_stable_id = result.get("stable_id")
                    refseq_stable_id_version = result.get("stable_id_version")

                selected_transcript = Transcript(
                    request_id="placeholder",
                    ens_stable_id=ens_stable_id,
                    ens_stable_id_version=ens_stable_id_version,
                    refseq_stable_id=refseq_stable_id,
                    refseq_stable_id_version=refseq_stable_id_version,
                    assembly=result.get("assembly"),
                    biotype=result.get("biotype"),
                    transcript_checksum=result.get("transcript_checksum"),
                    mane_type=result.get("mane_transcript_type"),
                    gene_name=result.get("genes", [{}])[0].get("name"),
                    gene_id=result.get("genes", [{}])[0].get("stable_id"),
                    gene_id_version=result.get("genes", [{}])[0].get(
                        "stable_id_version"
                    ),
                    genomic_ranges=GenomicRange(
                        range_id="range_id",
                        loc_start=result.get("loc_start"),
                        loc_end=result.get("loc_end"),
                        loc_strand=result.get("loc_strand"),
                        loc_region=result.get("loc_region"),
                        loc_checksum=result.get("loc_checksum"),
                    ),
                    exons=exons,
                    utrs=utrs,
                    exon_set_checksum=result.get("exon_set_checksum"),
                )
                if result.get("mane_transcript_type") == "MANE Select":
                    SelectedTranscripts.mane_transcript = selected_transcript
                    SelectedTranscripts.is_mane_transcript = True
                elif result.get("mane_transcript_type") == "MANE Plus Clinical":
                    SelectedTranscripts.clinical_plus_transcript = selected_transcript
                    SelectedTranscripts.is_clinical_plus_transcript = True

        return transcripts

    async def close(self):
        await self.client.aclose()
