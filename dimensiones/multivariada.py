"""Dimensión relacional y multivariada.

Calcula la evidencia de las preguntas y los conocimientos evidentes de la
dimensión. Ejecutar desde la raíz del repositorio:

    python dimensiones/multivariada.py
"""

import pandas as pd

RUTA = "data/violencia_intrafamiliar.csv"
SIN_ARMAS = "SIN EMPLEO DE ARMAS"


def cargar_datos(ruta=RUTA):
    df = pd.read_csv(ruta, dtype={"CODIGO DANE": str})
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
    df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce")
    for columna in ["MUNICIPIO", "GENERO", "GRUPO ETARIO"]:
        df[columna] = df[columna].fillna("No reporta")
    df["AÑO"] = df["FECHA HECHO"].dt.year
    df["MES"] = df["FECHA HECHO"].dt.to_period("M")
    df["CON_ARMA"] = df["ARMAS MEDIOS"] != SIN_ARMAS
    return df


def indicadores(df):
    total = df["CANTIDAD"].sum()
    combinacion = combinaciones(df).iloc[0]
    return {
        "victimas": int(total),
        "pct_mujeres": df.loc[df["GENERO"] == "FEMENINO", "CANTIDAD"].sum() / total * 100,
        "pct_con_arma": df.loc[df["CON_ARMA"], "CANTIDAD"].sum() / total * 100,
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
    return tabla


def genero_por_grupo_etario(df):
    """Porcentaje de cada género dentro de cada grupo etario (conocimiento 1)."""
    return pd.crosstab(
        df["GRUPO ETARIO"], df["GENERO"], values=df["CANTIDAD"], aggfunc="sum", normalize="index"
    ).mul(100)


def armas_por_departamento(df):
    """Porcentaje de víctimas por arma/medio y de mujeres en cada departamento (conocimiento 2)."""
    tabla = pd.crosstab(
        df["DEPARTAMENTO"], df["ARMAS MEDIOS"], values=df["CANTIDAD"], aggfunc="sum", normalize="index"
    ).fillna(0).mul(100)
    total = df.groupby("DEPARTAMENTO")["CANTIDAD"].sum()
    mujeres = df[df["GENERO"] == "FEMENINO"].groupby("DEPARTAMENTO")["CANTIDAD"].sum()
    tabla["% MUJERES"] = mujeres / total * 100
    tabla["VICTIMAS"] = total
    return tabla.sort_values("CONTUNDENTES", ascending=False)


def registro_por_departamento(df):
    """Registros, víctimas, víctimas por registro y % de menores y adolescentes (conocimiento 3)."""
    menores = df["GRUPO ETARIO"].isin(["MENORES", "ADOLESCENTES"])
    tabla = df.groupby("DEPARTAMENTO").agg(
        REGISTROS=("CANTIDAD", "size"), VICTIMAS=("CANTIDAD", "sum")
    )
    tabla["VICTIMAS_POR_REGISTRO"] = tabla["VICTIMAS"] / tabla["REGISTROS"]
    tabla["PCT_VICTIMAS_PAIS"] = tabla["VICTIMAS"] / tabla["VICTIMAS"].sum() * 100
    tabla["PCT_MENORES_ADOLESCENTES"] = (
        df[menores].groupby("DEPARTAMENTO")["CANTIDAD"].sum() / tabla["VICTIMAS"] * 100
    )
    return tabla.sort_values("VICTIMAS", ascending=False)


def victimas_por_mes(df):
    """Víctimas por mes, para detectar periodos inusuales (diciembre de 2025)."""
    return df.groupby("MES")["CANTIDAD"].sum()


if __name__ == "__main__":
    datos = cargar_datos()
    print("Indicadores:", {k: round(float(v), 1) for k, v in indicadores(datos).items()})
    print("\nTop combinaciones género · grupo etario · arma/medio")
    print(combinaciones(datos).head(10).round(2).to_string(index=False))
    print("\n% de género dentro de cada grupo etario")
    print(genero_por_grupo_etario(datos).round(1))
    print("\n% por arma/medio y % mujeres por departamento")
    print(armas_por_departamento(datos).round(1).to_string())
    print("\nRegistro por departamento")
    print(registro_por_departamento(datos).head(8).round(1).to_string())
    print("\nVíctimas por mes")
    print(victimas_por_mes(datos).to_string())
