# Cambios en Base de Datos - Función Editar Paciente

## ¿Qué cambió?

Se agregó la funcionalidad de **editar pacientes** que incluye los campos:
- `direccion`
- `obra_social`
- `numero_afiliado`

Estos campos ya existían en el modelo de dominio `Paciente`, pero **NO estaban incluidos** en el esquema de respuesta de la API (`PacienteResponse`).

## ¿Necesito recrear la base de datos?

**NO es necesario** recrear la base de datos porque:

1. **Los campos ya existían** en la tabla `pacientes` desde el principio
2. SQLAlchemy maneja automáticamente la estructura de las tablas
3. Solo se actualizó el esquema de respuesta de la API

## ¿Qué fue corregido?

### Backend

1. **`src/api/schemas.py`**
   - Se agregaron los campos faltantes a `PacienteResponse`:
     - `direccion: str`
     - `obra_social: Optional[str]`
     - `numero_afiliado: Optional[str]`

2. **`src/api/routes/pacientes.py`**
   - Se corrigió el método `delete` para pasar la entidad en lugar del ID
   - Se agregó el endpoint `PUT /pacientes/{id}` para editar pacientes
   - Se agregó validación de unicidad de DNI y email al editar

3. **`src/api/schemas.py`**
   - Se agregó `PacienteUpdate` con todos los campos opcionales para edición

### Frontend

1. **`frontend/js/api.js`**
   - Se agregó el método `updatePaciente(id, data)`

2. **`frontend/index.html`**
   - Se agregó modal `modal-editar-paciente` con formulario completo
   - Se agregó botón de editar en la tabla de pacientes

3. **`frontend/js/app.js`**
   - Se agregaron funciones:
     - `abrirModalEditarPaciente(id)` - Abre modal y carga datos
     - `cerrarModalEditarPaciente()` - Cierra modal
     - Event listener para el formulario de edición
   - Se modificó `loadPacientesTable()` para incluir botón de editar

## ¿Qué hacer si quiero empezar desde cero?

Si deseas empezar con una base de datos limpia:

```bash
# Opción 1: Eliminar el archivo de la base de datos
rm data/turnos_medicos.db

# Opción 2: Usar el script de generación (si existe)
python -m src.repositories.generate_test_data
```

La próxima vez que ejecutes la aplicación, se creará automáticamente con la estructura correcta.

## Verificación

Para verificar que todo funciona:

1. Inicia la aplicación: `python main.py`
2. Ve a la sección "Pacientes"
3. Intenta editar un paciente existente
4. Los campos `direccion`, `obra_social` y `numero_afiliado` ahora deberían guardarse y mostrarse correctamente

## Notas Importantes

- **SQLAlchemy** crea las tablas automáticamente basándose en los modelos de dominio
- La función `create_tables()` en `database.py` es **idempotente** (solo crea las tablas si no existen)
- Los datos de ejemplo se insertan solo si no existen previamente (verificación por DNI)
