# App de Certificados — Instrucciones para agentes

App Flask (Python 3.12, `uv`, nunca `pip`) de Academia Horizonte (formación técnica a empresas): reemplaza el proceso manual en Excel/Word de emitir certificados por cohorte. Cruza 2 Excel, guarda en BD, aplica reglas fijas (sin IA) y genera PDF.

## Comandos (fuente: `pyproject.toml`, `app.py`, `cargar_datos.py`)

- `uv run app.py` — arranca Flask en puerto 5000 (`app` es la variable de la app).
- `uv run cargar_datos.py` — crea tablas y carga los Excel a la BD.
- `uv sync` — instalar/actualizar dependencias. `pyproject.toml` manda en local; `requirements.txt` solo existe para el deploy en Vercel (`vercel.json` usa `app.py`).
- No hay tests, linter ni CI. Verificación = correr `cargar_datos.py` y comprobar las cifras de control de abajo.

## Decisiones técnicas (aprobadas en el análisis, ver `PLAN.md`)

- Excel: `pandas` + `openpyxl` (groupby/mean para R1–R2, `dtype=str` para IDs). Descartados: solo `openpyxl` (promedios a mano, más errores), `xlrd` (obsoleto para .xlsx).
- Web: `Flask` (app pequeña, Jinja incluido, encaja con `vercel.json`). Descartados: Django (sobredimensionado), FastAPI (para APIs JSON, aquí sale HTML + PDF).
- PDF: `fpdf2` (A4 horizontal, simple). BD: `psycopg[binary]` + Supabase (`prepare_threshold=None`) con caída a SQLite local.
- Orden de construcción: 1) validar cruce de datos, 2) backend Flask, 3) interfaz. Cada etapa se valida (tester-datos + revisor) antes de seguir.

## Arquitectura MVC (respetarla) — alias del usuario: Bodega = datos, Cocina = backend en `app.py`, Salón = frontend

- Bodega: `INSUMOS/` y `models/datos.py` (ÚNICO que habla con la BD: `get_connection()`, `crear_tablas()`, `guardar_*`, `contar_*`, `obtener_*`).
- Cocina (toda la lógica, NUNCA en la interfaz): `models/certificados.py` — reglas del negocio (`NOTA_MINIMA = 70`, `ASISTENCIA_MINIMA = 80`, `ASISTENCIA_CRITICA = 50`). `procesar_certificados()` y `obtener_detalle_estudiante()` viven aquí.
- `services/carga_excel.py` — lee los Excel con pandas/openpyxl y persiste vía `models.datos`.
- `services/generador_pdf.py` — PDF con fpdf2, A4 horizontal. Colores `#14213D` / `#B8923D`.
- `controllers/` — solo rutas Flask, sin cálculos. `tablero.py` → `/` y `/cargar`; `certificados.py` → `/certificado/<id>/<programa>` (403 si no es elegible) y `/descargar-todos` (.zip).
- Salón (solo muestra, no calcula ni decide): `views/` — plantillas Jinja. **OJO: aún no existe en el repo** (`ls views` falla). `tablero.py` espera `tablero.html`; si `cargar.html` falta, `/cargar` (GET) redirige a `/`.
- `src/app_certificados/__init__.py` es un stub, ignorarlo.

## Datos y BD (verificado en código)

- Fuente: `INSUMOS/` en disco (**mayúsculas**). Hojas: `Estudiantes` (24 filas) y `Evaluaciones` (88 filas). Columnas según `COLUMNAS_MAESTRO` / `COLUMNAS_EVALUACIONES` en `services/carga_excel.py`.
- `Identificacion` siempre texto sin espacios (`_limpiar_identificacion()` quita `.0` espurio de Excel).
- BD dual en `models/datos.py`: si `DATABASE_URL` (en `.env`, ver `.env.ejemplo`) empieza con `postgresql://` usa Supabase con `psycopg.connect(..., prepare_threshold=None, row_factory=dict_row)`; si no, SQLite local `certificados.db`. Sin FK estricta a propósito (para detectar inconsistencias R6).

## Reglas y cifras de control (la entrega solo vale si salen)

- R1 agrupa por `identificacion + programa` (un certificado por estudiante y programa). R2: Promedio = suma de Notas / cantidad de módulos; Asistencia = promedio de `asistencia_pct`; redondeo a 2 decimales.
- R3 Aprobación: prom ≥ 70 y asist ≥ 80. R4 Participación: prom < 70 y asist ≥ 80. R5 Sin certificado: asist < 80. Los límites INCLUYEN el valor. R6 inconsistencias (no certifican): sin evaluaciones, id no en maestro, asistencia < 50 %.
- Esperado: **19 Aprobación, 3 Participación, 1 Sin certificado, 3 inconsistencias** (304560321 Javier Espinoza sin evaluaciones; 999880777 no en maestro; Fernanda Zúñiga asist 36.25). Controles: Camila Rojas Méndez 101230456 = 91.25/96.25 Aprobación; Luis Acuña Blanco = 72.0/81.67 Aprobación.

## Gotchas que un agente adivinaría mal

1. **Caso de `INSUMOS/` vs `insumos/`**: el disco trae mayúsculas pero `carga_excel.py` y `tablero.py` usan `insumos/...` en minúsculas. Funciona en Windows, **falla en Linux/Vercel**. Al tocar rutas, normalizar a una sola forma.
2. **Sin `views/`**: cualquier cambio de plantilla primero debe crear la carpeta y `tablero.html`.
3. **`.env` existe y está en `.gitignore`**: nunca leerlo, mostrarlo ni hardcodear credenciales. La conexión solo vía `DATABASE_URL` + `python-dotenv`.
4. **`INSUMOS/` es solo lectura**: nunca modificarlo.
5. `emite_certificado` (en `models/certificados.py`) es la única puerta para el PDF/ZIP: `Aprobación` o `Participación` sin inconsistencia. No duplicar esa lógica en controladores.

## Cómo trabajar aquí

- Español sencillo (usuario principiante). Plan corto antes de construir, entregas pequeñas indicando archivos y capa (models/services/controllers/views).
- Código simple y comentado en español, señalando los ladrillos: variables, tipos, condicionales, bucles y funciones.
- Al cerrar cada entrega: subagentes `.agents/agents/tester-datos.md` (prueba, solo lee+ejecuta) y `revisor.md` (revisa). Nunca les pedir que editen código.
