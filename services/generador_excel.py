"""
services/generador_excel.py
Servicio para armar en memoria un archivo Excel con los resultados
calculados (contadores, tabla de estudiantes e inconsistencias).
No escribe nada en el disco: usa BytesIO y lo devuelve al controlador.
"""

import io
from typing import Any, Dict

import pandas as pd

# Columnas de la hoja principal, en el orden en que se muestran en pantalla
COLUMNAS_RESULTADOS = [
    "Identificación",
    "Nombre completo",
    "Correo",
    "Programa",
    "Cohorte",
    "Módulos",
    "Promedio",
    "Asistencia %",
    "Certificado",
    "Emite certificado",
    "Motivo inconsistencia",
]


def generar_excel_resultados(datos: Dict[str, Any]) -> io.BytesIO:
    """
    Recibe el diccionario que devuelve procesar_certificados() y arma un
    Excel con tres hojas: Resultados, Contadores e Inconsistencias.
    Devuelve un BytesIO listo para enviar con send_file.
    """
    filas = []
    # LADRILLO: bucle (convertimos cada estudiante calculado en una fila del Excel)
    for est in datos["estudiantes_tablero"]:
        filas.append({
            "Identificación": est.get("identificacion", ""),
            "Nombre completo": est.get("nombre_completo", ""),
            "Correo": est.get("correo", ""),
            "Programa": est.get("programa", ""),
            "Cohorte": est.get("cohorte", ""),
            "Módulos": est.get("modulos", 0),
            "Promedio": est.get("promedio_nota"),
            "Asistencia %": est.get("promedio_asistencia"),
            "Certificado": est.get("tipo_certificado", ""),
            "Emite certificado": "Sí" if est.get("emite_certificado") else "No",
            "Motivo inconsistencia": est.get("motivo_inconsistencia") or "",
        })

    df_resultados = pd.DataFrame(filas, columns=COLUMNAS_RESULTADOS)

    contadores = datos["contadores"]
    df_contadores = pd.DataFrame(
        [
            {"Categoría": "Aprobación", "Cantidad": contadores["aprobacion"]},
            {"Categoría": "Participación", "Cantidad": contadores["participacion"]},
            {"Categoría": "Sin certificado", "Cantidad": contadores["sin_certificado"]},
            {"Categoría": "Inconsistencias", "Cantidad": contadores["inconsistencias"]},
        ]
    )

    filas_inc = []
    # LADRILLO: bucle (una fila por cada inconsistencia detectada)
    for inc in datos["inconsistencias"]:
        filas_inc.append({
            "Identificación": inc.get("identificacion", ""),
            "Nombre": inc.get("nombre_completo", ""),
            "Programa": inc.get("programa", ""),
            "Motivo": inc.get("motivo", ""),
            "Tipo de error": inc.get("tipo_error", ""),
        })
    df_inconsistencias = pd.DataFrame(
        filas_inc,
        columns=["Identificación", "Nombre", "Programa", "Motivo", "Tipo de error"],
    )

    # LADRILLO: BytesIO = caja en memoria; el Excel se arma ahí, no en disco
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_resultados.to_excel(writer, sheet_name="Resultados", index=False)
        df_contadores.to_excel(writer, sheet_name="Contadores", index=False)
        df_inconsistencias.to_excel(writer, sheet_name="Inconsistencias", index=False)

    buffer.seek(0)
    return buffer
