import pytest
from sqlalchemy.orm import Session

from gearsentry.db.session import get_engine


@pytest.fixture
def session():
    engine = get_engine("sqlite:///:memory:")
    with Session(engine) as s:
        yield s
