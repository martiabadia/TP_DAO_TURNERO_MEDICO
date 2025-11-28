/**
 * Módulo de Historial Clínico - Sistema de Turnos Médicos
 * Gestiona la visualización y edición del historial clínico de pacientes
 */

// ============================================================
// ESTADO DEL MÓDULO
// ============================================================

const historialState = {
    pacienteActual: null,
    consultaActual: null,
    consultas: [],
    itemRecetaCount: 0
};

// ============================================================
// INICIALIZACIÓN
// ============================================================

function initHistorial() {
    // Limpiar estado
    historialState.pacienteActual = null;
    historialState.consultaActual = null;
    historialState.consultas = [];
    
    // Ocultar secciones
    document.getElementById('historial-paciente-info').style.display = 'none';
    document.getElementById('historial-consultas-container').style.display = 'none';
    
    // Limpiar campos
    document.getElementById('historial-buscar-dni').value = '';
    document.getElementById('historial-fecha-desde').value = '';
    document.getElementById('historial-fecha-hasta').value = '';
    
    // Configurar eventos de formularios
    setupHistorialEventListeners();
}

function setupHistorialEventListeners() {
    // Formulario de consulta
    const formConsulta = document.getElementById('form-consulta');
    if (formConsulta) {
        formConsulta.onsubmit = async (e) => {
            e.preventDefault();
            await guardarConsulta();
        };
    }
    
    // Formulario de receta
    const formReceta = document.getElementById('form-receta');
    if (formReceta) {
        formReceta.onsubmit = async (e) => {
            e.preventDefault();
            await guardarReceta();
        };
    }
    
    // Búsqueda por Enter
    const inputDNI = document.getElementById('historial-buscar-dni');
    if (inputDNI) {
        inputDNI.onkeypress = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                buscarHistorialPorDNI();
            }
        };
    }
}

// ============================================================
// BÚSQUEDA DE HISTORIAL
// ============================================================

async function buscarHistorialPorDNI() {
    const dni = document.getElementById('historial-buscar-dni').value.trim();
    
    if (!dni) {
        showToast('Ingrese un DNI para buscar', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const fechaDesde = document.getElementById('historial-fecha-desde').value || null;
        const fechaHasta = document.getElementById('historial-fecha-hasta').value || null;
        
        // Buscar paciente por DNI
        const paciente = await api.getPacienteByDNI(dni);
        
        // Obtener historial
        const historial = await api.getHistorialPaciente(paciente.id, fechaDesde, fechaHasta);
        
        // Guardar estado
        historialState.pacienteActual = paciente;
        historialState.consultas = historial.consultas;
        
        // Mostrar información
        mostrarInfoPaciente(historial);
        mostrarConsultas(historial.consultas);
        
        showToast(`Historial de ${historial.paciente_nombre} cargado`, 'success');
        
    } catch (error) {
        console.error('Error buscando historial:', error);
        showToast('No se encontró paciente con ese DNI', 'error');
        
        // Ocultar secciones
        document.getElementById('historial-paciente-info').style.display = 'none';
        document.getElementById('historial-consultas-container').style.display = 'none';
    } finally {
        hideLoading();
    }
}

async function verHistorialPaciente(pacienteId) {
    try {
        showLoading();
        
        // Obtener historial
        const historial = await api.getHistorialPaciente(pacienteId);
        
        // Obtener paciente completo
        const paciente = await api.getPacienteById(pacienteId);
        
        // Guardar estado
        historialState.pacienteActual = paciente;
        historialState.consultas = historial.consultas;
        
        // Navegar a la página de historial
        navigateTo('historial');
        
        // Actualizar campo de búsqueda
        document.getElementById('historial-buscar-dni').value = paciente.dni;
        
        // Mostrar información
        mostrarInfoPaciente(historial);
        mostrarConsultas(historial.consultas);
        
    } catch (error) {
        console.error('Error cargando historial:', error);
        showToast('Error al cargar el historial del paciente', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================
// VISUALIZACIÓN DE DATOS
// ============================================================

function mostrarInfoPaciente(historial) {
    document.getElementById('historial-paciente-nombre').textContent = historial.paciente_nombre;
    document.getElementById('historial-paciente-dni').textContent = historial.paciente_dni;
    document.getElementById('historial-total-consultas').textContent = historial.total_consultas;
    
    // Contar recetas
    let totalRecetas = 0;
    historial.consultas.forEach(c => {
        totalRecetas += c.recetas ? c.recetas.length : 0;
    });
    document.getElementById('historial-total-recetas').textContent = totalRecetas;
    
    document.getElementById('historial-paciente-info').style.display = 'block';
}

function mostrarConsultas(consultas) {
    const container = document.getElementById('historial-consultas-list');
    const sinConsultas = document.getElementById('historial-sin-consultas');
    const consultasContainer = document.getElementById('historial-consultas-container');
    
    consultasContainer.style.display = 'block';
    
    if (!consultas || consultas.length === 0) {
        container.innerHTML = '';
        sinConsultas.style.display = 'flex';
        return;
    }
    
    sinConsultas.style.display = 'none';
    
    container.innerHTML = consultas.map(consulta => {
        const fecha = new Date(consulta.fecha_atencion);
        const fechaStr = fecha.toLocaleDateString('es-AR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
        });
        const horaStr = fecha.toLocaleTimeString('es-AR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const recetasCount = consulta.recetas ? consulta.recetas.length : 0;
        
        return `
            <div class="consulta-card" onclick="verDetalleConsulta(${JSON.stringify(consulta).replace(/"/g, '&quot;')})">
                <div class="consulta-fecha">
                    <div class="fecha-dia">${fecha.getDate()}</div>
                    <div class="fecha-mes">${fecha.toLocaleDateString('es-AR', { month: 'short' })}</div>
                    <div class="fecha-año">${fecha.getFullYear()}</div>
                </div>
                <div class="consulta-contenido">
                    <div class="consulta-header-info">
                        <h4>${consulta.especialidad?.nombre || 'Consulta General'}</h4>
                        <span class="consulta-hora"><i class="fas fa-clock"></i> ${horaStr}</span>
                    </div>
                    <p class="consulta-medico">
                        <i class="fas fa-user-md"></i> ${consulta.medico?.nombre_completo || 'Médico no especificado'}
                    </p>
                    <p class="consulta-diagnostico">
                        <strong>Diagnóstico:</strong> ${consulta.diagnostico || 'No especificado'}
                    </p>
                    <div class="consulta-badges">
                        ${recetasCount > 0 ? `<span class="badge badge-info"><i class="fas fa-prescription"></i> ${recetasCount} receta(s)</span>` : ''}
                    </div>
                </div>
                <div class="consulta-acciones">
                    <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); verDetalleConsulta(${JSON.stringify(consulta).replace(/"/g, '&quot;')})">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================
// DETALLE DE CONSULTA
// ============================================================

function verDetalleConsulta(consulta) {
    historialState.consultaActual = consulta;
    
    const fecha = new Date(consulta.fecha_atencion);
    
    document.getElementById('consulta-det-fecha').textContent = fecha.toLocaleString('es-AR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('consulta-det-medico').textContent = consulta.medico?.nombre_completo || 'No especificado';
    document.getElementById('consulta-det-especialidad').textContent = consulta.especialidad?.nombre || 'No especificada';
    document.getElementById('consulta-det-motivo').textContent = consulta.motivo || 'No especificado';
    document.getElementById('consulta-det-diagnostico').textContent = consulta.diagnostico || 'No especificado';
    document.getElementById('consulta-det-observaciones').textContent = consulta.observaciones || 'Sin observaciones';
    document.getElementById('consulta-det-indicaciones').textContent = consulta.indicaciones || 'Sin indicaciones';
    
    // Mostrar recetas
    const recetasContainer = document.getElementById('consulta-det-recetas');
    if (consulta.recetas && consulta.recetas.length > 0) {
        recetasContainer.innerHTML = consulta.recetas.map(receta => {
            const estadoClass = receta.estado === 'ACTIVA' ? 'badge-success' : 
                               receta.estado === 'ANULADA' ? 'badge-danger' : 'badge-warning';
            
            return `
                <div class="receta-card">
                    <div class="receta-header">
                        <span><i class="fas fa-prescription"></i> Receta #${receta.id}</span>
                        <span class="badge ${estadoClass}">${receta.estado}</span>
                    </div>
                    <div class="receta-fecha">
                        <i class="fas fa-calendar"></i> ${new Date(receta.fecha_emision).toLocaleDateString('es-AR')}
                    </div>
                    <div class="receta-items">
                        ${receta.items.map(item => `
                            <div class="receta-item">
                                <strong>${item.medicamento}</strong>
                                ${item.dosis ? `<span class="item-dosis">${item.dosis}</span>` : ''}
                                ${item.frecuencia ? `<span class="item-frecuencia">${item.frecuencia}</span>` : ''}
                                ${item.duracion ? `<span class="item-duracion">Durante: ${item.duracion}</span>` : ''}
                                ${item.indicaciones ? `<p class="item-indicaciones">${item.indicaciones}</p>` : ''}
                            </div>
                        `).join('')}
                    </div>
                    <div class="receta-acciones">
                        <button class="btn btn-sm btn-primary" onclick="descargarRecetaPDF(${receta.id})">
                            <i class="fas fa-file-pdf"></i> Descargar PDF
                        </button>
                        ${receta.estado === 'ACTIVA' ? `
                            <button class="btn btn-sm btn-danger" onclick="anularRecetaConfirm(${receta.id})">
                                <i class="fas fa-ban"></i> Anular
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    } else {
        recetasContainer.innerHTML = '<p class="text-muted">No hay recetas emitidas para esta consulta</p>';
    }
    
    document.getElementById('modal-ver-consulta').classList.add('show');
}

function cerrarModalVerConsulta() {
    document.getElementById('modal-ver-consulta').classList.remove('show');
}

// ============================================================
// CREAR/EDITAR CONSULTA
// ============================================================

function abrirModalNuevaConsulta(turnoId) {
    document.getElementById('modal-consulta-titulo').innerHTML = '<i class="fas fa-notes-medical"></i> Nueva Consulta';
    document.getElementById('consulta-id').value = '';
    document.getElementById('consulta-turno-id').value = turnoId;
    document.getElementById('consulta-motivo').value = '';
    document.getElementById('consulta-diagnostico').value = '';
    document.getElementById('consulta-observaciones').value = '';
    document.getElementById('consulta-indicaciones').value = '';
    
    document.getElementById('modal-consulta').classList.add('show');
}

function abrirModalEditarConsulta() {
    const consulta = historialState.consultaActual;
    if (!consulta) return;
    
    cerrarModalVerConsulta();
    
    document.getElementById('modal-consulta-titulo').innerHTML = '<i class="fas fa-edit"></i> Editar Consulta';
    document.getElementById('consulta-id').value = consulta.id;
    document.getElementById('consulta-turno-id').value = consulta.turno?.id || '';
    document.getElementById('consulta-motivo').value = consulta.motivo || '';
    document.getElementById('consulta-diagnostico').value = consulta.diagnostico || '';
    document.getElementById('consulta-observaciones').value = consulta.observaciones || '';
    document.getElementById('consulta-indicaciones').value = consulta.indicaciones || '';
    
    document.getElementById('modal-consulta').classList.add('show');
}

function cerrarModalConsulta() {
    document.getElementById('modal-consulta').classList.remove('show');
}

async function guardarConsulta() {
    const consultaId = document.getElementById('consulta-id').value;
    const turnoId = document.getElementById('consulta-turno-id').value;
    
    const consultaData = {
        motivo: document.getElementById('consulta-motivo').value,
        diagnostico: document.getElementById('consulta-diagnostico').value,
        observaciones: document.getElementById('consulta-observaciones').value,
        indicaciones: document.getElementById('consulta-indicaciones').value
    };
    
    try {
        showLoading();
        
        if (consultaId) {
            // Actualizar consulta existente
            await api.updateConsulta(consultaId, consultaData);
            showToast('Consulta actualizada correctamente', 'success');
        } else {
            // Crear nueva consulta
            consultaData.id_turno = parseInt(turnoId);
            await api.createConsulta(consultaData);
            showToast('Consulta registrada correctamente', 'success');
        }
        
        cerrarModalConsulta();
        
        // Recargar historial si estamos en esa página
        if (historialState.pacienteActual) {
            await buscarHistorialPorDNI();
        }
        
    } catch (error) {
        console.error('Error guardando consulta:', error);
        showToast(error.message || 'Error al guardar la consulta', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================
// GESTIÓN DE RECETAS
// ============================================================

function abrirModalNuevaReceta(consultaId) {
    document.getElementById('receta-consulta-id').value = consultaId;
    historialState.itemRecetaCount = 0;
    
    const container = document.getElementById('receta-items-container');
    container.innerHTML = '';
    
    // Agregar primer item
    agregarItemReceta();
    
    document.getElementById('modal-receta').classList.add('show');
}

function cerrarModalReceta() {
    document.getElementById('modal-receta').classList.remove('show');
}

function agregarItemReceta() {
    historialState.itemRecetaCount++;
    const index = historialState.itemRecetaCount;
    
    const container = document.getElementById('receta-items-container');
    const itemHtml = `
        <div class="receta-item-form" id="receta-item-${index}">
            <div class="item-header">
                <h4>Medicamento ${index}</h4>
                ${index > 1 ? `<button type="button" class="btn btn-sm btn-danger" onclick="eliminarItemReceta(${index})"><i class="fas fa-trash"></i></button>` : ''}
            </div>
            <div class="form-row">
                <div class="form-group" style="flex: 2;">
                    <label>Medicamento *</label>
                    <input type="text" name="medicamento-${index}" required placeholder="Nombre del medicamento">
                </div>
                <div class="form-group">
                    <label>Dosis</label>
                    <input type="text" name="dosis-${index}" placeholder="Ej: 500mg">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Frecuencia</label>
                    <input type="text" name="frecuencia-${index}" placeholder="Ej: Cada 8 horas">
                </div>
                <div class="form-group">
                    <label>Duración</label>
                    <input type="text" name="duracion-${index}" placeholder="Ej: 7 días">
                </div>
            </div>
            <div class="form-group">
                <label>Indicaciones especiales</label>
                <textarea name="indicaciones-${index}" rows="2" placeholder="Indicaciones adicionales"></textarea>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', itemHtml);
}

function eliminarItemReceta(index) {
    const item = document.getElementById(`receta-item-${index}`);
    if (item) {
        item.remove();
    }
}

async function guardarReceta() {
    const consultaId = document.getElementById('receta-consulta-id').value;
    
    // Recolectar items
    const items = [];
    const itemForms = document.querySelectorAll('.receta-item-form');
    
    itemForms.forEach(form => {
        const index = form.id.replace('receta-item-', '');
        const medicamento = form.querySelector(`[name="medicamento-${index}"]`).value.trim();
        
        if (medicamento) {
            items.push({
                medicamento: medicamento,
                dosis: form.querySelector(`[name="dosis-${index}"]`).value.trim() || null,
                frecuencia: form.querySelector(`[name="frecuencia-${index}"]`).value.trim() || null,
                duracion: form.querySelector(`[name="duracion-${index}"]`).value.trim() || null,
                indicaciones: form.querySelector(`[name="indicaciones-${index}"]`).value.trim() || null
            });
        }
    });
    
    if (items.length === 0) {
        showToast('Debe agregar al menos un medicamento', 'warning');
        return;
    }
    
    const recetaData = {
        id_consulta: parseInt(consultaId),
        items: items
    };
    
    try {
        showLoading();
        
        await api.createReceta(recetaData);
        showToast('Receta emitida correctamente', 'success');
        
        cerrarModalReceta();
        
        // Recargar historial
        if (historialState.pacienteActual) {
            await buscarHistorialPorDNI();
            
            // Reabrir el modal con los datos actualizados de la consulta
            const consultaActualizada = historialState.consultas.find(c => c.id === parseInt(consultaId));
            if (consultaActualizada) {
                verDetalleConsulta(consultaActualizada);
            }
        }
        
    } catch (error) {
        console.error('Error creando receta:', error);
        showToast(error.message || 'Error al emitir la receta', 'error');
    } finally {
        hideLoading();
    }
}

async function anularRecetaConfirm(recetaId) {
    if (!confirm('¿Está seguro de que desea anular esta receta? Esta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        showLoading();
        
        await api.anularReceta(recetaId);
        showToast('Receta anulada correctamente', 'success');
        
        cerrarModalVerConsulta();
        
        // Recargar historial
        if (historialState.pacienteActual) {
            await buscarHistorialPorDNI();
        }
        
    } catch (error) {
        console.error('Error anulando receta:', error);
        showToast(error.message || 'Error al anular la receta', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================
// INTEGRACIÓN CON TURNOS
// ============================================================

async function registrarConsultaDesdeturno(turnoId) {
    // Primero verificar si ya existe una consulta para este turno
    try {
        const consulta = await api.getConsultaPorTurno(turnoId);
        // Si existe, abrir para editar
        historialState.consultaActual = consulta;
        abrirModalEditarConsulta();
    } catch (error) {
        // Si no existe, abrir para crear
        abrirModalNuevaConsulta(turnoId);
    }
}

function emitirRecetaDesdeConsulta() {
    if (!historialState.consultaActual) {
        showToast('Debe seleccionar una consulta primero', 'warning');
        return;
    }
    
    cerrarModalVerConsulta();
    abrirModalNuevaReceta(historialState.consultaActual.id);
}

// ============================================================
// DESCARGA DE PDF DE RECETA
// ============================================================

async function descargarRecetaPDF(recetaId) {
    try {
        showLoading();
        await api.descargarRecetaPDF(recetaId);
        showToast('Receta descargada correctamente', 'success');
    } catch (error) {
        console.error('Error al descargar receta:', error);
        showToast('Error al descargar la receta: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================
// EXPORTAR FUNCIONES GLOBALES
// ============================================================

window.initHistorial = initHistorial;
window.buscarHistorialPorDNI = buscarHistorialPorDNI;
window.verHistorialPaciente = verHistorialPaciente;
window.verDetalleConsulta = verDetalleConsulta;
window.cerrarModalVerConsulta = cerrarModalVerConsulta;
window.abrirModalNuevaConsulta = abrirModalNuevaConsulta;
window.abrirModalEditarConsulta = abrirModalEditarConsulta;
window.cerrarModalConsulta = cerrarModalConsulta;
window.abrirModalNuevaReceta = abrirModalNuevaReceta;
window.cerrarModalReceta = cerrarModalReceta;
window.agregarItemReceta = agregarItemReceta;
window.eliminarItemReceta = eliminarItemReceta;
window.anularRecetaConfirm = anularRecetaConfirm;
window.descargarRecetaPDF = descargarRecetaPDF;
window.registrarConsultaDesdeturno = registrarConsultaDesdeturno;
window.emitirRecetaDesdeConsulta = emitirRecetaDesdeConsulta;
