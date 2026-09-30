"""Dimensión temporal.

Calcula la evidencia de las preguntas y los conocimientos evidentes de la
dimensión temporal (evolución de las víctimas a través del tiempo). Ejecutar
desde la raíz del repositorio:

    python dimensiones/temporal.py
"""

import pandas as pd

RUTA = "data/violencia_intrafamiliar.csv"


def cargar_datos(ruta=RUTA):
    df = pd.read_csv(ruta, dtype={"CODIGO DANE": str})
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
    df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce")
    df["AÑO"] = df["FECHA HECHO"].dt.year
    df["MES"] = df["FECHA HECHO"].dt.to_period("M")
    df["TRIMESTRE"] = df["FECHA HECHO"].dt.quarter
    return df


_df_cache = None


def cargar_datos_cacheada(ruta=RUTA):
    """Igual que cargar_datos(), pero solo lee y procesa el CSV una vez por
    proceso (evita releer las ~92.000 filas en cada request de Flask)."""
    global _df_cache
    if _df_cache is None:
        _df_cache = cargar_datos(ruta)
    return _df_cache


def resumen_general(df):
    """Datos generales del encabezado del tablero."""
    return {
        "registros": len(df),
        "victimas": int(df["CANTIDAD"].sum()),
        "fecha_inicial": df["FECHA HECHO"].min().date(),
        "fecha_final": df["FECHA HECHO"].max().date(),
        "anios": sorted(df["AÑO"].dropna().unique().astype(int).tolist()),
    }


def aplicar_filtros(df, anio=None, desde=None, hasta=None):
    """Aplica los 2 filtros interactivos del tablero: año y rango de fechas."""
    filtrado = df
    if anio and anio != "todos":
        filtrado = filtrado[filtrado["AÑO"] == int(anio)]
    if desde:
        filtrado = filtrado[filtrado["FECHA HECHO"] >= pd.to_datetime(desde)]
    if hasta:
        filtrado = filtrado[filtrado["FECHA HECHO"] <= pd.to_datetime(hasta)]
    return filtrado


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


def indicadores(df, df_completo=None):
    """Los tres indicadores del tablero, calculados sobre el subconjunto filtrado.

    df_completo (sin filtrar) se usa solo para la comparación año contra año,
    que necesita conocer todos los años disponibles para saber qué meses son
    comunes a todos ellos.
    """
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

    comp, comunes = comparacion_anual(df_completo)
    variacion_anual = None
    if len(comp) >= 2:
        v_ini, v_fin = comp["VICTIMAS"].iloc[0], comp["VICTIMAS"].iloc[-1]
        if v_ini:
            variacion_anual = round((v_fin / v_ini - 1) * 100, 1)

    return {
        "victimas": total,
        "variacion_ultimo_mes": variacion,
        "mes_pico": mes_pico,
        "mes_valle": mes_valle,
        "variacion_anual": variacion_anual,
        "meses_comparados": comunes,
    }


def victimas_por_dia(df, mes="2025-12"):
    """Víctimas por día de un mes, para revisar si la carga está incompleta
    (evidencia de la anomalía de diciembre de 2025)."""
    datos_mes = df[df["MES"] == pd.Period(mes, freq="M")]
    return datos_mes.groupby(datos_mes["FECHA HECHO"].dt.day)["CANTIDAD"].sum()


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
