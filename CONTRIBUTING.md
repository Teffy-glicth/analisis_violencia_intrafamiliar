# Reglas de trabajo del equipo

## 1. Ramas

Nadie trabaja directamente en `main`. Cada integrante usa solo su rama:

| Integrante |             Rama                |
|------------|---------------------------------|
|      1     | `feature/dimension-poblacional` |
|      2     | `feature/dimension-territorial` |
|      3     | `feature/dimension-temporal`    |
|      4     | `feature/dimension-multivariada`|

## 2. Flujo obligatorio

```bash
git checkout main
git pull origin main
git checkout -b feature/dimension-XXX    
git add .
git commit -m "Agrega gráfica de ..."
git push -u origin feature/dimension-XXX
```

Luego, en GitHub, abrir un **pull request** hacia `main` y pedir revisión a la integrante 1. Las correcciones se hacen en la misma rama y se vuelve a hacer `git push`.

Cuando se fusione un PR, cada una actualiza su rama:

```bash
git checkout feature/dimension-XXX
git pull origin main
```

## 3. Commits

- **Mínimo 3 commits** por integrante sobre su dimensión.
- Mensajes descriptivos: `Agrega gráfica de víctimas por grupo etario` (no `cambios` ni `final`, ni ningún nombre de commit sin sentido).
- Git debe estar configurado con el **mismo correo de la cuenta de GitHub**.

## 4. Archivos

- Cada integrante edita solo `dimensiones/<su_dimension>.py` y `templates/<su_dimension>.html`.
- `app.py`, `templates/base.html` y `requirements.txt` solo los modifica su responsable.
- Nadie modifica ni reemplaza `data/violencia_intrafamiliar.csv`.

## 5. Reglas de datos (iguales para todas)

```python - como se abre el csv al empezar la dimensión
df = pd.read_csv("data/violencia_intrafamiliar.csv", dtype={"CODIGO DANE": str}) # Abre el archivo y deja el codigo dane como texto
df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0) # convierte CANTIDAD a número
df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"], dayfirst=True, errors="coerce") # convierte DECHA HECHO  a la fecha real
```

- **Número de víctimas = SUMA de `CANTIDAD`**, nunca conteo de filas.
- Los vacíos se muestran como **"No reporta"**; no se eliminan.
- Periodo analizado: **2025–2026**.

## 6. Contenido mínimo de cada tablero

Título, pregunta, descripción de variables, 3 indicadores, 3 visualizaciones, 2 filtros, interpretación de cada gráfica, 3 conocimientos evidentes, 1 limitación y 1 decisión.