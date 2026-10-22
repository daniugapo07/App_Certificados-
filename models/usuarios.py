"""
models/usuarios.py
Usuarios de la aplicación para la pantalla de entrada.

Todavía no hay base de datos: los dos usuarios (administrador y usuario
normal) se leen de variables de entorno con os.environ.get.
Si alguna de esas variables falta, se usan valores de demostración y la
pantalla de entrada muestra un aviso de "modo demostración".
"""

import os
from typing import Any, Dict, List, Optional

# LADRILLO: diccionario (usuarios de demostración, solo si faltan las variables)
USUARIOS_DEMO = {
    "admin": {"correo": "admin@academia.com", "clave": "admin123"},
    "usuario": {"correo": "usuario@academia.com", "clave": "usuario123"},
}

# LADRILLO: diccionario (qué variables de entorno usa cada rol)
VARIABLES_ENTORNO = {
    "admin": ("ADMIN_CORREO", "ADMIN_CLAVE"),
    "usuario": ("USUARIO_CORREO", "USUARIO_CLAVE"),
}


def obtener_usuarios() -> List[Dict[str, Any]]:
    """
    Devuelve la lista de usuarios configurados.
    Cada usuario es un diccionario con: correo, clave, rol y es_demo.
    """
    usuarios: List[Dict[str, Any]] = []

    # LADRILLO: bucle (recorremos los dos roles: admin y usuario)
    for rol, (variable_correo, variable_clave) in VARIABLES_ENTORNO.items():
        correo = (os.environ.get(variable_correo) or "").strip()
        clave = (os.environ.get(variable_clave) or "").strip()

        # LADRILLO: condicional (si falta el correo o la clave, usamos el demo)
        es_demo = not correo or not clave
        if not correo:
            correo = USUARIOS_DEMO[rol]["correo"]
        if not clave:
            clave = USUARIOS_DEMO[rol]["clave"]

        usuarios.append({
            "correo": correo,
            "clave": clave,
            "rol": rol,
            "es_demo": es_demo,
        })

    return usuarios


def esta_en_modo_demostracion() -> bool:
    """True si al menos uno de los dos usuarios usa valores de demostración."""
    return any(usuario["es_demo"] for usuario in obtener_usuarios())


def usuarios_de_demostracion() -> List[Dict[str, Any]]:
    """Devuelve solo los usuarios que usan valores de demostración (para el aviso)."""
    return [usuario for usuario in obtener_usuarios() if usuario["es_demo"]]


def verificar_credenciales(correo: str, clave: str) -> Optional[Dict[str, str]]:
    """
    Comprueba si el correo y la clave coinciden con alguno de los usuarios.
    Devuelve {'correo': ..., 'rol': ...} si coincide, o None si no.
    """
    correo_limpio = (correo or "").strip().lower()
    clave_limpia = clave or ""

    # LADRILLO: bucle (buscamos el usuario que coincida en correo y clave)
    for usuario in obtener_usuarios():
        coincide_correo = usuario["correo"].strip().lower() == correo_limpio
        coincide_clave = usuario["clave"] == clave_limpia
        if coincide_correo and coincide_clave:
            return {"correo": usuario["correo"], "rol": usuario["rol"]}

    return None
