from flask import Flask, render_template, request

from dimensiones.temporal import cargar_datos, contexto


app = Flask(__name__)
datos_temporales = cargar_datos()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/poblacional")
def poblacional():
    return render_template("poblacional.html")


@app.route("/territorial")
def territorial():
    return render_template("territorial.html")


@app.route("/temporal")
def temporal():
    datos = contexto(datos_temporales, request.args)
    return render_template("temporal.html", **datos)


@app.route("/multivariada")
def multivariada():
    return render_template("multivariada.html")


if __name__ == "__main__":
    app.run(debug=True)
