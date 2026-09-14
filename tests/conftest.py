import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def set_test_db():
    tmpdir = tempfile.mkdtemp()
    os.environ["DB_PATH"] = os.path.join(tmpdir, "test.db")
    yield
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def client():
    from app import app

    with TestClient(app) as c:
        yield c
