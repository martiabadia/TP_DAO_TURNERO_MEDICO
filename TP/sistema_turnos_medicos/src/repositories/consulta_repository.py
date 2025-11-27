"""Repositorio para la entidad Consulta (Historia Clínica)."""
from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.domain.consulta import Consulta
from src.domain.turno import Turno
from src.repositories.base_repository import BaseRepository


class ConsultaRepository(BaseRepository[Consulta]):
    """Repositorio para Consultas (Historia Clínica)."""

    def __init__(self, session: Session):
        super().__init__(session, Consulta)

    def get_by_turno(self, turno_id: int) -> Optional[Consulta]:
        """
        Obtiene la consulta asociada a un turno.
        
        Args:
            turno_id: ID del turno
        
        Returns:
            Consulta o None si no existe
        """
        stmt = select(Consulta).where(
            Consulta.id_turno == turno_id,
            Consulta.activo == True  # noqa: E712
        )
        return self.session.scalar(stmt)

    def get_por_paciente(
        self,
        paciente_id: int,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Consulta]:
        """
        Obtiene historia clínica de un paciente.
        
        Args:
            paciente_id: ID del paciente
            fecha_desde: Fecha inicial (opcional)
            fecha_hasta: Fecha final (opcional)
        
        Returns:
            Lista de consultas ordenadas por fecha descendente
        """
        stmt = select(Consulta).join(
            Consulta.turno
        ).options(
            joinedload(Consulta.turno).joinedload(Turno.medico),
            joinedload(Consulta.turno).joinedload(Turno.especialidad)
        ).where(
            Consulta.turno.has(id_paciente=paciente_id),
            Consulta.activo == True  # noqa: E712
        )
        
        if fecha_desde:
            stmt = stmt.where(Consulta.fecha_atencion >= fecha_desde)
        
        if fecha_hasta:
            stmt = stmt.where(Consulta.fecha_atencion <= fecha_hasta)
        
        stmt = stmt.order_by(Consulta.fecha_atencion.desc())
        return list(self.session.scalars(stmt).unique().all())

    def get_por_medico(
        self,
        medico_id: int,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Consulta]:
        """
        Obtiene consultas realizadas por un médico.
        
        Args:
            medico_id: ID del médico
            fecha_desde: Fecha inicial (opcional)
            fecha_hasta: Fecha final (opcional)
        
        Returns:
            Lista de consultas ordenadas por fecha descendente
        """
        stmt = select(Consulta).join(
            Consulta.turno
        ).options(
            joinedload(Consulta.turno).joinedload(Turno.paciente)
        ).where(
            Consulta.turno.has(id_medico=medico_id),
            Consulta.activo == True  # noqa: E712
        )
        
        if fecha_desde:
            stmt = stmt.where(Consulta.fecha_atencion >= fecha_desde)
        
        if fecha_hasta:
            stmt = stmt.where(Consulta.fecha_atencion <= fecha_hasta)
        
        stmt = stmt.order_by(Consulta.fecha_atencion.desc())
        return list(self.session.scalars(stmt).unique().all())

    def existe_para_turno(self, turno_id: int) -> bool:
        """
        Verifica si ya existe una consulta para el turno dado.
        
        Args:
            turno_id: ID del turno
        
        Returns:
            True si existe, False en caso contrario
        """
        return self.get_by_turno(turno_id) is not None
