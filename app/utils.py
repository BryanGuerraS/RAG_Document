def validar_claves_api(langchain_api_key: str, cohere_api_key: str):
    """
    Valida que las claves de API requeridas estén presentes.

    Parameters:
        langchain_api_key (str): Clave de Langchain API.
        cohere_api_key (str): Clave de Cohere API.

    Raises:
        ValueError: Si alguna clave está ausente.
    """
    if not langchain_api_key:
        raise ValueError("La clave LANGCHAIN_API_KEY no está definida.")
    if not cohere_api_key:
        raise ValueError("La clave COHERE_API_KEY no está definida.")