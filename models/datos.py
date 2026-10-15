"""
models/datos.py
Módulo responsable exclusivo de la comunicación con la base de datos (PostgreSQL en Supabase o SQLite local).
"""

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Carga variables de entorno desde .env
load_dotenv()

# LADRILLO: condicional (en Vercel el disco es de solo lectura salvo /tmp)
if os.getenv("VERCEL"):
    DB_FILE_SQLITE = Path("/tmp/certificados.db")
else:
    DB_FILE_SQLITE = Path(__file__).resolve().parent.parent / "certificados.db"


def es_postgres() -> bool:
    """Verifica si DATABASE_URL está configurada para PostgreSQL/Supabase."""
    url = (os.getenv("DATABASE_URL") or "").strip()
    return url.startswith("postgresql://") or url.startswith("postgres://")


def get_connection():
    """
    Retorna una conexión a la base de datos:
    - PostgreSQL (Supabase) con psycopg si DATABASE_URL está definida.
    - SQLite local si no hay DATABASE_URL configurada.
    """
    if es_postgres():
        import psycopg
        from psycopg.rows import dict_row

        db_url = os.getenv("DATABASE_URL").strip()
        return psycopg.connect(db_url, prepare_threshold=None, row_factory=dict_row)
    else:
        conn = sqlite3.connect(str(DB_FILE_SQLITE))
        conn.row_factory = sqlite3.Row
        return conn


def crear_tablas() -> None:
    """
    Crea las tablas 'estudiantes' y 'evaluaciones' si no existen.
    No se define Foreign Key estricta para registrar y detectar
    inconsistencias del negocio (regla R6).
    """
    if es_postgres():
        sql = """
        CREATE TABLE IF NOT EXISTS estudiantes (
            identificacion TEXT PRIMARY KEY,
            nombre_completo TEXT NOT NULL,
            correo TEXT,
            programa TEXT NOT NULL,
            cohorte TEXT
        );

        CREATE TABLE IF NOT EXISTS evaluaciones (
            id SERIAL PRIMARY KEY,
            identificacion TEXT NOT NULL,
            programa TEXT NOT NULL,
            modulo TEXT NOT NULL,
            nota NUMERIC,
            asistencia_pct NUMERIC,
            fecha_cierre TEXT
        );
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
    else:
        sql = """
        CREATE TABLE IF NOT EXISTS estudiantes (
            identificacion TEXT PRIMARY KEY,
            nombre_completo TEXT NOT NULL,
            correo TEXT,
            programa TEXT NOT NULL,
            cohorte TEXT
        );

        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identificacion TEXT NOT NULL,
            programa TEXT NOT NULL,
            modulo TEXT NOT NULL,
            nota REAL,
            asistencia_pct REAL,
            fecha_cierre TEXT
        );
        """
        with get_connection() as conn:
            conn.executescript(sql)
            conn.commit()


def guardar_estudiantes(estudiantes: List[Dict[str, Any]]) -> int:
    """
    Reemplaza transaccionalmente los registros de la tabla estudiantes.
    Retorna la cantidad de registros insertados.
    """
    conn = get_connection()
    try:
        ph = "%s" if es_postgres() else "?"
        query = f"""
        INSERT INTO estudiantes (identificacion, nombre_completo, correo, programa, cohorte)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph});
        """
        params = [
            (
                e["identificacion"],
                e["nombre_completo"],
                e.get("correo"),
                e["programa"],
                e.get("cohorte"),
            )
            for e in estudiantes
        ]

        if es_postgres():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM estudiantes;")
                if estudiantes:
                    cur.executemany(query, params)
            conn.commit()
        else:
            with conn:
                conn.execute("DELETE FROM estudiantes;")
                if estudiantes:
                    conn.executemany(query, params)
    finally:
        conn.close()

    return len(estudiantes)


def guardar_evaluaciones(evaluaciones: List[Dict[str, Any]]) -> int:
    """
    Reemplaza transaccionalmente los registros de la tabla evaluaciones.
    Retorna la cantidad de registros insertados.
    """
    conn = get_connection()
    try:
        ph = "%s" if es_postgres() else "?"
        query = f"""
        INSERT INTO evaluaciones (identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph});
        """
        params = [
            (
                e["identificacion"],
                e["programa"],
                e["modulo"],
                e.get("nota"),
                e.get("asistencia_pct"),
                e.get("fecha_cierre"),
            )
            for e in evaluaciones
        ]

        if es_postgres():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM evaluaciones;")
                if evaluaciones:
                    cur.executemany(query, params)
            conn.commit()
        else:
            with conn:
                conn.execute("DELETE FROM evaluaciones;")
                if evaluaciones:
                    conn.executemany(query, params)
    finally:
        conn.close()

    return len(evaluaciones)


def contar_estudiantes() -> int:
    """Retorna el total de registros en la tabla estudiantes."""
    conn = get_connection()
    try:
        if es_postgres():
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS total FROM estudiantes;")
                fila = cur.fetchone()
                return fila["total"] if fila else 0
        else:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS total FROM estudiantes;")
            fila = cur.fetchone()
            return fila["total"] if fila else 0
    finally:
        conn.close()


def contar_evaluaciones() -> int:
    """Retorna el total de registros en la tabla evaluaciones."""
    conn = get_connection()
    try:
        if es_postgres():
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS total FROM evaluaciones;")
                fila = cur.fetchone()
                return fila["total"] if fila else 0
        else:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS total FROM evaluaciones;")
            fila = cur.fetchone()
            return fila["total"] if fila else 0
    finally:
        conn.close()


def obtener_estudiantes() -> List[Dict[str, Any]]:
    """Retorna todos los registros de estudiantes ordenados por identificación."""
    conn = get_connection()
    try:
        query = "SELECT identificacion, nombre_completo, correo, programa, cohorte FROM estudiantes ORDER BY identificacion;"
        if es_postgres():
            with conn.cursor() as cur:
                cur.execute(query)
                return [dict(r) for r in cur.fetchall()]
        else:
            cur = conn.cursor()
            cur.execute(query)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def obtener_evaluaciones() -> List[Dict[str, Any]]:
    """Retorna todos los registros de evaluaciones ordenados por identificación y módulo."""
    conn = get_connection()
    try:
        query = "SELECT id, identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre FROM evaluaciones ORDER BY identificacion, modulo;"
        if es_postgres():
            with conn.cursor() as cur:
                cur.execute(query)
                return [dict(r) for r in cur.fetchall()]
        else:
            cur = conn.cursor()
            cur.execute(query)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
