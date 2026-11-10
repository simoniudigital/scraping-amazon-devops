"""Los tres métodos deben extraer lo mismo de la página de prueba (sin conectarse a Amazon)."""
import shutil

import pytest
from scrapy.http import HtmlResponse

from comun import armar_producto
from scraper_beautifulsoup import parsear
from scraper_scrapy import ProductoAmazonSpider

ESPERADO = {
    "titulo": "Set de prueba de 3 lienzos decorativos",
    "precio": 120500.5,
    "moneda": "COP",
    "calificacion": 4.5,
    "num_calificaciones": 1234,
    "tienda": "TiendaPrueba",
    "disponibilidad": "Disponible",
    "categoria": "Hogar y Cocina › Obras de Arte y Material Decorativo › Pósteres",
    "histograma_pct": {"5": 80, "4": 10, "3": 6, "2": 0, "1": 4},
}


def verificar(producto):
    for campo, valor in ESPERADO.items():
        assert producto[campo] == valor, campo
    assert producto["caracteristicas"] == ["Tamaño 12x16 pulgadas.", "Marco de madera, listo para colgar."]
    assert [r["titulo"] for r in producto["resenas"]] == ["Muy bonito", "Llegó tarde"]
    assert producto["resenas"][0]["texto"] == "Los colores son intensos."
    assert producto["resenas"][1]["estrellas"] == "3 de 5 estrellas"


def test_beautifulsoup(html_producto):
    verificar(armar_producto("BeautifulSoup", parsear(html_producto), 0))


def test_scrapy(ruta_producto):
    respuesta = HtmlResponse(url=ruta_producto.as_uri(), body=ruta_producto.read_bytes(), encoding="utf-8")
    spider = ProductoAmazonSpider()
    (producto,) = list(spider.extraer(respuesta, "prueba"))
    assert producto["fuente"] == "prueba"
    verificar(producto)


def test_scrapy_con_captcha_no_inventa_datos(html_captcha, tmp_path, monkeypatch):
    import scraper_scrapy
    monkeypatch.setattr(scraper_scrapy, "HTML_GUARDADO", tmp_path / "no_existe.html")
    respuesta = HtmlResponse(url="https://www.amazon.com/dp/X", body=html_captcha.encode(), encoding="utf-8")
    assert list(ProductoAmazonSpider().parse(respuesta)) == []


@pytest.mark.skipif(not (shutil.which("google-chrome") or shutil.which("chrome")
                         or shutil.which("chromium") or shutil.which("chromium-browser")),
                    reason="Google Chrome no está instalado")
def test_selenium(ruta_producto):
    from scraper_selenium import scrapear
    verificar(scrapear(headless=True, url=ruta_producto.as_uri(), captura=None))
