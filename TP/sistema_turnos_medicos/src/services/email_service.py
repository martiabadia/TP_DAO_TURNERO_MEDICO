"""
Servicio para envío de correos electrónicos.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)

    def enviar_correo(self, destinatario: str, asunto: str, cuerpo: str):
        """Envía un correo electrónico simple."""
        if not self.smtp_user or not self.smtp_password:
            print(f"Simulando envío de correo a {destinatario}: {asunto}")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = destinatario
            msg['Subject'] = asunto

            msg.attach(MIMEText(cuerpo, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, destinatario, text)
            server.quit()
            print(f"Correo enviado exitosamente a {destinatario}")
        except Exception as e:
            print(f"Error al enviar correo: {e}")

    def enviar_recordatorio_turno(self, turno, paciente):
        """Envía un recordatorio de turno."""
        asunto = "Recordatorio de Turno Médico"
        cuerpo = f"""
        Hola {paciente.nombre},
        
        Te recordamos que tienes un turno médico programado para mañana.
        
        Fecha y Hora: {turno.fecha_hora.strftime('%d/%m/%Y %H:%M')}
        Médico: Dr/a. {turno.medico.nombre_completo}
        Especialidad: {turno.especialidad.nombre}
        
        Por favor, si no puedes asistir, recuerda cancelar el turno con anticipación.
        
        Saludos,
        Sistema de Turnos Médicos
        """
        self.enviar_correo(paciente.email, asunto, cuerpo)
