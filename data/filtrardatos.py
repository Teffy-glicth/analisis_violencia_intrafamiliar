import pandas as pd

ENTRADA = "data/violencia_intrafamiliar_completo.csv"
SALIDA = "data/violencia_intrafamiliar.csv"
ANIOS = [2025, 2026]

df = pd.read_csv(ENTRADA, dtype=str)
print("Registros del archivo completo:", len(df))

fechas = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce")
print("Fechas que no se pudieron leer:", fechas.isna().sum())

filtrado = df[fechas.dt.year.isin(ANIOS)]
filtrado.to_csv(SALIDA, index=False, encoding="utf-8")

print("Registros filtrados", ANIOS, ":", len(filtrado))
print(filtrado["FECHA HECHO"].head())