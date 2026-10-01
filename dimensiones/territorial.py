"""Cálculos de la dimensión territorial."""

from pathlib import Path

import pandas as pd

RUTA = Path(__file__).resolve().parent.parent / "data" / "violencia_intrafamiliar.csv"
ANIOS = [2025, 2026]


def cargar_datos(ruta=RUTA):
    df = pd.read_csv(ruta, dtype={"CODIGO DANE": str})
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
    df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce")
    df["AÑO"] = df["FECHA HECHO"].dt.year
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].fillna("No reporta")
    df["MUNICIPIO"] = df["MUNICIPIO"].fillna("No reporta")
    df["CODIGO DANE"] = df["CODIGO DANE"].fillna("")
    df["CODIGO MUNICIPIO"] = df["CODIGO DANE"].str[:5]
    df["NIVEL TERRITORIAL"] = df["CODIGO DANE"].str[-3:].eq("000").map({
        True: "Código municipal (terminación 000)",
        False: "Centro poblado (terminación distinta de 000)",
    })
    return df


def filtrar(df, departamento="", anio=""):
    if departamento in df["DEPARTAMENTO"].values:
        df = df[df["DEPARTAMENTO"] == departamento]
    if anio in [str(a) for a in ANIOS]:
        df = df[df["AÑO"] == int(anio)]
    return df


def num(valor, decimales=0):
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _nombre_reportado(valores):
    nombres = valores[valores != "No reporta"]
    return nombres.mode().iloc[0] if not nombres.empty else "No reporta"


def por_departamento(df):
    tabla = df.groupby("DEPARTAMENTO", as_index=False).agg(
        VICTIMAS=("CANTIDAD", "sum"),
        REGISTROS=("CANTIDAD", "size"),
    )
    total = tabla["VICTIMAS"].sum()
    tabla["PORCENTAJE"] = tabla["VICTIMAS"] / total * 100 if total else 0
    return tabla.sort_values("VICTIMAS", ascending=False).reset_index(drop=True)


def por_municipio(df):
    tabla = (
        df.groupby(["DEPARTAMENTO", "CODIGO MUNICIPIO"], as_index=False, dropna=False)
        .agg(
            MUNICIPIO=("MUNICIPIO", _nombre_reportado),
            VICTIMAS=("CANTIDAD", "sum"),
            REGISTROS=("CANTIDAD", "size"),
        )
    )
    total = tabla["VICTIMAS"].sum()
    tabla["PORCENTAJE"] = tabla["VICTIMAS"] / total * 100 if total else 0
    tabla["TERRITORIO"] = tabla.apply(
        lambda fila: f'{fila["MUNICIPIO"]} ({fila["DEPARTAMENTO"]})',
        axis=1,
    )
    return tabla.sort_values("VICTIMAS", ascending=False).reset_index(drop=True)


def por_nivel_territorial(df):
    tabla = df.groupby("NIVEL TERRITORIAL", as_index=False).agg(
        VICTIMAS=("CANTIDAD", "sum"),
        REGISTROS=("CANTIDAD", "size"),
        CODIGOS=("CODIGO DANE", "nunique"),
    )
    total = tabla["VICTIMAS"].sum()
    tabla["PORCENTAJE"] = tabla["VICTIMAS"] / total * 100 if total else 0
    return tabla


def concentracion_municipal(df):
    tabla = por_municipio(df)
    tabla = tabla[tabla["VICTIMAS"] > 0].copy().reset_index(drop=True)
    total = tabla["VICTIMAS"].sum()
    if not total:
        return {"puntos": [], "municipios_50": 0, "municipios_80": 0, "total_municipios": 0}

    tabla["ACUMULADO"] = tabla["VICTIMAS"].cumsum()
    tabla["PORCENTAJE_ACUMULADO"] = tabla["ACUMULADO"] / total * 100
    tabla["ORDEN"] = range(1, len(tabla) + 1)
    puntos = [
        {
            "x": int(fila["ORDEN"]),
            "y": round(float(fila["PORCENTAJE_ACUMULADO"]), 2),
            "territorio": fila["TERRITORIO"],
            "victimas": int(fila["VICTIMAS"]),
            "acumulado": int(fila["ACUMULADO"]),
        }
        for _, fila in tabla.iterrows()
    ]
    municipios_80 = int((tabla["PORCENTAJE_ACUMULADO"] < 80).sum() + 1)
    return {
        "puntos": puntos,
        "municipios_50": int((tabla["PORCENTAJE_ACUMULADO"] < 50).sum() + 1),
        "municipios_80": municipios_80,
        "pct_municipios_80": round(municipios_80 / len(tabla) * 100, 2),
        "total_municipios": len(tabla),
    }


def tabla_ranking(df):
    tabla = por_municipio(df)
    filas = []
    tabla = tabla.sort_values(
        ["VICTIMAS", "TERRITORIO"],
        ascending=[False, True],
        kind="stable",
    ).reset_index(drop=True)
    for indice, fila in tabla.iterrows():
        filas.append({
            "posicion": indice + 1,
            "territorio": fila["TERRITORIO"],
            "codigo": fila["CODIGO MUNICIPIO"],
            "registros": num(fila["REGISTROS"]),
            "victimas": num(fila["VICTIMAS"]),
            "porcentaje": num(fila["PORCENTAJE"], 4),
            "busqueda": f'{fila["TERRITORIO"]} {fila["CODIGO MUNICIPIO"]}'.casefold(),
        })
    return filas


def resumen(df):
    municipios = por_municipio(df)
    con_victimas = municipios[municipios["VICTIMAS"] > 0]
    total = df["CANTIDAD"].sum()
    maximo = con_victimas.iloc[0] if not con_victimas.empty else None
    return {
        "total": num(total),
        "registros": num(len(df)),
        "municipios": num(len(municipios)),
        "territorios_codificados": num(df["CODIGO DANE"].nunique()),
        "municipio_max": maximo["TERRITORIO"] if maximo is not None else "Sin datos",
        "victimas_max": num(maximo["VICTIMAS"]) if maximo is not None else "0",
        "pct_max": num(maximo["PORCENTAJE"], 2) if maximo is not None else "0,00",
    }


def _texto_grafica(tabla, columna):
    return {
        "etiquetas": tabla[columna].astype(str).tolist(),
        "victimas": [int(valor) for valor in tabla["VICTIMAS"]],
        "porcentajes": [round(float(valor), 2) for valor in tabla["PORCENTAJE"]],
    }


def _comparacion_cundinamarca(df):
    departamentos = por_departamento(df)
    cundinamarca = departamentos[
        departamentos["DEPARTAMENTO"].str.casefold() == "cundinamarca"
    ]["VICTIMAS"].sum()
    demas = departamentos[
        departamentos["DEPARTAMENTO"].str.casefold() != "cundinamarca"
    ]
    otros = demas["VICTIMAS"].sum()
    total = cundinamarca + otros

    return {
        "etiquetas": ["Cundinamarca", f"Los demás ({len(demas)} departamentos)"],
        "victimas": [int(cundinamarca), int(otros)],
        "porcentajes": [
            round(float(cundinamarca / total * 100), 2) if total else 0,
            round(float(otros / total * 100), 2) if total else 0,
        ],
    }


def graficas(df, df_comparacion=None):
    departamentos = por_departamento(df)
    municipios = por_municipio(df).head(12)
    return {
        "departamentos": _texto_grafica(departamentos, "DEPARTAMENTO"),
        "municipios": _texto_grafica(municipios, "TERRITORIO"),
        "comparacion_cundinamarca": _comparacion_cundinamarca(
            df if df_comparacion is None else df_comparacion
        ),
        "concentracion": concentracion_municipal(df),
    }


def datos_conocimientos(df):
    departamentos = por_departamento(df)
    municipios = por_municipio(df)
    niveles = por_nivel_territorial(df).set_index("NIVEL TERRITORIAL")
    total_victimas = df["CANTIDAD"].sum()
    top5 = departamentos.head(5)
    top_municipio = municipios.iloc[0]
    municipios_con_victimas = municipios[municipios["VICTIMAS"] > 0]
    victimas_minimas = municipios_con_victimas["VICTIMAS"].min()
    bottom_municipio = municipios_con_victimas[municipios_con_victimas["VICTIMAS"] == victimas_minimas].iloc[0]
    municipal = niveles.loc["Código municipal (terminación 000)"]
    centro = niveles.loc["Centro poblado (terminación distinta de 000)"]

    return {
        "departamento_mayor": departamentos.iloc[0]["DEPARTAMENTO"],
        "victimas_departamento_mayor": num(departamentos.iloc[0]["VICTIMAS"]),
        "pct_departamento_mayor": num(departamentos.iloc[0]["PORCENTAJE"], 2),
        "departamento_menor": departamentos.iloc[-1]["DEPARTAMENTO"],
        "victimas_departamento_menor": num(departamentos.iloc[-1]["VICTIMAS"]),
        "pct_top5_departamentos": num(top5["VICTIMAS"].sum() / total_victimas * 100, 2) if total_victimas else "0,00",
        "municipio_mayor": top_municipio["TERRITORIO"],
        "victimas_municipio_mayor": num(top_municipio["VICTIMAS"]),
        "pct_municipio_mayor": num(top_municipio["PORCENTAJE"], 2),
        "municipio_menor": bottom_municipio["TERRITORIO"],
        "victimas_municipio_menor": num(bottom_municipio["VICTIMAS"]),
        "municipios_empatados_minimo": num(
            (municipios_con_victimas["VICTIMAS"] == victimas_minimas).sum()
        ),
        "diferencia_municipios": num(
            top_municipio["VICTIMAS"] / victimas_minimas if victimas_minimas else 0,
            1,
        ),
        "registros_codigo_municipal": num(municipal["REGISTROS"]),
        "victimas_codigo_municipal": num(municipal["VICTIMAS"]),
        "pct_codigo_municipal": num(municipal["PORCENTAJE"], 2),
        "codigos_municipales": num(municipal["CODIGOS"]),
        "registros_centros": num(centro["REGISTROS"]),
        "victimas_centros": num(centro["VICTIMAS"]),
        "pct_centros": num(centro["PORCENTAJE"], 2),
        "codigos_centros": num(centro["CODIGOS"]),
    }


def pagina(df, args):
    departamento = args.get("departamento", "")
    anio = args.get("anio", "")
    datos = filtrar(df, departamento, anio)
    info = {
        "departamentos": sorted(df["DEPARTAMENTO"].unique()),
        "anios": ANIOS,
        "depto_elegido": departamento if departamento in df["DEPARTAMENTO"].values else "",
        "anio_elegido": anio if anio in [str(a) for a in ANIOS] else "",
        "periodo": f'{df["FECHA HECHO"].min():%d/%m/%Y} al {df["FECHA HECHO"].max():%d/%m/%Y}',
        "general": resumen(df),
        "conocimiento": datos_conocimientos(df),
        "hay_datos": not datos.empty,
    }
    if info["hay_datos"]:
        info["r"] = resumen(datos)
        info["tabla"] = tabla_ranking(datos)
        info["graficas"] = graficas(datos, filtrar(df, "", anio))
    return info
