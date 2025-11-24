# Cómo ejecutar el Sistema de Turnos Médicos

## Prerrequisitos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

## Instalación

1.  **Crear un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    # En Windows:
    .\venv\Scripts\activate
    # En Linux/Mac:
    source venv/bin/activate
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Ejecución

1.  **Iniciar el servidor:**
    Ejecuta el siguiente comando desde la raíz del proyecto:
    ```bash
    python main.py
    ```
    
    Esto iniciará:
    - La API REST en el puerto 8000.
    - El planificador de recordatorios (Scheduler).
    - La base de datos (se creará automáticamente el archivo `turnos.db` y se cargarán datos de ejemplo).

## Testing y Uso

1.  **Interfaz de Documentación (Swagger UI):**
    - Abre tu navegador en: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
    - Aquí puedes probar todos los endpoints (Crear médicos, turnos, pacientes, etc.).

2.  **Frontend (Si está disponible):**
    - Abre: [http://localhost:8000](http://localhost:8000)

3.  **Configuración de Email (Opcional):**
    Para que el envío de correos funcione realmente, configura las variables de entorno antes de ejecutar:
    - `SMTP_SERVER` (default: smtp.gmail.com)
    - `SMTP_PORT` (default: 587)
    - `SMTP_USER` (tu email)
    - `SMTP_PASSWORD` (tu contraseña de aplicación)

    En Windows (PowerShell):
    ```powershell
    $env:SMTP_USER="tucorreo@gmail.com"
    $env:SMTP_PASSWORD="tucontraseña"
    python main.py
    ```

## Verificación de Funcionalidades Nuevas

### 1. Gestión de Médicos (Frontend)
1.  Abre [http://localhost:8000](http://localhost:8000).
2.  Haz clic en el botón **"Médicos"** en la barra de navegación superior.
3.  **Crear Médico**:
    - Ve a la pestaña "Nuevo Médico".
    - Completa el formulario (Matrícula, DNI, Nombre, etc.).
    - Selecciona al menos una especialidad.
    - Haz clic en "Registrar Médico".
4.  **Listar y Eliminar**:
    - Verás al nuevo médico en la pestaña "Listado".
    - Puedes eliminarlo usando el botón rojo de basura.

### 2. Recordatorios de Email
- El sistema verifica automáticamente cada hora si hay turnos próximos (entre 23.5 y 24.5 horas en el futuro).
- Para probarlo:
    1.  Asegúrate de tener configuradas las variables de entorno SMTP.
    2.  Crea un turno para mañana a esta misma hora (aprox).
    3.  Espera a que el scheduler se ejecute (o reinicia la app para forzar el chequeo inicial).
    4.  Deberías ver en la consola: `Se enviaron X recordatorios`.
