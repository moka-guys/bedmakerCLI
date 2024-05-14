"""Module handles user requests, passing them on the appropriate functions."""

import asyncio
import os
from io import StringIO
import pathlib
import rich
from rich.table import Table
from rich.box import SIMPLE
from contextlib import contextmanager
from typing import List, Optional
import httpx
import pandas as pd

# import transcripts
from bedmaker.common.tark_api import MANETranscriptFetcher
import typer
from rich.console import Console
from rich import box
from rich.tree import Tree
from rich.panel import Panel
from rich.pretty import pprint
from bedmaker.common.models import Request, Transcript, Exon
from bedmaker.common.exceptions import InvalidTranscriptId
from bedmaker.transcripts.api import transcriptsDB

from bedmaker.common.db import DB
import bedmaker.transcripts


def input_file():
    """
    Record metadata about a file that is uploaded by the user
    """
    pass


class requestsDB:
    """
    Class to handle requests to the database
    """

    def __init__(self, db_path):
        self._db_path = db_path
        self._db = DB(db_path, ".requests_db")

    def mane_transcript_request(
        self, requested_id: str, requested_id_type: str
    ) -> Request:
        """
        Request a MANE transcript
        """
        pass

    def non_mane_transcript_request(
        self, requested_id: str, requested_id_type: str
    ) -> Request:
        """
        Request a non-MANE transcript
        """
        pass

    def snp_request(self, requested_id: str, requested_id_type: str) -> Request:
        """
        Request a SNP
        """
        pass

    def region_request(self, requested_id: str, requested_id_type: str) -> Request:
        """
        Request a region
        """
        pass

    def gene_request(self, requested_id: str, requested_id_type: str) -> Request:
        """
        Request a gene
        """
        pass

    def add_request(self, request: Request) -> int:
        """
        Add a request to the database
        """
        uid: str
        request_id
        requested_id_type: str
        requested_id_feature_type: Optional[str] = None  # transcript, gene, SNP, region
        requested_id_version: Optional[int] = None
        requested_date = datetime.now()
        is_mane_transcript: bool
        is_clinical_plus_transcript: bool
        is_partnered_transcript_included: bool
        is_duplicated_transcript: bool
        duplicated_transcript: Optional[str] = None
        ens_gene_name: Optional[str]

        request_id = self._db.create(request.to_dict())
        self._db.update(request_id, {"id": request_id})
        return request_id

    def delete_request(self, request_id: int) -> None:
        """Remove a request from db with given request_id."""
        try:
            self._db.delete(request_id)
        except KeyError as exc:
            raise InvalidTranscriptId(request_id) from exc

    def update_request(self, transcript_id: int, transcript_mods: Request) -> None:
        """Update a request with modifications."""
        try:
            self._db.update(transcript_id, transcript_mods.to_dict())
        except KeyError as exc:
            raise InvalidTranscriptId(transcript_id) from exc

    def list_requests():
        """
        List all the requests in the database
        """
        pass
