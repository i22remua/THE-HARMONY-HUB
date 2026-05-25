"""
Almacenes temporales en memoria usados por partes simples del backend.

No sustituyen Firestore ni la persistencia real del proyecto; son estructuras
livianas para mantener estado de proceso durante desarrollo local o flujos
internos concretos.
"""

checkins_store: list[dict] = []
feedback_store: list[dict] = []
recommendations_store: list[dict] = []

# Estadísticas mínimas de feedback por modo para lógica ligera no persistente.
mode_feedback_stats: dict[str, dict[str, int]] = {}
