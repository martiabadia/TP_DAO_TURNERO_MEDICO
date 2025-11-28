from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, case, desc
from sqlalchemy.orm import Session

from src.repositories.database import DatabaseManager
from src.domain.turno import Turno
from src.domain.medico import Medico
from src.domain.paciente import Paciente
from src.domain.especialidad import Especialidad
from src.domain.estado_turno import EstadoTurno

class ReporteService:
    def __init__(self):
        self.db = DatabaseManager()

    def get_turnos_por_medico(self, fecha_inicio: date, fecha_fin: date, medico_id: Optional[int] = None, especialidad_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene el listado de turnos en un rango de fechas, con filtros opcionales de médico y especialidad.
        """
        with self.db.get_session() as session:
            query = session.query(Turno).join(Paciente).join(Especialidad).join(Medico).join(EstadoTurno).filter(
                Turno.activo == True,
                func.date(Turno.fecha_hora) >= fecha_inicio,
                func.date(Turno.fecha_hora) <= fecha_fin
            )

            if medico_id:
                query = query.filter(Turno.id_medico == medico_id)
            
            if especialidad_id:
                query = query.filter(Turno.id_especialidad == especialidad_id)

            turnos = query.order_by(Turno.fecha_hora).all()

            resultado = []
            for turno in turnos:
                resultado.append({
                    "fecha_hora": turno.fecha_hora.isoformat(),
                    "paciente": f"{turno.paciente.nombre} {turno.paciente.apellido}",
                    "medico": f"{turno.medico.nombre} {turno.medico.apellido}",
                    "especialidad": turno.especialidad.nombre,
                    "estado": turno.estado.descripcion
                })
            return resultado

    def get_turnos_por_especialidad(self, fecha_inicio: date, fecha_fin: date, medico_id: Optional[int] = None, especialidad_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Cuenta la cantidad de turnos por especialidad en un rango de fechas, con filtros opcionales.
        """
        with self.db.get_session() as session:
            query = session.query(
                Especialidad.nombre,
                func.count(Turno.id).label('cantidad')
            ).join(Turno, Turno.id_especialidad == Especialidad.id).filter(
                Turno.activo == True,
                func.date(Turno.fecha_hora) >= fecha_inicio,
                func.date(Turno.fecha_hora) <= fecha_fin
            )

            if medico_id:
                query = query.filter(Turno.id_medico == medico_id)
            
            if especialidad_id:
                query = query.filter(Turno.id_especialidad == especialidad_id)

            results = query.group_by(Especialidad.id, Especialidad.nombre).order_by(desc('cantidad')).all()

            return [{"especialidad": nombre, "cantidad": cantidad} for nombre, cantidad in results]

    def get_pacientes_atendidos(self, fecha_inicio: date, fecha_fin: date, medico_id: Optional[int] = None, especialidad_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene los pacientes atendidos (turnos con estado 'ASIS') en un rango de fechas.
        """
        with self.db.get_session() as session:
            query = session.query(Turno).join(Paciente).join(Medico).join(Especialidad).join(EstadoTurno).filter(
                Turno.activo == True,
                EstadoTurno.codigo == "ASIS",
                func.date(Turno.fecha_hora) >= fecha_inicio,
                func.date(Turno.fecha_hora) <= fecha_fin
            )

            if medico_id:
                query = query.filter(Turno.id_medico == medico_id)
            
            if especialidad_id:
                query = query.filter(Turno.id_especialidad == especialidad_id)

            turnos = query.order_by(Turno.fecha_hora).all()

            resultado = []
            for turno in turnos:
                resultado.append({
                    "fecha": turno.fecha_hora.date().isoformat(),
                    "paciente": f"{turno.paciente.nombre} {turno.paciente.apellido}",
                    "dni": turno.paciente.dni,
                    "medico": f"{turno.medico.nombre} {turno.medico.apellido}",
                    "especialidad": turno.especialidad.nombre
                })
            return resultado

    def get_estadisticas_asistencia(self, fecha_inicio: date, fecha_fin: date, medico_id: Optional[int] = None, especialidad_id: Optional[int] = None) -> Dict[str, int]:
        """
        Calcula la cantidad de asistencias e inasistencias con filtros opcionales.
        Asistencias: Estado 'ASIS'
        Inasistencias: Estado 'INAS'
        """
        with self.db.get_session() as session:
            base_query = session.query(func.count(Turno.id)).join(EstadoTurno).filter(
                Turno.activo == True,
                func.date(Turno.fecha_hora) >= fecha_inicio,
                func.date(Turno.fecha_hora) <= fecha_fin
            )

            if medico_id:
                base_query = base_query.filter(Turno.id_medico == medico_id)
            
            if especialidad_id:
                base_query = base_query.filter(Turno.id_especialidad == especialidad_id)

            # Contar asistencias
            asistencias = base_query.filter(EstadoTurno.codigo == "ASIS").scalar()

            # Contar inasistencias
            inasistencias = base_query.filter(EstadoTurno.codigo == "INAS").scalar()

            return {
                "asistencias": asistencias or 0,
                "inasistencias": inasistencias or 0
            }
