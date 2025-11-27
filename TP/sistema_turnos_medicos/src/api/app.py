"""
Aplicación principal de FastAPI.
Configura la API REST del sistema de turnos médicos.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from src.api.routes import pacientes, medicos, especialidades, turnos, reportes, historial
from src.repositories.database import db_manager
from src.repositories.init_data import inicializar_datos_base

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión de Turnos Médicos",
    description="API REST para gestión de turnos médicos - Universidad DAO",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos (frontend)
static_path = Path(__file__).parent.parent.parent / "frontend"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ============================================================
# EVENTOS DE INICIO Y CIERRE
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Inicializa la base de datos al arrancar la aplicación."""
    print("=" * 60)
    print("INICIANDO SISTEMA DE TURNOS MÉDICOS")
    print("=" * 60)
    
    # Inicializar base de datos
    db_manager.initialize()
    print("✓ Gestor de BD inicializado")
    
    # Crear tablas
    db_manager.create_tables()
    print("✓ Tablas creadas/verificadas")
    
    # Inicializar datos base
    inicializar_datos_base()
    print("✓ Datos base inicializados")
    
    print("=" * 60)
    print("✓ SISTEMA LISTO")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cierra conexiones al apagar la aplicación."""
    print("\nCerrando sistema...")


# ============================================================
# RUTAS PRINCIPALES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Ruta raíz - sirve el frontend."""
    html_file = static_path / "index.html"
    if html_file.exists():
        return html_file.read_text(encoding="utf-8")
    else:
        return """
        <html>
            <head><title>Sistema de Turnos Médicos</title></head>
            <body>
                <h1>Sistema de Gestión de Turnos Médicos</h1>
                <p>API REST activa</p>
                <ul>
                    <li><a href="/api/docs">Documentación Swagger</a></li>
                    <li><a href="/api/redoc">Documentación ReDoc</a></li>
                </ul>
            </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {
        "status": "healthy",
        "service": "Sistema de Turnos Médicos",
        "version": "1.0.0"
    }


# ============================================================
# INCLUIR ROUTERS
# ============================================================

app.include_router(pacientes.router, prefix="/api")
app.include_router(medicos.router, prefix="/api")
app.include_router(especialidades.router, prefix="/api")
app.include_router(turnos.router, prefix="/api")
app.include_router(reportes.router, prefix="/api")
app.include_router(historial.router, prefix="/api")
