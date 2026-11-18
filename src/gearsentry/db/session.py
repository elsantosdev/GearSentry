import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from gearsentry.db.models import Base

DEFAULT_DB_URL = "sqlite:///gearsentry.db"


def get_engine(url: str | None = None) -> Engine:
    engine = create_engine(url or os.getenv("GEARSENTRY_DB", DEFAULT_DB_URL))
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    session = sessionmaker(engine, expire_on_commit=False)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
