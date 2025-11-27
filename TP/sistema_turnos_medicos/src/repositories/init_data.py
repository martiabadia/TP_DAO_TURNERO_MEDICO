"""Script para inicializar datos base del sistema."""
from datetime import date, datetime, time, timedelta

from src.domain.especialidad import Especialidad
from src.domain.estado_turno import EstadoTurno
from src.domain.medico import Medico
from src.domain.paciente import Paciente
from src.domain.disponibilidad import DisponibilidadMedico
from src.repositories.unit_of_work import UnitOfWork


def inicializar_estados_turno(uow: UnitOfWork) -> None:
    """
    Crea los estados de turno predefinidos.
    Estos son necesarios para que el sistema funcione.
    """
    estados = [
        EstadoTurno(
            codigo="PEND",
            descripcion="Pendiente - Turno reservado, pendiente de confirmación"
        ),
        EstadoTurno(
            codigo="CONF",
            descripcion="Confirmado - Turno confirmado por el paciente"
        ),
        EstadoTurno(
            codigo="CANC",
            descripcion="Cancelado - Turno cancelado antes de la fecha"
        ),
        EstadoTurno(
            codigo="ASIS",
            descripcion="Asistido - Paciente asistió a la consulta"
        ),
        EstadoTurno(
            codigo="INAS",
            descripcion="Inasistido - Paciente no asistió a la consulta"
        ),
    ]
    
    for estado in estados:
        # Verificar si ya existe
        existing = uow.estados_turno.get_by_codigo(estado.codigo)
        if existing is None:
            uow.estados_turno.add(estado)
            print(f"[INIT] Estado creado: {estado.codigo} - {estado.descripcion}")


def inicializar_especialidades_ejemplo(uow: UnitOfWork) -> None:
    """Crea especialidades de ejemplo para demostración."""
    especialidades = [
        Especialidad(
            nombre="Cardiología",
            descripcion="Especialidad médica que se encarga del estudio, diagnóstico y tratamiento de las enfermedades del corazón y del aparato circulatorio."
        ),
        Especialidad(
            nombre="Pediatría",
            descripcion="Especialidad médica que estudia al niño y sus enfermedades, desde el nacimiento hasta la adolescencia."
        ),
        Especialidad(
            nombre="Traumatología",
            descripcion="Especialidad médica que se dedica al estudio de las lesiones del aparato locomotor."
        ),
        Especialidad(
            nombre="Dermatología",
            descripcion="Especialidad médica que se ocupa del estudio de la estructura y función de la piel y sus enfermedades."
        ),
        Especialidad(
            nombre="Oftalmología",
            descripcion="Especialidad médica que estudia las enfermedades del ojo y sus tratamientos."
        ),
    ]
    
    for esp in especialidades:
        # Verificar si ya existe
        existing = uow.especialidades.get_by_nombre(esp.nombre)
        if existing is None:
            uow.especialidades.add(esp)
            print(f"[INIT] Especialidad creada: {esp.nombre}")


def inicializar_medicos_ejemplo(uow: UnitOfWork) -> None:
    """Crea médicos de ejemplo con especialidades y disponibilidades."""
    # Obtener especialidades
    cardio = uow.especialidades.get_by_nombre("Cardiología")
    pediatria = uow.especialidades.get_by_nombre("Pediatría")
    trauma = uow.especialidades.get_by_nombre("Traumatología")
    
    if not all([cardio, pediatria, trauma]):
        print("[INIT] ERROR: Especialidades no encontradas")
        return
    
    medicos_data = [
        {
            "matricula": "MP12345",
            "nombre": "María",
            "apellido": "González",
            "dni": "30123456",
            "email": "maria.gonzalez@hospital.com",
            "telefono": "261-1234567",
            "especialidades": [cardio],
            "disponibilidad": [
                # Lunes, Miércoles, Viernes 8-12
                (0, time(8, 0), time(12, 0), 30),  # Lunes
                (2, time(8, 0), time(12, 0), 30),  # Miércoles
                (4, time(8, 0), time(12, 0), 30),  # Viernes
            ]
        },
        {
            "matricula": "MP54321",
            "nombre": "Juan",
            "apellido": "Pérez",
            "dni": "28987654",
            "email": "juan.perez@hospital.com",
            "telefono": "261-7654321",
            "especialidades": [pediatria, trauma],
            "disponibilidad": [
                # Martes, Jueves 14-18
                (1, time(14, 0), time(18, 0), 30),  # Martes
                (3, time(14, 0), time(18, 0), 30),  # Jueves
            ]
        },
        {
            "matricula": "MP98765",
            "nombre": "Ana",
            "apellido": "Martínez",
            "dni": "32456789",
            "email": "ana.martinez@hospital.com",
            "telefono": "261-9876543",
            "especialidades": [trauma],
            "disponibilidad": [
                # Lunes a Viernes 9-13
                (0, time(9, 0), time(13, 0), 30),
                (1, time(9, 0), time(13, 0), 30),
                (2, time(9, 0), time(13, 0), 30),
                (3, time(9, 0), time(13, 0), 30),
                (4, time(9, 0), time(13, 0), 30),
            ]
        },
    ]
    
    for data in medicos_data:
        # Verificar si ya existe por matrícula, DNI o email
        existing_mat = uow.medicos.get_by_matricula(data["matricula"])
        existing_dni = uow.medicos.exists_dni(data["dni"])
        existing_email = uow.medicos.exists_email(data["email"])
        
        if existing_mat is not None or existing_dni or existing_email:
            continue
        
        # Crear médico
        medico = Medico(
            matricula=data["matricula"],
            nombre=data["nombre"],
            apellido=data["apellido"],
            dni=data["dni"],
            email=data["email"],
            telefono=data["telefono"]
        )
        
        # Asignar especialidades
        for esp in data["especialidades"]:
            medico.especialidades.append(esp)
        
        uow.medicos.add(medico)
        uow.flush()  # Para obtener el ID del médico
        
        # Crear disponibilidades
        for dia, hora_desde, hora_hasta, duracion in data["disponibilidad"]:
            disp = DisponibilidadMedico(
                id_medico=medico.id,
                dia_semana=dia,
                hora_desde=hora_desde,
                hora_hasta=hora_hasta,
                duracion_slot=duracion
            )
            uow.disponibilidades.add(disp)
        
        print(f"[INIT] Médico creado: Dr./Dra. {medico.nombre_completo} - {medico.matricula}")


def inicializar_pacientes_ejemplo(uow: UnitOfWork) -> None:
    """Crea pacientes de ejemplo."""
    pacientes_data = [
        {
            "dni": "35123456",
            "nombre": "Carlos",
            "apellido": "Rodríguez",
            "fecha_nacimiento": date(1988, 3, 15),
            "email": "carlos.rodriguez@email.com",
            "telefono": "261-2345678",
            "direccion": "Av. San Martín 1234, Mendoza",
            "obra_social": "OSDE",
            "numero_afiliado": "12345678/00"
        },
        {
            "dni": "40987654",
            "nombre": "Laura",
            "apellido": "Fernández",
            "fecha_nacimiento": date(1995, 7, 22),
            "email": "laura.fernandez@email.com",
            "telefono": "261-8765432",
            "direccion": "Calle Belgrano 567, Godoy Cruz",
            "obra_social": "Swiss Medical",
            "numero_afiliado": "87654321/01"
        },
        {
            "dni": "38456789",
            "nombre": "Roberto",
            "apellido": "Gómez",
            "fecha_nacimiento": date(1992, 11, 30),
            "email": "roberto.gomez@email.com",
            "telefono": "261-3456789",
            "direccion": "Av. Las Heras 890, Mendoza",
            "obra_social": "Osecac",
            "numero_afiliado": "45678912/02"
        },
        {
            "dni": "42789123",
            "nombre": "Sofía",
            "apellido": "López",
            "fecha_nacimiento": date(1998, 5, 18),
            "email": "sofia.lopez@email.com",
            "telefono": "261-4567891",
            "direccion": "Calle Mitre 234, Luján de Cuyo",
            "obra_social": "Osde",
            "numero_afiliado": "78912345/03"
        },
    ]
    
    for data in pacientes_data:
        # Verificar si ya existe por DNI o email
        existing_dni = uow.pacientes.get_by_dni(data["dni"])
        existing_email = uow.pacientes.get_by_email(data["email"])
        
        if existing_dni is not None or existing_email is not None:
            continue
        
        paciente = Paciente(**data)
        uow.pacientes.add(paciente)
        print(f"[INIT] Paciente creado: {paciente.nombre_completo} - DNI {paciente.dni}")


def inicializar_datos_base() -> None:
    """
    Inicializa todos los datos base del sistema.
    Se ejecuta al inicio de la aplicación.
    """
    print("\n" + "="*60)
    print("INICIALIZACIÓN DE DATOS BASE")
    print("="*60 + "\n")
    
    with UnitOfWork() as uow:
        try:
            # 1. Estados de turno (OBLIGATORIO)
            print("[1/4] Inicializando estados de turno...")
            inicializar_estados_turno(uow)
            
            # 2. Especialidades de ejemplo
            print("\n[2/4] Inicializando especialidades de ejemplo...")
            inicializar_especialidades_ejemplo(uow)
            
            # 3. Médicos de ejemplo con disponibilidades
            print("\n[3/4] Inicializando médicos de ejemplo...")
            inicializar_medicos_ejemplo(uow)
            
            # 4. Pacientes de ejemplo
            print("\n[4/4] Inicializando pacientes de ejemplo...")
            inicializar_pacientes_ejemplo(uow)
            
            # Commit de todos los cambios
            uow.commit()
            
            print("\n" + "="*60)
            print("INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n[ERROR] Error durante la inicialización: {e}")
            uow.rollback()
            raise


if __name__ == "__main__":
    # Para testing independiente
    from src.repositories.database import db_manager
    
    db_manager.initialize()
    db_manager.create_tables()
    inicializar_datos_base()
