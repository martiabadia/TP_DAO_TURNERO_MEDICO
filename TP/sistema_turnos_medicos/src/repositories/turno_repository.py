"""Repositorio para la entidad Turno."""
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, or_, select, String
from sqlalchemy.orm import Session, joinedload

from src.domain.turno import Turno
from src.repositories.base_repository import BaseRepository


class TurnoRepository(BaseRepository[Turno]):
    """Repositorio específico para Turnos."""

    def __init__(self, session: Session):
        super().__init__(session, Turno)

    def get_by_id_completo(self, turno_id: int) -> Optional[Turno]:
        """Obtiene turno por ID con todas las relaciones cargadas."""
        stmt = select(Turno).options(
            joinedload(Turno.paciente),
            joinedload(Turno.medico),
            joinedload(Turno.especialidad),
            joinedload(Turno.estado)
        ).where(
            Turno.id == turno_id,
            Turno.activo.is_(True)
        )
        return self.session.scalar(stmt)

    def get_por_medico(
        self,
        medico_id: int,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        solo_activos: bool = True
    ) -> List[Turno]:
        """
        Obtiene turnos de un médico en un rango de fechas.
        
        Args:
            medico_id: ID del médico
            fecha_desde: Fecha inicial (opcional)
            fecha_hasta: Fecha final (opcional)
            solo_activos: Si es True, solo estados PEND, CONF, ASIS
        
        Returns:
            Lista de turnos
        """
        stmt = select(Turno).options(
            joinedload(Turno.paciente),
            joinedload(Turno.especialidad),
            joinedload(Turno.estado)
        ).where(
            Turno.id_medico == medico_id,
            Turno.activo.is_(True)
        )
        
        if fecha_desde:
            stmt = stmt.where(Turno.fecha_hora >= datetime.combine(fecha_desde, datetime.min.time()))
        
        if fecha_hasta:
            stmt = stmt.where(Turno.fecha_hora <= datetime.combine(fecha_hasta, datetime.max.time()))
        
        if solo_activos:
            # Estados activos: PEND, CONF, ASIS
            from src.domain.estado_turno import EstadoTurno
            stmt = stmt.join(Turno.estado).where(
                EstadoTurno.codigo.in_(["PEND", "CONF", "ASIS"])
            )
        
        stmt = stmt.order_by(Turno.fecha_hora)
        return list(self.session.scalars(stmt).unique().all())

    def get_por_paciente(
        self,
        paciente_id: int,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Turno]:
        """
        Obtiene turnos de un paciente en un rango de fechas.
        
        Args:
            paciente_id: ID del paciente
            fecha_desde: Fecha inicial (opcional)
            fecha_hasta: Fecha final (opcional)
        
        Returns:
            Lista de turnos
        """
        stmt = select(Turno).options(
            joinedload(Turno.medico),
            joinedload(Turno.especialidad),
            joinedload(Turno.estado)
        ).where(
            Turno.id_paciente == paciente_id,
            Turno.activo.is_(True)
        )
        
        if fecha_desde:
            stmt = stmt.where(Turno.fecha_hora >= datetime.combine(fecha_desde, datetime.min.time()))
        
        if fecha_hasta:
            stmt = stmt.where(Turno.fecha_hora <= datetime.combine(fecha_hasta, datetime.max.time()))
        
        stmt = stmt.order_by(Turno.fecha_hora.desc())
        return list(self.session.scalars(stmt).unique().all())

    def get_por_medico_y_fecha(
        self,
        medico_id: int,
        fecha: date
    ) -> List[Turno]:
        """
        Obtiene todos los turnos de un médico para una fecha específica.
        Excluye turnos cancelados.
        
        Args:
            medico_id: ID del médico
            fecha: Fecha a buscar
        
        Returns:
            Lista de turnos del médico en esa fecha (excluyendo cancelados)
        """
        from src.domain.estado_turno import EstadoTurno
        
        fecha_inicio = datetime.combine(fecha, datetime.min.time())
        fecha_fin = datetime.combine(fecha, datetime.max.time())
        
        stmt = select(Turno).join(Turno.estado).where(
            Turno.id_medico == medico_id,
            Turno.fecha_hora >= fecha_inicio,
            Turno.fecha_hora <= fecha_fin,
            Turno.activo.is_(True),
            EstadoTurno.codigo != 'CANC'
        ).order_by(Turno.fecha_hora)
        
        return list(self.session.scalars(stmt).all())

    def get_por_especialidad(
        self,
        especialidad_id: int,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Turno]:
        """Obtiene turnos por especialidad en un rango de fechas."""
        stmt = select(Turno).options(
            joinedload(Turno.paciente),
            joinedload(Turno.medico),
            joinedload(Turno.estado)
        ).where(
            Turno.id_especialidad == especialidad_id,
            Turno.activo.is_(True)
        )
        
        if fecha_desde:
            stmt = stmt.where(Turno.fecha_hora >= datetime.combine(fecha_desde, datetime.min.time()))
        
        if fecha_hasta:
            stmt = stmt.where(Turno.fecha_hora <= datetime.combine(fecha_hasta, datetime.max.time()))
        
        stmt = stmt.order_by(Turno.fecha_hora)
        return list(self.session.scalars(stmt).unique().all())

    def verificar_solapamiento_medico(
        self,
        medico_id: int,
        fecha_hora_inicio: datetime,
        fecha_hora_fin: datetime,
        exclude_turno_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si hay turnos del médico que se solapen con el horario dado.
        
        Args:
            medico_id: ID del médico
            fecha_hora_inicio: Inicio del turno a verificar
            fecha_hora_fin: Fin del turno a verificar
            exclude_turno_id: ID de turno a excluir (útil para modificaciones)
        
        Returns:
            True si hay solapamiento, False en caso contrario
        """
        from src.domain.estado_turno import EstadoTurno
        
        # Obtener todos los turnos activos del médico en el día
        fecha_dia = fecha_hora_inicio.date()
        stmt = select(Turno).join(Turno.estado).where(
            Turno.id_medico == medico_id,
            Turno.activo.is_(True),
            EstadoTurno.codigo.in_(["PEND", "CONF", "ASIS"]),
            Turno.fecha_hora >= datetime.combine(fecha_dia, datetime.min.time()),
            Turno.fecha_hora < datetime.combine(fecha_dia, datetime.max.time())
        )
        
        if exclude_turno_id is not None:
            stmt = stmt.where(Turno.id != exclude_turno_id)
        
        turnos = list(self.session.scalars(stmt).all())
        
        # Verificar solapamiento en Python
        for turno in turnos:
            turno_fin = turno.fecha_hora + timedelta(minutes=turno.duracion_minutos)
            if turno.fecha_hora < fecha_hora_fin and turno_fin > fecha_hora_inicio:
                return True
        
        return False

    def verificar_solapamiento_paciente(
        self,
        paciente_id: int,
        fecha_hora_inicio: datetime,
        fecha_hora_fin: datetime,
        exclude_turno_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si el paciente tiene turnos que se solapen con el horario dado.
        
        Args:
            paciente_id: ID del paciente
            fecha_hora_inicio: Inicio del turno a verificar
            fecha_hora_fin: Fin del turno a verificar
            exclude_turno_id: ID de turno a excluir (útil para modificaciones)
        
        Returns:
            True si hay solapamiento, False en caso contrario
        """
        from src.domain.estado_turno import EstadoTurno
        
        # Obtener todos los turnos activos del paciente en el día
        fecha_dia = fecha_hora_inicio.date()
        stmt = select(Turno).join(Turno.estado).where(
            Turno.id_paciente == paciente_id,
            Turno.activo.is_(True),
            EstadoTurno.codigo.in_(["PEND", "CONF", "ASIS"]),
            Turno.fecha_hora >= datetime.combine(fecha_dia, datetime.min.time()),
            Turno.fecha_hora < datetime.combine(fecha_dia, datetime.max.time())
        )
        
        if exclude_turno_id is not None:
            stmt = stmt.where(Turno.id != exclude_turno_id)
        
        turnos = list(self.session.scalars(stmt).all())
        
        # Verificar solapamiento en Python
        for turno in turnos:
            turno_fin = turno.fecha_hora + timedelta(minutes=turno.duracion_minutos)
            if turno.fecha_hora < fecha_hora_fin and turno_fin > fecha_hora_inicio:
                return True
        
        return False

    def contar_por_estado(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> dict:
        """
        Cuenta turnos agrupados por estado en un rango de fechas.
        
        Returns:
            Diccionario con código de estado como clave y cantidad como valor
        """
        stmt = select(Turno).options(
            joinedload(Turno.estado)
        ).where(
            Turno.activo.is_(True)
        )
        
        if fecha_desde:
            stmt = stmt.where(Turno.fecha_hora >= datetime.combine(fecha_desde, datetime.min.time()))
        
        if fecha_hasta:
            stmt = stmt.where(Turno.fecha_hora <= datetime.combine(fecha_hasta, datetime.max.time()))
        
        turnos = list(self.session.scalars(stmt).all())
        
        # Contar por estado
        conteo = {}
        for turno in turnos:
            codigo = turno.estado.codigo
            conteo[codigo] = conteo.get(codigo, 0) + 1
        
        return conteo

    def get_turnos_en_rango(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        solo_confirmados: bool = True
    ) -> List[Turno]:
        """
        Obtiene turnos en un rango de fechas/horas específico.
        
        Args:
            fecha_inicio: Inicio del rango
            fecha_fin: Fin del rango
            solo_confirmados: Si es True, solo devuelve turnos confirmados (CONF)
        
        Returns:
            Lista de turnos en el rango
        """
        stmt = select(Turno).options(
            joinedload(Turno.paciente),
            joinedload(Turno.medico),
            joinedload(Turno.especialidad)
        ).where(
            Turno.activo.is_(True),
            Turno.fecha_hora >= fecha_inicio,
            Turno.fecha_hora <= fecha_fin
        )
        
        if solo_confirmados:
            stmt = stmt.join(Turno.estado).where(
                Turno.estado.has(codigo="CONF")
            )
            
        return list(self.session.scalars(stmt).unique().all())
