from flask import Flask, render_template, request

from dimensiones import poblacional as pb
from dimensiones import territorial as tr
from dimensiones import temporal as tp
from dimensiones import multivariada as mv


app = Flask(__name__)

DATOS_PB = pb.cargar_datos()
DATOS_TR = tr.cargar_datos()
DATOS_TP = tp.cargar_datos()
DATOS_MV = mv.cargar_datos()  # al iniciar se lee el CSV


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/poblacional")
def poblacional():
    return render_template("poblacional.html", **pb.pagina(DATOS_PB, request.args))


@app.route("/territorial")
def territorial():
    return render_template("territorial.html", **tr.pagina(DATOS_TR, request.args))


@app.route("/temporal")
def temporal():
    return render_template("temporal.html", **tp.contexto(DATOS_TP, request.args))


@app.route("/multivariada")
def multivariada():
    # Los filtros llegan en la URL (?departamento=...&anio=...); todo se calcula en dimensiones/multivariada.py
    return render_template("multivariada.html", **mv.contexto(DATOS_MV, request.args))


if __name__ == "__main__":
    app.run(debug=True)
