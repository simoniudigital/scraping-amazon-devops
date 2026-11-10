"""Pruebas de las funciones de limpieza compartidas."""
import pytest

from comun import (
    a_numero,
    armar_producto,
    detectar_moneda,
    es_captcha,
    histograma_desde_etiquetas,
    limpiar_resena,
)


@pytest.mark.parametrize("texto, esperado", [
    ("COP94,633.44", 94633.44),
    ("4.8 de 5 estrellas", 4.8),
    ("(104)", 104),
    ("(1,234)", 1234),
    ("", None),
    (None, None),
    ("sin números", None),
])
def test_a_numero(texto, esperado):
    assert a_numero(texto) == esperado


def test_limpiar_resena_quita_textos_de_accesibilidad():
    sucio = ("Brief content visible, double tap to read full content. Full content visible, "
             "double tap to read brief content. Excelente calidad. Leer más Leer menos")
    assert limpiar_resena(sucio) == "Excelente calidad."
    assert limpiar_resena(None) == ""


def test_histograma_con_espacio_duro_y_niveles_faltantes():
    etiquetas = ["El 91\xa0por ciento de las opiniones tienen 5\xa0estrellas",
                 "El 3\xa0por ciento de las opiniones tienen 1\xa0estrellas"]
    assert histograma_desde_etiquetas(etiquetas) == {"5": 91, "4": 0, "3": 0, "2": 0, "1": 3}
    assert histograma_desde_etiquetas([]) == {}


@pytest.mark.parametrize("texto, moneda", [
    ("COP94,633.44", "COP"),
    ("$29.99", "USD"),
    ("US$29.99", "USD"),
    ("", None),
])
def test_detectar_moneda(texto, moneda):
    assert detectar_moneda(texto) == moneda


def test_es_captcha(html_producto, html_captcha):
    assert es_captcha(html_captcha)
    assert not es_captcha(html_producto)
    assert es_captcha("<p>To continue, please click the Continue shopping button</p>")


def test_armar_producto_normaliza_campos():
    crudo = {"titulo": "Cuadro", "precio": "COP10,000.00", "calificacion": "4.5 de 5 estrellas",
             "num_calificaciones": "(12)", "tienda": "Visita la tienda de ABC",
             "categoria": "Hogar›Arte"}
    r = armar_producto("Prueba", crudo, 1.234)
    assert r["precio"] == 10000.0
    assert r["moneda"] == "COP"
    assert r["num_calificaciones"] == 12
    assert r["tienda"] == "ABC"
    assert r["categoria"] == "Hogar › Arte"
    assert r["tiempo_seg"] == 1.23
    assert r["fuente"] == "en vivo"
