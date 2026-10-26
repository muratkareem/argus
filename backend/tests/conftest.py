import pytest
from app.config import Settings
from app.main import create_app
from app.ml import synthetic, train
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def artifacts(tmp_path_factory):
    directory = tmp_path_factory.mktemp("artifacts")
    train(synthetic(700), directory, "synthetic")
    return directory


@pytest.fixture
def settings(tmp_path, artifacts):
    import os

    return Settings(
        database_url=os.environ.get("ARGUS_TEST_DATABASE_URL", f"sqlite:///{tmp_path}/test.db"),
        artifact_dir=artifacts,
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def csv_content():
    return synthetic(80, seed=84).to_csv(index=False).encode()


@pytest.fixture
def imported(client, csv_content):
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("fixture.csv", csv_content)},
        data={"provenance": "synthetic"},
    )
    assert response.status_code == 200, response.text
    return response.json()
