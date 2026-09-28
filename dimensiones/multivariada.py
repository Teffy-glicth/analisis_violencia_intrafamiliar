"""Dimensión relacional y multivariada.

Calcula la evidencia de las preguntas y los conocimientos evidentes de la
dimensión. Ejecutar desde la raíz del repositorio:

    python dimensiones/multivariada.py
"""

import pandas as pd

RUTA = "data/violencia_intrafamiliar.csv"
SIN_ARMAS = "SIN EMPLEO DE ARMAS"
ARMAS = ["CONTUNDENTES", "ARMA BLANCA / CORTOPUNZANTE", "ARMA DE FUEGO"]
MENORES = ["MENORES", "ADOLESCENTES"]


def cargar_datos(ruta=RUTA):
    df = pd.read_csv(ruta, dtype={"CODIGO DANE": str})
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
    df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce")
    for columna in ["MUNICIPIO", "GENERO", "GRUPO ETARIO"]:
        df[columna] = df[columna].fillna("No reporta")
    df["AÑO"] = df["FECHA HECHO"].dt.year
    df["MES"] = df["FECHA HECHO"].dt.to_period("M")
    df["CON_ARMA"] = df["ARMAS MEDIOS"].isin(ARMAS)
    # Los 5 primeros dígitos del código DANE identifican el municipio; los 3 últimos, el centro poblado.
    df["CODIGO MUNICIPIO"] = df["CODIGO DANE"].str[:5]
    return df


def resumen_general(df):
    """Datos generales del encabezado y vacíos que se muestran como «No reporta»."""
    municipios = df.loc[~df["CODIGO MUNICIPIO"].str.endswith("000"), "CODIGO MUNICIPIO"]
    return {
        "registros": len(df),
        "victimas": int(df["CANTIDAD"].sum()),
        "fecha_inicial": df["FECHA HECHO"].min().date(),
        "fecha_final": df["FECHA HECHO"].max().date(),
        "departamentos": df["DEPARTAMENTO"].nunique(),
        "municipios": municipios.nunique(),
        "victimas_sin_genero": int(df.loc[df["GENERO"] == "No reporta", "CANTIDAD"].sum()),
        "victimas_sin_grupo_etario": int(df.loc[df["GRUPO ETARIO"] == "No reporta", "CANTIDAD"].sum()),
        "registros_sin_municipio": int((df["MUNICIPIO"] == "No reporta").sum()),
    }


def indicadores(df):
    """Los tres indicadores del tablero."""
    total = df["CANTIDAD"].sum()
    mujeres = df.loc[df["GENERO"] == "FEMENINO", "CANTIDAD"].sum()
    con_arma = df.loc[df["CON_ARMA"], "CANTIDAD"].sum()
    combinacion = combinaciones(df).iloc[0]
    return {
        "victimas": int(total),
        "mujeres": int(mujeres),
        "pct_mujeres": mujeres / total * 100,
        "con_arma": int(con_arma),
        "pct_con_arma": con_arma / total * 100,
        "combinacion_principal": " · ".join(combinacion[["GENERO", "GRUPO ETARIO", "ARMAS MEDIOS"]]),
        "victimas_combinacion_principal": int(combinacion["CANTIDAD"]),
        "pct_combinacion_principal": combinacion["PORCENTAJE"],
    }


def combinaciones(df):
    """Víctimas por género, grupo etario y arma/medio (conocimiento 1)."""
    tabla = (
        df.groupby(["GENERO", "GRUPO ETARIO", "ARMAS MEDIOS"])["CANTIDAD"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    tabla["PORCENTAJE"] = tabla["CANTIDAD"] / tabla["CANTIDAD"].sum() * 100
    tabla["PORCENTAJE_ACUMULADO"] = tabla["PORCENTAJE"].cumsum()
    return tabla


def genero_por_grupo_etario(df):
    """Porcentaje de cada género dentro de cada grupo etario (conocimiento 1)."""
    return pd.crosstab(
        df["GRUPO ETARIO"], df["GENERO"], values=df["CANTIDAD"], aggfunc="sum", normalize="index"
    ).mul(100)


def armas_por_grupo_etario(df):
    """Porcentaje de cada arma/medio dentro de cada grupo etario (conocimiento 1)."""
    return pd.crosstab(
        df["GRUPO ETARIO"], df["ARMAS MEDIOS"], values=df["CANTIDAD"], aggfunc="sum", normalize="index"
    ).fillna(0).mul(100)


def mujeres_por_grupo_y_arma(df):
    """Porcentaje de mujeres y víctimas en cada cruce de grupo etario y arma/medio (conocimiento 1)."""
    tabla = df.groupby(["GRUPO ETARIO", "ARMAS MEDIOS"]).agg(VICTIMAS=("CANTIDAD", "sum"))
    mujeres = df[df["GENERO"] == "FEMENINO"].groupby(["GRUPO ETARIO", "ARMAS MEDIOS"])["CANTIDAD"].sum()
    tabla["PCT_MUJERES"] = (mujeres / tabla["VICTIMAS"] * 100).fillna(0)
    return tabla.reset_index()


def armas_nacional(df):
    """Porcentaje nacional de víctimas por arma/medio (referencia del conocimiento 2)."""
    return (
        df.groupby("ARMAS MEDIOS")["CANTIDAD"].sum()
        .div(df["CANTIDAD"].sum())
        .mul(100)
        .sort_values(ascending=False)
    )


def armas_por_departamento(df):
    """Porcentaje de víctimas por arma/medio y de mujeres en cada departamento (conocimiento 2)."""
    tabla = pd.crosstab(
        df["DEPARTAMENTO"], df["ARMAS MEDIOS"], values=df["CANTIDAD"], aggfunc="sum", normalize="index"
    ).fillna(0).mul(100)
    total = df.groupby("DEPARTAMENTO")["CANTIDAD"].sum()
    mujeres = df[df["GENERO"] == "FEMENINO"].groupby("DEPARTAMENTO")["CANTIDAD"].sum()
    con_arma = df[df["CON_ARMA"]].groupby("DEPARTAMENTO")["CANTIDAD"].sum()
    tabla["% CON ARMA"] = (con_arma / total * 100).fillna(0)
    tabla["% MUJERES"] = mujeres / total * 100
    tabla["VICTIMAS"] = total
    return tabla.sort_values("CONTUNDENTES", ascending=False)


def registro_por_departamento(df):
    """Registros, víctimas, víctimas por registro y % de menores y adolescentes (conocimiento 3)."""
    menores = df["GRUPO ETARIO"].isin(MENORES)
    tabla = df.groupby("DEPARTAMENTO").agg(
        REGISTROS=("CANTIDAD", "size"), VICTIMAS=("CANTIDAD", "sum")
    )
    tabla["VICTIMAS_POR_REGISTRO"] = tabla["VICTIMAS"] / tabla["REGISTROS"]
    tabla["PCT_REGISTROS_PAIS"] = tabla["REGISTROS"] / tabla["REGISTROS"].sum() * 100
    tabla["PCT_VICTIMAS_PAIS"] = tabla["VICTIMAS"] / tabla["VICTIMAS"].sum() * 100
    tabla["PCT_MENORES_ADOLESCENTES"] = (
        df[menores].groupby("DEPARTAMENTO")["CANTIDAD"].sum() / tabla["VICTIMAS"] * 100
    )
    return tabla.sort_values("VICTIMAS", ascending=False)


def menores_bogota_vs_resto(df, departamento="BOGOTA"):
    """Menores y adolescentes en Bogotá frente al resto del país (conocimiento 3)."""
    menores = df["GRUPO ETARIO"].isin(MENORES)
    es_bogota = df["DEPARTAMENTO"] == departamento
    menores_bogota = df.loc[menores & es_bogota, "CANTIDAD"].sum()
    return {
        "pct_menores_bogota": menores_bogota / df.loc[es_bogota, "CANTIDAD"].sum() * 100,
        "pct_menores_resto": (
            df.loc[menores & ~es_bogota, "CANTIDAD"].sum() / df.loc[~es_bogota, "CANTIDAD"].sum() * 100
        ),
        "pct_menores_pais_en_bogota": menores_bogota / df.loc[menores, "CANTIDAD"].sum() * 100,
    }


def registros_grandes(df, minimo=50):
    """Registros con muchas víctimas en una sola fila, por departamento (conocimiento 3)."""
    grandes = df[df["CANTIDAD"] >= minimo]
    return {
        "total": len(grandes),
        "por_departamento": grandes["DEPARTAMENTO"].value_counts(),
        "maximo": int(df["CANTIDAD"].max()),
    }


def victimas_por_mes(df):
    """Víctimas por mes, para detectar periodos inusuales (diciembre de 2025)."""
    return df.groupby("MES")["CANTIDAD"].sum()


def victimas_por_dia(df, mes="2025-12"):
    """Víctimas por día de un mes, para revisar si la carga está incompleta (diciembre de 2025)."""
    datos_mes = df[df["MES"] == pd.Period(mes, freq="M")]
    return datos_mes.groupby(datos_mes["FECHA HECHO"].dt.day)["CANTIDAD"].sum()


def comparacion_interanual(df, hasta_mes=7):
    """Víctimas de enero a hasta_mes en 2025 y 2026 por grupo etario y género, con su variación."""
    periodo = df[df["FECHA HECHO"].dt.month <= hasta_mes]
    tabla = periodo.pivot_table(
        index=["GRUPO ETARIO", "GENERO"], columns="AÑO", values="CANTIDAD", aggfunc="sum", fill_value=0
    )
    tabla["VARIACION_%"] = (tabla[2026] - tabla[2025]) / tabla[2025] * 100
    return tabla


def _redondear(diccionario):
    return {
        clave: round(float(valor), 1) if isinstance(valor, float) else valor
        for clave, valor in diccionario.items()
    }


if __name__ == "__main__":
    datos = cargar_datos()
    print("Resumen general:", resumen_general(datos))
    print("Indicadores:", _redondear(indicadores(datos)))

    print("\n--- Conocimiento 1 ---")
    print("Top combinaciones género · grupo etario · arma/medio")
    print(combinaciones(datos).head(10).round(2).to_string(index=False))
    print("\n% de género dentro de cada grupo etario")
    print(genero_por_grupo_etario(datos).round(1))
    print("\n% de arma/medio dentro de cada grupo etario")
    print(armas_por_grupo_etario(datos).round(1))
    print("\n% de mujeres por grupo etario y arma/medio")
    print(mujeres_por_grupo_y_arma(datos).round(1).to_string(index=False))

    print("\n--- Conocimiento 2 ---")
    print("% nacional por arma/medio")
    print(armas_nacional(datos).round(1).to_string())
    print("\n% por arma/medio y % mujeres por departamento")
    print(armas_por_departamento(datos).round(1).to_string())

    print("\n--- Conocimiento 3 ---")
    print("Registro por departamento")
    print(registro_por_departamento(datos).head(8).round(1).to_string())
    print("\nMenores y adolescentes:", _redondear(menores_bogota_vs_resto(datos)))
    grandes = registros_grandes(datos)
    print(f"Registros con 50 o más víctimas: {grandes['total']} (máximo {grandes['maximo']})")
    print(grandes["por_departamento"].to_string())

    print("\n--- Casos inusuales ---")
    print("Víctimas por mes")
    print(victimas_por_mes(datos).to_string())
    print("\nVíctimas por día en diciembre de 2025")
    print(victimas_por_dia(datos).to_string())
    print("\nEnero a julio: 2025 frente a 2026")
    print(comparacion_interanual(datos).round(1).to_string())
