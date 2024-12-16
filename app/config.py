import os
from dotenv import load_dotenv

# Lista de claves de entorno requeridas
REQUIRED_KEYS = [
    "LANGCHAIN_API_KEY",
    "COHERE_API_KEY",
    # Agrega aquí más claves si es necesario
]

def load_env_vars():
    """
    Carga las variables de entorno desde un archivo .env.
    """
    load_dotenv()
    
    # Validar que las claves necesarias estén presentes
    missing_keys = [key for key in REQUIRED_KEYS if not os.getenv(key)]
    
    if missing_keys:
        raise EnvironmentError(f"Faltan las siguientes claves de entorno: {', '.join(missing_keys)}")