"""
tests/test_app.py
Pruebas automáticas de la App de Certificados con el cliente de pruebas
de Flask. Simulan un navegador: no hace falta abrir la app ni usar un
navegador real.

Las variables de entorno se definen AQUÍ, antes de importar la app, para
que las pruebas no dependan del archivo .env de cada máquina.
"""

import io
import os
import re

import pandas as pd

# --- Credenciales de prueba (siempre las mismas, sin tocar el .env) ---
os.environ["ADMIN_CORREO"] = "admin@pruebas.com"
os.environ["ADMIN_CLAVE"] = "clave_admin"
os.environ["USUARIO_CORREO"] = "usuario@pruebas.com"
os.environ["USUARIO_CLAVE"] = "clave_usuario"
os.environ["SECRET_KEY"] = "clave_secreta_solo_para_pruebas"

# --- Base de datos: usar SQLite local y no depender de Supabase ---
# El string vacío evita que load_dotenv() lo reemplace con el valor del .env.
os.environ["DATABASE_URL"] = ""
os.environ["VERCEL"] = ""

from app import app  # noqa: E402  (se importa después de definir el entorno)


def cliente_de_pruebas():
    """Entrega un cliente que simula el navegador, con la app en modo prueba."""
    app.config.update(TESTING=True)
    return app.test_client()


def iniciar_sesion(cliente, correo, clave):
    """Simula el envío del formulario de entrada."""
    return cliente.post("/login", data={"correo": correo, "clave": clave})


def leer_insumo(nombre):
    """Lee un Excel de INSUMOS/ como bytes, sin modificarlo."""
    with open(f"INSUMOS/{nombre}", "rb") as archivo:
        return archivo.read()


def evaluaciones_con_camila_en_40():
    """
    Arma EN MEMORIA un Registro_Evaluaciones a partir del de INSUMOS,
    cambiando solo las notas de Camila Rojas Méndez (101230456) a 40.
    El archivo original nunca se modifica.
    """
    df = pd.read_excel(
        "INSUMOS/Registro_Evaluaciones.xlsx",
        sheet_name="Evaluaciones",
        dtype=str,
    )
    # LADRILLO: condicional por fila (la máscara marca solo las filas de Camila)
    mascara_camila = df["Identificacion"].astype(str).str.strip() == "101230456"
    df.loc[mascara_camila, "Nota"] = "40"

    # LADRILLO: BytesIO = caja en memoria para el Excel modificado
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Evaluaciones", index=False)
    buffer.seek(0)
    return buffer


def test_sin_sesion_redirige_a_login():
    """
    Simula a alguien que abre la página principal sin haberse autenticado:
    la app debe mandarlo a /login.
    """
    cliente = cliente_de_pruebas()

    respuesta = cliente.get("/")

    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_clave_incorrecta_no_entra():
    """
    Simula un intento de entrada con correo correcto y clave equivocada:
    debe quedarse en la pantalla de entrada y mostrar el mensaje de error.
    """
    cliente = cliente_de_pruebas()

    respuesta = cliente.post(
        "/login",
        data={"correo": "admin@pruebas.com", "clave": "clave_equivocada"},
    )

    assert respuesta.status_code == 200
    assert "Correo o contraseña incorrectos." in respuesta.get_data(as_text=True)


def test_usuario_no_puede_cargar():
    """
    Simula a un usuario normal que ya entró e intenta abrir el panel de
    administración escribiendo /cargar directamente en la URL:
    la ruta debe responder 403 (sin permiso).
    """
    cliente = cliente_de_pruebas()
    iniciar_sesion(cliente, "usuario@pruebas.com", "clave_usuario")

    respuesta = cliente.get("/cargar")

    assert respuesta.status_code == 403
    assert "solo para administradores" in respuesta.get_data(as_text=True)


def test_excel_modificado_cambia_contadores():
    """
    Simula al administrador subiendo un Registro_Evaluaciones con las notas
    de Camila Rojas Méndez (101230456) en 40. Como su asistencia sigue sobre
    80, pasa de Aprobación a Participación: 18 aprobación, 4 participación
    y 1 sin certificado.
    """
    cliente = cliente_de_pruebas()
    iniciar_sesion(cliente, "admin@pruebas.com", "clave_admin")

    respuesta = cliente.post(
        "/cargar",
        data={
            "accion": "ver",
            "maestro": (
                io.BytesIO(leer_insumo("Maestro_Estudiantes.xlsx")),
                "Maestro_Estudiantes.xlsx",
            ),
            "evaluaciones": (
                evaluaciones_con_camila_en_40(),
                "Registro_Evaluaciones.xlsx",
            ),
        },
        content_type="multipart/form-data",
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)

    # LADRILLO: expresión regular (lee el número que está dentro de cada tarjeta)
    aprobacion = int(re.search(r'numero verde">(\d+)<', cuerpo).group(1))
    participacion = int(re.search(r'numero azul">(\d+)<', cuerpo).group(1))
    sin_certificado = int(re.search(r'numero rojo">(\d+)<', cuerpo).group(1))

    assert (aprobacion, participacion, sin_certificado) == (18, 4, 1)
