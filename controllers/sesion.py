"""
controllers/sesion.py
Controlador de la pantalla de entrada: /login y /salir.
Aquí también vive el decorador requiere_login, que protege las rutas
que muestran datos: si no hay sesión, redirige a /login.
"""

from functools import wraps
from typing import Callable

from flask import Blueprint, redirect, render_template, request, session, url_for

from models.usuarios import (
    esta_en_modo_demostracion,
    usuarios_de_demostracion,
    verificar_credenciales,
)

sesion_bp = Blueprint("sesion", __name__)


def requiere_login(vista: Callable):
    """
    LADRILLO: función decoradora.
    Envuelve una ruta: si no hay correo guardado en la sesión, manda a
    /login. Si ya entró, deja pasar a la ruta original.
    """

    @wraps(vista)
    def envoltura(*args, **kwargs):
        # LADRILLO: condicional (sin sesión no se muestra nada)
        if not session.get("correo"):
            return redirect(url_for("sesion.login"))
        return vista(*args, **kwargs)

    return envoltura


def solo_admin(vista: Callable):
    """
    LADRILLO: función decoradora.
    Solo deja pasar a los usuarios con rol 'admin'.
    Si el rol de la sesión no es 'admin', responde 403 con la página
    views/sin_permiso.html (que explica el motivo y muestra la sesión).
    """

    @wraps(vista)
    def envoltura(*args, **kwargs):
        # LADRILLO: condicional (la sesión debe tener el rol exacto 'admin')
        if session.get("rol") != "admin":
            return render_template("sin_permiso.html"), 403
        return vista(*args, **kwargs)

    return envoltura


@sesion_bp.route("/login", methods=["GET", "POST"])
def login():
    """Muestra el formulario de entrada y valida correo y contraseña."""
    # Si ya hay una sesión abierta, no tiene sentido volver a entrar
    if session.get("correo"):
        return redirect(url_for("tablero.index"))

    error = None

    # LADRILLO: condicional (POST = enviaron el formulario)
    if request.method == "POST":
        correo = request.form.get("correo", "")
        clave = request.form.get("clave", "")

        usuario = verificar_credenciales(correo, clave)

        if usuario:
            # LADRILLO: diccionario (la sesión guarda quién entró y su rol)
            session.clear()
            session["correo"] = usuario["correo"]
            session["rol"] = usuario["rol"]
            return redirect(url_for("tablero.index"))

        # Credenciales incorrectas: la plantilla muestra este mensaje en rojo
        error = "Correo o contraseña incorrectos."

    return render_template(
        "login.html",
        error=error,
        modo_demostracion=esta_en_modo_demostracion(),
        usuarios_demo=usuarios_de_demostracion(),
    )


@sesion_bp.route("/salir")
def salir():
    """Borra la sesión y devuelve a la pantalla de entrada."""
    session.clear()
    return redirect(url_for("sesion.login"))
