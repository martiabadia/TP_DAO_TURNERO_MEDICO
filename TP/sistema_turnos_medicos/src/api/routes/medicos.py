"""
Rutas para gestión de médicos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas import MedicoResponse, MedicoListResponse, DisponibilidadResponse, MedicoCreate, MedicoUpdate
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
