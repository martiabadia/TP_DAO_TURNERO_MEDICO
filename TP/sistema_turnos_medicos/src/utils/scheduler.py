"""
Planificador de tareas en segundo plano.
"""
import asyncio
from datetime import datetime, timedelta
from src.repositories.unit_of_work import UnitOfWork
from src.services.email_service import EmailService

async def check_upcoming_appointments():
    """
    Verifica turnos próximos (24h) y envía recordatorios.
    Esta función se ejecutará periódicamente.
    """
    print("Ejecutando chequeo de recordatorios...")
    try:
        # Usar context manager para inicializar repositorios
        # UnitOfWork se encarga de obtener la sesión del DatabaseManager singleton
        with UnitOfWork() as uow:
            email_service = EmailService()
            
            # Definir rango de tiempo (ej. turnos entre 24h y 25h desde ahora)
            ahora = datetime.now()
            inicio_ventana = ahora + timedelta(hours=23, minutes=30)
            fin_ventana = ahora + timedelta(hours=24, minutes=30)
            
            # Buscar turnos confirmados en ese rango
            turnos = uow.turnos.get_turnos_en_rango(
                fecha_inicio=inicio_ventana,
                fecha_fin=fin_ventana,
                solo_confirmados=True
            )
            
            count = 0
            for turno in turnos:
                paciente = uow.pacientes.get_by_id(turno.id_paciente)
                if paciente:
                    email_service.enviar_recordatorio_turno(turno, paciente)
                    count += 1
            
            if count > 0:
                print(f"Se enviaron {count} recordatorios.")
            
    except Exception as e:
        print(f"Error en job de recordatorios: {e}")

async def start_scheduler():
    """Inicia el loop del planificador."""
    while True:
        await check_upcoming_appointments()
        # Esperar 1 hora antes del próximo chequeo
        await asyncio.sleep(3600)
