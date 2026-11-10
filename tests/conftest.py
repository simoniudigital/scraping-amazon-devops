import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scraping"))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def html_producto():
    return (FIXTURES / "producto.html").read_text(encoding="utf-8")


@pytest.fixture
def html_captcha():
    return (FIXTURES / "captcha.html").read_text(encoding="utf-8")


@pytest.fixture
def ruta_producto():
    return FIXTURES / "producto.html"
