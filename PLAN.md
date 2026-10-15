# Plan de implementación — App de Certificados (Academia Horizonte)

Construimos en 3 etapas, en este orden. Regla de oro: **ninguna etapa
se da por terminada sin pasar su validación**. Seguimos en modo Plan:
aquí solo se describe el trabajo, no se escribe código.

## Orden general

1. **Etapa 1 — Validar el cruce de datos** (Bodega + reglas).
2. **Etapa 2 — Backend con Flask** (Cocina).
3. **Etapa 3 — Interfaz web** (Salón).

## Etapa 1 — Validar el cruce de datos

**Objetivo:** demostrar con los Excel reales que el cruce
identificación + programa produce las cifras de control.

**Qué se hará:**
- Leer `INSUMOS/Maestro_Estudiantes.xlsx` (hoja `Estudiantes`, 24 filas)
  y `INSUMOS/Registro_Evaluaciones.xlsx` (hoja `Evaluaciones`, 88 filas),
  sin modificarlos.
- Limpiar `Identificacion` como texto sin espacios (quitar `.0` espurio).
- Agrupar por identificación + programa, calcular promedio de notas
  y promedio de asistencia (2 decimales) y aplicar R3–R6.
- Detectar las 3 inconsistencias (sin evaluaciones, fantasma, < 50 %).
- Archivos implicados (verificar, no crear): `services/carga_excel.py`,
  `models/datos.py`, `models/certificados.py`, `cargar_datos.py`.

**Validación (puerta de salida):**
- Cifras exactas: 19 Aprobación, 3 Participación, 1 Sin certificado,
  3 inconsistencias.
- Controles: Camila Rojas `101230456` = 91.25/96.25 Aprobación;
  Luis Acuña = 72.0/81.67 Aprobación.
- Lo comprueba el subagente `tester-datos` y lo revisa `revisor`.
- Sin este visto bueno, NO se pasa a la Etapa 2.

## Etapa 2 — Backend con Flask

**Objetivo:** servidor funcionando con las 4 rutas y PDFs correctos.

**Qué se hará:**
- `app.py`: crear la app Flask (variable `app`), puerto 5000,
  registrar los controladores.
- `controllers/tablero.py`: ruta `/` (tablero) y `/cargar`
  (formulario de subida de los 2 Excel).
- `controllers/certificados.py`: `/certificado/<id>/<programa>` (PDF;
  403 si no es elegible, 404 si no existe) y `/descargar-todos` (.zip).
- `services/generador_pdf.py`: certificado A4 horizontal con
  fpdf2, colores `#14213D` / `#B8923D`.
- Toda la lógica queda en modelos y servicios; los controladores
  solo llaman y sirven. Nada de cálculos en la interfaz.

**Validación (puerta de salida):**
- `uv run app.py` levanta sin errores; las 4 rutas responden.
- El .zip trae 22 PDF (19 + 3); los no elegibles dan 403.
- `tester-datos` prueba rutas y PDF; `revisor` revisa.
- Sin este visto bueno, NO se pasa a la Etapa 3.

## Etapa 3 — Interfaz web

**Objetivo:** páginas claras con el estilo de la Academia
(azul marino `#14213D` y dorado `#B8923D`).

**Qué se hará:**
- Crear `views/` (hoy no existe): `tablero.html` (contadores,
  tabla de estudiantes, alertas de inconsistencias) y `cargar.html`
  (formulario para subir los 2 Excel).
- Las plantillas solo muestran datos; no calculan ni deciden.

**Validación (puerta de salida):**
- Los números en pantalla coinciden con las cifras de control.
- Las 3 inconsistencias se ven como alertas, no como certificados.
- Revisión visual del estilo y prueba final de `tester-datos` + `revisor`.

## Gotchas a cuidar en todas las etapas

- `INSUMOS/` en disco va en mayúsculas; normalizar rutas (en Linux falla).
- Nunca modificar `INSUMOS/` ni leer/mostrar `.env`.
- `uv` (nunca `pip`); Python 3.12.
