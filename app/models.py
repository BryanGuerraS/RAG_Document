from pydantic import BaseModel

class SolicitudConsulta(BaseModel):
    """
    Modelo de datos para las solicitudes de consulta.
    """
    user_name: str
    question: str