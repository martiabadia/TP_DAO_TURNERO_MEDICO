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
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `Error ${response.status}`);
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
}

// Instancia global del cliente API
const api = new APIClient();
