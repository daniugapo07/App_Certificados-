"""
app.py
Punto de entrada de la App de Certificados de la Academia.
Inicializa Flask, configura la carpeta de plantillas 'views/' y registra las rutas.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from controllers.tablero import tablero_bp
from controllers.certificados import certificados_bp
from controllers.sesion import sesion_bp

# LADRILLO: variable (carpeta donde vive app.py, sin importar desde donde se ejecute)
BASE_DIR = Path(__file__).resolve().parent
# Trabajar siempre desde la raiz del proyecto: asi las rutas relativas
# como "INSUMOS/..." y "views/" funcionan aunque se arranque desde otra carpeta
os.chdir(BASE_DIR)

# Carga las variables del archivo .env (solo en local; en Vercel se
# configuran en el panel del proyecto). No sobreescribe las que ya existan.
load_dotenv()

# Configuración de la aplicación Flask
# views/ contiene las plantillas Jinja diseñadas por disenador-vistas
app = Flask(__name__, template_folder="views")
# LADRILLO: variable de entorno (clave con la que se firman las cookies de sesión).
# En producción conviene definir SECRET_KEY; si no existe, se usa una de respaldo.
app.secret_key = os.environ.get("SECRET_KEY") or "academia_certificados_2026"

# Cookies de sesión: no accesibles desde JavaScript y solo por HTTPS en Vercel
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("VERCEL"))

# LADRILLO: límite del envío completo. Vercel rechaza cuerpos de más de 4.5 MB.
app.config["MAX_CONTENT_LENGTH"] = int(4.5 * 1024 * 1024)

# Registro de controladores
app.register_blueprint(tablero_bp)
app.register_blueprint(certificados_bp)
app.register_blueprint(sesion_bp)


@app.errorhandler(413)
def archivo_demasiado_grande(error):
    """
    Página amable si el envío supera MAX_CONTENT_LENGTH.
    Evita que el usuario vea una página en blanco o un error crudo.
    """
    return (
        "<html lang='es'><head><meta charset='utf-8'>"
        "<title>Archivo demasiado grande</title></head>"
        "<body style='font-family: Arial, sans-serif; background: #f4f4f4; "
        "padding: 40px; text-align: center;'>"
        "<div style='background: white; max-width: 520px; margin: auto; "
        "padding: 30px; border-top: 5px solid #B8923D; border-radius: 8px;'>"
        "<h1 style='color: #14213D;'>Archivo demasiado grande</h1>"
        "<p style='color: #b71c1c;'>El envío supera el límite de 4.5 MB "
        "permitido por Vercel. Sube archivos más pequeños.</p>"
        "<p><a href='/' style='color: #14213D; font-weight: bold;'>"
        "Volver al tablero</a></p>"
        "</div></body></html>",
        413,
    )

# Arranque en produccion (Vercel): si la BD esta vacia, crear tablas y
# cargar los Excel de INSUMOS/. En local no hace nada porque ya hay datos.
# LADRILLO: condicional con proteccion (si falla, la app igual arranca)
try:
    from models.datos import crear_tablas, contar_estudiantes
    crear_tablas()
    if contar_estudiantes() == 0:
        from services.carga_excel import cargar_archivos_y_persistir
        cargar_archivos_y_persistir()
except Exception as err:
    # En Vercel este mensaje queda en los logs de la función y ayuda a
    # diagnosticar problemas de conexión con Supabase al arrancar.
    print(f"[arranque] No se pudo preparar la base de datos: {err}")

if __name__ == "__main__":
    # Levanta el servidor en el puerto 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
