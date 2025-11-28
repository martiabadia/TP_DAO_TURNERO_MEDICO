// Variables globales para los gráficos
let chartAsistencia = null;
let chartEspecialidad = null;

document.addEventListener('DOMContentLoaded', () => {
    // Inicializar fechas por defecto (mes actual)
    const hoy = new Date();
    const primerDiaMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1);

    document.getElementById('reporte-fecha-inicio').valueAsDate = primerDiaMes;
    document.getElementById('reporte-fecha-fin').valueAsDate = hoy;

    // Cargar médicos y especialidades para los selectores
    cargarMedicosSelector();
    cargarEspecialidadesSelector();
    
    // Mostrar filtros de la pestaña activa inicial (Asistencia)
    setTimeout(() => {
        console.log('Iniciando filtros...');
        actualizarFiltrosVisibles('tab-asistencia');
    }, 100);
});

// Función global para actualizar filtros visibles según la pestaña
window.actualizarFiltrosVisibles = function(tabId) {
    console.log('actualizarFiltrosVisibles llamada con:', tabId);
    
    const tabButton = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    if (!tabButton) {
        console.error('No se encontró el botón de tab:', tabId);
        return;
    }
    
    const filtrosNecesarios = tabButton.getAttribute('data-filtros') || '';
    console.log('Filtros necesarios:', filtrosNecesarios);
    
    const filtroMedico = document.getElementById('filtro-medico-group');
    const filtroEspecialidad = document.getElementById('filtro-especialidad-group');
    
    if (!filtroMedico) {
        console.error('No se encontró filtro-medico-group');
        return;
    }
    if (!filtroEspecialidad) {
        console.error('No se encontró filtro-especialidad-group');
        return;
    }
    
    // Remover clase visible de todos
    filtroMedico.classList.remove('visible');
    filtroEspecialidad.classList.remove('visible');
    
    // Agregar clase visible solo a los necesarios
    if (filtrosNecesarios.includes('medico')) {
        console.log('Mostrando filtro médico');
        filtroMedico.classList.add('visible');
    }
    if (filtrosNecesarios.includes('especialidad')) {
        console.log('Mostrando filtro especialidad');
        filtroEspecialidad.classList.add('visible');
    }
    
    console.log('Filtros actualizados. Médico visible:', filtroMedico.classList.contains('visible'), 'Especialidad visible:', filtroEspecialidad.classList.contains('visible'));
}

async function cargarMedicosSelector() {
    try {
        const medicos = await api.getMedicos();
        const select = document.getElementById('reporte-medico-select');
        select.innerHTML = '<option value="">Todos los médicos</option>';

        medicos.forEach(med => {
            const option = document.createElement('option');
            option.value = med.id;
            option.textContent = `${med.nombre} ${med.apellido} (${med.matricula})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Error al cargar médicos:", error);
        showToast("Error al cargar lista de médicos", "error");
    }
}

async function cargarEspecialidadesSelector() {
    try {
        const especialidades = await api.getEspecialidades();
        const select = document.getElementById('reporte-especialidad-select');
        select.innerHTML = '<option value="">Todas las especialidades</option>';

        especialidades.forEach(esp => {
            const option = document.createElement('option');
            option.value = esp.id;
            option.textContent = esp.nombre;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Error al cargar especialidades:", error);
        showToast("Error al cargar lista de especialidades", "error");
    }
}

async function actualizarReportes() {
    const fechaInicio = document.getElementById('reporte-fecha-inicio').value;
    const fechaFin = document.getElementById('reporte-fecha-fin').value;

    if (!fechaInicio || !fechaFin) {
        showToast("Seleccione un rango de fechas válido", "warning");
        return;
    }

    const medicoId = document.getElementById('reporte-medico-select').value;
    const especialidadId = document.getElementById('reporte-especialidad-select').value;

    showLoading();
    try {
        await Promise.all([
            cargarGraficoAsistencia(fechaInicio, fechaFin, medicoId, especialidadId),
            cargarGraficoEspecialidad(fechaInicio, fechaFin, medicoId, especialidadId),
            cargarReportePacientes(fechaInicio, fechaFin, medicoId, especialidadId),
            cargarReporteMedico(fechaInicio, fechaFin, medicoId, especialidadId)
        ]);

        showToast("Reportes actualizados correctamente", "success");
    } catch (error) {
        console.error("Error al actualizar reportes:", error);
        showToast("Error al obtener datos de reportes", "error");
    } finally {
        hideLoading();
    }
}

async function cargarGraficoAsistencia(inicio, fin, medicoId, especialidadId) {
    let url = `/reportes/asistencia?fecha_inicio=${inicio}&fecha_fin=${fin}`;
    if (medicoId) url += `&medico_id=${medicoId}`;
    if (especialidadId) url += `&especialidad_id=${especialidadId}`;

    const data = await api.request(url);

    const ctx = document.getElementById('chart-asistencia').getContext('2d');

    if (chartAsistencia) {
        chartAsistencia.destroy();
    }

    chartAsistencia = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Asistencias', 'Inasistencias'],
            datasets: [{
                data: [data.asistencias, data.inasistencias],
                backgroundColor: ['#4CAF50', '#F44336'],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: {
                    display: true,
                    text: 'Asistencia vs Inasistencia'
                }
            }
        }
    });
}

async function cargarGraficoEspecialidad(inicio, fin, medicoId, especialidadId) {
    let url = `/reportes/turnos-especialidad?fecha_inicio=${inicio}&fecha_fin=${fin}`;
    if (medicoId) url += `&medico_id=${medicoId}`;
    if (especialidadId) url += `&especialidad_id=${especialidadId}`;

    const data = await api.request(url);

    const ctx = document.getElementById('chart-especialidad').getContext('2d');

    if (chartEspecialidad) {
        chartEspecialidad.destroy();
    }

    chartEspecialidad = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.especialidad),
            datasets: [{
                label: 'Cantidad de Turnos',
                data: data.map(item => item.cantidad),
                backgroundColor: '#2196F3',
                borderColor: '#1976D2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Turnos por Especialidad'
                }
            }
        }
    });
}

async function cargarReporteMedico(fechaInicio, fechaFin, medicoId, especialidadId) {
    const tbody = document.getElementById('reporte-medico-tbody');
    const totalElement = document.getElementById('total-turnos-medico');
    tbody.innerHTML = '';
    if (totalElement) totalElement.textContent = 'Total: 0';

    let url = `/reportes/turnos-medico?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
    if (medicoId) url += `&medico_id=${medicoId}`;
    if (especialidadId) url += `&especialidad_id=${especialidadId}`;

    try {
        const data = await api.request(url);

        if (totalElement) totalElement.textContent = `Total: ${data.length}`;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay turnos en este período</td></tr>';
            return;
        }

        data.forEach(turno => {
            const row = document.createElement('tr');
            const fecha = new Date(turno.fecha_hora).toLocaleString();
            row.innerHTML = `
                <td>${fecha}</td>
                <td>${turno.paciente}</td>
                <td>${turno.especialidad}</td>
                <td><span class="badge badge-${getClassForEstado(turno.estado)}">${turno.estado}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error("Error al cargar reporte de médico:", error);
        showToast("Error al cargar datos del médico", "error");
    }
}

async function cargarReportePacientes(inicio, fin, medicoId, especialidadId) {
    let url = `/reportes/pacientes-atendidos?fecha_inicio=${inicio}&fecha_fin=${fin}`;
    if (medicoId) url += `&medico_id=${medicoId}`;
    if (especialidadId) url += `&especialidad_id=${especialidadId}`;

    const data = await api.request(url);
    const tbody = document.getElementById('reporte-pacientes-tbody');
    const totalElement = document.getElementById('total-pacientes-atendidos');

    tbody.innerHTML = '';
    if (totalElement) totalElement.textContent = `Total: ${data.length}`;

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay pacientes atendidos en este período</td></tr>';
        return;
    }

    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.fecha}</td>
            <td>${item.paciente}</td>
            <td>${item.dni}</td>
            <td>${item.medico}</td>
            <td>${item.especialidad}</td>
        `;
        tbody.appendChild(row);
    });
}

function getClassForEstado(estado) {
    switch (estado) {
        case 'PEND': return 'warning';
        case 'CONF': return 'info';
        case 'ASIS': return 'success';
        case 'CANC': return 'danger';
        case 'INAS': return 'secondary';
        default: return 'primary';
    }
}
