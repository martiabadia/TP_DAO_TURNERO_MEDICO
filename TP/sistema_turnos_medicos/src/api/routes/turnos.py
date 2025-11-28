"""
Rutas para gestión de turnos.
Endpoint principal del sistema.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from src.api.schemas import (
    TurnoResponse, TurnoCreate, TurnoUpdate, 
    SuccessResponse, HorarioDisponibleResponse
)
from src.api.dependencies import get_uow
from src.repositories.unit_of_work import UnitOfWork
from src.services.turno_service import TurnoService
from src.utils.exceptions import *

router = APIRouter(prefix="/turnos", tags=["Turnos"])


class MisTurnosResponse(BaseModel):
    turnos: List[TurnoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/", response_model=List[TurnoResponse])
def listar_turnos(
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    id_paciente: int = None,
    id_medico: int = None,
    codigo_estado: str = None,
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Lista turnos con filtros opcionales.
    Útil para ver la agenda completa o filtrada.
    """
    from sqlalchemy.orm import joinedload
    from src.domain.turno import Turno
    from src.domain.medico import Medico
    
    # Aplicar filtros básicos con eager loading
    query = uow.session.query(Turno).options(
        joinedload(Turno.paciente),
        joinedload(Turno.medico).joinedload(Medico.especialidades),
        joinedload(Turno.especialidad),
        joinedload(Turno.estado)
    )
    
    if fecha_desde:
        query = query.filter(Turno.fecha_hora >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Turno.fecha_hora <= fecha_hasta)
    if id_paciente:
        query = query.filter(Turno.id_paciente == id_paciente)
    if id_medico:
        query = query.filter(Turno.id_medico == id_medico)
    if codigo_estado:
        estado = uow.estados_turno.get_by_codigo(codigo_estado)
        if estado:
            query = query.filter(Turno.id_estado == estado.id)
    
    query = query.filter(Turno.activo == True)
    turnos = query.offset(skip).limit(limit).all()
    
    return turnos


@router.get("/paciente/{paciente_id}", response_model=List[TurnoResponse])
def obtener_turnos_paciente(
    paciente_id: int,
    solo_futuros: bool = True,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene todos los turnos de un paciente."""
    paciente = uow.pacientes.get_by_id(paciente_id)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con ID {paciente_id} no encontrado"
        )
    
    if solo_futuros:
        turnos = uow.turnos.get_turnos_futuros_paciente(paciente_id)
    else:
        turnos = uow.turnos.get_por_paciente(paciente_id)
    
    return turnos


@router.get("/medico/{medico_id}", response_model=List[TurnoResponse])
def obtener_turnos_medico(
    medico_id: int,
    fecha: date = None,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene todos los turnos de un médico, opcionalmente para una fecha específica."""
    from sqlalchemy.orm import joinedload
    from src.domain.turno import Turno
    from src.domain.medico import Medico
    from src.domain.estado_turno import EstadoTurno
    
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Query con eager loading de relaciones, excluyendo turnos cancelados
    query = uow.session.query(Turno).join(Turno.estado).filter(
        Turno.id_medico == medico_id,
        Turno.activo == True,
        EstadoTurno.codigo != 'CANC'
    ).options(
        joinedload(Turno.paciente),
        joinedload(Turno.medico).joinedload(Medico.especialidades),
        joinedload(Turno.especialidad),
        joinedload(Turno.estado)
    )
    
    if fecha:
        # Filtrar por fecha específica
        fecha_inicio = datetime.combine(fecha, datetime.min.time())
        fecha_fin = datetime.combine(fecha, datetime.max.time())
        query = query.filter(
            Turno.fecha_hora >= fecha_inicio,
            Turno.fecha_hora <= fecha_fin
        )
    
    turnos = query.all()
    return turnos


@router.get("/disponibles", response_model=List[HorarioDisponibleResponse])
def obtener_horarios_disponibles(
    id_medico: int = Query(..., description="ID del médico"),
    fecha: date = Query(..., description="Fecha para buscar disponibilidad"),
    duracion: int = Query(30, description="Duración del turno en minutos"),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Obtiene los horarios disponibles de un médico para una fecha específica.
    Este es el endpoint clave para la reserva eficiente de turnos.
    """
    # Validar que la fecha no sea en el pasado
    if fecha < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden solicitar turnos en fechas pasadas"
        )
    
    try:
        turno_service = TurnoService(uow)
        horarios = turno_service.obtener_horarios_disponibles(id_medico, fecha, duracion)
        
        return [
            HorarioDisponibleResponse(fecha_hora=h, disponible=True)
            for h in horarios
        ]
        
    except DisponibilidadException as e:
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener horarios: {str(e)}"
        )


@router.get("/calendario/{id_medico}")
def obtener_calendario_disponibilidad(
    id_medico: int,
    dias: int = Query(14, description="Cantidad de días a mostrar desde hoy"),
    duracion: int = Query(30, description="Duración del turno en minutos"),
    uow: UnitOfWork = Depends(get_uow)
) -> Dict[str, Dict]:
    """
    Obtiene un calendario con todos los horarios disponibles del médico
    para los próximos N días, indicando cuáles están bloqueados.
    Formato: {fecha: {"horarios": [horarios], "bloqueado": bool, "motivo_bloqueo": str}}
    """
    try:
        turno_service = TurnoService(uow)
        calendario = {}
        fecha_actual = date.today()
        
        # Obtener bloqueos del médico en el rango de fechas
        fecha_fin = fecha_actual + timedelta(days=dias)
        bloqueos = uow.bloqueos.get_por_medico(
            medico_id=id_medico,
            fecha_desde=fecha_actual,
            fecha_hasta=fecha_fin
        )
        
        for i in range(dias):
            fecha = fecha_actual + timedelta(days=i)
            fecha_str = fecha.isoformat()
            
            # Verificar si hay bloqueo para esta fecha
            bloqueado = False
            motivo_bloqueo = None
            
            for bloqueo in bloqueos:
                # Verificar si la fecha cae dentro del bloqueo
                if bloqueo.inicio.date() <= fecha <= bloqueo.fin.date():
                    bloqueado = True
                    motivo_bloqueo = bloqueo.motivo or "Médico no disponible"
                    break
            
            try:
                if bloqueado:
                    # Si está bloqueado, no mostrar horarios pero indicar el bloqueo
                    calendario[fecha_str] = {
                        "horarios": [],
                        "bloqueado": True,
                        "motivo_bloqueo": motivo_bloqueo
                    }
                else:
                    horarios = turno_service.obtener_horarios_disponibles(id_medico, fecha, duracion)
                    if horarios:
                        # Convertir a string ISO format
                        calendario[fecha_str] = {
                            "horarios": [h.isoformat() for h in horarios],
                            "bloqueado": False,
                            "motivo_bloqueo": None
                        }
            except DisponibilidadException:
                # El médico no atiende ese día
                continue
        
        return calendario
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener calendario: {str(e)}"
        )


@router.get("/{turno_id}", response_model=TurnoResponse)
def obtener_turno(
    turno_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene un turno específico por ID."""
    turno = uow.turnos.get_by_id(turno_id)
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Turno con ID {turno_id} no encontrado"
        )
    return turno


@router.post("/", response_model=TurnoResponse, status_code=status.HTTP_201_CREATED)
def crear_turno(
    turno_data: TurnoCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Crea un nuevo turno.
    Valida disponibilidad, solapamiento y todas las reglas de negocio.
    """
    try:
        turno_service = TurnoService(uow)
        
        turno = turno_service.crear_turno(
            paciente_id=turno_data.id_paciente,
            medico_id=turno_data.id_medico,
            especialidad_id=turno_data.id_especialidad,
            fecha_hora=turno_data.fecha_hora,
            duracion_minutos=turno_data.duracion_minutos,
            observaciones=turno_data.motivo
        )
        
        uow.commit()
        
        # Recargar el turno con todas las relaciones para la respuesta
        turno_completo = uow.turnos.get_by_id_completo(turno.id)
        return turno_completo
        
    except (
        DisponibilidadException,
        TurnoSolapamientoException,
        ValidationException,
        EntityNotFoundException
    ) as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear turno: {str(e)}"
        )


@router.patch("/{turno_id}", response_model=TurnoResponse)
def actualizar_turno(
    turno_id: int,
    turno_update: TurnoUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Actualiza el motivo o estado de un turno."""
    try:
        turno = uow.turnos.get_by_id(turno_id)
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Turno con ID {turno_id} no encontrado"
            )
        
        if turno_update.motivo is not None:
            turno.motivo = turno_update.motivo
        
        if turno_update.codigo_estado is not None:
            estado = uow.estados_turno.get_by_codigo(turno_update.codigo_estado)
            if not estado:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estado '{turno_update.codigo_estado}' no válido"
                )
            turno.id_estado = estado.id
        
        uow.commit()
        return turno
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar turno: {str(e)}"
        )


@router.post("/{turno_id}/confirmar", response_model=SuccessResponse)
def confirmar_turno(
    turno_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Confirma un turno pendiente."""
    try:
        turno = uow.turnos.get_by_id(turno_id)
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Turno con ID {turno_id} no encontrado"
            )
        
        # Obtener estado CONFIRMADO
        estado_conf = uow.estados_turno.get_by_codigo("CONF")
        if not estado_conf:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Estado CONFIRMADO no encontrado en el sistema"
            )
        
        turno.id_estado = estado_conf.id
        uow.commit()
        
        return SuccessResponse(message="Turno confirmado exitosamente")
        
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar turno: {str(e)}"
        )


@router.post("/{turno_id}/cancelar", response_model=SuccessResponse)
def cancelar_turno(
    turno_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Cancela un turno."""
    try:
        turno = uow.turnos.get_by_id(turno_id)
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Turno con ID {turno_id} no encontrado"
            )
        
        # Obtener estado CANCELADO
        estado_canc = uow.estados_turno.get_by_codigo("CANC")
        if not estado_canc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Estado CANCELADO no encontrado en el sistema"
            )
        
        turno.id_estado = estado_canc.id
        uow.commit()
        
        return SuccessResponse(message="Turno cancelado exitosamente")
        
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar turno: {str(e)}"
        )


@router.get("/mis-turnos/listar", response_model=MisTurnosResponse)
def listar_mis_turnos(
    dni: str = None,
    estado: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Lista todos los turnos con paginación.
    Si se proporciona DNI, filtra por paciente.
    Si se proporciona estado, filtra por estado del turno.
    """
    from sqlalchemy.orm import joinedload
    from src.domain.turno import Turno
    from src.domain.medico import Medico
    
    # Query base con eager loading
    query = uow.session.query(Turno).options(
        joinedload(Turno.paciente),
        joinedload(Turno.medico).joinedload(Medico.especialidades),
        joinedload(Turno.especialidad),
        joinedload(Turno.estado)
    )
    
    # Filtrar solo turnos activos
    query = query.filter(Turno.activo == True)
    
    # Filtrar por estado si se proporciona
    if estado:
        estado_obj = uow.estados_turno.get_by_codigo(estado)
        if estado_obj:
            query = query.filter(Turno.id_estado == estado_obj.id)
    
    # Filtrar por DNI si se proporciona
    if dni:
        paciente = uow.pacientes.get_by_dni(dni)
        if paciente:
            query = query.filter(Turno.id_paciente == paciente.id)
        else:
            # Si el DNI no existe, retornar vacío
            return MisTurnosResponse(
                turnos=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )
    
    # Ordenar por fecha de creación descendente (más recientes primero)
    query = query.order_by(Turno.fecha_creacion.desc())
    
    # Contar total
    total = query.count()
    
    # Aplicar paginación
    offset = (page - 1) * page_size
    turnos = query.offset(offset).limit(page_size).all()
    
    # Calcular total de páginas
    total_pages = (total + page_size - 1) // page_size
    
    # Convertir a TurnoResponse
    turnos_response = [TurnoResponse.model_validate(turno) for turno in turnos]
    
    return MisTurnosResponse(
        turnos=turnos_response,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.delete("/{turno_id}", response_model=SuccessResponse)
def eliminar_turno(
    turno_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Realiza soft delete de un turno."""
    try:
        turno = uow.turnos.get_by_id(turno_id)
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Turno con ID {turno_id} no encontrado"
            )
        
        uow.turnos.delete(turno_id)
        uow.commit()
        
        return SuccessResponse(message="Turno eliminado correctamente")
        
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar turno: {str(e)}"
        )
