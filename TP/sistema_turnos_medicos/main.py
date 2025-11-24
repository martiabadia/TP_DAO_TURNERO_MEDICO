"""
Script principal del Sistema de Gestión de Turnos Médicos.
Inicia el servidor web con FastAPI y Uvicorn.
"""
import sys
import uvicorn
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Función principal que inicia el servidor web."""
    print("=" * 60)
    print("SISTEMA DE GESTIÓN DE TURNOS MÉDICOS")
    print("Universidad - Diseño y Arquitectura Orientada a Objetos")
    print("=" * 60)
    print()
    print("Iniciando servidor web...")
    print()
    print("Acceda a la aplicación en:")
    print("  → http://localhost:8000")
    print()
    print("Documentación de la API:")
    print("  → http://localhost:8000/api/docs")
    print("=" * 60)
    print()
    
    # Iniciar servidor Uvicorn y Scheduler
    import asyncio
    from src.utils.scheduler import start_scheduler
    
    config = uvicorn.Config("src.api.app:app", host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    async def run_system():
        # Ejecutar servidor y scheduler concurrentemente
        await asyncio.gather(
            server.serve(),
            start_scheduler()
        )
        
    asyncio.run(run_system())


if __name__ == "__main__":
    main()
