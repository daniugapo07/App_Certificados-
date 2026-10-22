"""
controllers/tablero.py
Controlador para la ruta principal / (tablero de control).
No contiene lógica de negocio: delega en models.certificados.
"""

from flask import Blueprint, render_template
from models.certificados import procesar_certificados

tablero_bp = Blueprint("tablero", __name__)


@tablero_bp.route("/")
def index():
    """
    Ruta principal: obtiene los datos calculados por el modelo
    y delega la visualización a la plantilla de Jinja en views/.
    """
    datos = procesar_certificados()
    # LADRILLO: variable (cuantos certificados se pueden emitir, para mostrarlo en el boton)
    elegibles = sum(1 for e in datos["estudiantes_tablero"] if e.get("emite_certificado"))
    return render_template(
        "tablero.html",
        contadores=datos["contadores"],
        inconsistencias=datos["inconsistencias"],
        estudiantes=datos["estudiantes_tablero"],
        elegibles=elegibles,
    )


@tablero_bp.route("/cargar", methods=["GET", "POST"])
def cargar():
    """
    Ruta para la carga de los archivos Excel Maestro y Evaluaciones.
    GET: Muestra formulario de carga si existe cargar.html, o redirige a /.
    POST: Carga y persiste los archivos enviados o recarga desde insumos/.
    """
    from flask import request, redirect, url_for, flash
    from services.carga_excel import cargar_archivos_y_persistir

    if request.method == "POST":
        archivo_maestro = request.files.get("maestro")
        archivo_evaluaciones = request.files.get("evaluaciones")

        fuente_m = (
            archivo_maestro
            if (archivo_maestro and archivo_maestro.filename)
            else "INSUMOS/Maestro_Estudiantes.xlsx"
        )
        fuente_e = (
            archivo_evaluaciones
            if (archivo_evaluaciones and archivo_evaluaciones.filename)
            else "INSUMOS/Registro_Evaluaciones.xlsx"
        )

        try:
            res = cargar_archivos_y_persistir(fuente_m, fuente_e)
            flash(
                f"Carga exitosa: {res['estudiantes_cargados']} estudiantes y {res['evaluaciones_cargadas']} evaluaciones.",
                "success",
            )
        except Exception as err:
            flash(f"Error al procesar los archivos: {err}", "danger")

        return redirect(url_for("tablero.index"))

    try:
        return render_template("cargar.html")
    except Exception:
        return redirect(url_for("tablero.index"))
