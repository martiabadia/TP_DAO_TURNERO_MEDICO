"""
Rutas para gestión de pacientes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas import PacienteResponse, PacienteCreate, PacienteUpdate, SuccessResponse
from src.api.dependencies import get_uow
from src.repositories.unit_of_work import UnitOfWork
from src.domain.paciente import Paciente

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.get("/", response_model=List[PacienteResponse])
def listar_pacientes(
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow)
):
    """Lista todos los pacientes activos."""
    pacientes = uow.pacientes.get_all(skip=skip, limit=limit)
    return pacientes


@router.get("/{paciente_id}", response_model=PacienteResponse)
def obtener_paciente(
    paciente_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene un paciente por ID."""
    paciente = uow.pacientes.get_by_id(paciente_id)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con ID {paciente_id} no encontrado"
        )
    return paciente


@router.get("/dni/{dni}", response_model=PacienteResponse)
def obtener_paciente_por_dni(
    dni: str,
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene un paciente por DNI."""
    paciente = uow.pacientes.get_by_dni(dni)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con DNI {dni} no encontrado"
        )
    return paciente


@router.post("/", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def crear_paciente(
    paciente_data: PacienteCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Crea un nuevo paciente."""
    try:
        # Verificar si ya existe
        existing = uow.pacientes.get_by_dni(paciente_data.dni)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un paciente con DNI {paciente_data.dni}"
            )
        
        # Crear paciente
        paciente = Paciente(
            dni=paciente_data.dni,
            nombre=paciente_data.nombre,
            apellido=paciente_data.apellido,
            email=paciente_data.email,
            telefono=paciente_data.telefono,
            fecha_nacimiento=paciente_data.fecha_nacimiento,
            direccion=paciente_data.direccion,
            obra_social=paciente_data.obra_social,
            numero_afiliado=paciente_data.numero_afiliado
        )
        
        uow.pacientes.add(paciente)
        uow.commit()
        
        return paciente
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear paciente: {str(e)}"
        )


@router.put("/{paciente_id}", response_model=PacienteResponse)
def actualizar_paciente(
    paciente_id: int,
    paciente_data: PacienteUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Actualiza los datos de un paciente."""
    try:
        paciente = uow.pacientes.get_by_id(paciente_id)
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con ID {paciente_id} no encontrado"
            )
        
        # Verificar unicidad de DNI si se está actualizando
        if paciente_data.dni and paciente_data.dni != paciente.dni:
            if uow.pacientes.exists_dni(paciente_data.dni, exclude_id=paciente_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un paciente con DNI {paciente_data.dni}"
                )
        
        # Verificar unicidad de email si se está actualizando
        if paciente_data.email and paciente_data.email != paciente.email:
            if uow.pacientes.exists_email(paciente_data.email, exclude_id=paciente_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un paciente con email {paciente_data.email}"
                )
        
        # Actualizar campos
        if paciente_data.dni:
            paciente.dni = paciente_data.dni
        if paciente_data.nombre:
            paciente.nombre = paciente_data.nombre
        if paciente_data.apellido:
            paciente.apellido = paciente_data.apellido
        if paciente_data.email:
            paciente.email = paciente_data.email
        if paciente_data.telefono:
            paciente.telefono = paciente_data.telefono
        if paciente_data.fecha_nacimiento:
            paciente.fecha_nacimiento = paciente_data.fecha_nacimiento
        if paciente_data.direccion:
            paciente.direccion = paciente_data.direccion
        if paciente_data.obra_social is not None:
            paciente.obra_social = paciente_data.obra_social
        if paciente_data.numero_afiliado is not None:
            paciente.numero_afiliado = paciente_data.numero_afiliado
        
        uow.pacientes.update(paciente)
        uow.commit()
        
        return paciente
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar paciente: {str(e)}"
        )


@router.delete("/{paciente_id}", response_model=SuccessResponse)
def eliminar_paciente(
    paciente_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    """Realiza soft delete de un paciente."""
    try:
        paciente = uow.pacientes.get_by_id(paciente_id)
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con ID {paciente_id} no encontrado"
            )
        
        uow.pacientes.delete(paciente)
        uow.commit()
        
        return SuccessResponse(
            message=f"Paciente {paciente.nombre} {paciente.apellido} eliminado correctamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar paciente: {str(e)}"
        )
