import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Важно: задаём DB_PATH до импорта app
@pytest.fixture(scope="session", autouse=True)
def set_test_db():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    os.environ["DB_PATH"] = tmp.name
    yield
    os.unlink(tmp.name)

@pytest.fixture
def client():
    from app import app
    with TestClient(app) as c:
        yield c
