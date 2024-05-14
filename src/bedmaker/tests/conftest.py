import pytest
from bedmaker.transcripts.api import transcriptsDB


@pytest.fixture(scope="session")
def db(tmp_path_factory):
    """transcriptsDB object connected to a temporary database"""
    db_path = tmp_path_factory.mktemp("bedmaker_db")
    db_ = transcriptsDB(db_path)
    yield db_
    db_.close()


@pytest.fixture(scope="function")
def bedmaker_db(db):
    """TranscriptsDB object that's empty"""
    db.delete_all()
    return db
