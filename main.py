"""
Módulo principal para inicializar y ejecutar la API de FastAPI.

"""
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Inicializar la aplicación FastAPI
app = FastAPI()

# Cargar el archivo .env
load_dotenv()

# Claves API_KEY
langchain_api_key = os.getenv('LANGCHAIN_API_KEY')
cohere_api_key = os.getenv('COHERE_API_KEY')

# Inicializacion de entorno para medición en LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = langchain_api_key

# Carga de Documento

# Embedding

# Almacenamiento

# Query

# Respuesta

