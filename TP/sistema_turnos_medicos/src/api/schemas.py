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


class EspecialidadCreate(BaseModel):
    """Esquema para crear una especialidad."""
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre de la especialidad")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción de la especialidad")


class EspecialidadUpdate(BaseModel):
    """Esquema para actualizar una especialidad."""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)


class MedicoResponse(BaseModel):
    """Esquema de respuesta para médico."""
    id: int
    matricula: str
    nombre: str
    apellido: str
    dni: str
    email: str
    telefono: str
    direccion: Optional[str] = None
    genero: Optional[str] = None
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
    email: str
    especialidades: List[EspecialidadResponse] = []
    
    class Config:
        from_attributes = True


class PacienteResponse(BaseModel):
    """Esquema de respuesta para paciente."""
    id: int
    dni: str
    nombre: str
    apellido: str
    nombre_completo: str
    email: str
    telefono: str
    fecha_nacimiento: date
    direccion: str
    obra_social: Optional[str] = None
    numero_afiliado: Optional[str] = None
    
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


class DisponibilidadCreate(BaseModel):
    """Esquema para crear una disponibilidad."""
    dia_semana: int = Field(..., ge=0, le=6, description="0=Domingo, 1=Lunes, ..., 6=Sábado")
    hora_desde: time
    hora_hasta: time
    duracion_slot: int = Field(default=30, ge=15, le=120, description="Duración del turno en minutos")
    
    @field_validator('dia_semana')
    @classmethod
    def validar_dia_semana(cls, v: int) -> int:
        """Valida que el día de la semana esté en rango válido."""
        if not 0 <= v <= 6:
            raise ValueError("El día de la semana debe estar entre 0 (Domingo) y 6 (Sábado)")
        return v
    
    @field_validator('hora_hasta')
    @classmethod
    def validar_horarios(cls, v: time, info) -> time:
        """Valida que hora_hasta sea mayor a hora_desde."""
        if 'hora_desde' in info.data and v <= info.data['hora_desde']:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return v


class DisponibilidadUpdate(BaseModel):
    """Esquema para actualizar una disponibilidad."""
    hora_desde: Optional[time] = None
    hora_hasta: Optional[time] = None
    duracion_slot: Optional[int] = Field(None, ge=15, le=120)
    
    @field_validator('hora_hasta')
    @classmethod
    def validar_horarios(cls, v: Optional[time], info) -> Optional[time]:
        """Valida que hora_hasta sea mayor a hora_desde si ambos están presentes."""
        if v and 'hora_desde' in info.data and info.data['hora_desde'] and v <= info.data['hora_desde']:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return v


class BloqueoResponse(BaseModel):
    """Esquema de respuesta para bloqueo de médico."""
    id: int
    id_medico: int
    inicio: datetime
    fin: datetime
    motivo: Optional[str] = None
    
    class Config:
        from_attributes = True


class BloqueoCreate(BaseModel):
    """Esquema para crear un bloqueo (día completo)."""
    inicio: date = Field(..., description="Fecha de inicio del bloqueo (formato: YYYY-MM-DD)")
    fin: date = Field(..., description="Fecha de fin del bloqueo (formato: YYYY-MM-DD)")
    motivo: Optional[str] = Field(None, max_length=200, description="Motivo del bloqueo (vacaciones, capacitación, etc.)")
    
    @field_validator('fin')
    @classmethod
    def validar_fechas(cls, v: date, info) -> date:
        """Valida que la fecha de fin sea posterior a la de inicio."""
        if 'inicio' in info.data and v < info.data['inicio']:
            raise ValueError("La fecha de fin debe ser posterior o igual a la fecha de inicio")
        return v
    
    @field_validator('inicio')
    @classmethod
    def validar_fecha_futura(cls, v: date) -> date:
        """Valida que el bloqueo no sea del pasado."""
        if v < date.today():
            raise ValueError("No se pueden crear bloqueos en el pasado")
        return v


class BloqueoUpdate(BaseModel):
    """Esquema para actualizar un bloqueo."""
    inicio: Optional[date] = None
    fin: Optional[date] = None
    motivo: Optional[str] = Field(None, max_length=200)
    
    @field_validator('fin')
    @classmethod
    def validar_fechas(cls, v: Optional[date], info) -> Optional[date]:
        """Valida que la fecha de fin sea posterior a la de inicio si ambos están presentes."""
        if v and 'inicio' in info.data and info.data['inicio'] and v < info.data['inicio']:
            raise ValueError("La fecha de fin debe ser posterior o igual a la fecha de inicio")
        return v


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


class PacienteUpdate(BaseModel):
    """Esquema para actualizar un paciente."""
    dni: Optional[str] = Field(None, min_length=7, max_length=10)
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    apellido: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=10, max_length=20)
    fecha_nacimiento: Optional[date] = None
    direccion: Optional[str] = Field(None, min_length=5, max_length=200)
    obra_social: Optional[str] = Field(None, max_length=100)
    numero_afiliado: Optional[str] = Field(None, max_length=50)
    
    @field_validator('fecha_nacimiento')
    @classmethod
    def validar_fecha_nacimiento(cls, v: Optional[date]) -> Optional[date]:
        """Valida que la fecha de nacimiento sea coherente."""
        if v is None:
            return v
            
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
        """Valida que la fecha no sea del pasado."""
        # Permitir fechas de hoy y futuras
        # Comparar solo la fecha sin hora para evitar problemas de timezone
        hoy = datetime.now().date()
        fecha_turno = v.date()
        
        if fecha_turno < hoy:
            raise ValueError("La fecha del turno no puede ser del pasado")
        
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


# ============================================================
# ESQUEMAS DE REPORTES
# ============================================================

class TurnoReporteResponse(BaseModel):
    fecha_hora: str
    paciente: str
    especialidad: str
    estado: str

class EspecialidadReporteResponse(BaseModel):
    especialidad: str
    cantidad: int

class PacienteReporteResponse(BaseModel):
    fecha: str
    paciente: str
    dni: str
    medico: str
    especialidad: str

class AsistenciaReporteResponse(BaseModel):
    asistencias: int
    inasistencias: int


# ============================================================
# ESQUEMAS DE HISTORIAL CLÍNICO
# ============================================================

class ItemRecetaResponse(BaseModel):
    """Esquema de respuesta para item de receta."""
    id: int
    medicamento: str
    dosis: Optional[str] = None
    frecuencia: Optional[str] = None
    duracion: Optional[str] = None
    indicaciones: Optional[str] = None
    
    class Config:
        from_attributes = True


class RecetaResponse(BaseModel):
    """Esquema de respuesta para receta médica."""
    id: int
    id_consulta: int
    fecha_emision: date
    estado: str
    items: List[ItemRecetaResponse] = []
    
    class Config:
        from_attributes = True


class ConsultaResponse(BaseModel):
    """Esquema de respuesta para consulta médica (historial clínico)."""
    id: int
    id_turno: int
    motivo: Optional[str] = None
    observaciones: Optional[str] = None
    diagnostico: Optional[str] = None
    indicaciones: Optional[str] = None
    fecha_atencion: datetime
    recetas: List[RecetaResponse] = []
    
    class Config:
        from_attributes = True


class ConsultaCreate(BaseModel):
    """Esquema para crear una consulta (entrada de historial clínico)."""
    id_turno: int = Field(..., gt=0, description="ID del turno atendido")
    motivo: Optional[str] = Field(None, max_length=500, description="Motivo de la consulta")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones del médico")
    diagnostico: Optional[str] = Field(None, max_length=500, description="Diagnóstico médico")
    indicaciones: Optional[str] = Field(None, max_length=1000, description="Indicaciones al paciente")


class ConsultaUpdate(BaseModel):
    """Esquema para actualizar una consulta."""
    motivo: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = Field(None, max_length=1000)
    diagnostico: Optional[str] = Field(None, max_length=500)
    indicaciones: Optional[str] = Field(None, max_length=1000)


class ItemRecetaCreate(BaseModel):
    """Esquema para crear un item de receta."""
    medicamento: str = Field(..., min_length=2, max_length=200)
    dosis: Optional[str] = Field(None, max_length=160)
    frecuencia: Optional[str] = Field(None, max_length=160)
    duracion: Optional[str] = Field(None, max_length=160)
    indicaciones: Optional[str] = Field(None, max_length=500)


class RecetaCreate(BaseModel):
    """Esquema para crear una receta."""
    id_consulta: int = Field(..., gt=0, description="ID de la consulta asociada")
    items: List[ItemRecetaCreate] = Field(..., min_length=1, description="Lista de medicamentos")


class HistorialClinicoResponse(BaseModel):
    """Esquema de respuesta para historial clínico completo de un paciente."""
    paciente_id: int
    paciente_nombre: str
    paciente_dni: str
    total_consultas: int
    consultas: List[dict]  # Consultas con información del turno, médico, etc.
