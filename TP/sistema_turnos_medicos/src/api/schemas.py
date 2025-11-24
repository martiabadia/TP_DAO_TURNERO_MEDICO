"""
Esquemas Pydantic para la API REST.
Define los modelos de entrada/salida de datos.
"""
from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================
# ESQUEMAS DE RESPUESTA
# ============================================================

class EspecialidadResponse(BaseModel):
    """Esquema de respuesta para especialidad."""
    id: int
    nombre: str
    descripcion: Optional[str] = None
    
    class Config:
        from_attributes = True


class MedicoResponse(BaseModel):
    """Esquema de respuesta para médico."""
    id: int
    matricula: str
    nombre: str
    apellido: str
    especialidades: List[EspecialidadResponse] = []
    
    class Config:
        from_attributes = True


class MedicoListResponse(BaseModel):
    """Esquema simplificado para listar médicos."""
    id: int
    matricula: str
    nombre: str
    apellido: str
    nombre_completo: str
    especialidades: List[EspecialidadResponse] = []
    
    class Config:
        from_attributes = True


class PacienteResponse(BaseModel):
    """Esquema de respuesta para paciente."""
    id: int
    dni: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    fecha_nacimiento: date
    
    class Config:
        from_attributes = True


class EstadoTurnoResponse(BaseModel):
    """Esquema de respuesta para estado de turno."""
    id: int
    codigo: str
    descripcion: str
    
    class Config:
        from_attributes = True


class TurnoResponse(BaseModel):
    """Esquema de respuesta para turno."""
    id: int
    fecha_hora: datetime
    duracion_minutos: int
    motivo: Optional[str] = None
    paciente: PacienteResponse
    medico: MedicoListResponse
    especialidad: EspecialidadResponse
    estado: EstadoTurnoResponse
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


class DisponibilidadResponse(BaseModel):
    """Esquema de respuesta para disponibilidad."""
    id: int
    dia_semana: int
    hora_desde: time
    hora_hasta: time
    duracion_slot: int
    
    class Config:
        from_attributes = True


class HorarioDisponibleResponse(BaseModel):
    """Esquema de respuesta para horarios disponibles."""
    fecha_hora: datetime
    disponible: bool


# ============================================================
# ESQUEMAS DE SOLICITUD
# ============================================================

class MedicoCreate(BaseModel):
    """Esquema para crear un médico."""
    matricula: str = Field(..., min_length=4, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=80)
    apellido: str = Field(..., min_length=2, max_length=80)
    dni: str = Field(..., min_length=7, max_length=20)
    email: EmailStr
    telefono: str = Field(..., min_length=8, max_length=30)
    direccion: Optional[str] = Field(None, max_length=200)
    genero: Optional[str] = Field(None, max_length=20)
    especialidades_ids: List[int] = Field(..., min_length=1)


class MedicoUpdate(BaseModel):
    """Esquema para actualizar un médico."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=80)
    apellido: Optional[str] = Field(None, min_length=2, max_length=80)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=8, max_length=30)
    direccion: Optional[str] = Field(None, max_length=200)
    genero: Optional[str] = Field(None, max_length=20)
    especialidades_ids: Optional[List[int]] = None

class PacienteCreate(BaseModel):
    """Esquema para crear un paciente."""
    dni: str = Field(..., min_length=7, max_length=10)
    nombre: str = Field(..., min_length=2, max_length=50)
    apellido: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    telefono: str = Field(..., min_length=10, max_length=20)
    fecha_nacimiento: date
    direccion: str = Field(..., min_length=5, max_length=200)
    obra_social: Optional[str] = Field(None, max_length=100)
    numero_afiliado: Optional[str] = Field(None, max_length=50)
    
    @field_validator('fecha_nacimiento')
    @classmethod
    def validar_fecha_nacimiento(cls, v: date) -> date:
        """Valida que la fecha de nacimiento sea coherente."""
        if v >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior a hoy")
        
        edad = (date.today() - v).days // 365
        if edad > 120:
            raise ValueError("La fecha de nacimiento no es válida")
        
        return v


class TurnoCreate(BaseModel):
    """Esquema para crear un turno."""
    id_paciente: int = Field(..., gt=0)
    id_medico: int = Field(..., gt=0)
    id_especialidad: int = Field(..., gt=0)
    fecha_hora: datetime
    duracion_minutos: int = Field(default=30, ge=15, le=120)
    motivo: Optional[str] = Field(None, max_length=255)
    
    @field_validator('fecha_hora')
    @classmethod
    def validar_fecha_futura(cls, v: datetime) -> datetime:
        """Valida que la fecha sea futura."""
        if v <= datetime.now():
            raise ValueError("La fecha del turno debe ser futura")
        return v


class TurnoUpdate(BaseModel):
    """Esquema para actualizar un turno."""
    motivo: Optional[str] = Field(None, max_length=255)
    codigo_estado: Optional[str] = Field(None, max_length=10)


# ============================================================
# ESQUEMAS DE RESPUESTA CON LISTADOS
# ============================================================

class PaginationResponse(BaseModel):
    """Esquema para respuesta paginada."""
    total: int
    page: int
    page_size: int
    items: List[dict]


class ErrorResponse(BaseModel):
    """Esquema para respuestas de error."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Esquema para respuestas exitosas."""
    message: str
    data: Optional[dict] = None
