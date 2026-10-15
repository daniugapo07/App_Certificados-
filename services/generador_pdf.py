"""
services/generador_pdf.py
Servicio para la generación de certificados en formato PDF (A4 horizontal)
y empaquetado en archivo comprimido ZIP utilizando fpdf2.
"""

import io
import zipfile
from typing import Any, Dict, List
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Paleta corporativa institucional
COLOR_NAVY = (20, 33, 61)       # #14213D - Azul marino principal
COLOR_GOLD = (184, 146, 61)     # #B8923D - Dorado institucional
COLOR_DARK = (31, 41, 55)       # #1F2937 - Gris carbón para texto
COLOR_MUTED = (100, 116, 139)   # #64748B - Gris secundario
COLOR_BG_BOX = (248, 250, 252)  # Fondo suave para recuadro de métricas


class CertificadoPDF(FPDF):
    """Clase personalizada para maquetar el certificado institucional."""

    def dibujar_marco(self):
        """Dibuja marco perimetral con doble línea decorativa y esquinas doradas."""
        # Borde exterior dorado (grueso)
        self.set_line_width(1.5)
        self.set_draw_color(*COLOR_GOLD)
        self.rect(10, 10, 277, 190)

        # Borde interior azul marino (fino)
        self.set_line_width(0.6)
        self.set_draw_color(*COLOR_NAVY)
        self.rect(13, 13, 271, 184)

        # Esquinas decorativas doradas
        self.set_fill_color(*COLOR_GOLD)
        tam = 4
        self.rect(10, 10, tam, tam, "F")
        self.rect(287 - tam, 10, tam, tam, "F")
        self.rect(10, 200 - tam, tam, tam, "F")
        self.rect(287 - tam, 200 - tam, tam, tam, "F")


def generar_certificado_pdf(estudiante: Dict[str, Any]) -> bytes:
    """
    Genera el archivo PDF de un certificado en formato A4 horizontal (297 x 210 mm).
    Título según tipo: 'Certificado de Aprobación' o 'Certificado de Participación'.
    Incluye nombre, programa, cohorte, promedio y asistencia.
    """
    pdf = CertificadoPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # Decoración y marco
    pdf.dibujar_marco()

    # 1. Cabecera institucional
    pdf.set_xy(15, 22)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_GOLD)
    pdf.cell(267, 8, "ACADEMIA DE FORMACIÓN PROFESIONAL", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 2. Título del certificado según tipo
    tipo = estudiante.get("tipo_certificado", "Aprobación")
    titulo = f"Certificado de {tipo}"
    pdf.set_font("Helvetica", "B", 25)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(267, 13, titulo, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 3. Subtítulo introductorio
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(267, 6, "Otorga el presente reconocimiento a:", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 4. Nombre del estudiante
    pdf.set_font("Helvetica", "B", 21)
    pdf.set_text_color(*COLOR_NAVY)
    nombre = estudiante.get("nombre_completo", "")
    pdf.cell(267, 11, nombre, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 5. Identificación
    ident = estudiante.get("identificacion", "")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(267, 6, f"Identificación: {ident}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 6. Texto de cumplimiento
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(
        267,
        6,
        "Por haber completado satisfactoriamente los requisitos del programa de formación:",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # 7. Programa cursado
    programa = estudiante.get("programa", "")
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(267, 10, programa, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 8. Cohorte
    cohorte = estudiante.get("cohorte", "")
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(*COLOR_GOLD)
    pdf.cell(267, 6, f"Cohorte: {cohorte}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 9. Recuadro de métricas académicas (promedio y asistencia)
    pdf.ln(3)
    x_box = 60
    y_box = 133
    w_box = 177
    h_box = 18
    pdf.set_fill_color(*COLOR_BG_BOX)
    pdf.set_draw_color(*COLOR_GOLD)
    pdf.set_line_width(0.4)
    pdf.rect(x_box, y_box, w_box, h_box, "DF")

    prom_nota = estudiante.get("promedio_nota", 0.0)
    prom_asist = estudiante.get("promedio_asistencia", 0.0)

    pdf.set_xy(x_box, y_box + 4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*COLOR_NAVY)
    texto_metricas = (
        f"Calificación Promedio: {prom_nota:.2f} / 100        |        "
        f"Asistencia Registrada: {prom_asist:.2f} %"
    )
    pdf.cell(w_box, 10, texto_metricas, align="C")

    # 10. Líneas de firmas institucionales
    y_firmas = 168
    pdf.set_line_width(0.5)
    pdf.set_draw_color(*COLOR_MUTED)
    pdf.line(45, y_firmas, 115, y_firmas)
    pdf.line(182, y_firmas, 252, y_firmas)

    pdf.set_xy(45, y_firmas + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(70, 5, "Dirección Académica", align="C")

    pdf.set_xy(182, y_firmas + 2)
    pdf.cell(70, 5, "Coordinación de Programa", align="C")

    return bytes(pdf.output())


def generar_zip_certificados(estudiantes: List[Dict[str, Any]]) -> io.BytesIO:
    """
    Genera un archivo ZIP en memoria que contiene los PDFs de todos los estudiantes
    elegibles (Aprobación y Participación).
    Excluye automáticamente a los no elegibles (Sin certificado o inconsistencias).
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for est in estudiantes:
            # No se genera certificado si no es elegible
            if not est.get("emite_certificado"):
                continue

            pdf_bytes = generar_certificado_pdf(est)
            ident = est.get("identificacion", "desconocido")
            tipo = est.get("tipo_certificado", "Certificado")
            tipo_archivo = "Aprobacion" if "aprob" in str(tipo).lower() else "Participacion"
            nombre_archivo = f"Certificado_{ident}_{tipo_archivo}.pdf"
            zf.writestr(nombre_archivo, pdf_bytes)

    zip_buffer.seek(0)
    return zip_buffer
