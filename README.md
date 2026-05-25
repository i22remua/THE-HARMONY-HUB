# Harmony Hub

Harmony Hub es un TFG centrado en la generacion de sesiones musicales personalizadas para bienestar emocional. El proyecto combina una app Flutter, un backend FastAPI, aprendizaje a partir de feedback del usuario y materializacion final de playlists reales en Spotify.

## Que hace el proyecto

- recoge un check-in breve sobre objetivo, estado emocional, energia, entorno y preferencias
- genera una recomendacion de sesion musical explicable
- transforma esa recomendacion en una playlist real en Spotify
- aprende de sesiones previas y del feedback posterior
- mantiene un clasificador supervisado a nivel de sesion para ajustar la seleccion del modo

## Arquitectura general

```text
Flutter app (harmonyhub/)
  -> Auth + check-in + entorno + recomendacion + feedback
  -> llama al backend REST

FastAPI backend (backend_fastapi/)
  -> recomendador heuristico
  -> modelo supervisado de sesion
  -> perfil de aprendizaje del usuario
  -> catalogo musical local tipo MSD
  -> conexion con Spotify para OAuth y playlists

Documentacion TFG (tfg_documentacion/)
  -> memoria en LaTeX
  -> figuras, anexos y redaccion academica
```

## Estructura del repositorio

```text
harmonyhub/           App Flutter
backend_fastapi/      Backend FastAPI y servicios ML/recomendacion
tfg_documentacion/    Memoria del TFG en LaTeX
firestore.rules       Reglas de seguridad de Firestore
dataconnect/          Artefactos auxiliares de Firebase Data Connect
```

## Stack principal

- Flutter
- FastAPI
- Firebase Auth
- Firestore
- Spotify Web API
- scikit-learn
- catalogo local `msd_tracks` como base principal de candidatos

## Flujo funcional resumido

1. El usuario inicia sesion.
2. Realiza un check-in emocional y contextual.
3. La app envia el contexto al backend.
4. El backend calcula candidatos de sesion y, si procede, activa el modelo supervisado.
5. Se devuelve una recomendacion explicable.
6. Si el usuario la acepta, se genera una playlist real en Spotify.
7. El feedback posterior alimenta el aprendizaje del perfil y el mantenimiento del modelo.

## Puesta en marcha rapida

### 1. Backend

```bash
cd backend_fastapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Flutter

```bash
cd harmonyhub
flutter pub get
flutter run
```

## Nota importante sobre red local

En este estado del proyecto, el cliente Flutter puede apuntar a una IP local fija para probar en movil fisico. Si cambias de red o de IP, revisa:

- [harmonyhub/lib/core/network/api_client.dart](harmonyhub/lib/core/network/api_client.dart)

## Tests

Backend:

```bash
cd backend_fastapi
source .venv/bin/activate
python -m unittest discover -s tests
```

Frontend:

```bash
cd harmonyhub
flutter test
```

## Documentacion relevante

- [tfg_documentacion/](tfg_documentacion/)
- [backend_fastapi/DEFENSA_FUNCIONAMIENTO_HARMONY_HUB.md](backend_fastapi/DEFENSA_FUNCIONAMIENTO_HARMONY_HUB.md)
- [backend_fastapi/ML_AND_RECOMMENDER_ACADEMIC_TECHNICAL_EXPLANATION.md](backend_fastapi/ML_AND_RECOMMENDER_ACADEMIC_TECHNICAL_EXPLANATION.md)
- [backend_fastapi/CATALOG_SUMMARY_REPORT.md](backend_fastapi/CATALOG_SUMMARY_REPORT.md)
- [backend_fastapi/ML_SINGLE_PROFILE_EVIDENCE_TABLES.md](backend_fastapi/ML_SINGLE_PROFILE_EVIDENCE_TABLES.md)

## Estado del repositorio

Este repositorio contiene tanto el producto software como la memoria academica del TFG. La carpeta de referencia documental es:

- `tfg_documentacion/`

La implementacion movil y backend incluidas aqui corresponden al entregable funcional del proyecto.

## Antes de subirlo a GitHub

Revisa especialmente que no subas secretos ni artefactos locales:

- `backend_fastapi/.env`
- `backend_fastapi/firebase-service-account.json`
- entornos virtuales
- builds locales de Flutter
- PDFs finales, zips o ficheros temporales si no quieres publicar entregables pesados

## Licencia

Si vas a publicar el repositorio de forma abierta, te recomiendo anadir una licencia explicita antes de hacerlo publico.
