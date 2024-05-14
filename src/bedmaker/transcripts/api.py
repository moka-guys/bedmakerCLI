"""
API for the transcripts project
"""

from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel

from bedmaker.common.db import DB
from bedmaker.common.exceptions import MissingRefseqStableId, InvalidTranscriptId

# __all__ = [
#     "transcriptsDB",
#     "transcriptsException",
#     "MissingRefseqStableId",
#     "InvalidTranscriptId",
# ]


from typing import List, Optional

from enum import Enum

from bedmaker.common.models import UserRequest, Transcript, Exon, ManeList


class transcriptsDB:
    def __init__(self, db_path):
        self._db_path = db_path
        self._db = DB(db_path, ".transcripts_db")

    def add_transcript(self, transcript: Transcript) -> int:
        """Add a transcript, return the id of transcript."""
        if not transcript.refseq_stable_id:
            raise MissingRefseqStableId
        if transcript.ens_stable_id is None:
            transcript.ens_stable_id = ""
        transcript_id = self._db.create(transcript.to_dict())
        self._db.update(transcript_id, {"id": transcript_id})
        return transcript_id

    def get_transcript(self, transcript_id: int) -> Transcript:
        """Return a transcript with a matching id."""
        db_item = self._db.read(transcript_id)
        if db_item is not None:
            return Transcript.from_dict(db_item)
        else:
            raise InvalidTranscriptId(transcript_id)

    def list_transcripts(self, gene_name=None, location_range=None):
        """Return a list of transcripts filtered by gene name and/or location range."""
        all_transcripts = self._db.read_all()
        filtered_transcripts = all_transcripts

        if gene_name is not None:
            filtered_transcripts = [
                t for t in filtered_transcripts if t["gene_name"] == gene_name
            ]

        if location_range is not None:
            start, end = location_range
            filtered_transcripts = [
                t
                for t in filtered_transcripts
                if "location_start" in t
                and "location_end" in t
                and start <= t["location_start"] <= end
                and start <= t["location_end"] <= end
            ]

        return [Transcript.from_dict(t) for t in filtered_transcripts]

    def count(self) -> int:
        """Return the number of transcripts in db."""
        return self._db.count()

    def update_transcript(
        self, transcript_id: int, transcript_mods: Transcript
    ) -> None:
        """Update a transcript with modifications."""
        try:
            self._db.update(transcript_id, transcript_mods.to_dict())
        except KeyError as exc:
            raise InvalidTranscriptId(transcript_id) from exc

    def delete_transcript(self, transcript_id: int) -> None:
        """Remove a transcript from db with given transcript_id."""
        try:
            self._db.delete(transcript_id)
        except KeyError as exc:
            raise InvalidTranscriptId(transcript_id) from exc

    def delete_all(self) -> None:
        """Remove all transcripts from db."""
        self._db.delete_all()

    def close(self):
        self._db.close()

    def path(self):
        return self._db_path

    def read_db_to_nested_dict(self):
        nested_dict = {}

        for transcript in self._db.read_all():
            # Assuming 'ens_stable_id' is the unique identifier for each transcript
            transcript_id = transcript.get("ens_stable_id")

            # Directly use the transcript dictionary
            nested_dict[transcript_id] = transcript

        return nested_dict

    def stats(self) -> Dict[str, int]:
        """Calculate various statistics from the transcripts in the database."""
        total_transcripts = 0
        MANE_transcripts = 0
        clinical_plus_transcripts = 0
        total_exons = 0

        # Assuming self._db.all() returns a list of all transcripts in the database
        for transcript in self._db.read_all():
            total_transcripts += 1
            total_exons += len(
                transcript.get("exons", [])
            )  # Use .get() to avoid KeyError if 'exons' is missing

            if transcript.get("mane_type") == "MANE SELECT":
                MANE_transcripts += 1
            elif transcript.get("mane_type") == "MANE PLUS CLINICAL":
                clinical_plus_transcripts += 1

        return {
            "total_transcripts": total_transcripts,
            "MANE_transcripts": MANE_transcripts,
            "clinical_plus_transcripts": clinical_plus_transcripts,
            "total_exons": total_exons,
        }


class maneTranscriptsDB:
    def __init__(self, db_path):
        self._db_path = db_path
        self._db = DB(db_path, ".mane_db")

    def add_transcript(self, mane: ManeList) -> int:
        """Add a transcript, return the id of transcript."""
        transcript_id = self._db.create(mane.to_dict())
        self._db.update(transcript_id, {"id": transcript_id})
        return transcript_id

    def get_transcript(self, transcript_id: int) -> Transcript:
        """Return a transcript with a matching id."""
        db_item = self._db.read(transcript_id)
        if db_item is not None:
            return ManeList.from_dict(db_item)
        else:
            raise InvalidTranscriptId(transcript_id)

    def count(self) -> int:
        """Return the number of transcripts in db."""
        return self._db.count()

    def delete_all(self) -> None:
        """Remove all transcripts from db."""
        self._db.delete_all()

    def close(self):
        self._db.close()

    def path(self):
        return self._db_path
