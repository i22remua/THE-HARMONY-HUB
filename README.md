# Harmony Hub

Aplicacion movil y backend inteligente para generar playlists adaptativas en Spotify a partir del estado emocional del usuario, su contexto ambiental y un modelo hibrido de recomendacion con aprendizaje progresivo.

## Descripcion

Harmony Hub es un Trabajo Fin de Grado que combina:

- captura de estado emocional
- medicion de ruido ambiental
- recomendacion musical contextual
- generacion automatica de playlists reales en Spotify
- feedback posterior del usuario
- aprendizaje adaptativo a nivel de perfil y de sesion
- ranking hibrido de heuristicas y machine learning

El objetivo del sistema es ofrecer una experiencia musical personalizada, explicable y sensible al momento concreto de uso.

## Objetivo del proyecto

Harmony Hub busca diseñar e implementar un sistema capaz de:

1. registrar el contexto emocional del usuario
2. interpretar factores como energia, estres y ruido ambiental
3. generar recomendaciones musicales adaptadas al momento actual
4. transformar la recomendacion en una playlist real de Spotify
5. aprender progresivamente del feedback
6. combinar reglas heuristicas con un clasificador supervisado a nivel de sesion

## Arquitectura general

```text
harmonyhub/           Frontend Flutter
backend_fastapi/      Backend FastAPI + catalogo + ML + Spotify
tfg_documentacion/    Memoria del TFG en LaTeX
firestore.rules       Reglas de seguridad de Firestore
```

## Funcionalidades principales

### App Flutter

- autenticacion de usuario
- check-in emocional y contextual
- medicion opcional del entorno acustico
- visualizacion de recomendacion
- generacion de playlist real
- envio de feedback
- historial, perfil y aprendizaje

### Backend FastAPI

- recomendacion de sesion basada en contexto
- modelo supervisado de seleccion de modo
- aprendizaje del perfil del usuario
- catalogo musical local tipo MSD
- materializacion de canciones en Spotify
- mantenimiento y auditoria del modelo

### Documentacion del TFG

- memoria academica completa
- diagramas
- anexos tecnicos
- manuales y material de defensa

## Flujo funcional resumido

1. El usuario inicia sesion.
2. Realiza un check-in emocional.
3. La app recoge preferencias y, si se desea, senales del entorno.
4. El backend genera una recomendacion contextual.
5. El usuario puede materializarla como playlist real en Spotify.
6. Tras escucharla, envia feedback.
7. El sistema actualiza el aprendizaje y mantiene el modelo supervisado.

## Stack tecnologico

- Flutter
- FastAPI
- Firebase Authentication
- Cloud Firestore
- Spotify Web API
- scikit-learn

## Puesta en marcha

### Backend

```bash
cd backend_fastapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd harmonyhub
flutter pub get
flutter run
```

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

- [backend_fastapi/DEFENSA_FUNCIONAMIENTO_HARMONY_HUB.md](backend_fastapi/DEFENSA_FUNCIONAMIENTO_HARMONY_HUB.md)
- [backend_fastapi/ML_AND_RECOMMENDER_ACADEMIC_TECHNICAL_EXPLANATION.md](backend_fastapi/ML_AND_RECOMMENDER_ACADEMIC_TECHNICAL_EXPLANATION.md)
- [backend_fastapi/CATALOG_SUMMARY_REPORT.md](backend_fastapi/CATALOG_SUMMARY_REPORT.md)
- [backend_fastapi/ML_SINGLE_PROFILE_EVIDENCE_TABLES.md](backend_fastapi/ML_SINGLE_PROFILE_EVIDENCE_TABLES.md)
- [tfg_documentacion/](tfg_documentacion/)

## Nota sobre configuracion local

En este estado del proyecto, el cliente Flutter puede apuntar a una IP local concreta para probar en movil fisico. Si cambias de red o de IP, revisa:

- [harmonyhub/lib/core/network/api_client.dart](harmonyhub/lib/core/network/api_client.dart)

## Antes de publicar o clonar

Este repositorio deja fuera secretos y configuraciones sensibles como:

- `backend_fastapi/.env`
- `backend_fastapi/firebase-service-account.json`

Si otra persona quiere ejecutar el proyecto, debera crear sus propias credenciales y configuracion local.

## Licencia

Este repositorio incluye licencia MIT en [LICENSE](LICENSE).
