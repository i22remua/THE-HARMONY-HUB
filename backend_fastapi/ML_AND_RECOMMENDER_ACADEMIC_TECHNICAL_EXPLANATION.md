# Explicación Académica y Técnica del Modelo de ML y del Motor de Recomendación

## 1. Propósito del componente de aprendizaje automático

El componente de aprendizaje automático de Harmony Hub no selecciona canciones de forma directa. Su función principal es priorizar el modo de sesión más adecuado para un usuario en un contexto concreto. Esto significa que el modelo opera sobre una capa intermedia de decisión: a partir del estado emocional, el objetivo declarado, la energía, el estrés y otras preferencias contextuales, estima qué tipo de sesión tiene más probabilidad de resultar útil.

Desde un punto de vista académico, este planteamiento responde a una decisión de diseño deliberada. En lugar de confiar todo el sistema a un modelo de recomendación de canciones extremo a extremo, se adopta una arquitectura híbrida en la que el aprendizaje automático interviene en una decisión de alto nivel y deja la selección final de canciones a un motor de recomendación especializado. Esta separación permite mejorar la explicabilidad, reducir el riesgo de recomendaciones erráticas y hacer que la influencia del aprendizaje pueda ser auditada con más claridad.

En consecuencia, el modelo supervisado no sustituye al recomendador musical, sino que actúa como una capa de priorización contextual dentro de una cadena de decisión más amplia.

## 2. Problema que resuelve el modelo

El problema que aborda el modelo puede formularse como una tarea de clasificación o ranking entre varios modos de sesión candidatos. Dado un contexto de entrada, el sistema necesita decidir cuál de los modos disponibles es más adecuado para ese momento. Por ejemplo, ante un usuario con objetivo de relajación, estado emocional estresado, baja energía y preferencia por una intensidad suave, el sistema debe valorar si conviene una sesión más estable, más acompañada o más progresiva.

Sin este componente, la elección dependería exclusivamente de reglas heurísticas. Las heurísticas siguen siendo útiles y continúan formando parte del sistema, pero el modelo permite capturar patrones observados en sesiones previas con feedback real. De esta forma, el sistema puede adaptar mejor la priorización de modos a partir de la experiencia acumulada.

## 3. Variables de entrada y salida del modelo

Desde el punto de vista conceptual, el modelo recibe variables que describen el estado actual del usuario y el contexto de uso. Entre las más relevantes se encuentran:

- `mood`
- `goal`
- `stress_level`
- `energy_level`
- `vocal_preference`
- `intensity_preference`
- `exploration_preference`
- `popularity_preference`
- `session_duration_min`
- `desired_outcome`
- variables opcionales del entorno acústico cuando la medición es válida

La salida del modelo no es una canción ni una playlist, sino una distribución de probabilidad o puntuación relativa sobre varios modos de sesión candidatos. Posteriormente, el sistema combina estas puntuaciones con la heurística contextual para seleccionar el modo final.

## 4. Integración académica dentro del sistema híbrido

Harmony Hub utiliza una arquitectura híbrida formada por cuatro capas principales:

1. Una capa de entrada contextual, basada en el check-in conversacional del usuario.
2. Una capa heurística, que puntúa modos de sesión a partir de reglas de negocio.
3. Una capa de aprendizaje automático, que reordena o refuerza candidatos si existe evidencia suficiente.
4. Una capa de personalización musical y ranking de canciones sobre un catálogo propio.

Esta organización es importante porque permite explicar que la inteligencia del sistema no depende de un único modelo. El modelo supervisado aporta capacidad de adaptación estadística, pero trabaja en coordinación con reglas explícitas, memoria individual del usuario y una fase posterior de recomendación musical basada en catálogo.

Desde la perspectiva de un TFG, este enfoque es especialmente defendible porque:

- mejora la trazabilidad de decisiones,
- permite justificar abstenciones del modelo,
- reduce la opacidad frente a soluciones puramente end-to-end,
- facilita la validación parcial de cada capa.

## 5. Explicación académica del motor de recomendación

El motor de recomendación transforma una decisión abstracta de sesión en una propuesta musical concreta. Su objetivo no es únicamente encontrar canciones parecidas entre sí, sino construir una sesión coherente con el estado del usuario, con el objetivo funcional deseado y con las preferencias aprendidas.

El flujo conceptual del motor es el siguiente:

1. El usuario completa un check-in.
2. Se generan modos de sesión candidatos.
3. La heurística asigna puntuaciones iniciales.
4. El modelo de ML, si está disponible y pasa las puertas de calidad, ajusta la priorización.
5. Se construye un `generation_profile`.
6. A partir de ese perfil se seleccionan candidatos de un catálogo musical propio.
7. Los candidatos se rankean según señales funcionales, semánticas y de afinidad.
8. Finalmente, se intenta materializar la sesión como playlist real en Spotify.

El motor no depende exclusivamente de Spotify como fuente musical principal. La lógica final se apoya sobre todo en el catálogo `msd_tracks`, que actúa como base estructurada para el ranking musical. Spotify se usa principalmente para autenticación, perfil musical del usuario, recuperación de elementos de gusto reciente y materialización final de la playlist.

## 6. Uso del catálogo `msd_tracks`

Una parte clave del diseño final consiste en el uso del catálogo `msd_tracks` como fuente principal de trabajo del recomendador. En lugar de construir la recomendación directamente sobre búsquedas abiertas o sobre audio features extraídas dinámicamente de Spotify, el sistema dispone de un catálogo curado y enriquecido que contiene:

- identificadores propios,
- títulos y artistas,
- rasgos musicales relevantes,
- agrupaciones funcionales,
- señales de popularidad relativa,
- y metadatos útiles para el ranking.

Académicamente, esta decisión aporta varias ventajas:

- reduce la dependencia de APIs externas para la fase central de recomendación,
- permite mayor control experimental,
- facilita la reproducibilidad,
- y hace más estable la evaluación del motor.

Como consecuencia, la fase más creativa y determinista del sistema se realiza sobre `msd_tracks`, mientras que Spotify interviene en la fase de correspondencia final con canciones reales disponibles en la plataforma.

## 7. Explicación técnica del modelo de ML

Desde la perspectiva de implementación, el modelo se entrena con ejemplos persistidos tras sesiones reales con feedback. Cada vez que una sesión se cierra y el usuario aporta valoración, el backend registra un ejemplo estructurado en la colección `training_session_examples`. Ese ejemplo conserva tanto el contexto de entrada como el resultado de utilidad observado.

El entrenamiento se ejecuta de forma offline mediante un script dedicado. Este proceso:

- carga los ejemplos disponibles,
- prepara las variables,
- entrena el clasificador/ranker de modos de sesión,
- calcula métricas de rendimiento,
- y guarda metadatos de calidad y disponibilidad del modelo.

Entre los metadatos más importantes se incluyen:

- `balanced_accuracy`
- `roc_auc`
- `f1`
- `quality_score`
- cobertura por `mood`
- estado de disponibilidad del modelo

Esto permite que la fase de inferencia no dependa solo de la existencia física de un artefacto entrenado, sino también de su nivel de madurez y de la suficiencia de evidencia.

## 8. Puertas de calidad y umbral de madurez

El sistema no activa el modelo únicamente porque se hayan acumulado varias sesiones. En su lugar, utiliza un criterio basado en evidencia. El umbral de madurez se sustenta en dos niveles:

### 8.1. Gate global del modelo

El modelo debe cumplir unas condiciones mínimas de calidad global, expresadas mediante métricas de evaluación. Entre ellas destacan:

- `balanced_accuracy`
- `roc_auc`
- `f1`
- `quality_score`

El `quality_score` se obtiene como una combinación ponderada de dichas métricas, de forma que la disponibilidad del modelo no dependa de una única medida aislada.

### 8.2. Gate específica por `mood`

Además de la calidad global, el sistema exige cobertura suficiente en el estado emocional concreto. Para ello se evalúan señales como:

- `observation_strength`
- `label_balance`
- `mode_diversity`
- `coverage_ratio`

Esto significa que un modelo puede estar globalmente entrenado y, aun así, abstenerse de influir en un `mood` concreto si ese estado todavía no tiene evidencia suficiente.

Académicamente, este mecanismo es importante porque evita sobreinterpretar aprendizaje donde apenas existe muestra útil.

## 9. Aprendizaje individual del usuario

El aprendizaje automático global no es la única capa adaptativa del sistema. Harmony Hub mantiene además una memoria individual por usuario en `user_generation_preferences`. Esta memoria recoge patrones estables y señales acumuladas a partir de sesiones y feedback previos.

La implementación distingue tres niveles:

- señales de sesión,
- señales estables,
- señales específicas por `mood`.

Con estas señales el backend calcula:

- `session_taste_weight`
- `stable_taste_weight`
- `mood_learning_application_factor`

El objetivo es que la personalización no dependa únicamente del modelo global, sino también del comportamiento longitudinal del propio usuario.

## 10. Evolución desde una gate binaria a una aplicación progresiva

Durante el desarrollo se detectó un problema: la activación binaria por `mood` hacía que, incluso con aprendizaje global real, la interfaz pudiera seguir mostrando pesos del 0\% si el estado emocional concreto aún no superaba la gate conservadora. Esto generaba una percepción engañosa de ausencia total de aprendizaje.

Para resolverlo, la lógica evolucionó hacia una aplicación progresiva. En vez de anular completamente el aprendizaje cuando el `mood` aún no ha madurado, el sistema calcula un factor de aplicación parcial. De esta forma:

- si la evidencia es muy débil, la influencia sigue siendo mínima,
- si la evidencia es intermedia, se aplica una parte del aprendizaje,
- y si la evidencia ya es sólida, se permite el peso completo.

Como resultado, el sistema conserva prudencia, pero evita comportamientos excesivamente rígidos.

## 11. Explicación técnica del motor de recomendación

La implementación del motor de recomendación sigue una secuencia clara en backend:

1. El check-in se registra.
2. Se genera una recomendación de sesión.
3. Se calcula el modo seleccionado y la fuente de selección.
4. Se construye un `generation_profile`.
5. Se recuperan candidatos musicales desde `msd_tracks` y, cuando procede, señales del gusto del usuario en Spotify.
6. Se rankean tracks según coherencia con el perfil objetivo.
7. Se intenta resolver esos tracks a canciones reales de Spotify.
8. Si la materialización es posible, se crea la playlist final.

El backend registra en logs y persistencia elementos clave como:

- `selected_mode`
- `selection_source`
- `ml_enabled`
- `taste_profile_mode`
- `session_taste_weight`
- `stable_taste_weight`
- `queries_used`
- `selected_tracks`

Esto permite auditar tanto la decisión abstracta como la salida final.

## 12. Integración real del entorno acústico

La escucha del entorno constituye otra capa de contexto. El sistema mide varios segundos de audio ambiente y calcula métricas como:

- media de decibelios,
- desviación estándar,
- pico diferencial,
- ratio de transitorios,
- número de ráfagas,
- `sampleDensityHz`,
- `stabilityScore`,
- `confidence`.

Posteriormente, una capa de decisión determina si la medición es lo bastante fiable para influir realmente en la personalización. Esto evita que una medición ambigua o poco densa condicione la recomendación. En consecuencia, la aplicación distingue entre:

- entorno medido y usado para personalizar,
- entorno medido pero mantenido solo como referencia,
- entorno no medido.

Técnicamente, esta información ya puede persistirse como evidencia en:

- `checkins`
- `recommendations`
- `generated_playlists`

mediante campos como:

- `environment_measured`
- `environment_usage_status`
- `environment_usage_rationale`
- `environment_stability_score`
- `environment_sample_density_hz`

## 13. Cómo evidenciar académicamente que el sistema aprende en el tiempo

Para demostrar que el sistema aprende, no basta con enseñar capturas aisladas. La evidencia debe ser longitudinal. La memoria debería mostrar, sesión a sesión:

- el contexto declarado,
- el modo seleccionado,
- la fuente de selección,
- el feedback recibido,
- la evolución de los pesos aprendidos,
- el estado de la gate por `mood`,
- y la salida musical final.

Lo importante no es afirmar que el sistema aprende tras un número fijo de sesiones, sino demostrar que:

- aumenta la evidencia disponible,
- mejora la cobertura por `mood`,
- cambia el modo de aplicación del aprendizaje,
- y crece el peso efectivo de la memoria individual cuando existen señales suficientes.

## 14. Explicación como programador de las evidencias necesarias

Desde el punto de vista de implementación, las evidencias más útiles para documentar el funcionamiento real del sistema son:

### 14.1. Evidencia de entrada

- captura del check-in en la app,
- datos persistidos del check-in,
- medición del entorno si se ha utilizado.

### 14.2. Evidencia de decisión

- logs del backend con:
  - `selected_mode`
  - `selection_source`
  - `ml_enabled`
  - `mood_gate_passed`
  - `mood_quality_score`
  - `mood_learning_application_factor`

### 14.3. Evidencia de salida

- captura de la recomendación,
- captura de la playlist generada,
- documentos Firestore de `recommendations` y `generated_playlists`,
- tracks finales seleccionados.

### 14.4. Evidencia de aprendizaje longitudinal

- datos de `user_generation_preferences`,
- datos de `training_session_examples`,
- tablas comparativas por sesión y por `mood`.

## 15. Valor académico del enfoque adoptado

El valor principal del enfoque reside en que el sistema no trata el aprendizaje automático como una caja negra aislada, sino como una capa auditada dentro de un sistema híbrido explicable. Esto permite:

- justificar cuándo el modelo actúa,
- justificar cuándo se abstiene,
- demostrar qué parte depende del contexto actual,
- demostrar qué parte depende de memoria individual,
- y relacionar la salida final con evidencia observable.

Para un trabajo académico, esta combinación entre capacidad adaptativa, trazabilidad y control experimental ofrece una base más sólida que una solución monolítica menos explicable.

## 16. Cómo evidenciar específicamente la regresión logística

Dado que el clasificador final del sistema es una regresión logística, conviene evidenciarlo de forma explícita en la documentación. No basta con afirmar que el proyecto utiliza aprendizaje automático; es recomendable demostrar qué algoritmo se ha implementado, por qué se ha elegido y cómo se valida su rendimiento en el sistema real.

### 16.1. Evidencia técnica directa en el código

La evidencia más clara debe apoyarse en la implementación del pipeline de entrenamiento. En este proyecto, la regresión logística se identifica de forma directa en el script de entrenamiento del modelo:

- import del algoritmo `LogisticRegression`
- construcción explícita del clasificador final con:
  - `LogisticRegression(max_iter=1000, class_weight="balanced")`

Esto permite afirmar sin ambigüedad que el algoritmo de clasificación empleado es una regresión logística y no otro modelo distinto.

### 16.2. Evidencia del pipeline completo

Académicamente, conviene dejar claro que la regresión logística no actúa de forma aislada, sino como clasificador final dentro de un pipeline de preprocesado. Una forma clara de explicarlo es mediante una tabla como la siguiente:

| Etapa del pipeline | Técnica utilizada |
|---|---|
| Variables numéricas | `SimpleImputer(strategy="median")` + `StandardScaler` |
| Variables categóricas | `SimpleImputer(strategy="most_frequent")` + `OneHotEncoder(handle_unknown="ignore")` |
| Variables binarias | `passthrough` |
| Clasificador final | `LogisticRegression(max_iter=1000, class_weight="balanced")` |

Esta tabla permite mostrar que el modelo no es un bloque opaco, sino una secuencia bien definida de transformación y clasificación.

### 16.3. Justificación académica de la elección

La elección de una regresión logística puede justificarse de forma sólida en este proyecto por varias razones:

- funciona correctamente con volúmenes moderados de datos,
- produce probabilidades mediante `predict_proba`,
- mantiene buena interpretabilidad frente a modelos más complejos,
- presenta un coste computacional bajo,
- y resulta adecuada cuando el problema consiste en estimar utilidad o adecuación relativa a partir de variables estructuradas.

Por tanto, la regresión logística no debe presentarse como una elección casual, sino como una decisión coherente con:

- el tamaño del dataset disponible,
- la necesidad de explicabilidad,
- y la integración dentro de un sistema híbrido con heurística y reglas explícitas.

### 16.4. Evidencia experimental del modelo entrenado

La segunda gran prueba de que el sistema emplea realmente la regresión logística no está solo en el código, sino en sus resultados de entrenamiento. Para ello, deben mostrarse métricas reales generadas tras el entrenamiento y guardadas en los metadatos del modelo.

Entre las métricas más relevantes se encuentran:

- `balanced_accuracy`
- `roc_auc`
- `f1`
- `quality_score`

Estas métricas permiten evidenciar dos cosas:

1. que el modelo no solo está implementado, sino entrenado;
2. que su activación se basa en calidad observada, no solo en disponibilidad técnica.

### 16.5. Evidencia de uso en inferencia

Además de probar que el algoritmo entrenado es una regresión logística, conviene demostrar que realmente participa en la inferencia del sistema. Para ello, deben mostrarse evidencias como:

- logs con probabilidades de candidatos,
- `ml_enabled`,
- `selection_source`,
- `selected_mode_probability`,
- `mode_ml_probability`,
- y los ajustes `ml_delta` aplicados a los candidatos.

Esto demuestra que la regresión logística no se queda en un experimento offline, sino que influye en la decisión final cuando supera sus gates de calidad y cobertura.

### 16.6. Forma recomendada de documentarlo en la memoria

La forma más sólida de presentarlo en la memoria consiste en combinar cuatro piezas:

1. una definición breve del algoritmo utilizado,
2. una tabla del pipeline,
3. una justificación de por qué se eligió regresión logística,
4. y una tabla de métricas reales obtenidas tras el entrenamiento.

Una redacción académica válida sería:

“El clasificador final del pipeline supervisado se implementó mediante una regresión logística, seleccionada por su estabilidad con conjuntos de datos moderados, su capacidad para producir probabilidades interpretables y su adecuada integración dentro de un sistema híbrido de recomendación musical contextual.”

Una redacción más técnica sería:

“Tras el preprocesado de variables numéricas, categóricas y binarias, el pipeline entrena un clasificador `LogisticRegression(max_iter=1000, class_weight="balanced")`, cuya salida probabilística se utiliza para ajustar la priorización de modos de sesión candidatos.”

### 16.7. Qué no hace falta demostrar

Para este proyecto no es necesario desarrollar una derivación matemática extensa de la regresión logística. Lo relevante es:

- identificar el algoritmo correctamente,
- justificar su elección,
- mostrar su implementación,
- y presentar evidencia objetiva de su funcionamiento.

En un TFG aplicado, este nivel de evidencia suele ser suficiente y más útil que una formulación excesivamente teórica si no está conectada con el comportamiento real del sistema.

## 17. Resumen final

En Harmony Hub, el modelo de aprendizaje automático cumple una función de priorización de modos de sesión, mientras que el motor de recomendación traduce esa decisión a una propuesta musical concreta apoyada sobre el catálogo `msd_tracks`. La arquitectura final es híbrida, progresiva y auditable. El sistema combina:

- contexto declarado por el usuario,
- reglas heurísticas,
- modelo supervisado,
- memoria individual,
- contexto acústico opcional,
- y ranking musical sobre catálogo propio.

La explicación académica debe centrarse en justificar el diseño, las métricas y las gates de madurez. La explicación técnica debe mostrar cómo estos componentes se implementan realmente en colecciones, servicios, scripts y pantallas de la aplicación. La validación más sólida surge de combinar ambas perspectivas con evidencias longitudinales extraídas del uso real de la app.
