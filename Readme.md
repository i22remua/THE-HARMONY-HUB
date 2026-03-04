# 🎵 The Harmony Hub

> Una aplicación móvil inteligente que genera playlists adaptativas basadas en tu estado emocional y contexto acústico.

## 📋 Descripción del Proyecto

**The Harmony Hub** es una aplicación innovadora que combina Machine Learning, procesamiento digital de señales (DSP) y integración con Spotify para crear una experiencia de música personalizada única. El sistema analiza:

- 🧠 **Estado Emocional**: Registra y analiza tu estado emocional diario
- 🔊 **Contexto Acústico**: Clasifica el ruido ambiental en tiempo real
- 🎼 **Preferencias Musicales**: Aprende de tus interacciones (Reinforcement Learning)
- 🎧 **Recomendaciones**: Genera playlists que se adaptan a tu ánimo y ambiente

## 🎯 Objetivos Principales

1. **Análisis de Emociones**: Implementar modelos de ML que mapeen estado emocional a características musicales
2. **Interfaz Intuitiva**: Diseñar una UI mobile amigable para captura de estado de ánimo
3. **Motor de Recomendación**: API REST en la nube para generar playlists personalizadas
4. **Procesamiento de Audio**: DSP en tiempo real para clasificar ruido ambiental
5. **Seguridad**: Proteger datos sensibles del usuario (emociones, historial)

## 🏗️ Arquitectura del Proyecto

```
The Harmony Hub/
├── backend_python/          # Backend - ML & API
├── harmonyhub/              # Frontend Flutter
├── firebase/                # Firebase Functions & Rules
└── documentation/           # Documentación
```

**Para documentación detallada de arquitectura, ver**: [ARCHITECTURE.md](./ARCHITECTURE.md)

## 🚀 Comienzo rápido

### Requisitos Previos
- Python 3.11+
- Flutter 3.10+
- Node.js 18+
- Firebase CLI
- Spotify Developer Account

### Instalación Backend

```bash
cd backend_python

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar servidor
python main.py
```

El servidor estará disponible en `http://localhost:8000`

### Instalación Frontend

```bash
cd harmonyhub

# Instalar dependencias
flutter pub get

# Ejecutar en emulador/dispositivo
flutter run
```

### Configuración Firebase

```bash
cd firebase

# Login en Firebase
firebase login

# Inicializar proyecto (si es nuevo)
firebase init

# Desplegar
firebase deploy
```

**Para instrucciones detalladas**: [QUICK_START.md](./QUICK_START.md)

## 📁 Estructura de Directorio

### Backend Python (`backend_python/`)

```
backend_python/
├── api/                 # Rutas REST
├── ml_models/          # Modelos de Machine Learning
├── dsp/                # Procesamiento Digital de Señales
├── database/           # Repositorios de datos
├── services/           # Lógica de negocio
├── security/           # Autenticación y seguridad
├── config.py           # Configuración central
├── main.py             # Punto de entrada
└── requirements.txt    # Dependencias
```

### Frontend Flutter (`harmonyhub/lib/`)

```
lib/
├── core/               # Constantes, tema, utilidades
├── data/               # Acceso a datos
├── domain/             # Lógica de negocio
├── presentation/       # UI - Screens, Widgets
├── services/           # Servicios especializados
└── config/             # Configuración
```

## 🔌 Integraciones

### Firebase
- **Firestore**: Base de datos en tiempo real
- **Firebase Auth**: Autenticación de usuarios
- **Cloud Storage**: Almacenamiento de archivos
- **Cloud Functions**: Lógica en nube

### Spotify API
- Búsqueda de canciones
- Análisis de características de audio
- Gestión de reproductor
- Recomendaciones de Spotify

### Servicios Externos
- Audio Analysis API (clasificación de ruido)
- Analytics (seguimiento de comportamiento)

## 🔐 Seguridad

- ✅ Autenticación OAuth2 con Firebase Auth
- ✅ JWT tokens con renovación automática
- ✅ Cifrado de datos sensibles
- ✅ HTTPS/TLS para todas las comunicaciones
- ✅ Firestore Rules para control de acceso
- ✅ Certificate Pinning en mobile

## 📊 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login de usuario |
| POST | `/api/v1/mood/record` | Registrar estado emocional |
| GET | `/api/v1/mood/history` | Historial de emociones |
| POST | `/api/v1/audio/analyze` | Analizar ruido ambiental |
| GET | `/api/v1/recommendations` | Obtener recomendaciones |
| POST | `/api/v1/playlist/create` | Crear playlist |
| POST | `/api/v1/feedback/record` | Registrar feedback |

## 🛠️ Tecnologías

### Backend
- **FastAPI**: Framework web moderno
- **TensorFlow/PyTorch**: Machine Learning
- **Librosa**: Procesamiento de audio
- **Firebase Admin SDK**: Integración Firebase
- **Spotipy**: Cliente de Spotify
- **Redis**: Caché distribuido

### Frontend
- **Flutter**: Framework UI multiplataforma
- **Riverpod/Provider**: State Management
- **Firebase SDK**: Backend services
- **Spotify SDK**: Integración Spotify
- **Hive**: Base de datos local

### Infraestructura
- **Firebase**: Backend services
- **Google Cloud Run**: Computación sin servidor
- **Docker**: Containerización
- **GitHub Actions**: CI/CD

## 📈 Fases de Desarrollo

### ✅ Fase 1: MVP ()


### 🔄 Fase 2: Audio DSP ()


### 🤖 Fase 3: ML Avanzado ()


### 🚀 Fase 4: Optimización ()


## 📚 Documentación

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Diseño completo de la arquitectura
- [QUICK_START.md](./QUICK_START.md) - Guía de inicio rápido
- [API Documentation](./backend_python/docs/API.md) - Referencia de endpoints
- [ML Models Guide](./backend_python/ml_models/README.md) - Guía de modelos ML
- [DSP Guide](./backend_python/dsp/README.md) - Guía de procesamiento de señales

## 👥 Contribución

Para contribuir al proyecto:

1. Crear una rama: `git checkout -b feature/mi-feature`
2. Commit cambios: `git commit -am 'Add feature'`
3. Push a rama: `git push origin feature/mi-feature`
4. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

## 📬 Contacto

- 📧 Email: [i22remua@uco.com]
- 🐙 GitHub: [tu-github]
---

**Última actualización**: Febrero 2026

**Estado**: 🚧 En desarrollo - MVP en progreso

