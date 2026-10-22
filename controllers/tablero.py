"""
controllers/tablero.py
Controlador del tablero principal y del panel de administración.
No contiene lógica de negocio: lee los archivos en memoria, delega el
cálculo en models/services y muestra o descarga los resultados.
"""

from io import BytesIO

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.exceptions import RequestEntityTooLarge

from controllers.sesion import requiere_login, solo_admin
from models.certificados import procesar_certificados
from services.carga_excel import procesar_excel
from services.generador_excel import generar_excel_resultados

tablero_bp = Blueprint("tablero", __name__)

# Límite que se valida archivo por archivo. Vercel corta el envío completo en 4.5 MB.
TAMANO_MAXIMO_ARCHIVO = 4 * 1024 * 1024
TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ErrorArchivo(Exception):
    """Error controlado de validación de un archivo subido (mensaje entendible)."""


def _render_tablero(
    datos,
    origen,
    error_carga=None,
    aviso_datos_subidos=False,
):
    """Prepara los datos y renderiza la plantilla del tablero."""
    # LADRILLO: variable (cuantos certificados se pueden emitir, para el boton)
    elegibles = sum(1 for e in datos["estudiantes_tablero"] if e.get("emite_certificado"))
    # LADRILLO: condicional (las inconsistencias solo se envían a la vista si es admin)
    es_admin = session.get("rol") == "admin"
    return render_template(
        "tablero.html",
        contadores=datos["contadores"],
        inconsistencias=datos["inconsistencias"] if es_admin else [],
        estudiantes=datos["estudiantes_tablero"],
        elegibles=elegibles,
        origen=origen,
        error_carga=error_carga,
        aviso_datos_subidos=aviso_datos_subidos,
    )


def _leer_archivo(archivo, etiqueta):
    """
    Lee un archivo subido EN MEMORIA y lo devuelve como BytesIO.
    Lanza ValueError con un mensaje entendible si falta, no es .xlsx
    o pesa más de 4 MB.
    """
    # LADRILLO: condicional (el campo debe traer un archivo con nombre)
    if archivo is None or not archivo.filename:
        raise ErrorArchivo(f"Falta el archivo de {etiqueta}. Selecciona los dos Excel.")

    if not archivo.filename.lower().endswith(".xlsx"):
        raise ErrorArchivo(
            f"El archivo «{archivo.filename}» no es un Excel .xlsx válido."
        )

    contenido = archivo.read()
    if len(contenido) > TAMANO_MAXIMO_ARCHIVO:
        raise ErrorArchivo(
            f"El archivo «{archivo.filename}» pesa más de 4 MB. "
            "Sube una versión más liviana."
        )

    # LADRILLO: BytesIO.
    # Analogía: es como una caja de plástico dentro de la memoria del programa.
    # Guardamos ahí los bytes del Excel y pandas los lee como si fueran un
    # archivo del disco, pero nunca se crea nada en el disco (en Vercel es
    # de solo lectura).
    return BytesIO(contenido)


@tablero_bp.route("/")
@requiere_login
def index():
    """
    Ruta principal: muestra el tablero con los datos de fábrica (base de datos).
    El panel de carga solo aparece en la plantilla si el rol es admin.
    """
    return _render_tablero(procesar_certificados(), "Datos de fábrica")


@tablero_bp.route("/cargar", methods=["GET", "POST"])
@requiere_login
@solo_admin
def cargar():
    """
    Panel de administración.
    GET: vuelve al tablero, donde está el panel.
    POST: lee los dos Excel en memoria, recalcula y muestra la tabla
    o devuelve un Excel con los resultados, según el campo 'accion'.
    """
    if request.method == "GET":
        return redirect(url_for("tablero.index"))

    # LADRILLO: protección por si el envío completo supera el límite de Vercel
    try:
        accion = request.form.get("accion", "ver")
        archivo_maestro = request.files.get("maestro")
        archivo_evaluaciones = request.files.get("evaluaciones")
    except RequestEntityTooLarge:
        return _render_tablero(
            procesar_certificados(),
            "Datos de fábrica",
            error_carga=(
                "El envío supera el límite de 4.5 MB permitido por Vercel. "
                "Sube archivos más pequeños."
            ),
        )

    try:
        buffer_maestro = _leer_archivo(archivo_maestro, "Maestro de estudiantes")
        buffer_evaluaciones = _leer_archivo(
            archivo_evaluaciones, "Registro de evaluaciones"
        )

        # Reutiliza el mismo cálculo del tablero, pero con los datos subidos.
        # procesar_excel NO guarda en la base de datos.
        datos = procesar_excel(buffer_maestro, buffer_evaluaciones)

        # LADRILLO: condicional (el segundo botón pide el Excel en vez de la pantalla)
        if accion == "excel":
            buffer_excel = generar_excel_resultados(datos)
            return send_file(
                buffer_excel,
                mimetype=TIPO_EXCEL,
                as_attachment=True,
                download_name="Resultados_subidos.xlsx",
            )

        origen = (
            f"Archivos subidos: {archivo_maestro.filename} "
            f"y {archivo_evaluaciones.filename}"
        )
        return _render_tablero(datos, origen, aviso_datos_subidos=True)

    except RequestEntityTooLarge:
        mensaje = (
            "El envío supera el límite de 4.5 MB permitido por Vercel. "
            "Sube archivos más pequeños."
        )
    except ErrorArchivo as err:
        # Errores controlados: archivo faltante, extensión incorrecta o tamaño.
        mensaje = str(err)
    except Exception:
        # Errores de pandas/openpyxl: el archivo no es un Excel legible.
        mensaje = (
            "No se pudieron leer los archivos. Revisa que sean Excel válidos "
            "y que tengan las hojas y columnas requeridas."
        )

    # Si algo falló, se muestra el tablero de fábrica con el aviso rojo.
    return _render_tablero(procesar_certificados(), "Datos de fábrica", error_carga=mensaje)


@tablero_bp.route("/resultados-fabrica")
@requiere_login
@solo_admin
def descargar_fabrica():
    """
    Descarga en Excel los resultados de los datos de fábrica.
    procesar_excel() sin archivos lee directamente INSUMOS/.
    """
    datos = procesar_excel()
    buffer_excel = generar_excel_resultados(datos)
    return send_file(
        buffer_excel,
        mimetype=TIPO_EXCEL,
        as_attachment=True,
        download_name="Resultados_fabrica.xlsx",
    )
