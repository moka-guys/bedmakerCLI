from bedmaker.common.tark_api import MANETranscriptFetcher
from typer.testing import CliRunner
import bedmaker.transcripts.cli as transcripts
import pytest


def test_tark_api_settings():
    """
    Check setup of TARK API fetcher.
    """
    fetcher = MANETranscriptFetcher()
    assert fetcher.server_url == "http://tark.ensembl.org/"
    assert fetcher.client is not None


def test_id_type_checking():
    """
    Test the classification of IDs as either ensembl or Refseq.
    """
    fetcher = MANETranscriptFetcher()
    assert fetcher.check_id_type("ENST00000288602") == "ensembl"
    assert fetcher.check_id_type("NM_000551.3") == "refseq"


def test_id_version_detection():
    """
    Test whether the ID includes a version.
    """
    fetcher = MANETranscriptFetcher()
    assert fetcher.is_id_version_included("ENST00000288602.6") is True
    assert fetcher.is_id_version_included("ENST00000288602") is False
    assert fetcher.is_id_version_included("NM_000551.3") is True
    assert fetcher.is_id_version_included("NM_000551") is False


def test_empty(bedmaker_db):
    """
    Test creating an empty database.
    """
    assert bedmaker_db.count() == 0


@pytest.mark.asyncio
async def test_add_from_empty(bedmaker_db):
    """
    count should be 1 and transcript retrievable
    """
    fetcher = MANETranscriptFetcher()
    transcript_list = await fetcher.fetch_multiple_transcripts(
        ["NM_003722", "NM_000059"]
    )
    for transcript in transcript_list:
        bedmaker_db.add_transcript(transcript)
    assert bedmaker_db.count() == 2


#    assert bedmaker_db.get_card(i) == c


# def test_add_from_nonempty(cards_db_three_cards):
#     """
#     count should increase by 1 and card retrievable
#     """
#     cards_db = cards_db_three_cards
#     c = Card(summary="do something")
#     starting_count = cards_db.count()
#     i = cards_db.add_card(c)
#     assert cards_db.count() == starting_count + 1
#     assert cards_db.get_card(i) == c
