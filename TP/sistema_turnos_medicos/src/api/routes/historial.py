"""
Rutas para gestión del historial clínico de pacientes.
Permite consultar, crear y gestionar consultas médicas y recetas.
"""
from typing import List, Optional
from datetime import datetime, date
from io import BytesIO
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.api.schemas import (
    ConsultaResponse, ConsultaCreate, ConsultaUpdate,
    RecetaResponse, RecetaCreate, HistorialClinicoResponse,
    SuccessResponse
)
from src.api.dependencies import get_uow
from src.repositories.unit_of_work import UnitOfWork
from src.domain.consulta import Consulta
from src.domain.receta import Receta, ItemReceta

router = APIRouter(prefix="/historial", tags=["Historial Clínico"])

# ============================================================
# DATOS DE LA CLÍNICA (HARDCODEADOS)
# ============================================================
CLINICA_INFO = {
    "nombre": "CLÍNICA FICTICIA HOSPITAL PRIVADO",
    "direccion": "Av. Siempre Viva 742, Piso 3",
    "ciudad": "Ciudad Autónoma de Buenos Aires",
    "codigo_postal": "C1425",
    "telefono": "(011) 4567-8900",
    "email": "contacto@clinicaficticia.com.ar",
    "cuit": "30-12345678-9",
    "web": "www.clinicaficticia.com.ar"
}


# ============================================================
# ENDPOINTS DE CONSULTAS (HISTORIAL CLÍNICO)
# ============================================================

@router.get("/paciente/{paciente_id}", response_model=HistorialClinicoResponse)
def obtener_historial_paciente(
    paciente_id: int,
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Obtiene el historial clínico completo de un paciente.
    Incluye todas las consultas con sus recetas asociadas.
    """
    # Verificar que el paciente existe
    paciente = uow.pacientes.get_by_id(paciente_id)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con ID {paciente_id} no encontrado"
        )
    
    # Obtener consultas del paciente
    consultas = uow.consultas.get_por_paciente(
        paciente_id=paciente_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    
    # Construir respuesta enriquecida
    consultas_detalladas = []
    for consulta in consultas:
        turno = consulta.turno
        medico = turno.medico if turno else None
        especialidad = turno.especialidad if turno else None
        
        consulta_info = {
            "id": consulta.id,
            "fecha_atencion": consulta.fecha_atencion.isoformat() if consulta.fecha_atencion else None,
            "motivo": consulta.motivo,
            "observaciones": consulta.observaciones,
            "diagnostico": consulta.diagnostico,
            "indicaciones": consulta.indicaciones,
            "turno": {
                "id": turno.id if turno else None,
                "fecha_hora": turno.fecha_hora.isoformat() if turno else None,
            },
            "medico": {
                "id": medico.id if medico else None,
                "nombre_completo": medico.nombre_completo if medico else "N/A",
                "matricula": medico.matricula if medico else None,
            },
            "especialidad": {
                "id": especialidad.id if especialidad else None,
                "nombre": especialidad.nombre if especialidad else "N/A",
            },
            "recetas": [
                {
                    "id": receta.id,
                    "fecha_emision": receta.fecha_emision.isoformat() if receta.fecha_emision else None,
                    "estado": receta.estado,
                    "items": [
                        {
                            "id": item.id,
                            "medicamento": item.medicamento,
                            "dosis": item.dosis,
                            "frecuencia": item.frecuencia,
                            "duracion": item.duracion,
                            "indicaciones": item.indicaciones,
                        }
                        for item in receta.items
                    ]
                }
                for receta in consulta.recetas
            ]
        }
        consultas_detalladas.append(consulta_info)
    
    return HistorialClinicoResponse(
        paciente_id=paciente.id,
        paciente_nombre=paciente.nombre_completo,
        paciente_dni=paciente.dni,
        total_consultas=len(consultas_detalladas),
        consultas=consultas_detalladas
    )


@router.get("/consulta/{consulta_id}", response_model=ConsultaResponse)
def obtener_consulta(
    consulta_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene una consulta específica por ID."""
    consulta = uow.consultas.get_by_id(consulta_id)
    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada"
        )
    return consulta


@router.get("/turno/{turno_id}/consulta", response_model=ConsultaResponse)
def obtener_consulta_por_turno(
    turno_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene la consulta asociada a un turno específico."""
    consulta = uow.consultas.get_by_turno(turno_id)
    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe consulta para el turno {turno_id}"
        )
    return consulta


@router.post("/consulta", response_model=ConsultaResponse, status_code=status.HTTP_201_CREATED)
def crear_consulta(
    consulta_data: ConsultaCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Crea una nueva entrada en el historial clínico (consulta).
    Solo se puede crear para turnos en estado ASISTIDO (ASIS).
    """
    try:
        # Verificar que el turno existe
        turno = uow.turnos.get_by_id(consulta_data.id_turno)
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Turno con ID {consulta_data.id_turno} no encontrado"
            )
        
        # Verificar que el turno está en estado ASISTIDO
        if turno.estado.codigo != 'ASIS':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se puede crear consulta para turnos en estado ASISTIDO. Estado actual: {turno.estado.descripcion}"
            )
        
        # Verificar que no exista ya una consulta para este turno
        if uow.consultas.existe_para_turno(consulta_data.id_turno):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una consulta para el turno {consulta_data.id_turno}"
            )
        
        # Crear consulta
        consulta = Consulta(
            id_turno=consulta_data.id_turno,
            motivo=consulta_data.motivo,
            observaciones=consulta_data.observaciones,
            diagnostico=consulta_data.diagnostico,
            indicaciones=consulta_data.indicaciones,
            fecha_atencion=datetime.now()
        )
        
        uow.consultas.add(consulta)
        uow.commit()
        
        # Refrescar para obtener relaciones
        uow.session.refresh(consulta)
        return consulta
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear consulta: {str(e)}"
        )


@router.put("/consulta/{consulta_id}", response_model=ConsultaResponse)
def actualizar_consulta(
    consulta_id: int,
    consulta_data: ConsultaUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Actualiza una consulta existente."""
    try:
        consulta = uow.consultas.get_by_id(consulta_id)
        if not consulta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consulta con ID {consulta_id} no encontrada"
            )
        
        # Actualizar campos
        if consulta_data.motivo is not None:
            consulta.motivo = consulta_data.motivo
        if consulta_data.observaciones is not None:
            consulta.observaciones = consulta_data.observaciones
        if consulta_data.diagnostico is not None:
            consulta.diagnostico = consulta_data.diagnostico
        if consulta_data.indicaciones is not None:
            consulta.indicaciones = consulta_data.indicaciones
        
        uow.consultas.update(consulta)
        uow.commit()
        
        return consulta
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar consulta: {str(e)}"
        )


@router.delete("/consulta/{consulta_id}", response_model=SuccessResponse)
def eliminar_consulta(
    consulta_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Realiza soft delete de una consulta."""
    try:
        consulta = uow.consultas.get_by_id(consulta_id)
        if not consulta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consulta con ID {consulta_id} no encontrada"
            )
        
        uow.consultas.delete(consulta)
        uow.commit()
        
        return SuccessResponse(message=f"Consulta {consulta_id} eliminada correctamente")
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar consulta: {str(e)}"
        )


# ============================================================
# ENDPOINTS DE RECETAS
# ============================================================

@router.get("/consulta/{consulta_id}/recetas", response_model=List[RecetaResponse])
def obtener_recetas_consulta(
    consulta_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene todas las recetas de una consulta."""
    consulta = uow.consultas.get_by_id(consulta_id)
    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada"
        )
    
    return consulta.recetas


@router.get("/receta/{receta_id}", response_model=RecetaResponse)
def obtener_receta(
    receta_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene una receta específica por ID."""
    receta = uow.recetas.get_by_id(receta_id)
    if not receta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receta con ID {receta_id} no encontrada"
        )
    return receta


@router.post("/receta", response_model=RecetaResponse, status_code=status.HTTP_201_CREATED)
def crear_receta(
    receta_data: RecetaCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Crea una nueva receta para una consulta.
    La receta debe tener al menos un medicamento.
    """
    try:
        # Verificar que la consulta existe
        consulta = uow.consultas.get_by_id(receta_data.id_consulta)
        if not consulta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consulta con ID {receta_data.id_consulta} no encontrada"
            )
        
        # Crear receta
        receta = Receta(
            id_consulta=receta_data.id_consulta,
            fecha_emision=date.today(),
            estado="ACTIVA"
        )
        
        # Agregar items
        for item_data in receta_data.items:
            item = ItemReceta(
                medicamento=item_data.medicamento,
                dosis=item_data.dosis,
                frecuencia=item_data.frecuencia,
                duracion=item_data.duracion,
                indicaciones=item_data.indicaciones
            )
            receta.items.append(item)
        
        uow.recetas.add(receta)
        uow.commit()
        
        # Refrescar para obtener relaciones
        uow.session.refresh(receta)
        return receta
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear receta: {str(e)}"
        )


@router.post("/receta/{receta_id}/anular", response_model=RecetaResponse)
def anular_receta(
    receta_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Anula una receta existente."""
    try:
        receta = uow.recetas.get_by_id(receta_id)
        if not receta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receta con ID {receta_id} no encontrada"
            )
        
        if receta.estado != "ACTIVA":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se pueden anular recetas activas. Estado actual: {receta.estado}"
            )
        
        receta.anular()
        uow.recetas.update(receta)
        uow.commit()
        
        return receta
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al anular receta: {str(e)}"
        )


@router.delete("/receta/{receta_id}", response_model=SuccessResponse)
def eliminar_receta(
    receta_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Realiza soft delete de una receta."""
    try:
        receta = uow.recetas.get_by_id(receta_id)
        if not receta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receta con ID {receta_id} no encontrada"
            )
        
        uow.recetas.delete(receta)
        uow.commit()
        
        return SuccessResponse(message=f"Receta {receta_id} eliminada correctamente")
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar receta: {str(e)}"
        )


# ============================================================
# ENDPOINTS DE BÚSQUEDA Y ESTADÍSTICAS
# ============================================================

@router.get("/buscar/dni/{dni}")
def buscar_historial_por_dni(
    dni: str,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Busca el historial clínico de un paciente por DNI.
    Retorna el historial completo si se encuentra.
    """
    paciente = uow.pacientes.get_by_dni(dni)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró paciente con DNI {dni}"
        )
    
    # Reutilizar la función de obtener historial
    return obtener_historial_paciente(paciente.id, None, None, uow)


@router.get("/estadisticas/paciente/{paciente_id}")
def obtener_estadisticas_paciente(
    paciente_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Obtiene estadísticas del historial clínico de un paciente.
    """
    paciente = uow.pacientes.get_by_id(paciente_id)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con ID {paciente_id} no encontrado"
        )
    
    consultas = uow.consultas.get_por_paciente(paciente_id)
    
    # Calcular estadísticas
    total_consultas = len(consultas)
    total_recetas = sum(len(c.recetas) for c in consultas)
    
    # Especialidades visitadas
    especialidades = set()
    medicos_atendidos = set()
    for c in consultas:
        if c.turno:
            if c.turno.especialidad:
                especialidades.add(c.turno.especialidad.nombre)
            if c.turno.medico:
                medicos_atendidos.add(c.turno.medico.nombre_completo)
    
    # Última consulta
    ultima_consulta = consultas[0] if consultas else None
    
    return {
        "paciente_id": paciente_id,
        "paciente_nombre": paciente.nombre_completo,
        "total_consultas": total_consultas,
        "total_recetas": total_recetas,
        "especialidades_visitadas": list(especialidades),
        "cantidad_especialidades": len(especialidades),
        "medicos_atendidos": list(medicos_atendidos),
        "cantidad_medicos": len(medicos_atendidos),
        "ultima_consulta": {
            "fecha": ultima_consulta.fecha_atencion.isoformat() if ultima_consulta else None,
            "diagnostico": ultima_consulta.diagnostico if ultima_consulta else None,
        } if ultima_consulta else None
    }


# ============================================================
# GENERACIÓN DE PDF DE RECETA
# ============================================================

def generar_firma_hash(nombre_medico: str, matricula: str) -> str:
    """Genera un hash de firma digital a partir del nombre y matrícula del médico."""
    contenido = f"{nombre_medico}|{matricula}|{datetime.now().strftime('%Y%m%d')}"
    return hashlib.sha256(contenido.encode()).hexdigest()[:32].upper()


def crear_pdf_receta(receta, consulta, medico, paciente) -> BytesIO:
    """
    Genera un PDF profesional de la receta médica.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    style_clinica = ParagraphStyle(
        'ClinicaNombre',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        alignment=TA_CENTER,
        spaceAfter=2*mm
    )
    
    style_clinica_info = ParagraphStyle(
        'ClinicaInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER,
        spaceAfter=1*mm
    )
    
    style_titulo_seccion = ParagraphStyle(
        'TituloSeccion',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=8*mm,
        spaceAfter=4*mm
    )
    
    style_normal = ParagraphStyle(
        'NormalCustom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    
    style_medicamento = ParagraphStyle(
        'Medicamento',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        spaceBefore=4*mm,
        spaceAfter=2*mm
    )
    
    style_firma = ParagraphStyle(
        'Firma',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#374151')
    )
    
    # Contenido del PDF
    story = []
    
    # ===== ENCABEZADO DE LA CLÍNICA =====
    story.append(Paragraph(CLINICA_INFO["nombre"], style_clinica))
    story.append(Paragraph(
        f"{CLINICA_INFO['direccion']} - {CLINICA_INFO['ciudad']} ({CLINICA_INFO['codigo_postal']})",
        style_clinica_info
    ))
    story.append(Paragraph(
        f"Tel: {CLINICA_INFO['telefono']} | Email: {CLINICA_INFO['email']}",
        style_clinica_info
    ))
    story.append(Paragraph(
        f"CUIT: {CLINICA_INFO['cuit']} | {CLINICA_INFO['web']}",
        style_clinica_info
    ))
    
    # Línea separadora
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563eb')))
    story.append(Spacer(1, 5*mm))
    
    # ===== TÍTULO RECETA =====
    style_receta_titulo = ParagraphStyle(
        'RecetaTitulo',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER,
        spaceAfter=3*mm
    )
    story.append(Paragraph("RECETA MÉDICA", style_receta_titulo))
    story.append(Paragraph(
        f"<b>Receta N°:</b> {receta.id:06d}",
        ParagraphStyle('NumReceta', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 5*mm))
    
    # ===== DATOS DEL PACIENTE =====
    story.append(Paragraph("DATOS DEL PACIENTE", style_titulo_seccion))
    
    paciente_data = [
        ["Nombre completo:", paciente.nombre_completo if paciente else "N/A"],
        ["DNI:", paciente.dni if paciente else "N/A"],
        ["Obra Social:", paciente.obra_social if paciente and paciente.obra_social else "Particular"],
    ]
    
    tabla_paciente = Table(paciente_data, colWidths=[4*cm, 12*cm])
    tabla_paciente.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#475569')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tabla_paciente)
    
    # ===== MEDICAMENTOS RECETADOS =====
    story.append(Paragraph("MEDICAMENTOS", style_titulo_seccion))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
    
    for i, item in enumerate(receta.items, 1):
        story.append(Paragraph(f"<b>{i}. {item.medicamento.upper()}</b>", style_medicamento))
        
        detalles = []
        if item.dosis:
            detalles.append(f"<b>Dosis:</b> {item.dosis}")
        if item.frecuencia:
            detalles.append(f"<b>Frecuencia:</b> {item.frecuencia}")
        if item.duracion:
            detalles.append(f"<b>Duración:</b> {item.duracion}")
        
        if detalles:
            story.append(Paragraph(" | ".join(detalles), style_normal))
        
        if item.indicaciones:
            story.append(Paragraph(f"<i>Indicaciones: {item.indicaciones}</i>", style_normal))
        
        story.append(Spacer(1, 2*mm))
    
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
    
    # ===== DATOS DE LA RECETA =====
    story.append(Spacer(1, 5*mm))
    fecha_emision = receta.fecha_emision.strftime('%d/%m/%Y') if receta.fecha_emision else "N/A"
    story.append(Paragraph(f"<b>Fecha de emisión:</b> {fecha_emision}", style_normal))
    story.append(Paragraph(f"<b>Estado:</b> {receta.estado}", style_normal))
    
    # ===== FIRMA DEL MÉDICO =====
    story.append(Spacer(1, 15*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563eb')))
    story.append(Spacer(1, 8*mm))
    
    # Generar firma hash
    firma_hash = generar_firma_hash(
        medico.nombre_completo if medico else "N/A",
        medico.matricula if medico else "000000"
    )
    
    # Cuadro de firma
    firma_content = f"""
    <b>{medico.nombre_completo if medico else 'N/A'}</b><br/>
    Matrícula: {medico.matricula if medico else 'N/A'}<br/>
    <br/>
    <font size="8">Firma Digital: {firma_hash}</font>
    """
    
    story.append(Paragraph(firma_content, style_firma))
    story.append(Spacer(1, 5*mm))
    
    # Línea para firma manuscrita
    story.append(Paragraph("_" * 40, style_firma))
    story.append(Paragraph("Firma y Sello del Médico", style_firma))
    
    # ===== PIE DE PÁGINA =====
    story.append(Spacer(1, 10*mm))
    style_pie = ParagraphStyle(
        'PiePagina',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#94a3b8'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        f"Documento generado electrónicamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
        style_pie
    ))
    story.append(Paragraph(
        "Este documento es válido como receta médica según normativa vigente.",
        style_pie
    ))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


@router.get("/receta/{receta_id}/pdf")
def descargar_receta_pdf(
    receta_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Genera y descarga la receta en formato PDF.
    Incluye datos de la clínica, paciente, medicamentos y firma digital del médico.
    """
    # Obtener receta
    receta = uow.recetas.get_by_id(receta_id)
    if not receta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receta con ID {receta_id} no encontrada"
        )
    
    # Obtener consulta y datos relacionados
    consulta = receta.consulta
    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la consulta asociada a la receta"
        )
    
    turno = consulta.turno
    medico = turno.medico if turno else None
    paciente = turno.paciente if turno else None
    
    # Generar PDF
    pdf_buffer = crear_pdf_receta(receta, consulta, medico, paciente)
    
    # Nombre del archivo
    fecha_str = receta.fecha_emision.strftime('%Y%m%d') if receta.fecha_emision else 'sin_fecha'
    filename = f"receta_{receta_id}_{fecha_str}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
