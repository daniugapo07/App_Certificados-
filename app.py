"""
app.py
Punto de entrada de la App de Certificados de la Academia.
Inicializa Flask, configura la carpeta de plantillas 'views/' y registra las rutas.
"""

import os
from pathlib import Path
from flask import Flask
from controllers.tablero import tablero_bp
from controllers.certificados import certificados_bp

# LADRILLO: variable (carpeta donde vive app.py, sin importar desde donde se ejecute)
BASE_DIR = Path(__file__).resolve().parent
# Trabajar siempre desde la raiz del proyecto: asi las rutas relativas
# como "insumos/..." y "views/" funcionan aunque se arranque desde otra carpeta
os.chdir(BASE_DIR)

# Configuración de la aplicación Flask
# views/ contiene las plantillas Jinja diseñadas por disenador-vistas
app = Flask(__name__, template_folder="views")
app.secret_key = os.getenv("SECRET_KEY", "academia_certificados_2026")

# Registro de controladores
app.register_blueprint(tablero_bp)
app.register_blueprint(certificados_bp)

if __name__ == "__main__":
    # Levanta el servidor en el puerto 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
