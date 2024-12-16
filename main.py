"""
Módulo principal para inicializar y ejecutar la API de FastAPI.

"""
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain import hub
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma
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

def validar_claves_api():
    #Validacion de Claves API
    if not langchain_api_key or not cohere_api_key:
        raise ValueError("Las claves de API no están definidas en el archivo .env.")

def cargar_documento_en_chroma_db():
    # Carga de Documento
    loader = Docx2txtLoader("documento.docx")

    data = loader.load()

    # Division en Chunks
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n"],
        chunk_size=400, 
        chunk_overlap=30,
        add_start_index=True
    )

    all_splits = text_splitter.split_documents(data)

    # Embedding
    embeddings = CohereEmbeddings(model="embed-english-v3.0")
    
    # Cargar el vector store persistido
    vector_store = Chroma(
        collection_name="example_01",
        embedding_function=embeddings,  # Tu función de embeddings
        persist_directory="./chroma_langchain_db",  # Ruta donde se guardan los datos
    )

    vector_store.add_documents(documents=all_splits)
    
    print("Documento cargado con éxito")

@app.on_event("startup")
def startup_event():
    """
    Procesar el documento al iniciar la aplicación, si es necesario.
    """
    cargar_documento_en_chroma_db()
    





