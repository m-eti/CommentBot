import pytest
from main import load_config


@pytest.fixture()
def config():
    return load_config()


def test_load_config(config):
    assert "PASSWORD" in config
    assert "API_ID" in config
    assert "API_HASH" in config
    assert "accounts" in config
    assert "comments" in config
