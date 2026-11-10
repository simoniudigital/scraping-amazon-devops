"""Método 2: Selenium.

Abre Google Chrome, carga la ficha, espera a que aparezca el título y lee los
elementos directamente del navegador.

Si Amazon muestra una verificación (captcha o botón "Continue shopping"), el script
no la evade: espera a que la persona la complete a mano en la ventana de Chrome.

Uso:
    python scraper_selenium.py               # con ventana de Chrome visible
    python scraper_selenium.py --headless    # sin ventana (no permite resolver verificaciones)
"""
import argparse
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from comun import (DATA_DIR, SELECTORES as S, URL, armar_producto, es_captcha, guardar,
                   limpiar_resena, resumen)


def texto(contenedor, selector):
    elementos = contenedor.find_elements(By.CSS_SELECTOR, selector)
    return " ".join(elementos[0].get_attribute("textContent").split()) if elementos else None


def scrapear(headless=False):
    opciones = webdriver.ChromeOptions()
    if headless:
        opciones.add_argument("--headless=new")
    opciones.add_argument("--lang=es-CO")
    opciones.add_argument("--window-size=1366,900")
    driver = webdriver.Chrome(options=opciones)   # Selenium Manager instala el driver
    inicio = time.time()
    try:
        driver.get(URL)
        espera = 20
        if es_captcha(driver.page_source):
            if headless:
                raise RuntimeError("Amazon pidió una verificación. Ejecuta sin --headless y complétala a mano.")
            print("Amazon pidió una verificación: complétala en la ventana de Chrome (máx. 3 min)...")
            espera = 180
        try:
            WebDriverWait(driver, espera).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, S["titulo"])))
        except TimeoutException:
            raise RuntimeError(f"No apareció el producto (página: {driver.title!r}).") from None
        # Baja hasta las reseñas para que carguen y vuelve arriba para la captura
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, S["resena"])))
        except TimeoutException:
            print("Las reseñas no cargaron en 10 s; se continúa sin ellas.")
        driver.execute_script("window.scrollTo(0, 0);")

        crudo = {campo: texto(driver, S[campo]) for campo in
                 ("titulo", "precio", "num_calificaciones", "tienda", "disponibilidad", "categoria")}
        calificacion = driver.find_elements(By.CSS_SELECTOR, S["calificacion"])
        crudo["calificacion"] = calificacion[0].get_attribute("title") if calificacion else None
        crudo["caracteristicas"] = [" ".join(li.get_attribute("textContent").split())
                                    for li in driver.find_elements(By.CSS_SELECTOR, S["caracteristicas"])]
        crudo["histograma"] = [a.get_attribute("aria-label")
                               for a in driver.find_elements(By.CSS_SELECTOR, S["histograma"])]
        crudo["resenas"] = [{
            "titulo": texto(r, S["resena_titulo"]),
            "estrellas": texto(r, S["resena_estrellas"]),
            "fecha": texto(r, S["resena_fecha"]),
            "texto": limpiar_resena(texto(r, S["resena_texto"])),
        } for r in driver.find_elements(By.CSS_SELECTOR, S["resena"])]
        driver.save_screenshot(str(DATA_DIR / "captura_selenium.png"))
    finally:
        driver.quit()
    return armar_producto("Selenium", crudo, time.time() - inicio)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="ejecutar Chrome sin ventana")
    producto = scrapear(parser.parse_args().headless)
    print(resumen(producto))
    print("Guardado en", guardar(producto, "producto_selenium.json"))
