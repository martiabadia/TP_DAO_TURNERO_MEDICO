/**
 * Módulo de Gestión de Horarios y Bloqueos de Médicos
 * Maneja la asignación de horarios semanales y bloqueos (vacaciones, ausencias)
 */

// ============================================================
// ESTADO DEL MÓDULO
// ============================================================

const horariosState = {
    medicoSeleccionado: null,
    disponibilidades: [],
    bloqueos: [],
    modoEdicion: false,
    itemEditando: null
};

// ============================================================
// CONSTANTES
// ============================================================

const DIAS_SEMANA = [
    'Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'
];

const DIAS_CLASE = [
    'domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'
];

// ============================================================
// INICIALIZACIÓN
// ============================================================

async function initHorarios() {
    console.log('[Horarios] Inicializando módulo de horarios...');
    
    // Configurar vista inicial
    limpiarVistas();
    
    await cargarMedicosParaHorarios();
    setupEventListeners();
    console.log('[Horarios] Módulo inicializado correctamente');
}

function setupEventListeners() {
    // Selector de médico
    const medicoSelect = document.getElementById('medico-horarios-select');
    if (medicoSelect) {
        medicoSelect.addEventListener('change', onMedicoSelected);
    }
    
    // Botones de acción
    const btnNuevaDisponibilidad = document.getElementById('btn-nueva-disponibilidad');
    if (btnNuevaDisponibilidad) {
        btnNuevaDisponibilidad.addEventListener('click', mostrarFormularioDisponibilidad);
    }
    
    const btnNuevoBloqueo = document.getElementById('btn-nuevo-bloqueo');
    if (btnNuevoBloqueo) {
        btnNuevoBloqueo.addEventListener('click', mostrarFormularioBloqueo);
    }
    
    // Formularios
    const formDisponibilidad = document.getElementById('form-disponibilidad');
    if (formDisponibilidad) {
        formDisponibilidad.addEventListener('submit', guardarDisponibilidad);
    }
    
    const formBloqueo = document.getElementById('form-bloqueo');
    if (formBloqueo) {
        formBloqueo.addEventListener('submit', guardarBloqueo);
    }
    
    // Botones de cancelar
    const btnCancelarDisp = document.getElementById('btn-cancelar-disponibilidad');
    if (btnCancelarDisp) {
        btnCancelarDisp.addEventListener('click', cancelarFormularioDisponibilidad);
    }
    
    const btnCancelarBloq = document.getElementById('btn-cancelar-bloqueo');
    if (btnCancelarBloq) {
        btnCancelarBloq.addEventListener('click', cancelarFormularioBloqueo);
    }
}

// ============================================================
// CARGA DE MÉDICOS
// ============================================================

async function cargarMedicosParaHorarios() {
    try {
        console.log('[Horarios] Cargando médicos...');
        const medicos = await apiGetMedicos();
        console.log('[Horarios] Médicos cargados:', medicos);
        
        const select = document.getElementById('medico-horarios-select');
        
        if (!select) {
            console.error('[Horarios] No se encontró el select de médicos');
            return;
        }
        
        select.innerHTML = '<option value="">-- Seleccione un médico --</option>';
        
        medicos.forEach(medico => {
            const option = document.createElement('option');
            option.value = medico.id;
            option.textContent = `${medico.apellido}, ${medico.nombre} - Mat. ${medico.matricula}`;
            select.appendChild(option);
        });
        
        console.log('[Horarios] Select poblado con', medicos.length, 'médicos');
    } catch (error) {
        console.error('[Horarios] Error al cargar médicos:', error);
        showToast('Error al cargar la lista de médicos', 'error');
    }
}

// ============================================================
// EVENTOS DE MÉDICO
// ============================================================

async function onMedicoSelected(event) {
    const medicoId = event.target.value;
    
    if (!medicoId) {
        horariosState.medicoSeleccionado = null;
        limpiarVistas();
        return;
    }
    
    horariosState.medicoSeleccionado = parseInt(medicoId);
    await cargarDatosMedico();
}

async function cargarDatosMedico() {
    if (!horariosState.medicoSeleccionado) return;
    
    try {
        showLoading();
        
        // Cargar disponibilidades y bloqueos en paralelo
        const [disponibilidades, bloqueos] = await Promise.all([
            apiGetDisponibilidades(horariosState.medicoSeleccionado),
            apiGetBloqueos(horariosState.medicoSeleccionado)
        ]);
        
        horariosState.disponibilidades = disponibilidades;
        horariosState.bloqueos = bloqueos;
        
        renderDisponibilidades();
        renderBloqueos();
        mostrarSeccionesGestion();
        
    } catch (error) {
        console.error('Error al cargar datos del médico:', error);
        showToast('Error al cargar los horarios del médico', 'error');
    } finally {
        hideLoading();
    }
}

function limpiarVistas() {
    horariosState.disponibilidades = [];
    horariosState.bloqueos = [];
    
    const disponibilidadesContainer = document.getElementById('disponibilidades-container');
    if (disponibilidadesContainer) {
        disponibilidadesContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-arrow-up"></i>
                <div>
                    <strong>Seleccione un médico</strong> para gestionar sus horarios y disponibilidad.
                </div>
            </div>
        `;
    }
    
    const bloqueosContainer = document.getElementById('bloqueos-container');
    if (bloqueosContainer) {
        bloqueosContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-arrow-up"></i>
                <div>
                    <strong>Seleccione un médico</strong> para gestionar sus bloqueos y vacaciones.
                </div>
            </div>
        `;
    }
    
    ocultarSeccionesGestion();
}

function mostrarSeccionesGestion() {
    const seccionDisp = document.getElementById('seccion-disponibilidades');
    const seccionBloq = document.getElementById('seccion-bloqueos');
    
    if (seccionDisp) seccionDisp.style.display = 'block';
    if (seccionBloq) seccionBloq.style.display = 'block';
}

function ocultarSeccionesGestion() {
    const seccionDisp = document.getElementById('seccion-disponibilidades');
    const seccionBloq = document.getElementById('seccion-bloqueos');
    
    if (seccionDisp) seccionDisp.style.display = 'none';
    if (seccionBloq) seccionBloq.style.display = 'none';
}

// ============================================================
// RENDERIZADO DE DISPONIBILIDADES
// ============================================================

function renderDisponibilidades() {
    const container = document.getElementById('disponibilidades-container');
    if (!container) return;
    
    if (horariosState.disponibilidades.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                Este médico aún no tiene horarios asignados. Use el botón "Agregar Horario" para comenzar.
            </div>
        `;
        return;
    }
    
    // Agrupar por día de la semana
    const porDia = {};
    horariosState.disponibilidades.forEach(disp => {
        if (!porDia[disp.dia_semana]) {
            porDia[disp.dia_semana] = [];
        }
        porDia[disp.dia_semana].push(disp);
    });
    
    let html = '<div class="horarios-semanales">';
    
    // Mostrar todos los días (0-6)
    for (let dia = 0; dia < 7; dia++) {
        const disponibilidades = porDia[dia] || [];
        const claseActivo = disponibilidades.length > 0 ? 'activo' : 'inactivo';
        
        html += `
            <div class="dia-horario ${claseActivo}" data-dia="${dia}">
                <div class="dia-header ${DIAS_CLASE[dia]}">
                    <h4>${DIAS_SEMANA[dia]}</h4>
                </div>
                <div class="dia-content">
        `;
        
        if (disponibilidades.length === 0) {
            html += '<p class="sin-horario">Sin horarios</p>';
        } else {
            disponibilidades.forEach(disp => {
                html += `
                    <div class="horario-item" data-id="${disp.id}">
                        <div class="horario-info">
                            <i class="fas fa-clock"></i>
                            <span class="horario-texto">
                                ${disp.hora_desde} - ${disp.hora_hasta}
                            </span>
                            <span class="horario-duracion">
                                (${disp.duracion_slot} min)
                            </span>
                        </div>
                        <div class="horario-acciones">
                            <button class="btn-icon btn-edit" onclick="editarDisponibilidad(${disp.id})" 
                                    title="Editar">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-icon btn-delete" onclick="eliminarDisponibilidad(${disp.id})" 
                                    title="Eliminar">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
            });
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// ============================================================
// RENDERIZADO DE BLOQUEOS
// ============================================================

function renderBloqueos() {
    const container = document.getElementById('bloqueos-container');
    if (!container) return;
    
    if (horariosState.bloqueos.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                No hay bloqueos registrados para este médico.
            </div>
        `;
        return;
    }
    
    // Ordenar por fecha
    const bloqueosOrdenados = [...horariosState.bloqueos].sort((a, b) => {
        return new Date(a.inicio) - new Date(b.inicio);
    });
    
    let html = '<div class="lista-bloqueos">';
    
    bloqueosOrdenados.forEach(bloqueo => {
        const inicio = new Date(bloqueo.inicio);
        const fin = new Date(bloqueo.fin);
        const ahora = new Date();
        const esActivo = inicio <= ahora && fin >= ahora;
        const esFuturo = inicio > ahora;
        
        let estadoClase = 'pasado';
        let estadoTexto = 'Finalizado';
        let estadoIcono = 'fa-check-circle';
        
        if (esActivo) {
            estadoClase = 'activo';
            estadoTexto = 'En curso';
            estadoIcono = 'fa-clock';
        } else if (esFuturo) {
            estadoClase = 'futuro';
            estadoTexto = 'Programado';
            estadoIcono = 'fa-calendar';
        }
        
        html += `
            <div class="bloqueo-item ${estadoClase}" data-id="${bloqueo.id}">
                <div class="bloqueo-icono">
                    <i class="fas fa-ban"></i>
                </div>
                <div class="bloqueo-info">
                    <div class="bloqueo-fechas">
                        <strong>
                            ${formatearFecha(inicio)} - ${formatearFecha(fin)}
                        </strong>
                    </div>
                    <div class="bloqueo-motivo">
                        ${bloqueo.motivo || '<em>Sin motivo especificado</em>'}
                    </div>
                    <div class="bloqueo-estado">
                        <i class="fas ${estadoIcono}"></i>
                        <span>${estadoTexto}</span>
                    </div>
                </div>
                <div class="bloqueo-acciones">
                    ${esFuturo || esActivo ? `
                        <button class="btn-icon btn-edit" onclick="editarBloqueo(${bloqueo.id})" 
                                title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon btn-delete" onclick="eliminarBloqueo(${bloqueo.id})" 
                                title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// ============================================================
// FORMULARIOS - DISPONIBILIDADES
// ============================================================

function mostrarFormularioDisponibilidad() {
    horariosState.modoEdicion = false;
    horariosState.itemEditando = null;
    
    const modal = document.getElementById('modal-disponibilidad');
    const form = document.getElementById('form-disponibilidad');
    
    if (!modal || !form) return;
    
    // Resetear formulario
    form.reset();
    document.getElementById('disponibilidad-titulo').textContent = 'Agregar Horario';
    
    // Valores por defecto
    document.getElementById('disp-duracion-slot').value = 30;
    
    modal.style.display = 'flex';
}

async function editarDisponibilidad(id) {
    const disponibilidad = horariosState.disponibilidades.find(d => d.id === id);
    if (!disponibilidad) return;
    
    horariosState.modoEdicion = true;
    horariosState.itemEditando = id;
    
    const modal = document.getElementById('modal-disponibilidad');
    const form = document.getElementById('form-disponibilidad');
    
    if (!modal || !form) return;
    
    // Llenar formulario
    document.getElementById('disponibilidad-titulo').textContent = 'Editar Horario';
    document.getElementById('disp-dia-semana').value = disponibilidad.dia_semana;
    document.getElementById('disp-hora-desde').value = disponibilidad.hora_desde;
    document.getElementById('disp-hora-hasta').value = disponibilidad.hora_hasta;
    document.getElementById('disp-duracion-slot').value = disponibilidad.duracion_slot;
    
    // Deshabilitar día de semana en edición
    document.getElementById('disp-dia-semana').disabled = true;
    
    modal.style.display = 'flex';
}

async function guardarDisponibilidad(event) {
    event.preventDefault();
    
    const formData = {
        dia_semana: parseInt(document.getElementById('disp-dia-semana').value),
        hora_desde: document.getElementById('disp-hora-desde').value,
        hora_hasta: document.getElementById('disp-hora-hasta').value,
        duracion_slot: parseInt(document.getElementById('disp-duracion-slot').value)
    };
    
    // Validaciones básicas
    if (formData.hora_desde >= formData.hora_hasta) {
        showToast('La hora de fin debe ser posterior a la hora de inicio', 'error');
        return;
    }
    
    try {
        showLoading();
        
        if (horariosState.modoEdicion) {
            // Actualizar
            await apiUpdateDisponibilidad(
                horariosState.medicoSeleccionado,
                horariosState.itemEditando,
                formData
            );
            showToast('Horario actualizado correctamente', 'success');
        } else {
            // Crear
            await apiCreateDisponibilidad(horariosState.medicoSeleccionado, formData);
            showToast('Horario agregado correctamente', 'success');
        }
        
        // Recargar datos
        await cargarDatosMedico();
        cancelarFormularioDisponibilidad();
        
    } catch (error) {
        console.error('Error al guardar disponibilidad:', error);
        const mensaje = error.detail || 'Error al guardar el horario';
        showToast(mensaje, 'error');
    } finally {
        hideLoading();
    }
}

function cancelarFormularioDisponibilidad() {
    const modal = document.getElementById('modal-disponibilidad');
    if (modal) {
        modal.style.display = 'none';
    }
    
    const form = document.getElementById('form-disponibilidad');
    if (form) {
        form.reset();
    }
    
    // Re-habilitar día de semana
    const diaSelect = document.getElementById('disp-dia-semana');
    if (diaSelect) {
        diaSelect.disabled = false;
    }
    
    horariosState.modoEdicion = false;
    horariosState.itemEditando = null;
}

async function eliminarDisponibilidad(id) {
    const disponibilidad = horariosState.disponibilidades.find(d => d.id === id);
    if (!disponibilidad) return;
    
    const dia = DIAS_SEMANA[disponibilidad.dia_semana];
    const confirmacion = confirm(
        `¿Está seguro de eliminar el horario del ${dia} de ${disponibilidad.hora_desde} a ${disponibilidad.hora_hasta}?`
    );
    
    if (!confirmacion) return;
    
    try {
        showLoading();
        
        await apiDeleteDisponibilidad(horariosState.medicoSeleccionado, id);
        showToast('Horario eliminado correctamente', 'success');
        
        await cargarDatosMedico();
        
    } catch (error) {
        console.error('Error al eliminar disponibilidad:', error);
        showToast('Error al eliminar el horario', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================
// FORMULARIOS - BLOQUEOS
// ============================================================

function mostrarFormularioBloqueo() {
    horariosState.modoEdicion = false;
    horariosState.itemEditando = null;
    
    const modal = document.getElementById('modal-bloqueo');
    const form = document.getElementById('form-bloqueo');
    
    if (!modal || !form) return;
    
    // Resetear formulario
    form.reset();
    document.getElementById('bloqueo-titulo').textContent = 'Agregar Bloqueo';
    
    // Fecha mínima: hoy
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('bloqueo-inicio').min = hoy;
    document.getElementById('bloqueo-fin').min = hoy;
    
    modal.style.display = 'flex';
}

async function editarBloqueo(id) {
    const bloqueo = horariosState.bloqueos.find(b => b.id === id);
    if (!bloqueo) return;
    
    horariosState.modoEdicion = true;
    horariosState.itemEditando = id;
    
    const modal = document.getElementById('modal-bloqueo');
    const form = document.getElementById('form-bloqueo');
    
    if (!modal || !form) return;
    
    // Llenar formulario
    document.getElementById('bloqueo-titulo').textContent = 'Editar Bloqueo';
    
    const inicio = new Date(bloqueo.inicio);
    const fin = new Date(bloqueo.fin);
    
    // Formato YYYY-MM-DD para input type="date"
    document.getElementById('bloqueo-inicio').value = inicio.toISOString().slice(0, 10);
    document.getElementById('bloqueo-fin').value = fin.toISOString().slice(0, 10);
    document.getElementById('bloqueo-motivo').value = bloqueo.motivo || '';
    
    modal.style.display = 'flex';
}

async function guardarBloqueo(event) {
    event.preventDefault();
    
    const formData = {
        inicio: document.getElementById('bloqueo-inicio').value,
        fin: document.getElementById('bloqueo-fin').value,
        motivo: document.getElementById('bloqueo-motivo').value
    };
    
    // Validaciones
    if (new Date(formData.inicio) >= new Date(formData.fin)) {
        showToast('La fecha de fin debe ser posterior a la fecha de inicio', 'error');
        return;
    }
    
    try {
        showLoading();
        
        if (horariosState.modoEdicion) {
            // Actualizar
            await apiUpdateBloqueo(
                horariosState.medicoSeleccionado,
                horariosState.itemEditando,
                formData
            );
            showToast('Bloqueo actualizado correctamente', 'success');
        } else {
            // Crear
            await apiCreateBloqueo(horariosState.medicoSeleccionado, formData);
            showToast('Bloqueo agregado correctamente', 'success');
        }
        
        // Recargar datos
        await cargarDatosMedico();
        cancelarFormularioBloqueo();
        
    } catch (error) {
        console.error('Error al guardar bloqueo:', error);
        console.log('Error detail:', error.detail);
        console.log('Error message:', error.message);
        
        // Usar message si detail no está disponible
        const mensajeError = error.detail || error.message || 'Error desconocido';
        const mensaje = `Error al generar el bloqueo: ${mensajeError}`;
        
        showToast(mensaje, 'error');
    } finally {
        hideLoading();
    }
}

function cancelarFormularioBloqueo() {
    const modal = document.getElementById('modal-bloqueo');
    if (modal) {
        modal.style.display = 'none';
    }
    
    const form = document.getElementById('form-bloqueo');
    if (form) {
        form.reset();
    }
    
    horariosState.modoEdicion = false;
    horariosState.itemEditando = null;
}

async function eliminarBloqueo(id) {
    const bloqueo = horariosState.bloqueos.find(b => b.id === id);
    if (!bloqueo) return;
    
    const inicio = new Date(bloqueo.inicio);
    const confirmacion = confirm(
        `¿Está seguro de eliminar el bloqueo desde ${formatearFecha(inicio)}?\n\n` +
        `Motivo: ${bloqueo.motivo || 'Sin especificar'}`
    );
    
    if (!confirmacion) return;
    
    try {
        showLoading();
        
        await apiDeleteBloqueo(horariosState.medicoSeleccionado, id);
        showToast('Bloqueo eliminado correctamente', 'success');
        
        await cargarDatosMedico();
        
    } catch (error) {
        console.error('Error al eliminar bloqueo:', error);
        showToast('Error al eliminar el bloqueo', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================
// FUNCIONES AUXILIARES
// ============================================================

function formatearFecha(fecha) {
    const d = new Date(fecha);
    return d.toLocaleDateString('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function formatearHora(fecha) {
    const d = new Date(fecha);
    return d.toLocaleTimeString('es-AR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================================
// EXPORTAR FUNCIONES PÚBLICAS
// ============================================================

// Hacer disponibles globalmente las funciones que se llaman desde HTML
window.initHorarios = initHorarios;
window.editarDisponibilidad = editarDisponibilidad;
window.eliminarDisponibilidad = eliminarDisponibilidad;
window.editarBloqueo = editarBloqueo;
window.eliminarBloqueo = eliminarBloqueo;
