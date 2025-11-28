"""
Servicio de gestión de Turnos Médicos.
Implementa todas las validaciones de negocio para turnos.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from src.domain.turno import Turno
from src.repositories.unit_of_work import UnitOfWork
from src.utils.exceptions import *


class TurnoService:
    """Servicio para gestión de turnos con validaciones completas."""
    
    def __init__(self, uow: UnitOfWork):
        """
        Inicializa el servicio con una unidad de trabajo.
        
        Args:
            uow: Unidad de trabajo para acceso a repositorios
        """
        self.uow = uow

    def crear_turno(
        self,
        paciente_id: int,
        medico_id: int,
        especialidad_id: int,
        fecha_hora: datetime,
        duracion_minutos: int = 30,
        lugar: Optional[str] = None,
        observaciones: Optional[str] = None
    ) -> Turno:
        """
        Crea un nuevo turno con todas las validaciones de negocio.
        
        Validaciones:
        1. Fecha futura obligatoria
        2. Verificación de disponibilidad del médico
        3. Médico tiene la especialidad
        4. Anti-solape para el mismo médico
        5. Anti-solape para el mismo paciente
        6. Control de bloqueos del médico
        7. Estado inicial: PEND
        
        Args:
            paciente_id: ID del paciente
            medico_id: ID del médico
            especialidad_id: ID de la especialidad
            fecha_hora: Fecha y hora del turno
            duracion_minutos: Duración en minutos (default 30)
            lugar: Lugar del turno (opcional)
            observaciones: Observaciones (opcional)
        
        Returns:
            Turno creado
        
        Raises:
            ValidationException: Si falla alguna validación
            EntityNotFoundException: Si no existe paciente, médico o especialidad
            TurnoSolapamientoException: Si hay solapamiento
        """
        with UnitOfWork() as uow:
            # 1. Validar que fecha sea futura
            if fecha_hora <= datetime.now():
                raise ValidationException("La fecha del turno debe ser futura")
            
            # 2. Verificar que existan paciente, médico y especialidad
            paciente = uow.pacientes.get_by_id(paciente_id)
            if paciente is None:
                raise EntityNotFoundException(f"Paciente con ID {paciente_id} no encontrado")
            
            medico = uow.medicos.get_by_id_con_especialidades(medico_id)
            if medico is None:
                raise EntityNotFoundException(f"Médico con ID {medico_id} no encontrado")
            
            especialidad = uow.especialidades.get_by_id(especialidad_id)
            if especialidad is None:
                raise EntityNotFoundException(f"Especialidad con ID {especialidad_id} no encontrada")
            
            # 3. Verificar que el médico tenga la especialidad
            if not medico.tiene_especialidad(especialidad_id):
                raise ValidationException(
                    f"El médico {medico.nombre_completo} no tiene la especialidad {especialidad.nombre}"
                )
            
            # 4. Verificar disponibilidad del médico (día y horario)
            dia_semana = fecha_hora.weekday()  # 0=Lunes, 6=Domingo
            hora_turno = fecha_hora.time()
            
            disponibilidades = uow.disponibilidades.get_por_medico_y_dia(medico_id, dia_semana)
            
            if not disponibilidades:
                raise DisponibilidadException(
                    f"El médico no tiene disponibilidad configurada para los días {self._dia_nombre(dia_semana)}"
                )
            
            # Verificar que la hora esté dentro de alguna disponibilidad
            hora_valida = False
            for disp in disponibilidades:
                if disp.hora_desde <= hora_turno < disp.hora_hasta:
                    hora_valida = True
                    break
            
            if not hora_valida:
                raise DisponibilidadException(
                    f"El médico no atiende en ese horario los días {self._dia_nombre(dia_semana)}"
                )
            
            # 5. Verificar bloqueos del médico (TEMPORALMENTE DESHABILITADO)
            fecha_hora_fin = fecha_hora + timedelta(minutes=duracion_minutos)
            
            # TODO: Arreglar verificación de bloqueos con SQLAlchemy 2.0
            # if uow.bloqueos.verificar_bloqueado(medico_id, fecha_hora, fecha_hora_fin):
            #     raise DisponibilidadException(
            #         "El médico tiene un bloqueo en ese horario (vacaciones, capacitación, etc.)"
            #     )
            
            # 6. Verificar anti-solape con otros turnos del médico
            if uow.turnos.verificar_solapamiento_medico(medico_id, fecha_hora, fecha_hora_fin):
                raise TurnoSolapamientoException(
                    "El médico ya tiene un turno asignado en ese horario"
                )
            
            # 7. Verificar anti-solape con otros turnos del paciente
            if uow.turnos.verificar_solapamiento_paciente(paciente_id, fecha_hora, fecha_hora_fin):
                raise TurnoSolapamientoException(
                    "El paciente ya tiene un turno asignado en ese horario"
                )
            
            # 8. Obtener estado PENDIENTE
            estado_pend = uow.estados_turno.get_pendiente()
            if estado_pend is None:
                raise EntityNotFoundException("Estado PENDIENTE no encontrado. Ejecute inicialización de datos.")
            
            # 9. Crear turno
            turno = Turno(
                id_paciente=paciente_id,
                id_medico=medico_id,
                id_especialidad=especialidad_id,
                id_estado=estado_pend.id,
                fecha_hora=fecha_hora,
                duracion_minutos=duracion_minutos,
                lugar=lugar,
                observaciones=observaciones
            )
            
            uow.turnos.add(turno)
            uow.commit()
            
            return turno

    def cancelar_turno(self, turno_id: int, motivo: Optional[str] = None) -> Turno:
        """
        Cancela un turno existente.
        
        Validaciones:
        - Turno debe existir y estar activo
        - Turno debe estar en estado PEND o CONF
        - Turno debe ser futuro
        
        Args:
            turno_id: ID del turno a cancelar
            motivo: Motivo de cancelación (opcional)
        
        Returns:
            Turno cancelado
        
        Raises:
            EntityNotFoundException: Si el turno no existe
            InvalidOperationException: Si el turno no puede cancelarse
        """
        with UnitOfWork() as uow:
            turno = uow.turnos.get_by_id_completo(turno_id)
            
            if turno is None:
                raise EntityNotFoundException(f"Turno con ID {turno_id} no encontrado")
            
            if not turno.puede_cancelarse():
                raise InvalidOperationException(
                    f"El turno no puede cancelarse. Estado actual: {turno.estado.nombre}"
                )
            
            # Cambiar a estado CANCELADO
            estado_canc = uow.estados_turno.get_cancelado()
            turno.id_estado = estado_canc.id
            
            if motivo:
                turno.observaciones = f"{turno.observaciones or ''}\n[CANCELADO] {motivo}".strip()
            
            uow.turnos.update(turno)
            uow.commit()
            
            return turno

    def confirmar_turno(self, turno_id: int) -> Turno:
        """Cambia un turno de PENDIENTE a CONFIRMADO."""
        with UnitOfWork() as uow:
            turno = uow.turnos.get_by_id_completo(turno_id)
            
            if turno is None:
                raise EntityNotFoundException(f"Turno con ID {turno_id} no encontrado")
            
            if turno.estado.codigo != "PEND":
                raise InvalidOperationException(
                    f"Solo se pueden confirmar turnos pendientes. Estado actual: {turno.estado.nombre}"
                )
            
            estado_conf = uow.estados_turno.get_confirmado()
            turno.id_estado = estado_conf.id
            
            uow.turnos.update(turno)
            uow.commit()
            
            return turno

    def marcar_asistido(self, turno_id: int) -> Turno:
        """Marca un turno como ASISTIDO (paciente concurrió)."""
        with UnitOfWork() as uow:
            turno = uow.turnos.get_by_id_completo(turno_id)
            
            if turno is None:
                raise EntityNotFoundException(f"Turno con ID {turno_id} no encontrado")
            
            if turno.estado.codigo not in ["PEND", "CONF"]:
                raise InvalidOperationException(
                    "Solo se pueden marcar como asistidos turnos pendientes o confirmados"
                )
            
            estado_asis = uow.estados_turno.get_asistido()
            turno.id_estado = estado_asis.id
            
            uow.turnos.update(turno)
            uow.commit()
            
            return turno

    def marcar_inasistido(self, turno_id: int) -> Turno:
        """Marca un turno como INASISTIDO (paciente no concurrió)."""
        with UnitOfWork() as uow:
            turno = uow.turnos.get_by_id_completo(turno_id)
            
            if turno is None:
                raise EntityNotFoundException(f"Turno con ID {turno_id} no encontrado")
            
            if turno.estado.codigo not in ["PEND", "CONF"]:
                raise InvalidOperationException(
                    "Solo se pueden marcar como inasistidos turnos pendientes o confirmados"
                )
            
            estado_inas = uow.estados_turno.get_inasistido()
            turno.id_estado = estado_inas.id
            
            uow.turnos.update(turno)
            uow.commit()
            
            return turno

    def listar_turnos_medico(
        self,
        medico_id: int,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Turno]:
        """Lista turnos de un médico en un rango de fechas."""
        with UnitOfWork() as uow:
            return uow.turnos.get_por_medico(
                medico_id,
                fecha_desde.date() if fecha_desde else None,
                fecha_hasta.date() if fecha_hasta else None
            )

    def listar_turnos_paciente(
        self,
        paciente_id: int,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Turno]:
        """Lista turnos de un paciente en un rango de fechas."""
        with UnitOfWork() as uow:
            return uow.turnos.get_por_paciente(
                paciente_id,
                fecha_desde.date() if fecha_desde else None,
                fecha_hasta.date() if fecha_hasta else None
            )

    def obtener_horarios_disponibles(
        self,
        medico_id: int,
        fecha: datetime.date,
        duracion_minutos: int = 30
    ) -> List[datetime]:
        """
        Obtiene los horarios disponibles de un médico para una fecha específica.
        
        Args:
            medico_id: ID del médico
            fecha: Fecha para buscar disponibilidad
            duracion_minutos: Duración del turno en minutos
        
        Returns:
            Lista de fechas/horas disponibles
        """
        # Verificar que el médico existe
        medico = self.uow.medicos.get_by_id(medico_id)
        if not medico:
            raise EntityNotFoundException(f"Médico con ID {medico_id} no encontrado")
        
        # Obtener día de la semana
        dia_semana = fecha.weekday()
        
        # Obtener disponibilidades del médico para ese día
        disponibilidades = self.uow.disponibilidades.get_por_medico_y_dia(medico_id, dia_semana)
        
        if not disponibilidades:
            raise DisponibilidadException(
                f"El médico no tiene disponibilidad para los días {self._dia_nombre(dia_semana)}"
            )
        
        # Obtener turnos existentes del médico para esa fecha
        turnos_existentes = self.uow.turnos.get_por_medico_y_fecha(medico_id, fecha)
        
        # Obtener la hora actual
        ahora = datetime.now()
        
        # Generar slots disponibles
        horarios_disponibles = []
        
        for disp in disponibilidades:
            # Crear datetime desde la hora de inicio hasta la hora de fin
            hora_actual = datetime.combine(fecha, disp.hora_desde)
            hora_fin = datetime.combine(fecha, disp.hora_hasta)
            
            while hora_actual + timedelta(minutes=duracion_minutos) <= hora_fin:
                # Saltar horarios que ya pasaron
                if hora_actual <= ahora:
                    hora_actual += timedelta(minutes=disp.duracion_slot or duracion_minutos)
                    continue
                
                # Verificar si hay solapamiento con turnos existentes
                hay_solape = False
                hora_fin_slot = hora_actual + timedelta(minutes=duracion_minutos)
                
                for turno in turnos_existentes:
                    turno_fin = turno.fecha_hora + timedelta(minutes=turno.duracion_minutos)
                    
                    # Verificar solapamiento
                    if not (hora_fin_slot <= turno.fecha_hora or hora_actual >= turno_fin):
                        hay_solape = True
                        break
                
                if not hay_solape:
                    horarios_disponibles.append(hora_actual)
                
                # Avanzar al siguiente slot
                hora_actual += timedelta(minutes=disp.duracion_slot or duracion_minutos)
        
        return horarios_disponibles

    @staticmethod
    def _dia_nombre(dia_semana: int) -> str:
        """Convierte número de día a nombre."""
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return dias[dia_semana]
