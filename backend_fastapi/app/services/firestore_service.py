import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import FIREBASE_SERVICE_ACCOUNT_PATH

"""
Cliente compartido de Firestore para el backend.

El servicio inicializa Firebase una sola vez y reutiliza el cliente para evitar
coste repetido y errores por múltiples inicializaciones dentro del mismo
proceso.
"""

_app = None
_db = None


def get_firestore_client():
    """Devuelve un singleton del cliente Firestore ya autenticado."""
    global _app, _db

    if _db is not None:
        return _db

    if not firebase_admin._apps:
        # Solo inicializamos el SDK si aún no existe ninguna app global activa.
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_PATH)
        _app = firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db
