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
from deep_translator import GoogleTranslator
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
llm = ChatCohere(model="command-r-plus-04-2024", temperature=0)

# Inicializar variable para el vector store
vector_store = None

def translate_text(text, target_language):
    return GoogleTranslator(source='auto', target=target_language).translate(text)

def validar_claves_api():
    #Validacion de Claves API
    if not langchain_api_key or not cohere_api_key:
        raise ValueError("Las claves de API no están definidas en el archivo .env")

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
        collection_name="example_02",
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
    user_name: str
    question: str

# Función de recuperación de documentos
def retrieve(state: SolicitudConsulta):
    # Acceder a vector store global
    retrieved_docs = vector_store.similarity_search(state.question)
    # Retornar el contexto con el contenido de los documentos recuperados
    return {"context": [doc.page_content for doc in retrieved_docs]}

# Función para detectar el idioma de la consulta
def detectar_idioma(state: SolicitudConsulta):
    # Incluir ejemplos para few-shot learning en el prompt
    few_shot_examples = """
    Ejemplo 1:
    Pregunta: ¿Cómo estás?
    Respuesta: es

    Ejemplo 2:
    Question: How are you?
    Answer: en

    Exemplo 3:
    Pergunta: Como você está?
    Resposta: pt
    """

    prompt = f"""
    {few_shot_examples}
    Eres un asistente especializado en detectar idiomas. 
    Genera la respuesta en el formato mencionado en los ejemplos. 
    Si no puedes determinarlo con certeza, responde 'es' por defecto.

    Pregunta: {state.question}
     
    Respuesta:
    """

    # Llamar al modelo con el prompt formateado
    response = llm.invoke(prompt)
    
    # Devolver la respuesta generada
    return response.content

# Función para generar la respuesta
def generar_respuesta(state: SolicitudConsulta, context: list):
    # Instrucciones fijas y el formato del prompt
    prompt = """
    Eres un asistente para tareas de preguntas y respuestas. 
    Responde siempre en tercera persona.
    Usa los siguientes fragmentos de contexto recuperados para responder la pregunta. 
    Si no sabes la respuesta, simplemente di que no sabes. 
    Usa un máximo de una oración y mantén la respuesta concisa.
    Agrega emojis al final que resuman la respuesta generada.
    Genera la respuesta en español.

    Pregunta: {question}    

    Contexto: {context}

    Respuesta:
    """

    # Formatear el prompt con la pregunta y el contexto
    formatted_prompt = prompt.format(
        question=state.question, 
        context="\n\n".join(context)
    )

    # Llamar al modelo con el prompt formateado
    response = llm.invoke(formatted_prompt)
    
    return response.content

def traducir_respuesta(state:SolicitudConsulta, texto: str, idioma_destino: str):
    """
    Traduce un texto al idioma deseado utilizando el modelo de lenguaje.

    Parameters:
        texto (str): El texto que se desea traducir.
        idioma_destino (str): Código ISO 639-1 del idioma destino.

    Returns:
        str: El texto traducido.
    """
    # Few-shot examples para que el modelo entienda cómo traducir
    few_shot_examples = """
    Ejemplo 1:
    Texto: Emma decided to share her extra day with the people. 🌟🤸‍♀️
    Idioma destino: es
    Traducción: Emma decidió compartir su día extra con el pueblo. 🌟🤸‍♀️

    Ejemplo 2:
    Texto: Emma decidiu compartilhar seu dia extra com o povo. 🌟🤸‍♀️
    Idioma destino: en
    Traducción: Emma decided to share her extra day with the people. 🌟🤸‍♀️

    Ejemplo 3:
    Texto: Emma decidió compartir su día extra con el pueblo. 🌟🤸‍♀️
    Idioma destino: pt
    Traducción: Emma decidiu compartilhar seu dia extra com o povo. 🌟🤸‍♀️
    """

    # Crear el prompt para el modelo
    prompt = f"""
    {few_shot_examples}
    Solo traduce el siguiente texto al idioma indicado manteniendo los emojis en el final.

    Texto: {texto}
    Idioma destino: {idioma_destino}

    Traducción:
    """

    try:
        # Llamar al modelo para generar la traducción
        response = llm.invoke(prompt)
        # Devolver la respuesta generada
        return {
            "user_name": state.user_name,
            "answer": response.content,
        }
    except Exception as e:
        print(f"Error al traducir con el modelo: {e}")
        return texto  # Devuelve el texto original si hay un fallo

# Endpoint GET para la ruta raíz
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

# Endpoint POST para procesar solicitudes de consulta
@app.post("/consulta/")
async def consulta(state: SolicitudConsulta):
    # Paso 1: Recuperar documentos relacionados
    context_data = retrieve(state)

    # Paso 2: Generar respuesta utilizando los documentos recuperados
    idioma_detectado = detectar_idioma(state)
    respuesta_base = generar_respuesta(state, context_data["context"])
    respuesta_final = traducir_respuesta(state, respuesta_base, idioma_detectado)

    # Paso 3: Devolver la respuesta generada
    return respuesta_final