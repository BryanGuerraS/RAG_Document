from fastapi import FastAPI
from app.models import SolicitudConsulta
from app.config import load_env_vars
from app.db import cargar_documento_en_chroma_db
from app.services import procesar_consulta

# Inicializar la aplicación FastAPI
app = FastAPI()

@app.on_event("startup")
def startup_event():
    """
    Validar claves y procesar documento al iniciar el servidor.
    """
    load_env_vars()
    global vector_store 
    vector_store = cargar_documento_en_chroma_db()

@app.get("/")
async def root():
    """
    Muestra un mensaje de bienvenida cuando se accede a la raíz de la API.
    """
    return {
        "message": "¡Bienvenido a la API de consultas! Utiliza el endpoint /consulta/ para hacer preguntas."
    }

@app.get("/consulta/")
async def consulta_info():
    """
    Muestra un mensaje indicando que se debe usar POST para realizar consultas.
    """
    return {
        "message": "Este endpoint está diseñado para solicitudes POST. Envía tu consulta como JSON."
    }

@app.post("/consulta/")
async def consulta(state: SolicitudConsulta):
    """
    Procesa las solicitudes de consulta enviadas mediante POST.
    """
    return procesar_consulta(state, vector_store)