# Evidencia del funcionamiento del entorno, trazabilidad de entradas y flujo interno de Harmony Hub

## 1. Evidencia de que el entorno funciona realmente y cumple su función

En la versión final de Harmony Hub, el análisis del entorno no se incorpora como un dato accesorio, sino como una señal operativa que interviene en la personalización musical en varias fases del sistema. El flujo comienza en el cliente móvil, donde la aplicación realiza una captura temporal de audio mediante el micrófono del dispositivo y construye un perfil acústico a partir de medidas agregadas de intensidad sonora, variabilidad, rango dinámico y presencia de transitorios. A partir de estas señales se derivan, entre otros elementos, una categoría global de ruido, un contexto ambiental semántico, una estimación de confianza y un valor de estabilidad de la medición.

La evidencia de que esta capa funciona de forma efectiva se comprueba cuando, en la ejecución de una sesión real, el backend recibe y utiliza simultáneamente las señales `use_environment=True`, `environment_context`, `environment_confidence`, `environment_variability`, `environment_peak_delta`, `transient_ratio` y `burst_count`. Esto indica que el sistema no se limita a registrar que el entorno ha sido medido, sino que lo integra como parte del contexto de decisión.

La utilización real del entorno se manifiesta en cuatro niveles. En primer lugar, el clasificador supervisado de sesión lo incorpora como parte del contexto de entrada que utiliza para estimar la probabilidad de utilidad de cada modo candidato. En segundo lugar, el motor de generación musical calcula una fuerza de influencia ambiental, lo que permite ponderar cuánto debe afectar esa medición al perfil musical objetivo. En tercer lugar, el sistema añade consultas de búsqueda específicas asociadas tanto a la categoría de ruido como al contexto ambiental detectado. Finalmente, durante el ranking de canciones, se aplica un ajuste explícito a la puntuación heurística de cada pista según su adecuación al entorno real del usuario.

Por tanto, la verificación del funcionamiento correcto del entorno no debe limitarse a confirmar que el micrófono ha capturado sonido, sino a observar que se cumplen simultáneamente tres condiciones: el entorno se marca como activo en el backend, se genera una influencia ambiental positiva y aparecen consultas o ajustes derivados del contexto detectado. Cuando estas condiciones se cumplen, puede afirmarse con rigor que el entorno está interviniendo realmente en la generación de la playlist.

Conviene señalar que, en determinadas sesiones, los valores objetivo de valencia, energía y bailabilidad pueden permanecer aparentemente iguales antes y después del ajuste ambiental. Esto no implica que el entorno no haya sido aplicado, sino que el perfil previo ya se encontraba dentro del rango coherente para ese contexto acústico concreto. En esos casos, el efecto del entorno se traslada sobre todo al refuerzo de consultas, a la ponderación de la influencia ambiental y al ajuste del ranking posterior de candidatos musicales.

## 2. Procedencia y comprobación de cada entrada del usuario

Las entradas utilizadas por Harmony Hub se originan en tres capas distintas: datos declarados por el usuario, datos inferidos a partir del entorno y datos de contexto de sesión asociados a servicios externos o a la persistencia interna del sistema.

El primer grupo corresponde a los datos declarados explícitamente por el usuario durante la entrevista guiada de check-in. En esta fase se recogen el estado emocional (`mood`), el objetivo funcional de la sesión (`goal`), el nivel de energía, el nivel de estrés, la preferencia vocal, la preferencia de intensidad, el grado de exploración, la preferencia de popularidad, la duración estimada de la sesión y el resultado esperado al finalizarla (`desired_outcome`). Estas variables no se introducen como texto libre, sino a través de opciones cerradas definidas por la interfaz, lo que actúa como primer mecanismo de validación y reduce ambigüedades semánticas.

El segundo grupo procede del análisis acústico del entorno. La aplicación móvil transforma la captura del micrófono en un perfil estructurado que incluye la media y mediana de decibelios, el rango dinámico, la desviación estándar, la razón de transitorios, el número de ráfagas, la densidad de muestreo, la puntuación de estabilidad, la categoría de ruido, el contexto ambiental y una medida de confianza global. A diferencia de los inputs declarativos, estas señales no son elegidas por el usuario, sino inferidas automáticamente a partir de la medición.

El tercer grupo lo forman las entradas de contexto operacional, tales como el identificador del usuario de Spotify, el `recommendation_id` que enlaza la recomendación con la generación posterior de playlist, el token de acceso a Spotify y los datos de histórico aprendidos en sesiones anteriores. Estas señales no nacen del formulario de check-in, pero forman parte del contexto total con el que opera la aplicación.

La comprobación de cada entrada se produce en dos niveles. En el cliente, la propia interfaz guía y restringe la introducción de valores posibles. En el backend, las estructuras de validación formalizan esos valores y controlan que los campos numéricos se mantengan dentro de sus rangos definidos y que las categorías declaradas correspondan a las etiquetas esperadas por el sistema. Esta doble verificación permite afirmar que los inputs no solo son trazables, sino también consistentes desde el punto de vista lógico y técnico.

## 3. Interpretación de resultados esperados no estándar

Una de las características más relevantes del sistema es que no presupone que el resultado esperado del usuario deba coincidir necesariamente con la lectura más convencional de su objetivo funcional. Esto es especialmente importante en combinaciones aparentemente tensas, como solicitar una sesión de foco y, al mismo tiempo, indicar como resultado esperado el deseo de sentirse más acompañado.

En este tipo de caso, Harmony Hub no interpreta la entrada como una contradicción ni fuerza una sustitución del objetivo principal por el resultado esperado. En su lugar, resuelve la tensión mediante una combinación jerárquica y gradual de criterios. El objetivo funcional sigue siendo la señal dominante que determina para qué debe servir la sesión, mientras que el resultado esperado introduce un matiz afectivo sobre cómo debería sentirse el usuario al finalizarla.

Aplicado al ejemplo de `goal=foco` y `desired_outcome=mas_acompanado`, la interpretación final no conduce a una sesión de activación social o de relajación emocional completa, sino a una sesión que conserva la función de concentración, pero evita un carácter excesivamente frío, aislante o clínico. A nivel de perfil musical, esto suele traducirse en una energía media o media-baja, una valencia algo más cálida y una preferencia mayor por pistas que aporten presencia humana, proximidad semántica o calidez emocional sin romper la estabilidad atencional requerida por el foco.

En términos prácticos, el sistema intenta responder a la pregunta implícita del usuario: no solo quiero concentrarme, sino hacerlo sin sentir la sesión como algo distante o impersonal. Por ello, el motor de generación puede mantener un modo de foco, pero reforzar búsquedas y señales que privilegien texturas más cálidas, presencia vocal moderada o piezas con una carga afectiva de acompañamiento compatible con la concentración.

Esta capacidad de negociación entre señales funcionales y emocionales constituye una de las aportaciones más relevantes del sistema, ya que evita respuestas rígidas y aproxima la recomendación a un uso más realista y humano.

## 3.1. Tabla resumen de aprendizaje y ML

La siguiente tabla concentra los conceptos técnicos que más conviene dominar
para explicar la capa de aprendizaje de Harmony Hub de forma rápida, precisa y
defendible.

| Concepto | Qué significa | Cómo se calcula o aplica | Dónde verlo |
| --- | --- | --- | --- |
| `exploration_preference` | Controla cuánto debe abrirse la sesión a patrones menos habituales. | Modula el peso del aprendizaje previo: `familiar = 1.0`, `equilibrado = 0.75`, `descubrir = 0.4`. | `professional_playlist_model_service.py`, `_compute_taste_weights(...)` |
| `popularity_preference` | Controla si la música debe ser más conocida o más alternativa. | Orienta el perfil musical y el ranking, pero no el peso del aprendizaje. | `professional_playlist_model_service.py`, `build_generation_profile(...)` |
| Aprendizaje de sesión | Memoria contextual aprendida a partir de sesiones previas similares. | Se guarda en campos `session_*` y corrige el contexto actual cuando hay evidencia suficiente. | `user_preference_learning_service.py` |
| Aprendizaje estable | Memoria consolidada del usuario a nivel más global. | Se guarda en campos `stable_*` y pesa más cuando su confianza supera a la memoria contextual. | `user_preference_learning_service.py` |
| Masa base `1.0` | Reserva de peso para el contexto actual del check-in. | En `1.0 + raw_session_weight + raw_stable_weight`, ese `1.0` protege la señal presente y evita que el histórico sustituya al momento actual. | `professional_playlist_model_service.py`, `_compute_taste_weights(...)` |
| `session_weight` | Peso relativo de la memoria contextual aprendida. | Se obtiene normalizando `raw_session_weight` frente a la masa base y al peso estable. | `professional_playlist_model_service.py`, `_compute_taste_weights(...)` |
| `stable_weight` | Peso relativo de la memoria estable consolidada. | Se obtiene normalizando `raw_stable_weight` frente a la masa base y al peso de sesión. | `professional_playlist_model_service.py`, `_compute_taste_weights(...)` |
| Método de Wilson | Estimación prudente de confianza sobre una proporción positiva. | Penaliza muestras pequeñas o inestables; por eso un `2/2` no vale lo mismo que un `80/100`. | `professional_playlist_model_service.py` |
| `predict_proba` | Probabilidad estimada de que un candidato sea útil. | El modelo devuelve una probabilidad por fila y se toma la columna positiva: `model.predict_proba(X)[:, 1]`. | `session_mode_ml_service.py` |
| `thresholds` | Umbrales mínimos para activar o aceptar una decisión del modelo. | Se usan para la puerta de datos, la puerta de calidad global y la intervención del ML en una sesión real. | `session_mode_ml_service.py`, `train_ranking_model.py`, `session_mode_model_metadata.json` |
| `ml_delta` | Ajuste que el ML suma a la heurística del candidato. | `ml_delta = (prob - 0.5) * 10 * ml_weight`; si la probabilidad es alta, suma más puntos. | `session_mode_ml_service.py` |
| Peso operativo del componente supervisado | Grado real en que el clasificador modifica la decisión final. | No decide solo: se materializa en `ml_delta`, que corrige el score heurístico sin sustituirlo. | `session_mode_ml_service.py` + `recommender_service.py` |
| `ROC AUC` | Capacidad del modelo para separar positivos y negativos. | Puede leerse como la probabilidad de que el modelo puntúe más alto una sesión útil que una no útil. | `train_ranking_model.py` |
| Validación cruzada | Evaluación con varias particiones del mismo dataset. | El conjunto se divide en `folds`; se entrena en unos y se valida en otros, rotando para reducir dependencia de un único corte. | `train_ranking_model.py`, `StratifiedKFold`, `cross_validate`, `cross_val_predict` |
| Curvas exponenciales | Funciones de saturación para medir madurez o fuerza observacional. | Crecen rápido al principio y luego se estabilizan; unas pocas observaciones nuevas pesan mucho más que las muy tardías. | `train_ranking_model.py`, `professional_playlist_model_service.py` |
| Similitud vectorial | Medida semántica de parecido entre textos o embeddings. | Se usa sobre todo similitud coseno: cuanto más alineados estén dos vectores, mayor parecido semántico. | `lyrics_nlp_service.py`, `vector_recommendation_service.py` |
| Pipeline ML | Cadena completa de preprocesado y modelo usada igual en entrenamiento e inferencia. | Incluye imputación, escalado, codificación categórica y regresión logística, todo persistido en un único artefacto. | `train_ranking_model.py` |
| Archivo `.joblib` | Artefacto persistido del modelo ya entrenado. | Se genera con `joblib.dump(...)` y luego se carga con `joblib.load(...)`. | `train_ranking_model.py`, `session_mode_ml_service.py` |
| Auditoría del modelo | Registro trazable del estado operativo del clasificador. | Resume ejemplos, razones de reentrenado, thresholds y disponibilidad del modelo. | `session_mode_model_audit.json`, `session_mode_ml_audit_service.py` |
| Aprendizaje supervisado | Aprendizaje a partir de ejemplos etiquetados. | Cada sesión aporta contexto, candidato y etiqueta final `helpful` o no útil; con eso el modelo aprende a generalizar. | `ml_training_data_service.py`, `train_ranking_model.py` |

## 4. Flujo interno detallado de Harmony Hub desde el paso 0 hasta el feedback

### 4.0. Cuadro esquematizado del flujo final según los logs

Antes del detalle interno, conviene disponer de un cuadro corto que siga el
orden real en que el backend va emitiendo la traza por terminal. La utilidad de
este esquema es que permite recorrer una sesión completa leyendo únicamente las
etiquetas principales del log.

| Orden real | Etiqueta de log | Qué está ocurriendo | Qué demuestra | Salida observable |
| --- | --- | --- | --- | --- |
| 1 | `[AUTH] login_url_created` | El backend genera la URL OAuth de Spotify con PKCE. | La app puede iniciar autenticación real con Spotify. | `authorize_url`, `state` |
| 2 | `[AUTH] exchange_received` / `[AUTH] token_obtained` | El backend recibe el `code`, lo intercambia por token y valida los scopes. | La autenticación no es simulada y el token queda operativo. | `access_token`, `scope`, `expires_in` |
| 3 | `[PROFILE] profile_obtained` | Se consulta el perfil real del usuario en Spotify. | La cuenta musical está enlazada correctamente. | `spotify_user_id`, `display_name`, `country` |
| 4 | `POST /checkins/ ... 200 OK` | El check-in se guarda antes de recomendar. | La sesión queda persistida y trazable desde el inicio. | Confirmación HTTP `200 OK` |
| 5 | `[ML] model loaded` | Se carga el artefacto `.joblib` del clasificador de sesión. | El componente supervisado está disponible en runtime. | Mensaje de carga del modelo |
| 6 | `[ML] context` | El backend construye el contexto real de entrada para inferencia. | El ML usa `goal`, `mood`, estrés, energía, entorno y preferencias. | Diccionario completo de contexto |
| 7 | `[ML] probabilities` / `[ML] probability_spread` | El modelo estima probabilidades para los candidatos de modo. | El clasificador participa de forma cuantitativa y comparable. | Lista de probabilidades y dispersión |
| 8 | `[SESSION] CANDIDATE ...` | Cada candidato combina heurística base y `ml_delta`. | La decisión final es híbrida, no puramente heurística ni puramente ML. | `heuristic`, `ml_prob`, `ml_delta`, `final` |
| 9 | `[SESSION] selected_mode` / `selection_source` | Se selecciona el modo final de sesión. | El sistema deja trazabilidad de quién decidió y con qué apoyo. | `selected_mode`, `session_ml` o fallback |
| 10 | `[ENV] use_environment` / `environment_influence_strength` | El entorno medido entra en la recomendación y se pondera. | El micrófono influye realmente en la personalización. | `environment_context`, `env_strength` |
| 11 | `[ENV] target_adjustment` | Se corrigen los targets musicales por efecto del entorno. | El contexto acústico altera el perfil musical, no solo se almacena. | Valores `before` y `after` |
| 12 | `[ENV] noise_queries` / `context_queries` | El entorno activa señales semánticas auxiliares de búsqueda. | El sistema traduce el entorno en intención musical operativa. | Lista de queries derivadas |
| 13 | `[LEARNING] mood_gate_passed` / `mood_quality_score` | Se comprueba si el aprendizaje por `mood` puede intervenir. | El aprendizaje específico del estado emocional tiene una puerta de calidad. | Gate, score y factor de aplicación |
| 14 | `[INPUT] recommendation_id=...` | El flujo pasa de recomendación a generación de playlist. | Existe enlace trazable entre ambas mitades del proceso. | `recommendation_id` y snapshot del contexto |
| 15 | `[LEARNING] mode=... subtype=... curve=...` | El backend reconstruye el perfil musical para generar canciones. | Ya se conocen el subtipo funcional, la curva y los pesos de aprendizaje. | `subtype`, `curve`, `session_weight`, `stable_weight` |
| 16 | `[AFFINITY] source=msd_only` | La fuente principal de ranking es el catálogo local MSD. | El sistema no depende de Spotify como motor principal de descubrimiento. | `source=msd_only` |
| 17 | `[CATALOG] dataset_candidates=...` | Se extrae y ordena un conjunto inicial de canciones candidatas. | El catálogo local alimenta la generación musical real. | Número de candidatos y `top_track` |
| 18 | `[MATERIALIZATION] playable=...` | Se convierten candidatos del catálogo en canciones reales de Spotify. | La materialización funciona y resuelve URIs reproducibles. | `playable`, `cached`, `fresh`, `failed` |
| 19 | `[PLAYLIST] selected_tracks=...` | Se ensambla la playlist final respetando duración y coherencia. | El sistema no solo rankea, sino que construye una secuencia final usable. | `selected_tracks`, `target_ms`, `actual_ms` |
| 20 | `[PLAYLIST] created id=...` | La playlist se crea de verdad en la cuenta Spotify del usuario. | El flujo termina en una salida real reproducible. | `playlist_id`, nombre y `200 OK` |
| 21 | `POST /feedback/ ... 200 OK` | El usuario cierra la sesión enviando su valoración. | El sistema recoge evidencia posterior al uso real. | Confirmación HTTP `200 OK` |
| 22 | `[ML MAINTENANCE] start/train/done` | El backend detecta nuevos ejemplos y decide si reentrenar. | El ciclo de aprendizaje queda cerrado de extremo a extremo. | `labeled_examples`, `reason`, `trained=True/False` |

La lectura rápida correcta del log final, por tanto, no es simplemente “se ha
creado una playlist”, sino esta secuencia completa: Spotify se autentica, el
check-in se persiste, el ML puntúa candidatos, el entorno modifica targets, el
catálogo MSD aporta canciones, Spotify materializa la salida y el feedback
termina alimentando el mantenimiento del modelo.

La Tabla 1 resume de forma sintética y operativa el flujo interno completo de Harmony Hub, desde la apertura de la aplicación hasta la actualización del aprendizaje tras el envío de feedback.

| Paso | Fase | Entrada principal | Procesamiento interno | Dependencias implicadas | Salida / efecto |
| --- | --- | --- | --- | --- | --- |
| 0 | Inicio y autenticación | Apertura de la app y decisión de conectar Spotify | El cliente solicita la URL de autorización, ejecuta el intercambio PKCE y obtiene un token válido para operar sobre la cuenta musical del usuario. | App Flutter, FastAPI, Spotify Accounts, Spotify Web API | Sesión Spotify activa, `access_token` operativo y perfil musical enlazado. |
| 1 | Entrevista de check-in | `mood`, `goal`, energía, estrés, preferencia vocal, intensidad, exploración, popularidad, duración y `desired_outcome` | La interfaz guiada restringe y normaliza los inputs mediante opciones cerradas para evitar ambigüedad semántica y garantizar consistencia. | App Flutter, formularios del check-in | Contexto declarativo inicial de la sesión. |
| 2 | Medición ambiental | Activación del micrófono por parte del usuario | El cliente captura una ventana acústica corta y calcula media, variabilidad, picos, transitorios, ráfagas, estabilidad y confianza, a partir de las cuales infiere `noise_category` y `environment_context`. | Micrófono del dispositivo, `EnvironmentAudioService` | Perfil ambiental estructurado y listo para personalización. |
| 3 | Persistencia del check-in | Datos declarados y, si existe, perfil ambiental | El cliente guarda el check-in en Firestore, separando la parte operativa de la parte privada o sensible según la estructura del proyecto. | Flutter, Firestore | Check-in trazable y persistido. |
| 4 | Solicitud de recomendación | Payload de check-in completo | El frontend envía al backend todos los campos del contexto de sesión, incluyendo `use_environment` y las señales acústicas derivadas del micrófono cuando proceda. | Flutter, API de recomendaciones | Petición formal de recomendación de sesión. |
| 5 | Validación backend | Payload recibido desde el cliente | FastAPI valida rangos, tipos y etiquetas admitidas mediante esquemas formales antes de construir los candidatos de modo. | FastAPI, esquemas Pydantic | Entrada validada y lista para inferencia. |
| 6 | Construcción de candidatos | `goal`, `mood`, intensidad, resultado esperado, aprendizaje previo y entorno | El backend genera varios modos candidatos variando intensidad y subtipo, y para cada uno construye un `generation_profile` que resume la sesión. | `recommender_service`, `professional_playlist_model_service`, Firestore | Candidatos de modo con perfil funcional completo. |
| 7 | Heurística base de sesión | Candidatos de modo | Cada candidato recibe una puntuación heurística basada en alineación con el objetivo, intensidad, resultado esperado, memoria previa y coherencia contextual. | Servicios heurísticos internos | Ranking heurístico inicial de modos. |
| 8 | Clasificación supervisada | Candidatos ya construidos y contexto validado | Si el modelo está disponible, el backend estima probabilidades de utilidad por candidato, calcula `probability_spread` y ajusta el score con `ml_delta`. | `session_mode_ml_service`, artefacto ML, metadata del modelo | Ranking híbrido sesión = heurística + apoyo supervisado. |
| 9 | Selección de modo | Ranking híbrido final | El sistema decide el `selected_mode`, registra `selection_source`, deja constancia de si `ml_enabled` está activo y devuelve un `recommendation_id`. | FastAPI, lógica híbrida de recomendación | Recomendación final de sesión trazable. |
| 10 | Persistencia de la recomendación | Resultado de recomendación y contexto asociado | La recomendación se guarda en Firestore junto con el estado del entorno, la configuración declarada y los metadatos del aprendizaje aplicados. | Flutter, Firestore | Recomendación persistida y enlazada al resto del flujo. |
| 11 | Solicitud de generación de playlist | `recommendation_id` y contexto funcional de sesión | El cliente invoca el endpoint de generación musical reutilizando el modo recomendado y el resto de inputs relevantes. | Flutter, API Spotify propia del backend | Petición de playlist contextual real. |
| 12 | Reconstrucción del perfil musical | Recomendación, perfil Spotify, aprendizaje y entorno | El backend reconstruye el `generation_profile`, calcula targets musicales, activa queries semilla, exclusiones, pesos de aprendizaje y soporte contextual por entorno. | `professional_playlist_model_service`, perfil Spotify, Firestore | Perfil musical objetivo para selección de canciones. |
| 13 | Extracción de candidatos del catálogo | Perfil musical objetivo | El catálogo MSD actúa como fuente principal y devuelve canciones candidatas enriquecidas con rasgos musicales y señales derivadas. | `msd_catalog_service`, `dataset_recommendation_service`, `msd_tracks` | Pool inicial de canciones compatibles. |
| 14 | Ranking musical heurístico | Candidatos del catálogo | Cada track se puntúa por ajuste funcional, compatibilidad con el modo, entorno, resultado esperado, semántica textual y restricciones vocales. | `rank_candidate_tracks`, semántica textual, reglas de entorno | Lista ordenada de canciones candidatas. |
| 15 | Materialización en Spotify | Canciones rankeadas sin URI o con URI parcial | El backend busca coincidencias válidas título-artista y convierte los candidatos del catálogo en canciones reales reproducibles dentro de Spotify. | Spotify Web API, caché de emparejamientos, catálogo local | Candidatos materializados con URI reproducible. |
| 16 | Ensamblado final de playlist | Tracks ya materializados | Se construye la playlist respetando duración objetivo, máximo por artista, curva de activación, deduplicación semántica y restricción vocal solicitada. | `assemble_playlist`, lógica de curva, reglas de diversidad | Selección final de canciones de la sesión. |
| 17 | Creación real de playlist | Tracks seleccionados con URI | El backend crea la playlist en la cuenta Spotify del usuario y añade los ítems finales. | FastAPI, Spotify Web API | Playlist real disponible en la cuenta del usuario. |
| 18 | Persistencia de playlist | Metadatos de la playlist y tracks seleccionados | El cliente guarda en Firestore el resultado final, incluyendo `playlist_id`, `playlist_url`, modo, señales usadas y lista seleccionada. | Flutter, Firestore | Historial musical completo y consultable. |
| 19 | Recepción de feedback | `helpful`, `effect`, `post_session_state` y comentario si existe | El usuario cierra la sesión declarando la utilidad percibida y el cambio experimentado tras la escucha. | Flutter, formulario de feedback | Etiqueta funcional de la sesión. |
| 20 | Persistencia del feedback | Feedback del usuario y enlaces de sesión | El cliente guarda el feedback y el backend lo asocia a la recomendación y playlist concretas para conservar trazabilidad longitudinal. | Flutter, FastAPI, Firestore | Feedback trazable y conectado con la sesión real. |
| 21 | Actualización del aprendizaje individual | Feedback etiquetado y contexto de sesión | El backend actualiza la memoria por modo, el perfil estable del usuario y las estadísticas de aprendizaje por `mood`. | `user_preference_learning_service`, Firestore | Perfil aprendido refinado para futuras sesiones. |
| 22 | Generación de ejemplo supervisado | Contexto, modo recomendado, playlist y feedback | Se construye un ejemplo etiquetado de entrenamiento que resume la sesión completa y su valoración posterior. | `ml_training_data_service`, Firestore | Nuevo ejemplo supervisado persistido. |
| 23 | Mantenimiento automático del modelo | Detección de nuevos ejemplos etiquetados | El sistema audita el dataset, decide si corresponde reentrenar y actualiza los metadatos de disponibilidad y calidad del clasificador. | `session_mode_ml_automation_service`, pipeline ML | Modelo actualizado y listo para futuras recomendaciones. | 


### 4.1. Ejemplo guiado paso a paso para interpretar la tabla

Para facilitar la lectura de la Tabla 1, a continuación se presenta un ejemplo
concreto de sesión completa extraído de una traza real del sistema. El caso
seleccionado corresponde a un usuario que desea realizar una sesión de
relajación en estado neutral, con entorno medido activo, preferencia
instrumental y generación final materializada en Spotify.

**Configuración inicial del ejemplo**

- `goal = relajacion`
- `mood = neutral`
- `stress = 3`
- `energy = 3`
- `desired_outcome = mas_calmado`
- `vocal_preference = instrumental`
- `intensity_preference = suave`
- `exploration_preference = descubrir`
- `popularity_preference = alternativa`
- `use_environment = on`
- `noise_category = loud`
- `environment_context = Entorno mixto`

**Correspondencia paso a paso**

| Paso de la tabla | Qué ocurre en el ejemplo | Evidencia operativa observable |
| --- | --- | --- |
| 0 | El usuario abre la app y conecta Spotify. | El backend genera la URL OAuth, recibe el `code` PKCE y obtiene un `access_token` válido con `expires_in = 3600`. |
| 1 | El usuario completa el check-in declarando relajación como objetivo y deseo de acabar más calmado. | El contexto declarado incluye `goal = relajacion`, `mood = neutral`, `stress = 3`, `energy = 3`, `desired_outcome = mas_calmado`. |
| 2 | El usuario activa el micrófono y mide el entorno en un contexto acústico con bastante presencia sonora. | Se obtiene `noise_category = loud`, `environment_context = Entorno mixto`, `environment_confidence = 0.95`, `environment_variability = 2.7474`, `environment_peak_delta = 13.2875`, `transient_ratio = 0.4333`, `burst_count = 4`. |
| 3 | El cliente guarda el check-in en Firestore. | La traza confirma `POST /checkins/ HTTP/1.1 200 OK`. |
| 4 | La app solicita la recomendación al backend. | El endpoint `/recommendations/generate` recibe el payload con `use_environment = True` y preferencia `instrumental/suave/descubrir/alternativa`. |
| 5 | El backend valida tipos, rangos y categorías. | El payload se acepta y el flujo continúa sin errores estructurales. |
| 6 | El sistema genera tres candidatos de modo para la sesión de relajación. | Aparecen `relajacion_neutral_suave`, `relajacion_neutral_media` y `relajacion_neutral_alta`. |
| 7 | Cada candidato recibe una puntuación heurística inicial. | Se observan valores `heuristic = 46.0`, `17.0` y `6.0`, lo que ya favorece claramente la intensidad suave. |
| 8 | El clasificador supervisado entra en juego y estima probabilidades para los tres candidatos. | Se registra `ml_enabled = True`, `probabilities = [0.9454, 0.9479, 0.9479]`, `probability_spread = 0.0025` y threshold activo `min_selected_mode_probability = 0.14`. |
| 9 | Se selecciona el modo final de sesión mediante ranking híbrido. | El resultado final es `selected_mode = relajacion_neutral_suave`, `selection_source = session_ml`, `selected_mode_probability = 0.9454`, con `ml_delta = 8.91` y `final = 54.91`. |
| 10 | La recomendación queda guardada con su contexto completo. | La traza operativa muestra el `recommendation_id = 2d48eeaf-75bf-4279-87cf-f2309ff50e59`, que enlaza recomendación y generación. |
| 11 | El usuario decide convertir la recomendación en playlist real. | La app invoca `/spotify/generate-playlist` reutilizando ese `recommendation_id` y el mismo contexto funcional. |
| 12 | El backend reconstruye el perfil musical para la generación. | Se activa `subtype = stable_relaxation`, `curve = peak_then_settle`, `profile_mode = stable_weighted`, `session_weight = 0.169` y `stable_weight = 0.225`. |
| 13 | El entorno vuelve a aplicarse durante la generación musical. | Se registra `environment_influence_strength = 0.95` y el ajuste `energy: 0.12 -> 0.348`, además de `noise_queries = ['stable calm focus', 'warm ambient', 'soft but present chill']`. |
| 14 | El catálogo MSD actúa como fuente principal de candidatos musicales. | Se informa `source = msd_only`, `dataset_candidates = 60` y `top_track = Sunset Lover - Petit Biscuit` con `top_score = 123.85`. |
| 15 | El sistema materializa los candidatos mejor puntuados en Spotify. | Se obtienen `playable = 15`, `cached = 1`, `fresh = 14`, `failed = 2`, `searches = 16`, `rate_limited = False`. |
| 16 | Se ensambla la playlist final respetando duración y coherencia funcional. | Se seleccionan `selected_tracks = 10`, `uris = 10`, `target_ms = 2400000`, `actual_ms = 2725096`, `missing_duration = 0`. |
| 17 | La playlist se crea de verdad en la cuenta del usuario. | Se obtiene `playlist_id = 3ZHnCd43LnQch75n3vCx72` y la API responde `POST /spotify/generate-playlist ... 200 OK`. |
| 18 | La app puede guardar el resultado final en Firestore. | Quedan disponibles para persistencia el `playlist_id`, el nombre `Harmony Hub · Relajacion` y la lista de canciones resultante. |
| 19 | Tras la escucha, el usuario indica si la sesión fue útil. | La traza confirma `POST /feedback/ HTTP/1.1 200 OK`. |
| 20 | Ese feedback se persiste y se enlaza con la recomendación y la playlist generadas. | El sistema conserva la relación entre `recommendation_id`, playlist creada y valoración posterior. |
| 21 | El backend actualiza el aprendizaje individual del usuario. | La sesión alimenta los perfiles de aprendizaje y mantiene activo el bloque `mood_gate = True` con `mood_q = 81.63`. |
| 22 | Se genera un nuevo ejemplo supervisado para el modelo de sesión. | La traza de mantenimiento informa `labeled_examples = 65` frente a `previous_metadata_examples = 64`. |
| 23 | El mantenimiento automático revisa si debe reentrenarse el clasificador. | Se ejecuta `train | reason = new_labeled_examples_detected` y termina con `trained = True`. |

Este ejemplo permite observar con claridad que la tabla no representa una
secuencia abstracta, sino un proceso operativo real que puede verificarse tanto
en los logs del backend como en los objetos persistidos en Firestore y en la
creación final de la playlist en Spotify. En particular, el caso ilustra tres
propiedades importantes de Harmony Hub: el modelo supervisado ya puede
intervenir de manera efectiva en la selección del modo, el entorno medido por
el micrófono influye realmente en la personalización y la salida final del
sistema no es simulada, sino una playlist reproducible creada en la cuenta del
usuario.

El funcionamiento completo de Harmony Hub puede describirse como una cadena continua de decisiones y persistencia que conecta el estado declarado por el usuario con la generación de una playlist real y con la actualización posterior del aprendizaje del sistema.

El paso 0 comienza con la apertura de la aplicación y, cuando se desea generación real en Spotify, con la vinculación de la cuenta musical del usuario mediante el flujo de autenticación autorizado. En esta fase se obtiene el perfil de Spotify y el identificador operativo que permitirá crear playlists reales en la cuenta enlazada.

En el paso 1, la aplicación abre la entrevista guiada de check-in. Durante esta fase, el usuario declara su estado emocional actual, su objetivo principal, su nivel de energía, su nivel de estrés, sus preferencias sobre voz, intensidad, exploración y popularidad, la duración deseada de la sesión y el estado final que espera alcanzar. Esta entrevista constituye el núcleo declarativo del sistema y produce el primer contexto semántico de sesión.

En el paso 2, si el usuario activa la medición del entorno, la aplicación realiza una lectura del micrófono y genera un perfil acústico estructurado. Esta medición no se limita al volumen medio, sino que incorpora variabilidad, estabilidad, transitorios y ráfagas para distinguir entre silencio, conversación, ruido intermitente, actividad pública o ruido intenso continuo.

En el paso 3, el cliente persiste el check-in en Firestore, separando la información pública de la información emocional cifrada cuando corresponde. De este modo, la aplicación conserva trazabilidad operativa sin renunciar a la protección del dato sensible.

En el paso 4, el frontend envía al backend la petición de recomendación de sesión. Esta petición ya incluye tanto las respuestas declaradas por el usuario como las señales ambientales derivadas del micrófono y, si existe, el identificador del perfil Spotify enlazado.

En el paso 5, el backend valida estructuralmente el payload recibido y construye varios candidatos de modo. En la versión final, estos candidatos se generan variando la intensidad y construyendo para cada alternativa un perfil musical completo. Cada candidato recibe inicialmente una puntuación heurística basada en la cercanía al objetivo, la coherencia con la intensidad solicitada, la alineación con el resultado esperado y la memoria binaria acumulada por feedback anteriores.

En el paso 6, si el modelo supervisado de sesión está disponible y el `mood` actual cuenta con cobertura suficiente, el backend activa el clasificador ML y estima la probabilidad de utilidad de cada candidato. Esa probabilidad no sustituye la heurística, sino que se transforma en un ajuste incremental que se suma a la puntuación base. El resultado final es, por tanto, un ranking híbrido en el que conviven reglas interpretables y evidencia aprendida.

En el paso 7, el backend devuelve al cliente la recomendación final de sesión, junto con un `recommendation_id` que actúa como identificador de enlace para la segunda mitad del flujo. Esta respuesta incluye además información sobre si el ML ha estado activo, cuál ha sido la fuente de selección final y, cuando procede, la probabilidad estimada del modo seleccionado.

En el paso 8, la recomendación se persiste en Firestore junto con el contexto completo de la sesión, incluyendo señales de entorno, preferencias declaradas y estado del aprendizaje. Esto permite reconstruir posteriormente el razonamiento operativo seguido en cada sesión.

En el paso 9, si el usuario decide materializar la recomendación, el cliente invoca el endpoint de generación de playlist de Spotify. En este momento se transmite el mismo contexto funcional de la sesión y se enlaza la petición con la recomendación previamente obtenida.

En el paso 10, el backend vuelve a construir el perfil musical objetivo, esta vez ya orientado a la selección de canciones. Este perfil combina información del check-in, aprendizaje individual previo, resultado esperado, entorno acústico y señales derivadas de la sesión actual. A partir de ahí se formula un conjunto de consultas primarias, consultas reforzadas por entorno y ajustes de exclusión o afinidad.

En el paso 11, el sistema toma como fuente principal de ranking el catálogo MSD enriquecido con rasgos musicales. Sobre ese conjunto de candidatos aplica un pipeline de scoring heurístico que incluye ajuste funcional, ajuste por entorno, ajuste por resultado esperado y ajuste semántico-textual. Este último se apoya en la interpretación textual del contenido disponible para aproximar conceptos como calidez, tensión, foco o acompañamiento.

En el paso 12, el backend intenta materializar en Spotify las canciones mejor puntuadas, buscando coincidencias válidas por título y artista. Cuando obtiene un conjunto suficiente de URIs reproducibles, ensambla la playlist final respetando la duración objetivo, la variedad entre artistas y la curva de activación deseada para la sesión.

En el paso 13, la playlist se crea realmente en Spotify y su información básica se devuelve a la aplicación. El cliente la guarda también en Firestore, junto con el modo recomendado, el contexto empleado y los tracks seleccionados, de manera que la sesión quede completamente trazada.

En el paso 14, tras escuchar la sesión, el usuario proporciona feedback sobre su utilidad, su efecto y su estado posterior. Este feedback se persiste en Firestore tanto a nivel público como, cuando procede, en un bloque privado cifrado.

En el paso 15, el backend utiliza ese feedback para cerrar el ciclo de aprendizaje. En primer lugar, actualiza la memoria ligera por modo recomendado. En segundo lugar, actualiza el perfil aprendido del usuario, distinguiendo entre señales de sesión, señales estables y aprendizaje específico por `mood`. En tercer lugar, genera un ejemplo supervisado de sesión que resume el contexto, el modo seleccionado y las características agregadas de la playlist finalmente entregada.

En el paso 16, si el sistema detecta nuevos ejemplos etiquetados, se activa el mantenimiento automático del clasificador de modos. Este proceso audita el estado actual del dataset, reentrena el modelo si es necesario y deja actualizados los metadatos de disponibilidad y calidad del componente supervisado.

Desde una perspectiva de arquitectura, este flujo permite afirmar que Harmony Hub no es únicamente un generador de playlists, sino un sistema adaptativo completo que conecta adquisición de contexto, recomendación híbrida, generación musical reproducible, trazabilidad de sesión y realimentación supervisada.

## 5. Síntesis final

La versión final de Harmony Hub permite sostener con rigor tres afirmaciones. En primer lugar, que el entorno medido por el micrófono no se limita a ser mostrado en la interfaz, sino que influye realmente en la recomendación de sesión y en la construcción de la playlist. En segundo lugar, que cada entrada del usuario es trazable desde su origen, validada tanto en cliente como en backend y persistida dentro de un flujo coherente. En tercer lugar, que el sistema es capaz de resolver situaciones complejas en las que el objetivo funcional y el resultado esperado no coinciden de forma trivial, manteniendo una recomendación interpretable, híbrida y adaptativa.

Por ello, Harmony Hub puede presentarse en defensa como una solución final funcional, profesional y técnicamente consistente, cuyo comportamiento interno resulta auditable y cuya lógica de personalización puede explicarse de manera transparente.
