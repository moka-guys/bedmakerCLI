import tinydb
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel


class DB:
    def __init__(self, db_path: Path, db_file_prefix: str):
        """Initialize the database."""
        self._db = tinydb.TinyDB(db_path / f"{db_file_prefix}.json", create_dirs=True)

    def create(self, item: dict) -> int:
        """Create a new document in the database."""
        return self._db.insert(item)

    def read(self, transcript_id: int) -> Optional[Dict]:
        """Read a document by its ID."""
        return self._db.get(doc_id=transcript_id)

    def read_all(self) -> List[Dict]:
        """Read all documents in the database."""
        return self._db.all()

    def update(self, transcript_id: int, mods: Dict) -> None:
        """Update a document by its ID."""
        changes = {k: v for k, v in mods.items() if v is not None}
        self._db.update(changes, doc_ids=[transcript_id])

    def delete(self, transcript_id: int) -> None:
        """Delete a document by its ID."""
        self._db.remove(doc_ids=[transcript_id])

    def delete_all(self) -> None:
        """Delete all documents in the database."""
        self._db.truncate()

    def count(self) -> int:
        """Count the number of documents in the database."""
        return len(self._db)

    def close(self) -> None:
        """Close the database connection."""
        self._db.close()
