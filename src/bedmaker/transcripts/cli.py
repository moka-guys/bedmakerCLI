"""Command Line Interface (CLI) for transcripts project."""

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
from bedmaker.common.models import (
    UserRequest,
    UserInput,
    Transcript,
    Exon,
    Utr,
    GenomicRange,
)
from bedmaker.common.exceptions import InvalidTranscriptId
from bedmaker.transcripts.api import transcriptsDB

import bedmaker.transcripts

app = typer.Typer(add_completion=False)


@app.command()
def version():
    """Return version of transcripts application"""
    print(bedmaker.__version__)
    pass


async def fetch_mane_list():
    """Fetch MANE list from TARK API."""
    fetcher = MANETranscriptFetcher()
    console = Console()
    try:
        # Fetch MANE list and await the asynchronous operation
        json_data = await fetcher.fetch_mane_list()
        return json_data
    except Exception as e:
        console.log(f"Failed to return list of MANE transcripts from TARK API: {e}")
    finally:
        # Ensure the HTTP client is closed
        await fetcher.close()


@app.command()
def mane():
    """Return a table of MANE and CLINICAL PLUS transcripts"""

    # The rest of your code for creating and displaying the table remains unchanged
    mane_json = asyncio.run(fetch_mane_list())
    console = rich.console.Console()
    console.print(mane_json)


# Define the asynchronous function to fetch and add the transcript
async def fetch_and_add_transcript(stable_id: str, db):
    fetcher = MANETranscriptFetcher()
    console = Console()
    try:
        transcript = await fetcher.fetch_mane_transcript(stable_id)
        if transcript:
            db.add_transcript(transcript)
            console.log(f"Transcript with stable_id '{stable_id}' added successfully.")
        else:
            console.log(f"[red]No transcript data found for stable_id '{stable_id}'.")
    except Exception as e:
        console.log(f"Failed to add transcript with stable_id '{stable_id}': {e}")
    finally:
        # Ensure the HTTP client is closed
        await fetcher.close()


def add_ids(ids: str):
    ids_list = ids.split(",") if "," in ids else [ids]
    print(ids_list)
    with transcripts_db() as db:
        for id_ in ids_list:
            asyncio.run(fetch_and_add_transcript(id_.strip(), db))


def add_from_file(file_path: str):
    with open(file_path, "r") as file:
        ids = file.read().splitlines()
    # Flatten the list in case of comma-separated IDs in the file
    ids_list = [id_ for line in ids for id_ in line.split(",")]
    with transcripts_db() as db:
        for id_ in ids_list:
            if id_:  # Check if id_ is not an empty string
                asyncio.run(fetch_and_add_transcript(id_.strip(), db))


@app.command()
def add(
    ids: str,
    is_file: Optional[bool] = typer.Option(
        False, help="Indicate if the input is a file path."
    ),
):
    """Add transcripts to the database with the given stable ID(s) or from a file."""
    if is_file:
        add_from_file(ids)
    else:
        add_ids(ids)


@app.command()
def delete(stable_id: str):
    """Delete a transcript from the database by stable ID."""
    with transcripts_db() as db:
        try:
            db.delete_transcript_by_stable_id(stable_id)
            print(f"Transcript with stable_id '{stable_id}' deleted successfully.")
        except Exception as e:
            print(f"Failed to delete transcript with stable_id '{stable_id}': {e}")


@app.command()
def get(stable_id: str):
    """Retrieve and display information for a transcript by stable ID."""

    with transcripts_db() as db:
        try:
            transcript = db.get_transcript_by_stable_id(stable_id)
            print(f"Transcript Information for '{stable_id}': {transcript}")
        except ValueError as e:
            print(e)
        except Exception as e:
            print(f"An error occurred: {str(e)}")


@app.command()
def update(
    stable_id: str = typer.Option(
        ...,
        "--refseq-stable-id",
        help="The refeseq stable ID of the transcript to update",
    ),
    gene_name: Optional[str] = typer.Option(
        None, "-g", "--gene-name", help="Gene name to update"
    ),
    loc_start: Optional[int] = typer.Option(
        None, "-l", "--loc-start", help="Location start to update"
    ),
    loc_end: Optional[int] = typer.Option(
        None, "-e", "--loc-end", help="Location end to update"
    ),
):
    """Modify a transcript in the db with the given stable ID with new info."""
    with transcripts_db() as db:
        try:
            db.update_transcript(
                stable_id, gene_name=gene_name, loc_start=loc_start, loc_end=loc_end
            )
            print(f"Transcript with stable ID {stable_id} has been updated.")
        except InvalidTranscriptId:
            print(f"Error: Invalid stable ID {stable_id}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")


@app.command("list")
def list_transcripts():
    """
    List transcripts in db.
    """
    with transcripts_db() as db:
        the_transcripts = db.list_transcripts()
        table = Table(box=SIMPLE)
        table.add_column("RefSeq stable ID", style="cyan", no_wrap=True)
        table.add_column("Gene Name", style="red")
        table.add_column("MANE type", style="red")
        table.add_column("Chr", style="magenta")
        table.add_column("Start", style="magenta")
        table.add_column("End", style="magenta")
        table.add_column("Ensembl Stable ID", style="green")
        table.add_column("5'UTR start", style="red")
        table.add_column("5'UTR end", style="red")
        table.add_column("3'UTR start", style="red")
        table.add_column("3'UTR end", style="red")

        for transcript in the_transcripts:
            table.add_row(
                f"{transcript.refseq_stable_id}.{transcript.refseq_stable_id_version}"
                or "N/A",
                transcript.gene_name or "N/A",
                transcript.mane_type or "N/A",
                transcript.loc_region or "N/A",
                str(transcript.genomic_ranges.loc_start) or "N/A",
                str(transcript.genomic_ranges.loc_end) or "N/A",
                f"{transcript.ens_stable_id}.{transcript.ens_stable_id_version}"
                or "N/A",
                "placeholder",  # str(transcript.five_prime_utr_start) or "N/A",
                "placeholder",  # str(transcript.five_prime_utr_end) or "N/A",
                "placeholder",  # str(transcript.three_prime_utr_start) or "N/A",
                "placeholder",  # str(transcript.three_prime_utr_end) or "N/A",
            )

        console = rich.console.Console()
        console.print(table)


@app.command()
def tree():
    """Displays the transcripts and their exons as a tree in the console."""
    with transcripts_db() as db:
        nested_dict = db.read_db_to_nested_dict()

        root_tree = Tree("Transcripts", highlight=True)

        for transcript_id, details in nested_dict.items():
            transcript_node = root_tree.add(f"Transcript: {transcript_id}")

            table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
            table.add_column("Exon ID", style="cyan", no_wrap=True)
            table.add_column("Exon Order", style="bright_yellow")
            table.add_column("Chr", style="red")
            table.add_column("Strand", style="red")
            table.add_column("Start", style="red")
            table.add_column("End", style="red")

            for exon in details.get("exons", []):
                table.add_row(
                    str(exon.get("exon_id")) or "N/A",
                    str(exon.get("exon_order")) or "N/A",
                    str(exon.get("loc_region")) or "N/A",
                    str(exon.get("loc_strand")) or "N/A",
                    str(exon.get("loc_start")) or "N/A",
                    str(exon.get("loc_end")) or "N/A",
                )

            # Wrap the table in a Panel for better visual separation and style
            panel = Panel.fit(table, title="Exons", border_style="green", width=70)
            transcript_node.add(panel)

        console = Console()
        console.print(root_tree)


@app.command()
def config():
    """List the path to the transcripts db."""
    with transcripts_db() as db:
        print(db.path())


@app.command()
def count():
    """Return number of transcripts in db."""
    with transcripts_db() as db:
        print(db.count())


@app.command()
def translate():
    """Converts between Ensembl/RefSeq MANE transcript IDs."""
    with transcripts_db() as db:
        print(db.count())


@app.command()
def check():
    """Outputs a report in JSON format detailing any issues with the currently selected transcripts."""
    with transcripts_db() as db:
        print(db.count())


@app.command()
def example():
    """Adds example data for demonstration purposes."""
    # console = Console()
    # with console.status("Getting example transcripts..."):
    with transcripts_db() as db:
        for tx_id in [
            "NM_001114980",  # MANE PLUS CLINICAL (TP63)
            "NM_003722",  # MANE SELECT (TP63)
            "NP_009225",  # MANE SELECT (BRCA1) protein ID used, should skip
            "NP_000050",  # MANE SELECT (BRCA2) protein ID used, should skip
            "NM_007294",  # MANE SELECT (BRCA1)
            "NM_000059",  # MANE SELECT (BRCA2)
            "NM_003140",  # MANE SELECT Shortest gene (SRY)
            "NM_014908",  # MANE SELECT Single exon transcript (DOLK)
            "NM_002732",  # MANE SELECT Single exon transcript (PRKACG)
            "NM_022725",  # MANE SELECT Single exon transcript (FANCF)
            "NM_198586",  # MANE SELECT Single exon transcript (NHLRC1)
            "NM_006978",  # MANE SELECT Single exon transcript (RNF113A)
            "NM_000344",  # MANE SELECT Single exon transcript (SMN1)
            "NM_000361",  # MANE SELECT Single exon transcript (THBD)
            "NM_001267550",  # MANE SELECT 363 Exons (TTN) Longest gene
            "NM_133379",  # MANE PLUS CLINICAL (TTN)
            "NR_023343.1",  # Non-coding RNA (RNU4ATAC)
            "NM_017693",  # MANE SELECT BIVM
            "NM_000123",  # MANE SELECT ERCC5
            "NM_001204425",  # MANE SELECT BIVM-ERCC5 Readthrough
            "NM_001321154",  # MANE SELECT METTL8
            "NM_000344",  # MANE SELECT SMN1
            "NM_017411",  # MANE SELECT SMN2
        ]:
            asyncio.run(fetch_and_add_transcript(tx_id, db))


@app.command()
def stats():
    """Return stats on the number of transcripts and exons in db."""
    with transcripts_db() as db:
        pprint(db.stats())


@app.command()
def purge():
    """Delete all entries in db."""
    with transcripts_db() as db:
        db.delete_all()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    A CLI tool for managing and querying genomic transcript data. It allows for adding, updating, listing, and deleting transcript entries, as well as fetching data from external genomic APIs.
    """
    if ctx.invoked_subcommand is None:
        typer.echo("No command specified. Use --help to see available commands.")


def get_path():
    """
    Checks if the environment variable 'transcripts_DB_DIR' is set and returns the path to the database directory.
    """
    db_path_env = os.getenv("transcripts_DB_DIR", "")
    if db_path_env:
        db_path = pathlib.Path(db_path_env)
    else:
        db_path = pathlib.Path.home() / "transcripts_db"
    return db_path


@contextmanager
def transcripts_db():
    db_path = get_path()
    db = transcriptsDB(db_path)
    yield db
    db.close()


if __name__ == "__main__":
    app()
