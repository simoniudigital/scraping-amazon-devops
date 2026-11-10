"""Método 1: requests + BeautifulSoup.

Descarga el HTML de la ficha con una petición HTTP y lo recorre con selectores CSS.

Uso:  python scraper_beautifulsoup.py
"""
import time

import requests
from bs4 import BeautifulSoup

from comun import (HEADERS, HTML_GUARDADO, SELECTORES as S, URL, armar_producto, es_captcha,
                   guardar, limpiar_resena, resumen)


def texto(soup, selector):
    el = soup.select_one(selector)
    return el.get_text(" ", strip=True) if el else None


def scrapear():
    inicio = time.time()
    respuesta = requests.get(URL, headers=HEADERS, timeout=30)
    respuesta.raise_for_status()
    if es_captcha(respuesta.text):
        raise RuntimeError("Amazon respondió con un captcha; espera unos minutos y reintenta.")
    HTML_GUARDADO.write_text(respuesta.text, encoding="utf-8")

    soup = BeautifulSoup(respuesta.text, "lxml")
    crudo = {campo: texto(soup, S[campo]) for campo in
             ("titulo", "precio", "num_calificaciones", "tienda", "disponibilidad", "categoria")}
    calificacion = soup.select_one(S["calificacion"])
    crudo["calificacion"] = calificacion.get("title") if calificacion else None
    crudo["caracteristicas"] = [li.get_text(" ", strip=True) for li in soup.select(S["caracteristicas"])]
    crudo["histograma"] = [a["aria-label"] for a in soup.select(S["histograma"])]
    crudo["resenas"] = [{
        "titulo": texto(r, S["resena_titulo"]),
        "estrellas": texto(r, S["resena_estrellas"]),
        "fecha": texto(r, S["resena_fecha"]),
        "texto": limpiar_resena(texto(r, S["resena_texto"])),
    } for r in soup.select(S["resena"])]
    return armar_producto("BeautifulSoup", crudo, time.time() - inicio)


if __name__ == "__main__":
    producto = scrapear()
    print(resumen(producto))
    print("Guardado en", guardar(producto, "producto_bs4.json"))
