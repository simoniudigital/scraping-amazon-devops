"""Configuración y funciones comunes a los tres scrapers."""
import json
import re
from pathlib import Path

# Artículo seleccionado en Amazon
ASIN = "B0D21SJ6BR"
URL = f"https://www.amazon.com/dp/{ASIN}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0 Safari/537.36"
    ),
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}

# Selectores CSS de la ficha de producto de Amazon (los usan los tres métodos)
SELECTORES = {
    "titulo": "#productTitle",
    "precio": "#corePrice_feature_div .a-price .a-offscreen",
    "calificacion": "#acrPopover",
    "num_calificaciones": "#acrCustomerReviewText",
    "tienda": "#bylineInfo",
    "disponibilidad": "#availability",
    "categoria": "#wayfinding-breadcrumbs_feature_div",
    "caracteristicas": "#feature-bullets li",
    "histograma": "#cm_cr_dp_d_rating_histogram a[aria-label]",
    "resena": '[data-hook="review"]',
    "resena_titulo": '[data-hook="reviewTitle"]',
    "resena_estrellas": '[data-hook="review-star-rating"]',
    "resena_fecha": '[data-hook="review-date"]',
    "resena_texto": '[data-hook="reviewText"]',
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
HTML_GUARDADO = DATA_DIR / "pagina_amazon.html"   # lo escribe scraper_beautifulsoup.py


def a_numero(texto):
    """'COP94,633.44' -> 94633.44 · '4.8 de 5 estrellas' -> 4.8 · '(104)' -> 104"""
    if not texto:
        return None
    m = re.search(r"\d[\d,]*(?:\.\d+)?", texto)
    return float(m.group().replace(",", "")) if m else None


def limpiar_resena(texto):
    """Quita el texto de accesibilidad que Amazon antepone a cada reseña."""
    texto = re.sub(r"Brief content visible.*?read brief content\.\s*", "", texto or "")
    return re.sub(r"\s*(Leer más|Read more)\s*(Leer menos|Read less)?\s*$", "", texto).strip()


def histograma_desde_etiquetas(etiquetas):
    """['El 91 por ciento de las opiniones tienen 5 estrellas', ...] -> {'5': 91, ...}"""
    hist = {str(e): 0 for e in range(5, 0, -1)}  # Amazon no enlaza los niveles con 0 %
    for et in etiquetas:
        m = re.search(r"(\d+)\s*por ciento.*?(\d)\s*estrella", et or "")  # \s cubre el espacio duro
        if m:
            hist[m.group(2)] = int(m.group(1))
    return hist if any(hist.values()) else {}


def es_captcha(html):
    """Amazon a veces responde con un captcha o con la pantalla 'Continue shopping'."""
    pagina = html.lower()
    return "producttitle" not in pagina and ("captcha" in pagina or "continue shopping" in pagina)


def armar_producto(metodo, crudo, tiempo_seg, fuente="en vivo"):
    """Convierte los textos extraídos (iguales en los 3 métodos) en un registro limpio."""
    categoria = crudo.get("categoria")
    return {
        "metodo": metodo,
        "fuente": fuente,
        "asin": ASIN,
        "titulo": crudo.get("titulo"),
        "precio_cop": a_numero(crudo.get("precio")),
        "calificacion": a_numero(crudo.get("calificacion")),
        "num_calificaciones": int(a_numero(crudo.get("num_calificaciones")) or 0) or None,
        "tienda": (crudo.get("tienda") or "").replace("Visita la tienda de ", "") or None,
        "disponibilidad": crudo.get("disponibilidad"),
        "categoria": re.sub(r"\s*›\s*", " › ", categoria) if categoria else None,
        "caracteristicas": crudo.get("caracteristicas", []),
        "histograma_pct": histograma_desde_etiquetas(crudo.get("histograma", [])),
        "resenas": crudo.get("resenas", []),
        "tiempo_seg": round(tiempo_seg, 2),
    }


def guardar(registro, nombre):
    ruta = DATA_DIR / nombre
    ruta.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def resumen(r):
    return (f"[{r['metodo']}] {r['tiempo_seg']} s · fuente: {r['fuente']}\n"
            f"  Título       : {(r['titulo'] or '')[:80]}\n"
            f"  Precio       : {r['precio_cop']} COP\n"
            f"  Calificación : {r['calificacion']} ({r['num_calificaciones']} calificaciones)\n"
            f"  Tienda       : {r['tienda']}\n"
            f"  Histograma % : {r['histograma_pct']}\n"
            f"  Reseñas      : {len(r['resenas'])}")
