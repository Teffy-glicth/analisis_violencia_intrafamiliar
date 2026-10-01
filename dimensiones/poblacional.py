# Dimension poblacional
# Pregunta: ¿Cómo está compuesta y distribuida la población de víctimas de
# violencia intrafamiliar según sus principales características?
#
# Para ver los resultados en la terminal:  python dimensiones/poblacional.py

import os

import pandas as pd

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO = os.path.join(CARPETA, "data", "violencia_intrafamiliar.csv")

VARIABLES = ["GENERO", "GRUPO ETARIO", "ARMAS MEDIOS"]
ANIOS = [2025, 2026]


def cargar_datos():
    df = pd.read_csv(ARCHIVO, dtype={"CODIGO DANE": str})
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
    df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce")
    df["AÑO"] = df["FECHA HECHO"].dt.year

    # los vacios no se eliminan, quedan como "No reporta"
    for col in VARIABLES:
        df[col] = df[col].fillna("No reporta").replace("NO REPORTADO", "No reporta")
    return df


def filtrar(df, departamento="", anio=""):
    if departamento in df["DEPARTAMENTO"].values:
        df = df[df["DEPARTAMENTO"] == departamento]
    if anio in [str(a) for a in ANIOS]:
        df = df[df["AÑO"] == int(anio)]
    return df


def num(valor, decimales=0):
    # formato colombiano: 233.411 y 73,9
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def victimas_por(df, columna):
    # suma de CANTIDAD por categoria (no se cuentan filas) y su porcentaje
    tabla = df.groupby(columna)["CANTIDAD"].sum().sort_values(ascending=False).reset_index()
    tabla.columns = ["categoria", "victimas"]
    tabla["porcentaje"] = tabla["victimas"] / tabla["victimas"].sum() * 100

    # "No reporta" siempre de ultimo
    sin_dato = tabla["categoria"] == "No reporta"
    return pd.concat([tabla[~sin_dato], tabla[sin_dato]]).reset_index(drop=True)


def pct_de(tabla, categoria):
    fila = tabla[tabla["categoria"] == categoria]
    return fila["porcentaje"].sum()


def victimas_de(tabla, categoria):
    fila = tabla[tabla["categoria"] == categoria]
    return fila["victimas"].sum()


def participacion(df):
    # tabla de participacion por categoria con el grupo predominante y el minoritario
    filas = []
    nombres = {"GENERO": "Género", "GRUPO ETARIO": "Grupo etario", "ARMAS MEDIOS": "Arma o medio"}
    for col in VARIABLES:
        tabla = victimas_por(df, col)
        con_dato = tabla[tabla["categoria"] != "No reporta"]
        for i, fila in tabla.iterrows():
            if fila["categoria"] == "No reporta":
                grupo = "Sin dato"
            elif fila["categoria"] == con_dato["categoria"].iloc[0]:
                grupo = "Predominante"
            elif fila["categoria"] == con_dato["categoria"].iloc[-1]:
                grupo = "Minoritario"
            else:
                grupo = ""
            filas.append({
                "variable": nombres[col] if i == 0 else "",
                "categoria": fila["categoria"].capitalize() if fila["categoria"] != "No reporta" else "No reporta",
                "victimas": num(fila["victimas"]),
                "porcentaje": num(fila["porcentaje"], 2),
                "grupo": grupo,
            })
    return filas


def resumen(df):
    genero = victimas_por(df, "GENERO")
    edad = victimas_por(df, "GRUPO ETARIO")
    armas = victimas_por(df, "ARMAS MEDIOS")

    total = df["CANTIDAD"].sum()
    mujeres = victimas_de(genero, "FEMENINO")
    hombres = victimas_de(genero, "MASCULINO")
    nna = victimas_de(edad, "MENORES") + victimas_de(edad, "ADOLESCENTES")
    predominante = edad[edad["categoria"] != "No reporta"].iloc[0]

    return {
        "total": num(total),
        "registros": num(len(df)),
        "por_registro": num(total / len(df), 1),
        "mujeres": num(mujeres),
        "pct_mujeres": num(pct_de(genero, "FEMENINO"), 1),
        "pct_hombres": num(pct_de(genero, "MASCULINO"), 1),
        "pct_genero_nr": num(pct_de(genero, "No reporta"), 1),
        "mujeres_por_hombre": num(mujeres / hombres, 1) if hombres else None,
        "grupo_predominante": predominante["categoria"].capitalize(),
        "pct_grupo_predominante": num(predominante["porcentaje"], 1),
        "victimas_grupo_predominante": num(predominante["victimas"]),
        "pct_adultos": num(pct_de(edad, "ADULTOS"), 1),
        "nna": num(nna),
        "pct_nna": num(nna / total * 100, 1),
        "uno_de_cada": round(total / nna) if nna else None,
        "pct_sin_armas": num(pct_de(armas, "SIN EMPLEO DE ARMAS"), 1),
        "pct_con_arma": num(100 - pct_de(armas, "SIN EMPLEO DE ARMAS") - pct_de(armas, "No reporta"), 1),
        "pct_contundentes": num(pct_de(armas, "CONTUNDENTES"), 1),
        "pct_arma_blanca": num(pct_de(armas, "ARMA BLANCA / CORTOPUNZANTE"), 2),
        "pct_arma_fuego": num(pct_de(armas, "ARMA DE FUEGO"), 2),
    }


def datos_conocimientos(df):
    # cifras que se usan en los conocimientos (siempre con todo el periodo)
    genero = victimas_por(df, "GENERO")
    edad = victimas_por(df, "GRUPO ETARIO")
    armas = victimas_por(df, "ARMAS MEDIOS")

    mujeres_2025 = pct_de(victimas_por(filtrar(df, anio="2025"), "GENERO"), "FEMENINO")
    mujeres_2026 = pct_de(victimas_por(filtrar(df, anio="2026"), "GENERO"), "FEMENINO")

    por_depto = df.pivot_table(index="DEPARTAMENTO", columns="GENERO", values="CANTIDAD", aggfunc="sum", fill_value=0)
    pct_depto = por_depto["FEMENINO"] / por_depto.sum(axis=1) * 100

    mujeres_adultas = df[(df["GENERO"] == "FEMENINO") & (df["GRUPO ETARIO"] == "ADULTOS")]["CANTIDAD"].sum()

    return {
        "mujeres_2025": num(mujeres_2025, 1),
        "mujeres_2026": num(mujeres_2026, 1),
        "depto_min": pct_depto.idxmin().capitalize(),
        "pct_depto_min": num(pct_depto.min(), 1),
        "depto_max": pct_depto.idxmax().capitalize(),
        "pct_depto_max": num(pct_depto.max(), 1),
        # si se contaran filas en vez de sumar CANTIDAD
        "mujeres_contando_filas": num((df["GENERO"] == "FEMENINO").mean() * 100, 1),
        "adultos": num(victimas_de(edad, "ADULTOS")),
        "menores": num(victimas_de(edad, "MENORES")),
        "pct_menores": num(pct_de(edad, "MENORES"), 1),
        "adolescentes": num(victimas_de(edad, "ADOLESCENTES")),
        "pct_adolescentes": num(pct_de(edad, "ADOLESCENTES"), 1),
        "menores_por_adolescente": num(victimas_de(edad, "MENORES") / victimas_de(edad, "ADOLESCENTES"), 1),
        "sin_armas": num(victimas_de(armas, "SIN EMPLEO DE ARMAS")),
        "contundentes": num(victimas_de(armas, "CONTUNDENTES")),
        "arma_blanca": num(victimas_de(armas, "ARMA BLANCA / CORTOPUNZANTE")),
        "arma_fuego": num(victimas_de(armas, "ARMA DE FUEGO")),
        "uno_de_cada_contundente": round(100 / pct_de(armas, "CONTUNDENTES")),
        "pct_mujeres_adultas": num(mujeres_adultas / df["CANTIDAD"].sum() * 100, 1),
    }


def para_grafica(tabla, decimales=1):
    # listas que usa Chart.js en la plantilla
    etiquetas = []
    for _, fila in tabla.iterrows():
        nombre = fila["categoria"].capitalize() if fila["categoria"] != "No reporta" else "No reporta"
        etiquetas.append(f"{nombre} ({num(fila['porcentaje'], decimales)} %)")
    return {
        "etiquetas": etiquetas,
        "victimas": [int(v) for v in tabla["victimas"]],
        "porcentajes": [round(p, 2) for p in tabla["porcentaje"]],
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
        "hay_datos": len(datos) > 0,
    }
    if info["hay_datos"]:
        info["r"] = resumen(datos)
        info["tabla"] = participacion(datos)
        info["graficas"] = {
            "genero": para_grafica(victimas_por(datos, "GENERO")),
            "edad": para_grafica(victimas_por(datos, "GRUPO ETARIO")),
            "armas": para_grafica(victimas_por(datos, "ARMAS MEDIOS"), 2),
        }
    return info


if __name__ == "__main__":
    df = cargar_datos()
    print("Registros:", len(df), "| Victimas:", int(df["CANTIDAD"].sum()))
    for col in VARIABLES:
        print("\n" + col)
        print(victimas_por(df, col).round(2).to_string(index=False))
    print("\nResumen:", resumen(df))
    print("\nConocimientos:", datos_conocimientos(df))