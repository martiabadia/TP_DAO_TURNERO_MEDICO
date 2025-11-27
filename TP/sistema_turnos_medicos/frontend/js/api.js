/**
 * API Client para el Sistema de Turnos Médicos
 * Maneja todas las peticiones HTTP al backend
 */

const API_BASE_URL = '/api';

class APIClient {
    /**
     * Realiza una petición HTTP
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            
            // Leer el texto primero para evitar problemas con el stream
            const responseText = await response.text();
            
            let data;
            try {
                // Intentar parsear como JSON
                data = responseText ? JSON.parse(responseText) : {};
            } catch (e) {
                // Si no es JSON válido, usar como texto plano
                data = { detail: responseText || `Error ${response.status}` };
            }

            if (!response.ok) {
                // Log detallado del error
                console.error('❌ Error Response:', {
                    status: response.status,
                    statusText: response.statusText,
                    data: data,
                    dataString: JSON.stringify(data, null, 2),
                    url: url
                });
                
                // Extraer el mensaje de error apropiado
                let errorMessage;
                if (data.detail) {
                    // FastAPI devuelve errores en detail
                    if (Array.isArray(data.detail)) {
                        // Errores de validación de Pydantic
                        errorMessage = data.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
                        console.error('Errores de validación:', data.detail);
                    } else {
                        errorMessage = String(data.detail);
                    }
                } else {
                    errorMessage = JSON.stringify(data) || response.statusText || `Error ${response.status}`;
                }
                
                console.error('Mensaje de error final:', errorMessage);
                throw new Error(errorMessage);
            }

            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // ============================================================
    // PACIENTES
    // ============================================================

    async getPacientes(skip = 0, limit = 100) {
        return this.request(`/pacientes?skip=${skip}&limit=${limit}`);
    }

    async getPacienteById(id) {
        return this.request(`/pacientes/${id}`);
    }

    async getPacienteByDNI(dni) {
        return this.request(`/pacientes/dni/${dni}`);
    }

    async createPaciente(pacienteData) {
        return this.request('/pacientes/', {
            method: 'POST',
            body: JSON.stringify(pacienteData),
        });
    }

    async updatePaciente(id, pacienteData) {
        return this.request(`/pacientes/${id}`, {
            method: 'PUT',
            body: JSON.stringify(pacienteData),
        });
    }

    async deletePaciente(id) {
        return this.request(`/pacientes/${id}`, {
            method: 'DELETE',
        });
    }

    // ============================================================
    // MÉDICOS
    // ============================================================

    async getMedicos(skip = 0, limit = 100) {
        return this.request(`/medicos?skip=${skip}&limit=${limit}`);
    }

    async getMedicoById(id) {
        return this.request(`/medicos/${id}`);
    }

    async getMedicosByEspecialidad(especialidadId) {
        return this.request(`/medicos/especialidad/${especialidadId}`);
    }

    async getDisponibilidadesMedico(medicoId) {
        return this.request(`/medicos/${medicoId}/disponibilidades`);
    }

    async createMedico(medicoData) {
        return this.request('/medicos/', {
            method: 'POST',
            body: JSON.stringify(medicoData),
        });
    }

    async updateMedico(medicoId, updateData) {
        return this.request(`/medicos/${medicoId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData),
        });
    }

    async getMedicoById(id) {
        return this.request(`/medicos/${id}`);
    }

    async deleteMedico(medicoId) {
        return this.request(`/medicos/${medicoId}`, {
            method: 'DELETE',
        });
    }

    // ============================================================
    // ESPECIALIDADES
    // ============================================================

    async getEspecialidades(skip = 0, limit = 100) {
        return this.request(`/especialidades?skip=${skip}&limit=${limit}`);
    }

    async getEspecialidadById(id) {
        return this.request(`/especialidades/${id}`);
    }

    // ============================================================
    // TURNOS
    // ============================================================

    async getTurnos(filters = {}) {
        const params = new URLSearchParams();

        if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
        if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
        if (filters.id_paciente) params.append('id_paciente', filters.id_paciente);
        if (filters.id_medico) params.append('id_medico', filters.id_medico);
        if (filters.codigo_estado) params.append('codigo_estado', filters.codigo_estado);
        if (filters.skip) params.append('skip', filters.skip);
        if (filters.limit) params.append('limit', filters.limit);

        const query = params.toString();
        return this.request(`/turnos${query ? '?' + query : ''}`);
    }

    async getTurnoById(id) {
        return this.request(`/turnos/${id}`);
    }

    async getTurnosPaciente(pacienteId, soloFuturos = true) {
        return this.request(`/turnos/paciente/${pacienteId}?solo_futuros=${soloFuturos}`);
    }

    async getTurnosMedico(medicoId, fecha = null) {
        const params = fecha ? `?fecha=${fecha}` : '';
        return this.request(`/turnos/medico/${medicoId}${params}`);
    }

    async getHorariosDisponibles(medicoId, fecha, duracion = 30) {
        const params = new URLSearchParams({
            id_medico: medicoId,
            fecha: fecha,
            duracion: duracion,
        });
        return this.request(`/turnos/disponibles?${params}`);
    }

    async getCalendarioDisponibilidad(medicoId, dias = 14, duracion = 30) {
        const params = new URLSearchParams({
            dias: dias,
            duracion: duracion,
        });
        return this.request(`/turnos/calendario/${medicoId}?${params}`);
    }

    async getTurnosByMedico(medicoId) {
        return this.request(`/turnos/medico/${medicoId}`);
    }

    async createTurno(turnoData) {
        return this.request('/turnos/', {
            method: 'POST',
            body: JSON.stringify(turnoData),
        });
    }

    async updateTurno(turnoId, updateData) {
        return this.request(`/turnos/${turnoId}`, {
            method: 'PATCH',
            body: JSON.stringify(updateData),
        });
    }

    async confirmarTurno(turnoId) {
        return this.request(`/turnos/${turnoId}/confirmar`, {
            method: 'POST',
        });
    }

    async cancelarTurno(turnoId) {
        return this.request(`/turnos/${turnoId}/cancelar`, {
            method: 'POST',
        });
    }

    async deleteTurno(turnoId) {
        return this.request(`/turnos/${turnoId}`, {
            method: 'DELETE',
        });
    }

    // ============================================================
    // DISPONIBILIDADES (HORARIOS)
    // ============================================================

    async getDisponibilidades(medicoId) {
        return this.request(`/medicos/${medicoId}/disponibilidades`);
    }

    async createDisponibilidad(medicoId, disponibilidadData) {
        return this.request(`/medicos/${medicoId}/disponibilidades`, {
            method: 'POST',
            body: JSON.stringify(disponibilidadData),
        });
    }

    async updateDisponibilidad(medicoId, disponibilidadId, updateData) {
        return this.request(`/medicos/${medicoId}/disponibilidades/${disponibilidadId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData),
        });
    }

    async deleteDisponibilidad(medicoId, disponibilidadId) {
        return this.request(`/medicos/${medicoId}/disponibilidades/${disponibilidadId}`, {
            method: 'DELETE',
        });
    }

    // ============================================================
    // BLOQUEOS (VACACIONES, AUSENCIAS)
    // ============================================================

    async getBloqueos(medicoId, fechaDesde = null, fechaHasta = null) {
        let url = `/medicos/${medicoId}/bloqueos`;
        const params = new URLSearchParams();
        
        if (fechaDesde) params.append('fecha_desde', fechaDesde);
        if (fechaHasta) params.append('fecha_hasta', fechaHasta);
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }
        
        return this.request(url);
    }

    async createBloqueo(medicoId, bloqueoData) {
        return this.request(`/medicos/${medicoId}/bloqueos`, {
            method: 'POST',
            body: JSON.stringify(bloqueoData),
        });
    }

    async updateBloqueo(medicoId, bloqueoId, updateData) {
        return this.request(`/medicos/${medicoId}/bloqueos/${bloqueoId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData),
        });
    }

    async deleteBloqueo(medicoId, bloqueoId) {
        return this.request(`/medicos/${medicoId}/bloqueos/${bloqueoId}`, {
            method: 'DELETE',
        });
    }

    // ============================================================
    // ESPECIALIDADES
    // ============================================================

    async getEspecialidades() {
        return this.request('/especialidades/');
    }

    async createEspecialidad(especialidadData) {
        return this.request('/especialidades/', {
            method: 'POST',
            body: JSON.stringify(especialidadData),
        });
    }

    async updateEspecialidad(especialidadId, updateData) {
        return this.request(`/especialidades/${especialidadId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData),
        });
    }

    async deleteEspecialidad(especialidadId) {
        return this.request(`/especialidades/${especialidadId}`, {
            method: 'DELETE',
        });
    }
}

// Instancia global del cliente API
const api = new APIClient();

// Funciones helper para acceso rápido
const apiGetMedicos = () => api.getMedicos();
const apiGetMedicosByEspecialidad = (especialidadId) => api.getMedicosByEspecialidad(especialidadId);
const apiGetDisponibilidades = (medicoId) => api.getDisponibilidades(medicoId);
const apiCreateDisponibilidad = (medicoId, data) => api.createDisponibilidad(medicoId, data);
const apiUpdateDisponibilidad = (medicoId, id, data) => api.updateDisponibilidad(medicoId, id, data);
const apiDeleteDisponibilidad = (medicoId, id) => api.deleteDisponibilidad(medicoId, id);
const apiGetBloqueos = (medicoId, desde, hasta) => api.getBloqueos(medicoId, desde, hasta);
const apiCreateBloqueo = (medicoId, data) => api.createBloqueo(medicoId, data);
const apiUpdateBloqueo = (medicoId, id, data) => api.updateBloqueo(medicoId, id, data);
const apiDeleteBloqueo = (medicoId, id) => api.deleteBloqueo(medicoId, id);
