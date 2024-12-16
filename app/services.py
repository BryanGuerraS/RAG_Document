from langchain_chroma import Chroma
from app.models import SolicitudConsulta
from langchain_cohere import ChatCohere
from deep_translator import GoogleTranslator

# Inicialización del modelo Cohere
llm = ChatCohere(model="command-r-plus-04-2024", temperature=0)

def retrieve(state: SolicitudConsulta, vector_store:Chroma):
    """
    Recupera documentos relacionados con la consulta del usuario desde el vector store.

    Parameters:
        state (SolicitudConsulta): Contiene la pregunta y el nombre del usuario.

    Returns:
        dict: Contexto con los fragmentos de documentos relevantes.
    """
    retrieved_docs = vector_store.similarity_search(state.question)
    return {"context": [doc.page_content for doc in retrieved_docs]}

def detectar_idioma(state: SolicitudConsulta):
    """
    Detecta el idioma de la consulta utilizando un modelo de lenguaje.

    Parameters:
        state (SolicitudConsulta): Contiene la pregunta del usuario.

    Returns:
        str: Código del idioma detectado (por ejemplo, 'es' para español).
    """
    # Incluir ejemplos para el modelo de detección de idioma
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
    response = llm.invoke(prompt)
    return response.content

def generar_respuesta(state: SolicitudConsulta, context: list):
    """
    Genera una respuesta utilizando el contexto recuperado de los documentos.

    Parameters:
        state (SolicitudConsulta): Contiene la pregunta del usuario.
        context (list): Lista de fragmentos de documentos relacionados.

    Returns:
        str: Respuesta generada.
    """
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
    formatted_prompt = prompt.format(
        question=state.question, 
        context="\n\n".join(context)
    )
    response = llm.invoke(formatted_prompt)
    return response.content

def traducir_respuesta(state: SolicitudConsulta, texto: str, idioma_destino: str):
    """
    Traduce la respuesta generada al idioma deseado.

    Parameters:
        state (SolicitudConsulta): Contiene el nombre del usuario.
        texto (str): El texto que se desea traducir.
        idioma_destino (str): El idioma de destino (código ISO 639-1, como 'es' para español).

    Returns:
        dict: Contiene el nombre del usuario y la respuesta traducida.
    """
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

    prompt = f"""
    {few_shot_examples}
    Solo traduce el siguiente texto al idioma indicado manteniendo los emojis al final.

    Texto: {texto}
    Idioma destino: {idioma_destino}

    Traducción:
    """
    try:
        response = llm.invoke(prompt)
        return {
            "user_name": state.user_name,
            "answer": response.content,
        }
    except Exception as e:
        print(f"Error al traducir con el modelo: {e}")
        return texto  # Devuelve el texto original si hay un fallo

def procesar_consulta(state: SolicitudConsulta, vector_store:Chroma):
    """
    Procesa una consulta desde el usuario: recuperar contexto, generar y traducir la respuesta.

    Parameters:
        state (SolicitudConsulta): Contiene la consulta del usuario.

    Returns:
        dict: Contiene la respuesta generada, ya traducida si es necesario.
    """
    context_data = retrieve(state, vector_store)
    idioma_detectado = detectar_idioma(state)
    respuesta_base = generar_respuesta(state, context_data["context"])
    respuesta_final = traducir_respuesta(state, respuesta_base, idioma_detectado)
    return respuesta_final
