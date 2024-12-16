"""
Módulo principal para inicializar y ejecutar la API de FastAPI.

"""
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain import hub
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import ChatCohere
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

# Inicializar modelo de o Cohere
llm = ChatCohere(model="command-r-plus-04-2024")

# Inicializar variable para el vector store
vector_store = None

def validar_claves_api():
    #Validacion de Claves API
    if not langchain_api_key or not cohere_api_key:
        raise ValueError("Las claves de API no están definidas en el archivo .env.")

def cargar_documento_en_chroma_db():
    global vector_store

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
    Validar claves y procesar documento al iniciar el servidor.
    """
    validar_claves_api()
    cargar_documento_en_chroma_db()

# Define estado para la solicitud de la API
class SolicitudConsulta(BaseModel):
    username: str
    question: str

# Función de recuperación de documentos
def retrieve(state: SolicitudConsulta):
    # Acceder a vector store global
    retrieved_docs = vector_store.similarity_search(state.question)
    # Retornar el contexto con el contenido de los documentos recuperados
    return {"context": [doc.page_content for doc in retrieved_docs]}

# Función para generar la respuesta
def generate(state: SolicitudConsulta, context: list):
    # Instrucciones fijas y el formato del prompt
    prompt = """
    Eres un asistente para tareas de preguntas y respuestas. 
    Responde siempre en tercera persona.
    Usa los siguientes fragmentos de contexto recuperados para responder la pregunta. 
    Si no sabes la respuesta, simplemente di que no sabes. 
    Usa un máximo de una oración y mantén la respuesta concisa.
    Coloca emojis al final a modo de resumen.
    
    Pregunta: {question}

    Contexto: {context}

    Respuesta:
    """
    
    # Formatear el prompt con la pregunta y el contexto
    formatted_prompt = prompt.format(question=state.question, context="\n\n".join(context))

    # Llamar al modelo con el prompt formateado
    response = llm.invoke(formatted_prompt)

    # Devolver la respuesta generada
    return {
        "answer": response.content,
        #"full_prompt": formatted_prompt  # Mostrar el prompt completo para depuración, si es necesario
    }

# Endpoint para recibir las solicitudes y generar respuestas
@app.post("/consulta/")
async def consulta(state: SolicitudConsulta):
    # Paso 1: Recuperar documentos relacionados
    context_data = retrieve(state)

    # Paso 2: Generar respuesta utilizando los documentos recuperados
    response_data = generate(state, context_data["context"])

    # Paso 3: Devolver la respuesta generada
    return response_data