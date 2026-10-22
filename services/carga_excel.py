"""
services/carga_excel.py
Servicio para la lectura, validación y persistencia de archivos Excel.
Los archivos en insumos/ son de solo lectura.
"""

from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from models.certificados import procesar_certificados
from models.datos import guardar_estudiantes, guardar_evaluaciones

COLUMNAS_MAESTRO = [
    "Identificacion",
    "Nombre_Completo",
    "Correo",
    "Programa",
    "Cohorte",
]

COLUMNAS_EVALUACIONES = [
    "Identificacion",
    "Programa",
    "Modulo",
    "Nota",
    "Asistencia_Pct",
    "Fecha_Cierre",
]


def _limpiar_identificacion(val: Any) -> str:
    """Convierte cualquier valor a string limpio sin espacios ni decimales espurios."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2].strip()
    return s


def _limpiar_texto(val: Any) -> str:
    """Limpia cadenas de texto y maneja valores nulos."""
    if pd.isna(val):
        return ""
    return str(val).strip()


def leer_maestro_excel(ruta_archivo: Any = "INSUMOS/Maestro_Estudiantes.xlsx") -> List[Dict[str, Any]]:
    """
    Lee y valida la hoja 'Estudiantes' de Maestro_Estudiantes.xlsx.
    Retorna una lista de diccionarios listos para persistir.
    Soporta rutas en disco y objetos tipo archivo en memoria.
    """
    nombre_fuente = "archivo"
    if isinstance(ruta_archivo, (str, Path)):
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            raise FileNotFoundError(f"El archivo maestro no existe: {ruta}")
        nombre_fuente = ruta.name
        fuente = ruta
    else:
        fuente = ruta_archivo

    df = pd.read_excel(fuente, sheet_name="Estudiantes", dtype=str)
    # Limpiar nombres de columnas
    df.columns = [str(col).strip() for col in df.columns]

    # Validar columnas requeridas
    columnas_presentes = set(df.columns)
    columnas_esperadas = set(COLUMNAS_MAESTRO)
    if not columnas_esperadas.issubset(columnas_presentes):
        faltantes = columnas_esperadas - columnas_presentes
        raise ValueError(
            f"El archivo maestro ({nombre_fuente}) no contiene las columnas requeridas. Faltan: {faltantes}"
        )

    estudiantes = []
    for _, fila in df.iterrows():
        ident = _limpiar_identificacion(fila["Identificacion"])
        if not ident:
            continue  # Ignorar filas vacías
        estudiantes.append({
            "identificacion": ident,
            "nombre_completo": _limpiar_texto(fila["Nombre_Completo"]),
            "correo": _limpiar_texto(fila["Correo"]),
            "programa": _limpiar_texto(fila["Programa"]),
            "cohorte": _limpiar_texto(fila["Cohorte"]),
        })

    return estudiantes


def leer_evaluaciones_excel(ruta_archivo: Any = "INSUMOS/Registro_Evaluaciones.xlsx") -> List[Dict[str, Any]]:
    """
    Lee y valida la hoja 'Evaluaciones' de Registro_Evaluaciones.xlsx.
    Retorna una lista de diccionarios listos para persistir.
    Soporta rutas en disco y objetos tipo archivo en memoria.
    """
    nombre_fuente = "archivo"
    if isinstance(ruta_archivo, (str, Path)):
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            raise FileNotFoundError(f"El archivo de evaluaciones no existe: {ruta}")
        nombre_fuente = ruta.name
        fuente = ruta
    else:
        fuente = ruta_archivo

    df = pd.read_excel(fuente, sheet_name="Evaluaciones")
    # Limpiar nombres de columnas
    df.columns = [str(col).strip() for col in df.columns]

    # Validar columnas requeridas
    columnas_presentes = set(df.columns)
    columnas_esperadas = set(COLUMNAS_EVALUACIONES)
    if not columnas_esperadas.issubset(columnas_presentes):
        faltantes = columnas_esperadas - columnas_presentes
        raise ValueError(
            f"El archivo de evaluaciones ({nombre_fuente}) no contiene las columnas requeridas. Faltan: {faltantes}"
        )

    evaluaciones = []
    for _, fila in df.iterrows():
        ident = _limpiar_identificacion(fila["Identificacion"])
        if not ident:
            continue  # Ignorar filas vacías

        # Conversión segura de nota y asistencia
        nota_val = fila["Nota"]
        nota = float(nota_val) if pd.notna(nota_val) else None

        asistencia_val = fila["Asistencia_Pct"]
        asistencia = float(asistencia_val) if pd.notna(asistencia_val) else None

        # Formato de fecha
        fecha_val = fila["Fecha_Cierre"]
        if pd.isna(fecha_val):
            fecha_str = None
        elif hasattr(fecha_val, "strftime"):
            fecha_str = fecha_val.strftime("%Y-%m-%d")
        else:
            fecha_str = str(fecha_val).strip()

        evaluaciones.append({
            "identificacion": ident,
            "programa": _limpiar_texto(fila["Programa"]),
            "modulo": _limpiar_texto(fila["Modulo"]),
            "nota": nota,
            "asistencia_pct": asistencia,
            "fecha_cierre": fecha_str,
        })

    return evaluaciones


def cargar_archivos_y_persistir(
    ruta_maestro: str | Path = "INSUMOS/Maestro_Estudiantes.xlsx",
    ruta_evaluaciones: str | Path = "INSUMOS/Registro_Evaluaciones.xlsx",
) -> Dict[str, int]:
    """
    Lee los dos archivos Excel, valida la estructura y persiste los datos
    delegando exclusivamente en el modelo models.datos.
    """
    estudiantes = leer_maestro_excel(ruta_maestro)
    evaluaciones = leer_evaluaciones_excel(ruta_evaluaciones)

    cant_est = guardar_estudiantes(estudiantes)
    cant_eva = guardar_evaluaciones(evaluaciones)

    return {
        "estudiantes_cargados": cant_est,
        "evaluaciones_cargadas": cant_eva,
    }


def leer_datos_excel(
    archivo_maestro: Any = None,
    archivo_evaluaciones: Any = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Lee los dos Excel y devuelve (estudiantes, evaluaciones).
    Si no se pasa un archivo, lee el de la carpeta INSUMOS/ (datos de fábrica).
    Acepta rutas en disco o archivos en memoria (BytesIO).
    """
    # LADRILLO: condicional (sin archivo subido, usamos el Excel de fábrica)
    estudiantes = leer_maestro_excel(
        archivo_maestro if archivo_maestro is not None else "INSUMOS/Maestro_Estudiantes.xlsx"
    )
    evaluaciones = leer_evaluaciones_excel(
        archivo_evaluaciones
        if archivo_evaluaciones is not None
        else "INSUMOS/Registro_Evaluaciones.xlsx"
    )
    return estudiantes, evaluaciones


def procesar_excel(
    archivo_maestro: Any = None,
    archivo_evaluaciones: Any = None,
) -> Dict[str, Any]:
    """
    Lee los Excel (subidos o de INSUMOS) y aplica las reglas del negocio,
    SIN guardar nada en la base de datos. Devuelve el mismo diccionario
    que procesar_certificados(), reutilizando esa función.
    """
    estudiantes, evaluaciones = leer_datos_excel(archivo_maestro, archivo_evaluaciones)
    return procesar_certificados(estudiantes=estudiantes, evaluaciones=evaluaciones)
