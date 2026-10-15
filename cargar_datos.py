"""
cargar_datos.py
Script para inicializar las tablas en Supabase y cargar los datos desde los archivos Excel.
"""

import sys
from models.datos import crear_tablas, contar_estudiantes, contar_evaluaciones
from services.carga_excel import cargar_archivos_y_persistir


def main():
    print("=== App de Certificados - Carga de Datos Inicial ===")
    try:
        print("\n--- Conectando y creando tablas en Supabase ---")
        crear_tablas()
        print("Tablas 'estudiantes' y 'evaluaciones' verificadas/creadas con éxito.")

        print("\n--- Cargando datos desde archivos Excel (insumos/) ---")
        resultado = cargar_archivos_y_persistir()
        print(f"Estudiantes procesados e insertados: {resultado['estudiantes_cargados']}")
        print(f"Evaluaciones procesadas e insertadas: {resultado['evaluaciones_cargadas']}")

        print("\n--- Verificación de registros en Supabase ---")
        total_estudiantes = contar_estudiantes()
        total_evaluaciones = contar_evaluaciones()

        print(f"Total de filas en tabla 'estudiantes': {total_estudiantes}")
        print(f"Total de filas en tabla 'evaluaciones': {total_evaluaciones}")
        print("\n¡Carga inicial completada con éxito!")

    except ValueError as e:
        print(f"\n[ERROR DE CONFIGURACIÓN]: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR INESPERADO]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
