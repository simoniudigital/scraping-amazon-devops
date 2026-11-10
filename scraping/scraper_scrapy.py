"""Método 3: Scrapy.

Un Spider solicita la ficha, extrae los campos con los selectores de Scrapy
(CSS y XPath) y exporta el resultado con el sistema de FEEDS.

Si Amazon le responde con un captcha, el spider no intenta evadirlo: lo registra
y procesa la copia del HTML que guardó scraper_beautifulsoup.py (data/pagina_amazon.html).

Uso:  python scraper_scrapy.py
"""
import time

import scrapy
from scrapy.crawler import CrawlerProcess

from comun import (DATA_DIR, HEADERS, HTML_GUARDADO, SELECTORES as S, URL, armar_producto,
                   es_captcha, limpiar_resena)


def limpio(lista):
    return " ".join(" ".join(lista).split()) or None


class ProductoAmazonSpider(scrapy.Spider):
    name = "producto_amazon"
    start_urls = [URL]
    custom_settings = {
        "USER_AGENT": HEADERS["User-Agent"],
        "DEFAULT_REQUEST_HEADERS": {"Accept-Language": HEADERS["Accept-Language"]},
        "ROBOTSTXT_OBEY": True,   # /dp/ está permitido en robots.txt de Amazon
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 1,
        "LOG_LEVEL": "WARNING",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inicio = time.time()

    def parse(self, response):
        if es_captcha(response.text):
            self.logger.warning("Amazon respondió con un captcha a Scrapy (HTTP %s).", response.status)
            if HTML_GUARDADO.exists():
                self.logger.warning("Se procesa la copia guardada: %s", HTML_GUARDADO.name)
                yield scrapy.Request(HTML_GUARDADO.as_uri(), callback=self.extraer,
                                     cb_kwargs={"fuente": "HTML guardado (captcha en vivo)"})
            return
        yield from self.extraer(response, "en vivo")

    def extraer(self, response, fuente):
        crudo = {campo: limpio(response.css(f"{S[campo]} ::text").getall()) for campo in
                 ("precio", "num_calificaciones", "tienda", "disponibilidad", "categoria")}
        # XPath para el título y la calificación (atributo title)
        crudo["titulo"] = response.xpath("normalize-space(//span[@id='productTitle'])").get()
        crudo["calificacion"] = response.xpath("//*[@id='acrPopover']/@title").get()
        crudo["caracteristicas"] = [limpio(li.css("::text").getall())
                                    for li in response.css(S["caracteristicas"])]
        crudo["histograma"] = response.css(f"{S['histograma']}::attr(aria-label)").getall()
        crudo["resenas"] = [{
            "titulo": limpio(r.css(f"{S['resena_titulo']} ::text").getall()),
            "estrellas": limpio(r.css(f"{S['resena_estrellas']} ::text").getall()),
            "fecha": limpio(r.css(f"{S['resena_fecha']} ::text").getall()),
            "texto": limpiar_resena(limpio(r.css(f"{S['resena_texto']} ::text").getall())),
        } for r in response.css(S["resena"])]
        yield armar_producto("Scrapy", crudo, time.time() - self.inicio, fuente)


if __name__ == "__main__":
    salida = DATA_DIR / "producto_scrapy.json"
    proceso = CrawlerProcess(settings={
        "FEEDS": {str(salida): {"format": "json", "encoding": "utf8", "indent": 2, "overwrite": True}},
    })
    proceso.crawl(ProductoAmazonSpider)
    proceso.start()
    print("Guardado en", salida)
