
# Análisis de la violencia intrafamiliar en Colombia

Aplicación web desarrollada con **Python, Flask y Bootstrap** que presenta el análisis exploratorio del conjunto de datos *Reporte Delito Violencia Intrafamiliar Policía Nacional*, publicado en el Portal Nacional de Datos Abiertos de Colombia.

## Integrantes

| # | Nombre                                  |                        Responsabilidad                       |              Rama               |
|---|-----------------------------------------|--------------------------------------------------------------|---------------------------------|
| 1 | Esteffy Geraldine Bachiller Carrillo    | Dimensión poblacional y administración del repositorio       | `feature/dimension-poblacional` |
| 2 | Juan Pablo Villarraga Espitia           | Dimensión territorial y configuración de Flask               | `feature/dimension-territorial` |
| 3 | Manuel Felipe Murcia Suárez             | Dimensión temporal y publicación de la aplicación            | `feature/dimension-temporal`    |
| 4 | Johan Orlando Martínez Suárez           | Dimensión relacional y multivariada, elaboración del informe | `feature/dimension-multivariada`|

## Conjunto de datos

- **Nombre:** Reporte Delito Violencia Intrafamiliar Policía Nacional
- **Entidad:** Dirección General de la Policía Nacional – DIPON (fuente DIJIN)
- **URL:** https://www.datos.gov.co/Seguridad-y-Defensa/Reporte-Delito-Violencia-Intrafamiliar-Polic-a-Nac/vuyt-mqpw
- **Población:** víctimas de violencia intrafamiliar registradas por la Policía Nacional en los municipios de Colombia
- **Periodo analizado:** 2025–2026
- **Archivo:** `data/violencia_intrafamiliar.csv`

| Variable     |        Tipo             | Descripción                         |
|--------------|-------------------------|-------------------------------------|
| DEPARTAMENTO | Territorial, categórica | Departamento donde ocurrió el hecho |
| MUNICIPIO    | Territorial, categórica | Municipio donde ocurrió el hecho    |
| CODIGO DANE  | Territorial             | Código DANE del municipio           |
| ARMAS MEDIOS | Categórica              | Arma o medio empleado               |
| FECHA HECHO  | Temporal                | Fecha en que ocurrió el hecho       |
| GENERO       | Categórica              | Género de la víctima                |
| GRUPO ETARIO | Categórica              | Grupo de edad de la víctima         |
| CANTIDAD     | Numérica                | Número de víctimas del registro     |

## Ejecución local

_(La completa el integrante 2.)_

## Aplicación publicada

_(La completa el integrante 3.)_

## Reglas de trabajo

Antes de empezar, lee CONTRIBUTING.md