"""
models/certificados.py
Módulo que define y aplica las reglas del negocio para la emisión de certificados.
Constantes fijas:
- NOTA_MINIMA = 70
- ASISTENCIA_MINIMA = 80
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional
from models.datos import obtener_estudiantes, obtener_evaluaciones

# Constantes fijas de negocio
NOTA_MINIMA = 70.0
ASISTENCIA_MINIMA = 80.0
ASISTENCIA_CRITICA = 50.0

TIPO_APROBACION = "Aprobación"
TIPO_PARTICIPACION = "Participación"
TIPO_SIN_CERTIFICADO = "Sin certificado"
TIPO_INCONSISTENCIA = "Inconsistencia"


def determinar_tipo_certificado(promedio_nota: float, promedio_asistencia: float) -> str:
    """
    Determina la categoría de certificado según las reglas:
    - R3: Aprobación: promedio >= 70 y asistencia >= 80 (límites incluidos)
    - R4: Participación: promedio < 70 y asistencia >= 80
    - R5: Sin certificado: asistencia < 80
    """
    if promedio_asistencia >= ASISTENCIA_MINIMA:
        if promedio_nota >= NOTA_MINIMA:
            return TIPO_APROBACION
        else:
            return TIPO_PARTICIPACION
    else:
        return TIPO_SIN_CERTIFICADO


def procesar_certificados() -> Dict[str, Any]:
    """
    Aplica las reglas del negocio R1 a R6 sobre los datos de la base de datos:
    - R1: Agrupa evaluaciones por identificacion + programa.
    - R2: Calcula promedios redondeados a 2 decimales.
    - R3: Aprobación (promedio >= 70 y asistencia >= 80).
    - R4: Participación (promedio < 70 y asistencia >= 80).
    - R5: Sin certificado (asistencia < 80).
    - R6: Detección de inconsistencias (sin evaluaciones, no está en maestro, asistencia < 50%).

    Retorna un diccionario con:
    - contadores: {'aprobacion': N, 'participacion': N, 'sin_certificado': N, 'inconsistencias': N}
    - inconsistencias: lista de registros con anomalías detectadas
    - estudiantes_tablero: lista consolidada de estudiantes para la vista de tabla
    """
    estudiantes = obtener_estudiantes()
    evaluaciones = obtener_evaluaciones()

    # R1: Agrupar evaluaciones por (identificacion, programa)
    evals_por_clave = defaultdict(list)
    for ev in evaluaciones:
        clave = (str(ev["identificacion"]).strip(), str(ev["programa"]).strip())
        evals_por_clave[clave].append(ev)

    estudiantes_por_ident = {str(e["identificacion"]).strip(): e for e in estudiantes}

    contadores = {
        "aprobacion": 0,
        "participacion": 0,
        "sin_certificado": 0,
        "inconsistencias": 0,
    }

    inconsistencias: List[Dict[str, Any]] = []
    estudiantes_tablero: List[Dict[str, Any]] = []

    # Procesar estudiantes del maestro
    for est in estudiantes:
        ident = str(est["identificacion"]).strip()
        programa = str(est["programa"]).strip()
        nombre = est.get("nombre_completo", "")
        correo = est.get("correo", "")
        cohorte = est.get("cohorte", "")

        evs = evals_por_clave.get((ident, programa), [])

        # R6: Estudiante del maestro sin evaluaciones
        if not evs:
            inconsistencias.append({
                "identificacion": ident,
                "nombre_completo": nombre,
                "programa": programa,
                "motivo": "Estudiante en maestro sin evaluaciones registradas",
                "tipo_error": "SIN_EVALUACIONES",
            })
            estudiantes_tablero.append({
                "identificacion": ident,
                "nombre_completo": nombre,
                "correo": correo,
                "programa": programa,
                "cohorte": cohorte,
                "promedio_nota": None,
                "promedio_asistencia": None,
                "modulos": 0,  # LADRILLO: variable (sin evaluaciones, cero modulos)
                "tipo_certificado": TIPO_INCONSISTENCIA,
                "es_inconsistente": True,
                "motivo_inconsistencia": "Sin evaluaciones",
                "emite_certificado": False,
            })
            continue

        # R2: Promedios redondeados a 2 decimales
        notas_validas = [float(e["nota"]) for e in evs if e.get("nota") is not None]
        asist_validas = [float(e["asistencia_pct"]) for e in evs if e.get("asistencia_pct") is not None]

        prom_nota = round(sum(notas_validas) / len(notas_validas), 2) if notas_validas else 0.0
        prom_asist = round(sum(asist_validas) / len(asist_validas), 2) if asist_validas else 0.0

        tipo_cert = determinar_tipo_certificado(prom_nota, prom_asist)
        es_inconsistente = False
        motivo_inconsistencia = None

        # R6: Asistencia menor al 50%
        if prom_asist < ASISTENCIA_CRITICA:
            es_inconsistente = True
            motivo_inconsistencia = f"Asistencia menor al 50 % ({prom_asist} %)"
            inconsistencias.append({
                "identificacion": ident,
                "nombre_completo": nombre,
                "programa": programa,
                "motivo": f"Asistencia crítica menor a 50%: {prom_asist}%",
                "tipo_error": "ASISTENCIA_BAJA",
            })

        # Actualizar contadores
        if tipo_cert == TIPO_APROBACION:
            contadores["aprobacion"] += 1
        elif tipo_cert == TIPO_PARTICIPACION:
            contadores["participacion"] += 1
        elif tipo_cert == TIPO_SIN_CERTIFICADO:
            contadores["sin_certificado"] += 1

        estudiantes_tablero.append({
            "identificacion": ident,
            "nombre_completo": nombre,
            "correo": correo,
            "programa": programa,
            "cohorte": cohorte,
            "promedio_nota": prom_nota,
            "promedio_asistencia": prom_asist,
            "modulos": len(evs),  # LADRILLO: variable (cantidad de modulos cursados, 3 o 4)
            "tipo_certificado": tipo_cert,
            "es_inconsistente": es_inconsistente,
            "motivo_inconsistencia": motivo_inconsistencia,
            "emite_certificado": tipo_cert in (TIPO_APROBACION, TIPO_PARTICIPACION) and not es_inconsistente,
        })

    # R6: Identificación con evaluaciones que no está en el maestro
    for (ident, prog), evs in evals_por_clave.items():
        if ident not in estudiantes_por_ident:
            inconsistencias.append({
                "identificacion": ident,
                "nombre_completo": "No registrado en Maestro",
                "programa": prog,
                "motivo": "Identificación con evaluaciones no existe en el maestro",
                "tipo_error": "NO_EN_MAESTRO",
            })

    contadores["inconsistencias"] = len(inconsistencias)

    return {
        "contadores": contadores,
        "inconsistencias": inconsistencias,
        "estudiantes_tablero": estudiantes_tablero,
    }


def obtener_detalle_estudiante(identificacion: str, programa: str = "") -> Optional[Dict[str, Any]]:
    """
    Retorna los datos calculados de un estudiante específico para su certificado.
    Realiza comparación limpia y flexible de identificación y programa.
    """
    resumen = procesar_certificados()
    ident_limpia = str(identificacion).strip()
    prog_limpio = str(programa).strip().lower()

    # R1: el certificado es por identificacion + programa, asi que ambos deben coincidir
    for est in resumen["estudiantes_tablero"]:
        if (
            est["identificacion"] == ident_limpia
            and est["programa"].strip().lower() == prog_limpio
        ):
            return est

    return None
