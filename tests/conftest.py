"""Data prep / fixtures for tests."""
import codecs

import pytest
from bs4 import BeautifulSoup


@pytest.fixture(scope="session")
def track_meta_soup():
    file_ = codecs.open("tests/test.html", "r", "utf-8")
    return BeautifulSoup(file_.read(), features="html.parser")
