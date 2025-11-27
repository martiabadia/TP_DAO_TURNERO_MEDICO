"""
Rutas para gestión de médicos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas import (
    MedicoResponse, MedicoListResponse, DisponibilidadResponse, 
    MedicoCreate, MedicoUpdate, DisponibilidadCreate, DisponibilidadUpdate,
    BloqueoResponse, BloqueoCreate, BloqueoUpdate
)
from src.api.dependencies import get_uow
from src.repositories.unit_of_work import UnitOfWork

router = APIRouter(prefix="/medicos", tags=["Médicos"])


@router.get("/", response_model=List[MedicoListResponse])
def listar_medicos(
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow)
):
    """Lista todos los médicos activos."""
    medicos = uow.medicos.get_all(skip=skip, limit=limit)
    return [
        MedicoListResponse(
            id=m.id,
            matricula=m.matricula,
            nombre=m.nombre,
            apellido=m.apellido,
            nombre_completo=m.nombre_completo,
            email=m.email,
            especialidades=m.especialidades
        )
        for m in medicos
    ]


@router.get("/{medico_id}", response_model=MedicoResponse)
def obtener_medico(
    medico_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene un médico por ID con sus especialidades."""
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    return medico


@router.get("/especialidad/{especialidad_id}", response_model=List[MedicoListResponse])
def listar_medicos_por_especialidad(
    especialidad_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Lista médicos que tienen una especialidad específica."""
    medicos = uow.medicos.get_por_especialidad(especialidad_id)
    return [
        MedicoListResponse(
            id=m.id,
            matricula=m.matricula,
            nombre=m.nombre,
            apellido=m.apellido,
            nombre_completo=m.nombre_completo,
            email=m.email,
            especialidades=m.especialidades
        )
        for m in medicos
    ]


@router.get("/{medico_id}/disponibilidades", response_model=List[DisponibilidadResponse])
def obtener_disponibilidades_medico(
    medico_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene las disponibilidades semanales de un médico."""
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    disponibilidades = uow.disponibilidades.get_por_medico(medico_id)
    return disponibilidades


@router.post("/", response_model=MedicoResponse, status_code=status.HTTP_201_CREATED)
def crear_medico(
    medico_data: MedicoCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Registra un nuevo médico.
    Valida unicidad de matrícula, DNI y email.
    """
    # Validaciones de unicidad
    if uow.medicos.exists_matricula(medico_data.matricula):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un médico con esa matrícula"
        )
    
    if uow.medicos.exists_dni(medico_data.dni):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un médico con ese DNI"
        )
        
    if uow.medicos.exists_email(medico_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un médico con ese email"
        )
    
    # Validar especialidades
    especialidades = []
    for esp_id in medico_data.especialidades_ids:
        esp = uow.especialidades.get_by_id(esp_id)
        if not esp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Especialidad con ID {esp_id} no encontrada"
            )
        especialidades.append(esp)
    
    # Crear médico
    from src.domain.medico import Medico
    nuevo_medico = Medico(
        matricula=medico_data.matricula,
        nombre=medico_data.nombre,
        apellido=medico_data.apellido,
        dni=medico_data.dni,
        email=medico_data.email,
        telefono=medico_data.telefono,
        direccion=medico_data.direccion,
        genero=medico_data.genero,
        especialidades=especialidades,
        activo=True
    )
    
    uow.medicos.add(nuevo_medico)
    uow.commit()
    
    return nuevo_medico


@router.put("/{medico_id}", response_model=MedicoResponse)
def actualizar_medico(
    medico_id: int,
    medico_update: MedicoUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Actualiza datos de un médico.
    La matrícula NO se puede modificar.
    """
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Validar unicidad si cambian email
    if medico_update.email and medico_update.email != medico.email:
        if uow.medicos.exists_email(medico_update.email, exclude_id=medico_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro médico"
            )
        medico.email = medico_update.email
        
    # Actualizar campos simples
    if medico_update.nombre:
        medico.nombre = medico_update.nombre
    if medico_update.apellido:
        medico.apellido = medico_update.apellido
    if medico_update.telefono:
        medico.telefono = medico_update.telefono
    if medico_update.direccion:
        medico.direccion = medico_update.direccion
    if medico_update.genero:
        medico.genero = medico_update.genero
        
    # Actualizar especialidades
    if medico_update.especialidades_ids is not None:
        especialidades = []
        for esp_id in medico_update.especialidades_ids:
            esp = uow.especialidades.get_by_id(esp_id)
            if not esp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Especialidad con ID {esp_id} no encontrada"
                )
            especialidades.append(esp)
        medico.especialidades = especialidades
    
    uow.commit()
    return medico


@router.delete("/{medico_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_medico(
    medico_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Baja lógica de un médico.
    No permite baja si tiene turnos pendientes.
    """
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Validar turnos pendientes
    if uow.medicos.get_con_turnos_pendientes(medico_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el médico porque tiene turnos pendientes"
        )
    
    uow.medicos.delete(medico)
    uow.commit()


# ============================================================
# ENDPOINTS PARA DISPONIBILIDADES (HORARIOS)
# ============================================================

@router.post("/{medico_id}/disponibilidades", response_model=DisponibilidadResponse, status_code=status.HTTP_201_CREATED)
def crear_disponibilidad(
    medico_id: int,
    disponibilidad: DisponibilidadCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Crea una nueva disponibilidad horaria para un médico.
    Valida que no haya solapamiento con horarios existentes.
    """
    # Verificar que el médico existe
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Verificar solapamiento de horarios
    if uow.disponibilidades.verificar_solapamiento(
        medico_id=medico_id,
        dia_semana=disponibilidad.dia_semana,
        hora_desde=disponibilidad.hora_desde,
        hora_hasta=disponibilidad.hora_hasta
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un horario que se solapa con el ingresado para ese día"
        )
    
    # Crear disponibilidad
    from src.domain.disponibilidad import DisponibilidadMedico
    nueva_disponibilidad = DisponibilidadMedico(
        id_medico=medico_id,
        dia_semana=disponibilidad.dia_semana,
        hora_desde=disponibilidad.hora_desde,
        hora_hasta=disponibilidad.hora_hasta,
        duracion_slot=disponibilidad.duracion_slot,
        activo=True
    )
    
    uow.disponibilidades.add(nueva_disponibilidad)
    uow.commit()
    
    return nueva_disponibilidad


@router.put("/{medico_id}/disponibilidades/{disponibilidad_id}", response_model=DisponibilidadResponse)
def actualizar_disponibilidad(
    medico_id: int,
    disponibilidad_id: int,
    disponibilidad_update: DisponibilidadUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Actualiza una disponibilidad existente.
    Valida que no haya solapamiento si se modifican los horarios.
    """
    # Verificar que el médico existe
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Obtener disponibilidad
    disponibilidad = uow.disponibilidades.get_by_id(disponibilidad_id)
    if not disponibilidad or disponibilidad.id_medico != medico_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disponibilidad con ID {disponibilidad_id} no encontrada para este médico"
        )
    
    # Determinar horarios finales
    hora_desde_final = disponibilidad_update.hora_desde or disponibilidad.hora_desde
    hora_hasta_final = disponibilidad_update.hora_hasta or disponibilidad.hora_hasta
    
    # Validar que hora_hasta sea mayor a hora_desde
    if hora_desde_final >= hora_hasta_final:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La hora de fin debe ser posterior a la hora de inicio"
        )
    
    # Verificar solapamiento si cambian los horarios
    if disponibilidad_update.hora_desde or disponibilidad_update.hora_hasta:
        if uow.disponibilidades.verificar_solapamiento(
            medico_id=medico_id,
            dia_semana=disponibilidad.dia_semana,
            hora_desde=hora_desde_final,
            hora_hasta=hora_hasta_final,
            exclude_id=disponibilidad_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El horario modificado se solapa con otro horario existente"
            )
    
    # Actualizar campos
    if disponibilidad_update.hora_desde:
        disponibilidad.hora_desde = disponibilidad_update.hora_desde
    if disponibilidad_update.hora_hasta:
        disponibilidad.hora_hasta = disponibilidad_update.hora_hasta
    if disponibilidad_update.duracion_slot:
        disponibilidad.duracion_slot = disponibilidad_update.duracion_slot
    
    uow.commit()
    return disponibilidad


@router.delete("/{medico_id}/disponibilidades/{disponibilidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_disponibilidad(
    medico_id: int,
    disponibilidad_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Elimina (baja lógica) una disponibilidad de un médico.
    """
    # Verificar que el médico existe
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Obtener disponibilidad
    disponibilidad = uow.disponibilidades.get_by_id(disponibilidad_id)
    if not disponibilidad or disponibilidad.id_medico != medico_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disponibilidad con ID {disponibilidad_id} no encontrada para este médico"
        )
    
    uow.disponibilidades.delete(disponibilidad)
    uow.commit()


# ============================================================
# ENDPOINTS PARA BLOQUEOS (VACACIONES, AUSENCIAS)
# ============================================================

@router.get("/{medico_id}/bloqueos", response_model=List[BloqueoResponse])
def obtener_bloqueos_medico(
    medico_id: int,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Obtiene los bloqueos de un médico en un rango de fechas.
    Si no se especifican fechas, obtiene todos los bloqueos activos futuros.
    """
    from datetime import datetime, date
    
    # Verificar que el médico existe
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Convertir fechas si se proporcionan
    fecha_desde_obj = None
    fecha_hasta_obj = None
    
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha_desde inválido. Use YYYY-MM-DD"
            )
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha_hasta inválido. Use YYYY-MM-DD"
            )
    
    # Si no se especifican fechas, usar desde hoy en adelante
    if not fecha_desde_obj:
        fecha_desde_obj = date.today()
    
    bloqueos = uow.bloqueos.get_por_medico(
        medico_id=medico_id,
        fecha_desde=fecha_desde_obj,
        fecha_hasta=fecha_hasta_obj
    )
    
    return bloqueos


@router.post("/{medico_id}/bloqueos", response_model=BloqueoResponse, status_code=status.HTTP_201_CREATED)
def crear_bloqueo(
    medico_id: int,
    bloqueo: BloqueoCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Crea un bloqueo para un médico (vacaciones, capacitación, etc.).
    El bloqueo es por día completo (00:00:00 a 23:59:59).
    Valida que no haya turnos ya asignados en ese período.
    """
    from datetime import datetime, time as dt_time
    
    # Verificar que el médico existe
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Convertir fechas a datetime (día completo)
    inicio_dt = datetime.combine(bloqueo.inicio, dt_time.min)  # 00:00:00
    fin_dt = datetime.combine(bloqueo.fin, dt_time(23, 59, 59))  # 23:59:59
    
    # Verificar si ya está bloqueado en ese período
    if uow.bloqueos.verificar_bloqueado(
        medico_id=medico_id,
        fecha_hora_inicio=inicio_dt,
        fecha_hora_fin=fin_dt
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un bloqueo que se solapa con el período indicado"
        )
    
    # Verificar si hay turnos asignados en ese período
    turnos_afectados = uow.turnos.get_por_medico(
        medico_id=medico_id,
        fecha_desde=bloqueo.inicio,
        fecha_hasta=bloqueo.fin
    )
    
    # Filtrar turnos confirmados
    turnos_conflicto = [
        t for t in turnos_afectados 
        if t.estado.codigo in ['PENDIENTE', 'CONFIRMADO']
    ]
    
    if turnos_conflicto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Existen {len(turnos_conflicto)} turno(s) confirmado(s) en ese período. Debe cancelarlos primero."
        )
    
    # Crear bloqueo
    from src.domain.disponibilidad import BloqueoMedico
    nuevo_bloqueo = BloqueoMedico(
        id_medico=medico_id,
        inicio=inicio_dt,
        fin=fin_dt,
        motivo=bloqueo.motivo,
        activo=True
    )
    
    uow.bloqueos.add(nuevo_bloqueo)
    uow.commit()
    
    return nuevo_bloqueo


@router.put("/{medico_id}/bloqueos/{bloqueo_id}", response_model=BloqueoResponse)
def actualizar_bloqueo(
    medico_id: int,
    bloqueo_id: int,
    bloqueo_update: BloqueoUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Actualiza un bloqueo existente.
    El bloqueo es por día completo (00:00:00 a 23:59:59).
    Valida que no afecte turnos ya asignados si se modifican las fechas.
    """
    from datetime import datetime, time as dt_time
    
    # Verificar que el médico existe
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Obtener bloqueo
    bloqueo = uow.bloqueos.get_by_id(bloqueo_id)
    if not bloqueo or bloqueo.id_medico != medico_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bloqueo con ID {bloqueo_id} no encontrado para este médico"
        )
    
    # Convertir fechas actuales (datetime) a date para comparación
    fecha_inicio_actual = bloqueo.inicio.date()
    fecha_fin_actual = bloqueo.fin.date()
    
    # Determinar fechas finales
    inicio_fecha = bloqueo_update.inicio if bloqueo_update.inicio else fecha_inicio_actual
    fin_fecha = bloqueo_update.fin if bloqueo_update.fin else fecha_fin_actual
    
    # Validar que fin sea mayor o igual a inicio
    if inicio_fecha > fin_fecha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior o igual a la fecha de inicio"
        )
    
    # Convertir a datetime
    inicio_dt = datetime.combine(inicio_fecha, dt_time.min)
    fin_dt = datetime.combine(fin_fecha, dt_time(23, 59, 59))
    
    # Si se modifican fechas, verificar turnos afectados
    if bloqueo_update.inicio or bloqueo_update.fin:
        turnos_afectados = uow.turnos.get_por_medico(
            medico_id=medico_id,
            fecha_desde=inicio_fecha,
            fecha_hasta=fin_fecha
        )
        
        turnos_conflicto = [
            t for t in turnos_afectados 
            if t.estado.codigo in ['PENDIENTE', 'CONFIRMADO']
        ]
        
        if turnos_conflicto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Existen {len(turnos_conflicto)} turno(s) confirmado(s) en el nuevo período"
            )
    
    # Actualizar campos
    if bloqueo_update.inicio:
        bloqueo.inicio = inicio_dt
    if bloqueo_update.fin:
        bloqueo.fin = fin_dt
    if bloqueo_update.motivo is not None:
        bloqueo.motivo = bloqueo_update.motivo
    
    uow.commit()
    return bloqueo


@router.delete("/{medico_id}/bloqueos/{bloqueo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_bloqueo(
    medico_id: int,
    bloqueo_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Elimina (baja lógica) un bloqueo de un médico.
    """
    # Verificar que el médico existe
    medico = uow.medicos.get_by_id(medico_id)
    if not medico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Médico con ID {medico_id} no encontrado"
        )
    
    # Obtener bloqueo
    bloqueo = uow.bloqueos.get_by_id(bloqueo_id)
    if not bloqueo or bloqueo.id_medico != medico_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bloqueo con ID {bloqueo_id} no encontrado para este médico"
        )
    
    uow.bloqueos.delete(bloqueo)
    uow.commit()
