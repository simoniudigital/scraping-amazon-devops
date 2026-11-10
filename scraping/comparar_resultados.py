"""Une los resultados de los tres métodos en tablas CSV/Excel.

Uso:  python comparar_resultados.py
"""
import json

import pandas as pd

from comun import DATA_DIR

ARCHIVOS = {"BeautifulSoup": "producto_bs4.json", "Selenium": "producto_selenium.json",
            "Scrapy": "producto_scrapy.json"}
CAMPOS = ["titulo", "precio", "moneda", "calificacion", "num_calificaciones", "tienda",
          "disponibilidad", "categoria"]


def cargar(carpeta=DATA_DIR):
    registros = []
    for archivo in ARCHIVOS.values():
        ruta = carpeta / archivo
        if ruta.exists():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            registros.extend(datos if isinstance(datos, list) else [datos])
    return registros


def tabla_comparativa(registros):
    filas = []
    for r in registros:
        filas.append({
            "metodo": r["metodo"],
            "fuente": r["fuente"],
            "tiempo_seg": r["tiempo_seg"],
            "campos_ok": f"{sum(r[c] not in (None, '') for c in CAMPOS)}/{len(CAMPOS)}",
            **{c: r[c] for c in CAMPOS},
            "caracteristicas": len(r["caracteristicas"]),
            "resenas": len(r["resenas"]),
        })
    return pd.DataFrame(filas)


def tabla_resenas(registro):
    df = pd.DataFrame(registro["resenas"])
    if not df.empty:
        df["estrellas"] = df["estrellas"].str.extract(r"(\d)").astype(int)
        df["fecha"] = df["fecha"].str.replace(r"^.* el ", "", regex=True)
    return df


if __name__ == "__main__":
    registros = cargar()
    comparacion = tabla_comparativa(registros)
    resenas = tabla_resenas(registros[0])
    print(comparacion.T.to_string())
    comparacion.to_csv(DATA_DIR / "comparacion_metodos.csv", index=False, encoding="utf-8-sig")
    resenas.to_csv(DATA_DIR / "resenas.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(DATA_DIR / "resultados_amazon.xlsx") as excel:
        comparacion.to_excel(excel, sheet_name="comparacion", index=False)
        resenas.to_excel(excel, sheet_name="resenas", index=False)
    print("\nGuardado: comparacion_metodos.csv, resenas.csv y resultados_amazon.xlsx en data/")
