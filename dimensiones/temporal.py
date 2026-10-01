"""Dimensión temporal.

Calcula la evidencia de las preguntas y los conocimientos evidentes de la
dimensión temporal (evolución de las víctimas a través del tiempo). Ejecutar
desde la raíz del repositorio:

    python dimensiones/temporal.py
"""

from pathlib import Path

import pandas as pd


RUTA = Path(__file__).resolve().parent.parent / "data" / "violencia_intrafamiliar.csv"


def cargar_datos(ruta=RUTA):
    df = pd.read_csv(ruta, dtype={"CODIGO DANE": str})
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
    df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce")
    df["AÑO"] = df["FECHA HECHO"].dt.year
    df["MES"] = df["FECHA HECHO"].dt.to_period("M")
    df["TRIMESTRE"] = df["FECHA HECHO"].dt.quarter
    return df


def resumen_general(df):
    """Datos generales del encabezado del tablero."""
    return {
        "registros": len(df),
        "victimas": int(df["CANTIDAD"].sum()),
        "fecha_inicial": df["FECHA HECHO"].min().date(),
        "fecha_final": df["FECHA HECHO"].max().date(),
    }


# --- Tablero: filtros, datos de las gráficas e indicadores ---


GRANULARIDADES = {"mes", "trimestre"}


def leer_filtros(parametros):
    """Valida los filtros recibidos en la URL (?desde=...&hasta=...&granularidad=...).

    Los dos filtros resuelven preguntas distintas y no se solapan:
      - desde/hasta: QUÉ periodo se analiza (antes había además un selector de
        año, pero se quitó porque dejaba elegir el mismo periodo de dos formas
        distintas — observación de revisión del PR).
      - granularidad: CÓMO se agrupa ese periodo en la gráfica principal
        (mes a mes o trimestre a trimestre). No cambia qué datos entran al
        análisis, solo cómo se presentan.
    """
    desde = parametros.get("desde") or None
    hasta = parametros.get("hasta") or None
    granularidad = parametros.get("granularidad") or "mes"
    if granularidad not in GRANULARIDADES:
        granularidad = "mes"
    return desde, hasta, granularidad


def filtrar(df, desde=None, hasta=None):
    if desde:
        df = df[df["FECHA HECHO"] >= pd.to_datetime(desde)]
    if hasta:
        df = df[df["FECHA HECHO"] <= pd.to_datetime(hasta)]
    return df


def serie_mensual(df):
    """Víctimas por mes (visualización 1)."""
    serie = df.groupby("MES")["CANTIDAD"].sum().sort_index()
    return pd.DataFrame({"PERIODO": serie.index.astype(str), "VICTIMAS": serie.values})


def serie_trimestral(df):
    """Víctimas por trimestre y año, para ver estacionalidad (visualización 2)."""
    tabla = df.groupby(["AÑO", "TRIMESTRE"])["CANTIDAD"].sum().reset_index()
    tabla["ETIQUETA"] = (
        "Q" + tabla["TRIMESTRE"].astype(int).astype(str) + "-" + tabla["AÑO"].astype(int).astype(str)
    )
    return tabla.sort_values(["AÑO", "TRIMESTRE"])


def meses_comunes(df):
    """Meses (1-12) presentes en TODOS los años del conjunto de datos, para
    poder comparar periodos equivalentes sin sesgar por un año incompleto."""
    por_anio = df.groupby("AÑO")["FECHA HECHO"].apply(lambda s: set(s.dt.month))
    if len(por_anio) < 2:
        return set(range(1, 13))
    return set.intersection(*por_anio.tolist())


def comparacion_anual(df):
    """Víctimas por año, usando solo los meses comunes a todos los años
    (visualización 3: comparación año contra año)."""
    comunes = meses_comunes(df)
    sub = df[df["FECHA HECHO"].dt.month.isin(comunes)]
    tabla = sub.groupby("AÑO")["CANTIDAD"].sum().reset_index().rename(columns={"CANTIDAD": "VICTIMAS"})
    return tabla.sort_values("AÑO"), sorted(comunes)


def datos_mensual(df):
    serie = serie_mensual(df)
    return {"labels": serie["PERIODO"].tolist(), "valores": [int(v) for v in serie["VICTIMAS"]]}


def datos_trimestral(df):
    tabla = serie_trimestral(df)
    return {"labels": tabla["ETIQUETA"].tolist(), "valores": [int(v) for v in tabla["CANTIDAD"]]}


def datos_periodo(df, granularidad="mes"):
    """Visualización 1: víctimas por periodo, agrupadas por mes o por trimestre
    según el filtro de granularidad (no según el rango de fechas)."""
    if granularidad == "trimestre":
        base = datos_trimestral(df)
    else:
        base = datos_mensual(df)
    return {**base, "granularidad": granularidad}


def datos_variacion(df):
    """Visualización 2 (nueva): variación porcentual mes a mes dentro del
    periodo filtrado. El primer mes del rango no tiene mes anterior con el
    que compararse, así que se omite."""
    serie = serie_mensual(df)
    if len(serie) < 2:
        return {"labels": [], "valores": []}
    variacion = serie["VICTIMAS"].pct_change().mul(100).iloc[1:]
    return {
        "labels": serie["PERIODO"].iloc[1:].tolist(),
        "valores": [round(float(v), 1) for v in variacion],
    }


def datos_comparacion(df_completo):
    tabla, comunes = comparacion_anual(df_completo)
    return {
        "anios": [int(a) for a in tabla["AÑO"]],
        "valores": [int(v) for v in tabla["VICTIMAS"]],
        "meses_comunes": comunes,
    }


def indicadores(df, df_completo=None):
    """Los tres indicadores del tablero, calculados sobre el subconjunto filtrado."""
    df_completo = df if df_completo is None else df_completo
    mensual = serie_mensual(df)
    total = int(df["CANTIDAD"].sum())

    variacion = None
    if len(mensual) >= 2:
        ultimo, anterior = mensual["VICTIMAS"].iloc[-1], mensual["VICTIMAS"].iloc[-2]
        if anterior:
            variacion = round((ultimo / anterior - 1) * 100, 1)

    mes_pico = mes_valle = None
    if not mensual.empty:
        fila_pico = mensual.loc[mensual["VICTIMAS"].idxmax()]
        fila_valle = mensual.loc[mensual["VICTIMAS"].idxmin()]
        mes_pico = {"periodo": fila_pico["PERIODO"], "victimas": int(fila_pico["VICTIMAS"])}
        mes_valle = {"periodo": fila_valle["PERIODO"], "victimas": int(fila_valle["VICTIMAS"])}

    _, comunes = comparacion_anual(df_completo)

    return {
        "victimas": total,
        "variacion_ultimo_mes": variacion,
        "mes_pico": mes_pico,
        "mes_valle": mes_valle,
        "meses_comparados": len(comunes),
    }


def victimas_por_dia(df, mes="2025-12"):
    """Víctimas por día de un mes (evidencia de la anomalía de diciembre de 2025)."""
    datos_mes = df[df["MES"] == pd.Period(mes, freq="M")]
    return datos_mes.groupby(datos_mes["FECHA HECHO"].dt.day)["CANTIDAD"].sum()


def contexto(df, parametros):
    """Todo lo que necesita la plantilla temporal.html, según los filtros de la URL."""
    desde, hasta, granularidad = leer_filtros(parametros)
    datos = filtrar(df, desde, hasta)
    return {
        "resumen": resumen_general(df),
        "indicadores": indicadores(datos, df_completo=df) if len(datos) else None,
        "filtros": {"desde": desde, "hasta": hasta, "granularidad": granularidad},
        "graficas": {
            "periodo": datos_periodo(datos, granularidad),
            "variacion": datos_variacion(datos),
            "comparacion": datos_comparacion(df),
        },
    }


def _redondear(diccionario):
    return {
        clave: (round(float(valor), 1) if isinstance(valor, float) else valor)
        for clave, valor in diccionario.items()
    }


if __name__ == "__main__":
    datos = cargar_datos()
    print("Resumen general:", resumen_general(datos))
    print("Indicadores:", _redondear(indicadores(datos)))

    print("\nSerie mensual")
    print(serie_mensual(datos).to_string(index=False))

    print("\nSerie trimestral")
    print(serie_trimestral(datos).to_string(index=False))

    print("\nComparación año contra año (meses comunes)")
    comp, comunes = comparacion_anual(datos)
    print("Meses comparados:", comunes)
    print(comp.to_string(index=False))

    print("\nVíctimas por día en diciembre de 2025 (evidencia de carga incompleta)")
    print(victimas_por_dia(datos).to_string())
