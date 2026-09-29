"""Dimensión relacional y multivariada.

Calcula la evidencia de las preguntas y los conocimientos evidentes de la
dimensión. Ejecutar desde la raíz del repositorio:

    python dimensiones/multivariada.py
"""

from pathlib import Path

import pandas as pd

# Ruta absoluta para que funcione sin importar desde qué carpeta se ejecute Flask.
RUTA = Path(__file__).resolve().parent.parent / "data" / "violencia_intrafamiliar.csv"
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


# --- Tablero: filtros, datos de las gráficas e interpretaciones ---

GRUPOS_TABLERO = ["ADULTOS", "ADOLESCENTES", "MENORES"]
ARMAS_TABLERO = ARMAS + [SIN_ARMAS]
MINIMO_CELDA = 30  # por debajo de este número de víctimas el porcentaje no es confiable
ANIOS = [2025, 2026]


def _pct(valor):
    return f"{valor:.1f}".replace(".", ",") + " %"


def _variacion(valor):
    """17.0 -> '+17,0 %'."""
    return ("+" if valor > 0 else "") + _pct(valor)


def _entero(valor):
    return f"{int(valor):,}".replace(",", ".")


def _mayuscula(texto):
    return texto[:1].upper() + texto[1:]


def _nombre(texto):
    """QUINDÍO -> Quindío; NORTE DE SANTANDER -> Norte de Santander."""
    if texto == "BOGOTA":  # el conjunto de datos lo escribe sin tilde
        return "Bogotá"
    return " ".join(
        palabra.lower() if palabra in ("DE", "DEL", "LA", "Y") else palabra.capitalize()
        for palabra in texto.split()
    )


def _lista(elementos):
    """['a', 'b', 'c'] -> 'a, b y c'."""
    return elementos[0] if len(elementos) == 1 else ", ".join(elementos[:-1]) + " y " + elementos[-1]


def _etiqueta(genero, grupo, arma):
    return f"{genero.capitalize()} · {grupo.lower()} · {arma.lower()}"


def leer_filtros(df, parametros):
    """Valida los filtros recibidos en la URL (?departamento=...&anio=...)."""
    departamento = parametros.get("departamento") or None
    if departamento not in set(df["DEPARTAMENTO"]):
        departamento = None
    anio = parametros.get("anio") or None
    anio = int(anio) if anio in {str(a) for a in ANIOS} else None
    return departamento, anio


def filtrar(df, departamento=None, anio=None):
    if departamento:
        df = df[df["DEPARTAMENTO"] == departamento]
    if anio:
        df = df[df["AÑO"] == anio]
    return df


def datos_combinaciones(df, cantidad=10):
    """Visualización 1: combinaciones de género, grupo etario y arma/medio con más víctimas."""
    tabla = combinaciones(df).head(cantidad)
    return [
        {
            "etiqueta": _etiqueta(fila["GENERO"], fila["GRUPO ETARIO"], fila["ARMAS MEDIOS"]),
            "victimas": int(fila["CANTIDAD"]),
            "porcentaje": round(float(fila["PORCENTAJE"]), 1),
            "acumulado": round(float(fila["PORCENTAJE_ACUMULADO"]), 1),
        }
        for _, fila in tabla.iterrows()
    ]


def datos_mujeres(df):
    """Visualización 2: % de mujeres en cada cruce de grupo etario y arma/medio."""
    tabla = mujeres_por_grupo_y_arma(df).set_index(["GRUPO ETARIO", "ARMAS MEDIOS"])
    celdas = []
    for grupo in GRUPOS_TABLERO:
        fila = []
        for arma in ARMAS_TABLERO:
            victimas = int(tabla["VICTIMAS"].get((grupo, arma), 0))
            fila.append({
                "victimas": victimas,
                "porcentaje": round(float(tabla["PCT_MUJERES"].get((grupo, arma), 0)), 1),
                "confiable": victimas >= MINIMO_CELDA,
            })
        celdas.append(fila)
    return {"grupos": GRUPOS_TABLERO, "armas": ARMAS_TABLERO, "celdas": celdas}


def datos_departamentos(df):
    """Visualización 3: % de víctimas por arma/medio en cada departamento, ordenado por % con arma."""
    tabla = armas_por_departamento(df).sort_values("% CON ARMA", ascending=False)
    return {
        "departamentos": list(tabla.index),
        "armas": ARMAS_TABLERO,
        "porcentajes": {
            arma: [round(float(v), 1) for v in tabla.get(arma, pd.Series(0, index=tabla.index))]
            for arma in ARMAS_TABLERO
        },
        "con_arma": [round(float(v), 1) for v in tabla["% CON ARMA"]],
        "victimas": [int(v) for v in tabla["VICTIMAS"]],
    }


def _alcance(departamento, anio):
    lugar = f"en {_nombre(departamento)}" if departamento else "en el país"
    periodo = f"durante {anio}" + (" (enero a julio)" if anio == 2026 else "") if anio else "entre 2025 y 2026"
    return f"{lugar} {periodo}"


def interpretar_combinaciones(combinaciones_top, departamento, anio):
    if len(combinaciones_top) < 3:
        return "No hay suficientes combinaciones con el filtro seleccionado para compararlas."
    primera, segunda, tercera = combinaciones_top[:3]
    veces = f"{primera['victimas'] / segunda['victimas']:.1f}".replace(".", ",")
    return (
        f"{_mayuscula(_alcance(departamento, anio))}, la combinación «{primera['etiqueta']}» reúne el "
        f"{_pct(primera['porcentaje'])} de las víctimas, {veces} veces la segunda («{segunda['etiqueta']}», "
        f"{_pct(segunda['porcentaje'])}). Las tres primeras combinaciones suman el {_pct(tercera['acumulado'])}: "
        "la violencia intrafamiliar registrada se concentra en muy pocas combinaciones de género, edad y medio."
    )


def interpretar_mujeres(df, mujeres):
    partes = []
    for grupo, fila in zip(mujeres["grupos"], mujeres["celdas"]):
        confiables = [celda["porcentaje"] for celda in fila if celda["confiable"]]
        if not confiables:
            partes.append(f"en {grupo.lower()}, sin víctimas suficientes para comparar")
        elif len(confiables) == 1:
            partes.append(f"en {grupo.lower()}, el {_pct(confiables[0])}")
        else:
            partes.append(f"en {grupo.lower()}, entre el {_pct(min(confiables))} y el {_pct(max(confiables))}")
    texto = "Porcentaje de mujeres víctimas según el arma o medio: " + "; ".join(partes) + "."

    victimas_grupo = df.groupby("GRUPO ETARIO")["CANTIDAD"].sum()
    if victimas_grupo.get("ADULTOS", 0) >= MINIMO_CELDA and victimas_grupo.get("MENORES", 0) >= MINIMO_CELDA:
        genero = genero_por_grupo_etario(df)
        adultos, menores = genero.loc["ADULTOS", "FEMENINO"], genero.loc["MENORES", "FEMENINO"]
        comparacion = "más pareja" if abs(menores - 50) < abs(adultos - 50) else "menos pareja"
        texto += (
            f" En total, las mujeres son el {_pct(adultos)} de las víctimas adultas y el {_pct(menores)} de las "
            f"menores: la afectación entre sexos es {comparacion} en niños y niñas que en adultos."
        )
    return texto + f" Las celdas grises tienen menos de {MINIMO_CELDA} víctimas y su porcentaje no es confiable."


def interpretar_departamentos(df, deptos, departamento, anio):
    nombres, con_arma = deptos["departamentos"], deptos["con_arma"]
    if not nombres:
        return "No hay datos para el año seleccionado."
    nacional = df.loc[df["CON_ARMA"], "CANTIDAD"].sum() / df["CANTIDAD"].sum() * 100
    primeros = _lista([f"{_nombre(n)} ({_pct(p)})" for n, p in zip(nombres[:3], con_arma[:3])])
    casi_sin_armas = [_nombre(n) for n, p in zip(nombres, con_arma) if p < 2]
    texto = (
        f"{_mayuscula(_alcance(None, anio))}, el {_pct(nacional)} de las víctimas fueron agredidas con arma o "
        f"medio, pero el porcentaje cambia mucho entre departamentos: encabezan {primeros}"
    )
    if casi_sin_armas:
        texto += f", mientras {_lista(casi_sin_armas)} registran menos del 2 %"
    texto += "."
    if departamento in nombres:
        puesto = nombres.index(departamento) + 1
        texto += (
            f" {_nombre(departamento)} registra {_pct(con_arma[puesto - 1])} con arma o medio y ocupa el puesto "
            f"{puesto} de {len(nombres)}."
        )
    return texto + (
        " Una diferencia tan amplia entre territorios sugiere que también influye la forma de diligenciar "
        "el campo ARMAS MEDIOS, no solo el hecho."
    )


# --- Cifras de los conocimientos, casos inusuales, limitación y decisión (siempre con todos los datos) ---

MINIMO_DEPARTAMENTO = 1000  # para priorizar departamentos se ignoran los que tienen muy pocas víctimas
PRIORIZADOS = 5


def cifras_conocimientos(df):
    """Cifras ya formateadas que usa el texto de la página; se calculan sobre todo el periodo."""
    total = df["CANTIDAD"].sum()
    genero = genero_por_grupo_etario(df)
    armas_grupo = armas_por_grupo_etario(df)
    tabla_combinaciones = combinaciones(df)
    armas_pais = armas_nacional(df)
    deptos = armas_por_departamento(df)
    registro = registro_por_departamento(df)
    menores = menores_bogota_vs_resto(df)
    grandes = registros_grandes(df)
    meses = victimas_por_mes(df)
    dias = victimas_por_dia(df, "2025-12")
    interanual = comparacion_interanual(df)

    def combinacion(genero_, grupo, arma):
        fila = tabla_combinaciones[
            (tabla_combinaciones["GENERO"] == genero_)
            & (tabla_combinaciones["GRUPO ETARIO"] == grupo)
            & (tabla_combinaciones["ARMAS MEDIOS"] == arma)
        ]
        return float(fila["PORCENTAJE"].sum())

    # Conocimiento 1
    mujeres_adultas = genero.loc["ADULTOS", "FEMENINO"]
    hombres_adultos = genero.loc["ADULTOS", "MASCULINO"]
    mujeres_menores = genero.loc["MENORES", "FEMENINO"]
    hombres_menores = genero.loc["MENORES", "MASCULINO"]

    # Conocimiento 2
    grandes_deptos = deptos[deptos["VICTIMAS"] >= MINIMO_DEPARTAMENTO]
    priorizados = grandes_deptos.sort_values("CONTUNDENTES", ascending=False).head(PRIORIZADOS)
    casi_sin_contundentes = deptos[deptos["CONTUNDENTES"] < 2].sort_values("CONTUNDENTES", ascending=False)
    mayor = deptos["CONTUNDENTES"].idxmax()

    # Conocimiento 3
    bogota = registro.loc["BOGOTA"]
    resto = registro.drop(index="BOGOTA")[["REGISTROS", "VICTIMAS"]].sum()

    # Casos inusuales
    diciembre = pd.Period("2025-12", freq="M")
    otros_meses = meses.drop(index=diciembre)
    por_mes_depto = df.pivot_table(index="DEPARTAMENTO", columns="MES", values="CANTIDAD", aggfunc="sum", fill_value=0)
    bajan_en_diciembre = int((por_mes_depto[diciembre] < por_mes_depto[pd.Period("2025-11", freq="M")]).sum())
    grupos_principales = interanual.drop(index="No reporta", level="GENERO").drop(index="No reporta", level="GRUPO ETARIO")
    todos_suben = bool((grupos_principales["VARIACION_%"] > 0).all())

    return {
        # Conocimiento 1
        "mujeres_adultos": _pct(mujeres_adultas),
        "mujeres_adolescentes": _pct(genero.loc["ADOLESCENTES", "FEMENINO"]),
        "mujeres_menores": _pct(mujeres_menores),
        "hombres_menores": _pct(hombres_menores),
        "combinacion_principal": _pct(tabla_combinaciones["PORCENTAJE"].iloc[0]),
        "tres_combinaciones": _pct(tabla_combinaciones["PORCENTAJE_ACUMULADO"].iloc[2]),
        "razon_adultos": f"{mujeres_adultas / hombres_adultos:.1f}".replace(".", ","),
        "razon_menores": f"{mujeres_menores / hombres_menores:.1f}".replace(".", ","),
        "contundentes_menores": _pct(armas_grupo.loc["MENORES", "CONTUNDENTES"]),
        "contundentes_adultos": _pct(armas_grupo.loc["ADULTOS", "CONTUNDENTES"]),
        # Conocimiento 2
        "priorizados": _lista([_nombre(d) for d in priorizados.index]),
        "priorizados_con_valor": _lista([f"{_nombre(d)} {_pct(v)}" for d, v in priorizados["CONTUNDENTES"].items()]),
        "casi_sin_contundentes": _lista(
            [f"{_nombre(d)} {_pct(v)}" for d, v in casi_sin_contundentes["CONTUNDENTES"].items()]
        ),
        "contundentes_pais": _pct(armas_pais["CONTUNDENTES"]),
        "sin_armas_pais": _pct(armas_pais[SIN_ARMAS]),
        "contundentes_min": _pct(deptos["CONTUNDENTES"].min()),
        "contundentes_max": _pct(deptos["CONTUNDENTES"].max()),
        "departamento_mayor": _nombre(mayor),
        "contundentes_mayor": _pct(deptos.loc[mayor, "CONTUNDENTES"]),
        "contundentes_quindio": _pct(deptos.loc["QUINDÍO", "CONTUNDENTES"]),
        "contundentes_risaralda": _pct(deptos.loc["RISARALDA", "CONTUNDENTES"]),
        "mujeres_depto_min": _pct(deptos["% MUJERES"].min()),
        "mujeres_depto_max": _pct(deptos["% MUJERES"].max()),
        "minimo_departamento": _entero(MINIMO_DEPARTAMENTO),
        # Conocimiento 3
        "bogota_registros": _entero(bogota["REGISTROS"]),
        "bogota_pct_registros": _pct(bogota["PCT_REGISTROS_PAIS"]),
        "bogota_victimas": _entero(bogota["VICTIMAS"]),
        "bogota_pct_victimas": _pct(bogota["PCT_VICTIMAS_PAIS"]),
        "bogota_por_registro": f"{bogota['VICTIMAS_POR_REGISTRO']:.1f}".replace(".", ","),
        "resto_por_registro": f"{resto['VICTIMAS'] / resto['REGISTROS']:.1f}".replace(".", ","),
        "subestimacion_bogota": f"{bogota['PCT_VICTIMAS_PAIS'] / bogota['PCT_REGISTROS_PAIS']:.0f}",
        "registros_grandes": _entero(grandes["total"]),
        "registros_grandes_bogota": _entero(grandes["por_departamento"].get("BOGOTA", 0)),
        "maximo_registro": _entero(grandes["maximo"]),
        "menores_bogota": _pct(menores["pct_menores_bogota"]),
        "menores_resto": _pct(menores["pct_menores_resto"]),
        "menores_pais_en_bogota": _pct(menores["pct_menores_pais_en_bogota"]),
        # Casos inusuales
        "diciembre": _entero(meses[diciembre]),
        "otros_meses_min": _entero(otros_meses.min()),
        "otros_meses_max": _entero(otros_meses.max()),
        "diciembre_dia_1": _entero(dias.iloc[0]),
        "diciembre_ultimo_dia": _entero(dias.iloc[-1]),
        "diciembre_departamentos_bajan": bajan_en_diciembre,
        "departamentos": df["DEPARTAMENTO"].nunique(),
        "interanual_alcance": "todos los grupos" if todos_suben else "la mayoría de los grupos",
        "interanual_mujeres_adultas": _variacion(interanual.loc[("ADULTOS", "FEMENINO"), "VARIACION_%"]),
        "interanual_menores_masculinos": _variacion(interanual.loc[("MENORES", "MASCULINO"), "VARIACION_%"]),
        # Decisión
        "mujeres_adultas_sin_armas_y_contundentes": _pct(
            combinacion("FEMENINO", "ADULTOS", SIN_ARMAS) + combinacion("FEMENINO", "ADULTOS", "CONTUNDENTES")
        ),
        "victimas": _entero(total),
    }


def contexto(df, parametros):
    """Todo lo que necesita la plantilla multivariada.html, según los filtros de la URL."""
    departamento, anio = leer_filtros(df, parametros)
    datos = filtrar(df, departamento, anio)
    datos_anio = filtrar(df, anio=anio)  # la visualización 3 compara todos los departamentos
    combinaciones_top = datos_combinaciones(datos)
    mujeres = datos_mujeres(datos)
    deptos = datos_departamentos(datos_anio)
    return {
        "resumen": resumen_general(df),
        "cifras": cifras_conocimientos(df),
        "indicadores": indicadores(datos) if len(datos) else None,
        "filtros": {
            "departamento": departamento,
            "anio": anio,
            "departamentos": sorted(df["DEPARTAMENTO"].unique()),
            "anios": ANIOS,
        },
        "graficas": {"combinaciones": combinaciones_top, "mujeres": mujeres, "departamentos": deptos},
        "interpretaciones": {
            "combinaciones": interpretar_combinaciones(combinaciones_top, departamento, anio),
            "mujeres": interpretar_mujeres(datos, mujeres),
            "departamentos": interpretar_departamentos(datos_anio, deptos, departamento, anio),
        },
    }


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
