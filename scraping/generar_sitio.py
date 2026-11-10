"""Genera el tablero web estático (public/) que se despliega en GitHub Pages.

Lee los resultados de los tres scrapers en data/ y escribe una sola página HTML
sin dependencias externas, más una copia de los datos para descargar.

Uso:  python scraping/generar_sitio.py [--salida public]
"""
import argparse
import os
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from comparar_resultados import CAMPOS, cargar
from comun import ASIN, DATA_DIR, URL

RAIZ = Path(__file__).resolve().parent.parent
DESCARGAS = ["producto_bs4.json", "producto_selenium.json", "producto_scrapy.json",
             "comparacion_metodos.csv", "resenas.csv"]

CSS = """
:root{--fondo:#f6f7f9;--tarjeta:#fff;--texto:#16191f;--suave:#5a6270;--borde:#e3e6ea;
  --marca:#232f3e;--acento:#ff9900;--barra:#f2a900;--ok:#1e7e34}
@media (prefers-color-scheme:dark){:root{--fondo:#0f1419;--tarjeta:#1a2028;--texto:#e8eaed;
  --suave:#a0a8b4;--borde:#2c343f;--marca:#e8eaed;--barra:#f2a900;--ok:#5cc178}}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  background:var(--fondo);color:var(--texto);line-height:1.5}
header{background:#232f3e;color:#fff;padding:28px 16px 24px}
header .cont,main{max-width:1040px;margin:0 auto}
header small{color:#ffb84d;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
header h1{margin:6px 0 4px;font-size:clamp(1.3rem,3vw,1.9rem);line-height:1.25}
header p{margin:0;color:#c9d1db}
header a{color:#ffb84d}
main{padding:20px 16px 40px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:20px}
.kpi,.tarjeta{background:var(--tarjeta);border:1px solid var(--borde);border-radius:10px}
.kpi{padding:14px 16px}
.kpi span{display:block;color:var(--suave);font-size:.85rem}
.kpi strong{font-size:1.5rem;font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:760px){.grid{grid-template-columns:1fr}}
.tarjeta{padding:16px 18px;margin-bottom:16px;min-width:0}
h2{font-size:1.05rem;margin:0 0 12px;color:var(--marca)}
.fila{display:grid;grid-template-columns:5.5rem 1fr 3rem;align-items:center;gap:8px;margin:6px 0}
.pista{background:var(--borde);border-radius:4px;height:14px;overflow:hidden}
.relleno{background:var(--barra);height:100%}
.fila b{text-align:right;font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--borde);vertical-align:top}
th{color:var(--suave);font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.tabla{overflow-x:auto}
.ok{color:var(--ok);font-weight:600}
ul{margin:0;padding-left:20px} li{margin-bottom:6px}
.resena{border-top:1px solid var(--borde);padding:10px 0}
.resena:first-of-type{border-top:0;padding-top:0}
.resena p{margin:4px 0 0;color:var(--suave)}
.estrellas{color:var(--acento);letter-spacing:1px}
img{max-width:100%;border-radius:8px;border:1px solid var(--borde)}
.descargas a{display:inline-block;margin:4px 8px 4px 0;padding:6px 10px;border:1px solid var(--borde);
  border-radius:6px;color:var(--texto);text-decoration:none;font-size:.85rem}
footer{color:var(--suave);font-size:.8rem;text-align:center;padding:0 16px 30px}
footer a{color:var(--suave)}
"""


def pesos(valor):
    return f"${valor:,.0f}".replace(",", ".") if valor else "—"


def histograma(hist):
    filas = []
    for estrellas in "54321":
        pct = hist.get(estrellas, 0)
        filas.append(f'<div class="fila"><span>{estrellas} estrellas</span>'
                     f'<div class="pista"><div class="relleno" style="width:{pct}%"></div></div>'
                     f'<b>{pct} %</b></div>')
    return "".join(filas) or "<p>Sin datos de calificaciones.</p>"


def tabla_metodos(registros):
    filas = []
    for r in registros:
        completos = sum(r[c] not in (None, "") for c in CAMPOS)
        filas.append(f"<tr><td>{escape(r['metodo'])}</td><td>{escape(r['fuente'])}</td>"
                     f'<td class="num">{r["tiempo_seg"]:.1f} s</td>'
                     f'<td class="num">{completos}/{len(CAMPOS)}</td>'
                     f'<td class="num">{len(r["resenas"])}</td></tr>')
    return ("<table><thead><tr><th>Método</th><th>Fuente</th><th>Tiempo</th><th>Campos</th>"
            "<th>Reseñas</th></tr></thead><tbody>" + "".join(filas) + "</tbody></table>")


def resenas(lista):
    if not lista:
        return "<p>Amazon pidió iniciar sesión para ver las reseñas en esta extracción.</p>"
    bloques = []
    for r in lista:
        n = int((r.get("estrellas") or "0")[0])
        fecha = (r.get("fecha") or "").split(" el ")[-1]
        bloques.append(f'<div class="resena"><span class="estrellas" aria-label="{n} de 5">'
                       f'{"★" * n}{"☆" * (5 - n)}</span> <strong>{escape(r.get("titulo") or "")}</strong>'
                       f' · <small>{escape(fecha)}</small><p>{escape(r.get("texto") or "")}</p></div>')
    return "".join(bloques)


def generar(salida, carpeta_datos=DATA_DIR):
    registros = cargar(carpeta_datos)
    if not registros:
        raise SystemExit(f"No hay resultados en {carpeta_datos}; ejecuta primero los scrapers.")
    p = registros[0]
    con_resenas = max(registros, key=lambda r: len(r["resenas"]))
    commit = os.environ.get("GITHUB_SHA", "")[:7]
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    generado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    salida = Path(salida)
    (salida / "data").mkdir(parents=True, exist_ok=True)
    for nombre in DESCARGAS + ["captura_selenium.png"]:
        if (carpeta_datos / nombre).exists():
            shutil.copy(carpeta_datos / nombre, salida / "data" / nombre)
    captura = ('<section class="tarjeta"><h2>Ficha capturada por Selenium</h2>'
               '<img src="data/captura_selenium.png" alt="Captura de la ficha del producto en Amazon"></section>'
               if (salida / "data" / "captura_selenium.png").exists() else "")
    descargas = "".join(f'<a href="data/{n}" download>{n}</a>' for n in DESCARGAS
                        if (salida / "data" / n).exists())
    pie_repo = (f' · <a href="https://github.com/{repo}">repositorio</a>'
                f' · commit <a href="https://github.com/{repo}/commit/{os.environ.get("GITHUB_SHA", "")}">{commit}</a>'
                if repo else "")

    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tablero scraping Amazon</title>
<meta name="description"
  content="Resultados del web scraping del artículo {ASIN} de Amazon con BeautifulSoup, Selenium y Scrapy.">
<style>{CSS}</style></head>
<body>
<header><div class="cont">
  <small>Web scraping · {escape(p['categoria'] or '')}</small>
  <h1>{escape(p['titulo'] or '')}</h1>
  <p>Tienda {escape(p['tienda'] or '—')} · ASIN {ASIN} · <a href="{URL}">ver en Amazon</a></p>
</div></header>
<main>
  <section class="kpis">
    <div class="kpi"><span>Precio</span><strong>{pesos(p['precio_cop'])}</strong> COP</div>
    <div class="kpi"><span>Calificación</span><strong>{p['calificacion'] or '—'}</strong> / 5</div>
    <div class="kpi"><span>Calificaciones</span><strong>{p['num_calificaciones'] or '—'}</strong></div>
    <div class="kpi"><span>Disponibilidad</span><strong class="ok">{escape(p['disponibilidad'] or '—')}</strong></div>
  </section>
  <div class="grid">
    <section class="tarjeta"><h2>Distribución de estrellas</h2>{histograma(p['histograma_pct'])}</section>
    <section class="tarjeta"><h2>Comparación de los tres métodos</h2>
      <div class="tabla">{tabla_metodos(registros)}</div></section>
  </div>
  <section class="tarjeta"><h2>Características del producto</h2>
    <ul>{"".join(f"<li>{escape(c)}</li>" for c in p['caracteristicas'])}</ul></section>
  <section class="tarjeta"><h2>Reseñas destacadas ({len(con_resenas['resenas'])})</h2>
    {resenas(con_resenas['resenas'])}</section>
  {captura}
  <section class="tarjeta descargas"><h2>Descargar datos</h2>{descargas}</section>
</main>
<footer>Programación para Análisis de Datos · IU Digital · generado {generado}{pie_repo}</footer>
</body></html>
"""
    (salida / "index.html").write_text(html, encoding="utf-8")
    return salida / "index.html"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--salida", default=str(RAIZ / "public"))
    print("Sitio generado en", generar(parser.parse_args().salida))
