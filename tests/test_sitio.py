"""El tablero web se genera correctamente a partir de los resultados de los scrapers."""
import json

import pytest

from comun import armar_producto, guardar
from generar_sitio import generar
from scraper_beautifulsoup import parsear


@pytest.fixture
def carpeta_datos(tmp_path, html_producto, monkeypatch):
    import comun
    monkeypatch.setattr(comun, "DATA_DIR", tmp_path)
    producto = armar_producto("BeautifulSoup", parsear(html_producto), 1.5)
    (tmp_path / "producto_bs4.json").write_text(json.dumps(producto, ensure_ascii=False), encoding="utf-8")
    producto_scrapy = dict(producto, metodo="Scrapy", fuente="HTML guardado (captcha en vivo)")
    guardar([producto_scrapy], "producto_scrapy.json")
    return tmp_path


def test_genera_index_con_los_datos(carpeta_datos, tmp_path):
    index = generar(tmp_path / "public", carpeta_datos)
    html = index.read_text(encoding="utf-8")
    assert "Set de prueba de 3 lienzos decorativos" in html
    assert "$120.500" in html
    assert "1234" in html
    assert 'style="width:80%"' in html
    assert "HTML guardado (captcha en vivo)" in html
    assert "Muy bonito" in html
    assert (tmp_path / "public" / "data" / "producto_bs4.json").exists()


def test_escapa_html(carpeta_datos, tmp_path):
    ruta = carpeta_datos / "producto_bs4.json"
    producto = json.loads(ruta.read_text(encoding="utf-8"))
    producto["titulo"] = "<script>alert(1)</script>"
    ruta.write_text(json.dumps(producto), encoding="utf-8")
    html = generar(tmp_path / "public", carpeta_datos).read_text(encoding="utf-8")
    assert "<script>alert(1)" not in html


def test_sin_datos_falla_con_mensaje(tmp_path):
    with pytest.raises(SystemExit, match="No hay resultados"):
        generar(tmp_path / "public", tmp_path)
