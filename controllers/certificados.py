"""
controllers/certificados.py
Controlador para la visualización y descarga de certificados individuales en PDF
y descarga masiva en archivo ZIP.
No contiene lógica de cálculo: delega en models y services.
"""

import io
from flask import Blueprint, abort, make_response, send_file
from models.certificados import obtener_detalle_estudiante, procesar_certificados
from services.generador_pdf import generar_certificado_pdf, generar_zip_certificados

certificados_bp = Blueprint("certificados", __name__)


@certificados_bp.route("/certificado/<identificacion>/<path:programa>")
def ver_certificado(identificacion: str, programa: str):
    """
    Genera y sirve el certificado individual en PDF para un estudiante y programa.
    Si el estudiante tiene condición 'Sin certificado' o inconsistencias, deniega la emisión.
    """
    estudiante = obtener_detalle_estudiante(identificacion, programa)
    if not estudiante:
        abort(404, description=f"No se encontró el estudiante con identificación {identificacion}.")

    # Regla de negocio: No se genera certificado para 'Sin certificado' ni inconsistencias
    if not estudiante.get("emite_certificado"):
        mensaje = (
            f"El estudiante {estudiante.get('nombre_completo', identificacion)} "
            f"tiene condición '{estudiante.get('tipo_certificado')}' y no es elegible para emisión de certificado."
        )
        return make_response((f"<h3>Acceso denegado</h3><p>{mensaje}</p>", 403))

    pdf_bytes = generar_certificado_pdf(estudiante)
    nombre_archivo = f"Certificado_{estudiante['identificacion']}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=nombre_archivo,
    )


@certificados_bp.route("/descargar-todos")
def descargar_todos():
    """
    Genera un archivo ZIP con todos los certificados emitibles (22 archivos)
    y lo sirve como descarga.
    """
    datos = procesar_certificados()
    estudiantes = datos["estudiantes_tablero"]

    zip_buffer = generar_zip_certificados(estudiantes)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="Certificados_Academia.zip",
    )
