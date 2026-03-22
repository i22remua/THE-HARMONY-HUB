# 🎵 Harmony Hub

> Aplicación móvil inteligente para generar playlists adaptativas en Spotify a partir del estado emocional del usuario, su contexto ambiental y un modelo híbrido de recomendación con aprendizaje progresivo.

---

## 📌 Descripción

**Harmony Hub** es una aplicación móvil desarrollada como Trabajo Final de Grado que combina:

- **captura de estado emocional**
- **medición de ruido ambiental**
- **recomendación musical contextual**
- **generación automática de playlists en Spotify**
- **feedback del usuario**
- **aprendizaje adaptativo**
- **ranking híbrido heurística + machine learning**

El objetivo del sistema es ofrecer una experiencia musical personalizada y contextual, capaz de evolucionar con el uso y con las preferencias reales del usuario.

---

## 🎯 Objetivo del proyecto

El propósito de Harmony Hub es diseñar e implementar un sistema capaz de:

1. registrar el contexto emocional del usuario
2. interpretar factores adicionales como energía, estrés y ruido ambiental
3. generar recomendaciones musicales adaptadas al momento actual
4. crear playlists reales en Spotify
5. aprender progresivamente del feedback del usuario
6. utilizar un modelo híbrido de recomendación combinando lógica heurística y machine learning

---

## ✅ Funcionalidades actuales

### Autenticación y persistencia
- Registro e inicio de sesión con **Firebase Authentication**
- Persistencia en **Cloud Firestore**
- Historial de uso por usuario autenticado

### Captura de contexto
- Check-in emocional manual
- Selección de:
  - mood
  - objetivo
  - estrés
  - energía
- Medición del ruido ambiental con micrófono
- Preferencias avanzadas:
  - voz: instrumental / indistinto / con voz
  - intensidad: suave / media / alta
  - exploración: familiar / equilibrado / descubrir
  - popularidad: mainstream / mixta / alternativa
  - duración objetivo

### Recomendación musical
- Generación de recomendación contextual desde backend
- Cálculo de:
  - modo recomendado
  - valencia objetivo
  - energía objetivo
  - rango BPM objetivo

### Integración con Spotify
- Conexión mediante **OAuth**
- Obtención del perfil del usuario
- Generación automática de playlists reales
- Apertura de playlists en Spotify

### Feedback y aprendizaje
- Envío de feedback:
  - helpful
  - effect
  - comentario opcional
- Actualización de perfil adaptativo del usuario
- Persistencia de:
  - géneros preferidos
  - géneros evitados
  - métricas acústicas preferidas
- Generación de dataset de entrenamiento

### Machine Learning
- Modelo de ranking entrenable con **scikit-learn**
- Enfoque híbrido:
  - score heurístico
  - score ML
  - score final combinado
- Activación automática del ranking híbrido cuando existe modelo entrenado

### Visualización
- Historial de:
  - check-ins
  - recomendaciones
  - feedback
  - playlists generadas
- Pantalla de aprendizaje del sistema
- Visualización de canciones seleccionadas y motivos de selección

---

## 🧠 Cómo funciona el sistema

El flujo principal es el siguiente:

1. El usuario inicia sesión.
2. Realiza un **check-in emocional**.
3. La app mide el **ruido ambiental**.
4. El backend genera una **recomendación contextual**.
5. El usuario puede **generar una playlist automática en Spotify**.
6. El sistema obtiene canciones candidatas.
7. Se aplica un **ranking heurístico** y, si existe modelo entrenado, un **ranking híbrido con ML**.
8. El usuario escucha la playlist y envía **feedback**.
9. El sistema actualiza el perfil adaptativo y genera **training examples**.
10. El modelo ML puede reentrenarse con esos datos.

---

## 🏗️ Arquitectura del sistema

Harmony Hub sigue una arquitectura cliente-servidor con servicios externos:

- **Frontend móvil:** Flutter
- **Backend REST:** FastAPI
- **Autenticación:** Firebase Authentication
- **Persistencia:** Cloud Firestore
- **Proveedor musical:** Spotify Web API
- **Machine Learning:** scikit-learn + joblib

⸻

📄 Licencia

Este proyecto puede mantenerse bajo licencia MIT si deseas distribución abierta.

⸻

📬 Contacto
	•	Email: i22remua@uco.es
	•	GitHub: i22remua

⸻

🏁 Estado del repositorio

Estado actual: prototipo funcional avanzado en transición a producto final y documentación completa de TFG.

Última actualización: marzo 2026

---

Si quieres, el siguiente paso te lo doy ya en formato **README más profesional todavía**, con:
- badges
- tabla de estado del proyecto
- secciones de “Known issues”
- y una versión más académica para que quede impecable en GitHub.
