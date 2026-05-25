# Tablas de evidencia del perfil único

Estas tablas están preparadas para reutilizarse en memoria, anexos o defensa
oral. Se basan en los datos reales del perfil `xabi05` recuperados de
`training_session_examples` y `user_generation_preferences`.

Este documento actúa como versión canónica de la evidencia del perfil único:
resume tanto las tablas cuantitativas como la lectura diagnóstica principal, de
modo que no haga falta mantener un diagnóstico narrativo separado con el mismo
contenido base.

## Tabla A. Resumen global del perfil

| Indicador | Valor |
|---|---:|
| Sesiones cerradas observadas en `training_session_examples` | `13` |
| Feedback útil real | `12` |
| Feedback no útil real | `1` |
| Feedback interno total del perfil estable/contextual | `25` |
| Feedback real que debe usarse como referencia operativa | `13` |
| Pesos globales teóricos calculados (`equilibrado`) | `session = 0.242`, `stable = 0.275` |
| `mood` con gate superada | `neutral` |
| `mood` cercanos pero aún no maduros | `triste`, `estresado`, `cansado` |
| Aplicación parcial real para `estresado` tras el ajuste | `session = 0.060`, `stable = 0.069` |

## Tabla B. Evidencia por mood

| Mood | Sesiones | Útiles | No útiles | Quality score | Observation strength | Gate | Lectura |
|---|---:|---:|---:|---:|---:|---|---|
| `neutral` | `4` | `4` | `0` | `63.86` | `0.632` | `PASS` | Ya puede activar aprendizaje aplicado |
| `triste` | `3` | `3` | `0` | `56.39` | `0.528` | `FAIL` | Cerca de madurar, pero aún sin gate |
| `estresado` | `2` | `2` | `0` | `45.14` | `0.393` | `FAIL` | La señal es positiva, pero todavía insuficiente |
| `cansado` | `2` | `2` | `0` | `47.36` | `0.393` | `FAIL` | Misma situación que `estresado` |
| `feliz` | `1` | `1` | `0` | `31.01` | `0.221` | `FAIL` | Muy poca evidencia |

## Tabla C. Secuencia real de sesiones observadas

| Sesión | Goal | Mood | Modo recomendado | Helpful | Effect | Estado final | Lectura evidenciable |
|---|---|---|---|---|---|---|---|
| `1` | `foco` | `cansado` | `foco_cansado_suave` | `Sí` | `mejoró` | `más centrado` | Primera señal positiva en `cansado` |
| `2` | `energia` | `triste` | `energia_triste_media` | `Sí` | `mejoró` | `más acompañado` | Arranque positivo del patrón `triste` |
| `3` | `relajacion` | `neutral` | `relajacion_neutral_suave` | `Sí` | `mejoró` | `más tranquilo` | Primer refuerzo claro en `neutral` |
| `4` | `foco` | `neutral` | `foco_neutral_media` | `Sí` | `mejoró` | `más centrado` | Consolidación de `neutral` |
| `5` | `energia` | `cansado` | `energia_cansado_media` | `Sí` | `mejoró` | `más animado` | Segunda sesión útil en `cansado` |
| `6` | `relajacion` | `triste` | `relajacion_triste_suave` | `Sí` | `mejoró` | `más acompañado` | Segunda sesión útil en `triste` |
| `7` | `foco` | `estresado` | `foco_estresado_media` | `Sí` | `mejoró` | `más centrado` | Primera evidencia en `estresado` |
| `8` | `energia` | `neutral` | `energia_neutral_media` | `Sí` | `mejoró` | `más animado` | `neutral` ya cubre varios objetivos |
| `9` | `relajacion` | `cansado` | `relajacion_cansado_suave` | `No` | `empeoró` | `peor` | Único contraejemplo, útil para no sesgar el perfil |
| `10` | `energia` | `triste` | `energia_triste_media` | `Sí` | `mejoró` | `más acompañado` | Tercera evidencia positiva en `triste` |
| `11` | `foco` | `neutral` | `foco_neutral_suave` | `Sí` | `mejoró` | `más centrado` | `neutral` alcanza madurez funcional |
| `12` | `relajacion` | `feliz` | `relajacion_feliz_alta` | `Sí` | `mejoró` | `más tranquilo` | Solo una observación, aún insuficiente |
| `13` | `foco` | `estresado` | `foco_estresado_media` | `Sí` | `mejoró` | `más centrado` | Segunda evidencia en `estresado`, todavía sin gate |

## Tabla D. Diagnóstico del 0% mostrado en la interfaz

| Elemento | Valor real | Interpretación |
|---|---|---|
| `Feedback útil: 23` en captura | No representa sesiones reales; mezcla contadores internos | Era un valor engañoso para el usuario |
| Sesiones reales observadas | `13` | Este es el volumen correcto de uso cerrrado |
| Útiles reales | `12` | Este es el aprendizaje positivo real |
| Estado de `estresado` | `FAIL` en la `mood gate`, pero con aplicación parcial | Ya no debería caer automáticamente a `0%` |
| Modo aplicado tras el ajuste | `progressive_contextual` | El sistema mezcla parte del gusto aprendido con prudencia |

## Tabla E. Conclusión de aprendizaje observable

| Pregunta | Respuesta evidenciada |
|---|---|
| ¿Existe aprendizaje global? | Sí. El perfil acumula preferencias y pesos teóricos positivos. |
| ¿Se aplica ya en todos los moods? | No. Solo `neutral` ha superado la gate conservadora completa, pero otros moods ya pueden recibir aplicación parcial. |
| ¿Está roto el aprendizaje? | No. El sistema conserva prudencia, pero ahora evita el salto binario a cero. |
| ¿Qué falta para que suba en `estresado`? | Más sesiones útiles del mismo `mood`, manteniendo consistencia positiva. |
| ¿Qué demuestra mejor el funcionamiento del ML en el tiempo? | El paso de una situación inicial sin cobertura suficiente a un `mood` como `neutral`, que sí alcanza gate y puede activar mezcla aprendida. |

## Nota metodológica

Para documentar el proyecto conviene distinguir siempre entre:

- `sesiones reales cerradas`
- `feedback útil real`
- `feedback_count` interno del perfil

El primero y el segundo sirven para la defensa funcional del sistema. El
tercero es un contador técnico interno y no debe presentarse como número real
de sesiones del usuario.

## Tabla F. Nueva evidencia longitudinal por bloques del plan

| Bloque | Casos observados | Evolución principal | Resultado evidenciable |
|---|---|---|---|
| `triste + energia` | `4` | `68.61 -> 78.85` con `application_factor=1.0` | Mood maduro y aprendizaje plenamente aplicado |
| `estresado + relajacion` | `3` | `55.49 / 0.55 -> 67.71 / 1.0` | Paso de aplicación prudente a aplicación completa |
| `cansado` | `3` | `56.98 / 0.55 -> 73.41 / 1.0` | Maduración del mood en varios objetivos (`foco`, `relajacion`, `energia`) |
| `neutral + relajacion` | `1` adicional | `63.86 / 1.0` | Refuerzo de un mood ya estable |

## Tabla G. Evolución observada de `estresado`

| Caso | Goal | Inputs clave | Mode | Profile mode | Session weight | Stable weight | Gate | Quality | Factor | Lectura |
|---|---|---|---|---|---:|---:|---|---:|---:|---|
| `E` | `relajacion` | `5/2`, instrumental, suave, familiar, mainstream, `env=on` | `relajacion_estresado_suave` | `progressive_contextual` | `0.163` | `0.177` | `FAIL` | `55.49` | `0.55` | Todavía prudente |
| `F` | `relajacion` | `5/2`, indistinto, suave, equilibrado, mixta, `env=off` | `relajacion_estresado_suave` | `stable_weighted` | `0.264` | `0.286` | `PASS` | `62.37` | `1.0` | Ya maduro |
| `G` | `relajacion` | `4/1`, con voz, suave, descubrir, alternativa, `env=off` | `relajacion_estresado_suave` | `stable_weighted` | `0.191` | `0.206` | `PASS` | `67.71` | `1.0` | Consolidación del mood |

## Tabla H. Evolución observada de `cansado`

| Caso | Goal | Inputs clave | Mode | Profile mode | Session weight | Stable weight | Gate | Quality | Factor | Lectura |
|---|---|---|---|---|---:|---:|---|---:|---:|---|
| `H` | `foco` | `3/2`, instrumental, suave, familiar, mixta, `env=on` | `foco_cansado_suave` | `progressive_contextual` | `0.165` | `0.178` | `FAIL` | `56.98` | `0.55` | Inicio todavía prudente |
| `I` | `relajacion` | `3/2`, instrumental, media, equilibrado, mixta, `env=off` | `relajacion_cansado_media` | `stable_weighted` | `0.268` | `0.287` | `PASS` | `63.86` | `1.0` | Supera gate y madura |
| `J` | `energia` | `4/1`, indistinto, media, equilibrado, alternativa, `env=on` | `energia_cansado_media` | `stable_weighted` | `0.270` | `0.288` | `PASS` | `73.41` | `1.0` | Evidencia fuerte y transversal |

## Tabla I. Evidencia adicional de `neutral`

| Caso | Goal | Mode | Profile mode | Session weight | Stable weight | Gate | Quality | Factor | Lectura |
|---|---|---|---|---:|---:|---|---:|---:|---|
| `K` | `relajacion` | `relajacion_neutral_suave` | `stable_weighted` | `0.271` | `0.289` | `PASS` | `63.86` | `1.0` | Refuerzo consistente de un mood ya maduro |

## Tabla J. Mantenimiento automático observado en las nuevas trazas

| Evento | Evidencia |
|---|---|
| Crecimiento de ejemplos etiquetados | `18 -> 19 -> 20 -> 21 -> 22 -> 23 -> 24 -> 25 -> 26 -> 28 -> 29` |
| Comportamiento del mantenimiento | `train | reason=new_labeled_examples_detected` |
| Resultado | Reentrenado automático consistente tras nuevo feedback |

## Lectura diagnóstica actualizada

- La nueva evidencia longitudinal ya no respalda solo la madurez de `neutral`.
- `triste`, `estresado` y `cansado` muestran trayectorias observables de
  maduración, con paso desde factores parciales (`0.55`) a aplicación completa
  (`1.0`).
- `estresado` y `cansado` dejan de ser solo moods “cercanos” y pasan a aportar
  casos defendibles de aprendizaje activo.
- `neutral` sigue siendo el mood más estable, pero ya no es el único ejemplo
  fuerte disponible.
- El sistema no solo aprende, sino que lo hace de forma gradual y auditable:
  los pesos suben, las gates cambian de estado y el mantenimiento automático
  acompaña cada nuevo cierre de sesión.

## Nota sobre el cambio de trazas

En los primeros registros aparece un logging más verboso, todavía heredado de
una fase previa del backend (`preferred_artist_names`, `queries_used`, `top`
tracks completos). Las últimas trazas ya reflejan la versión compacta y final
del runtime:

- `[AFFINITY] source=msd_only`
- `[CATALOG] ... ranking=heuristic_only`
- `[PLAYLIST] created ... | query_signal_count=...`

Esto es coherente con la arquitectura final del proyecto: `msd_tracks` como
fuente principal del ranking y Spotify como capa de materialización.

## Actualización corroborada con Firebase (`2026-05-13`)

La evidencia anterior sigue siendo útil para explicar la evolución del perfil,
pero a fecha de `2026-05-13` la foto real del sistema puede resumirse así:

### Tabla K. Estado real visible frente a estado real del modelo

| Nivel | Métrica | Valor |
|---|---|---:|
| Perfil visible (`user_generation_preferences/xabi05`) | `feedback_count` | `57` |
| Perfil visible (`user_generation_preferences/xabi05`) | `positive_feedback_count` | `56` |
| Perfil visible (`user_generation_preferences/xabi05`) | `negative_feedback_count` | `1` |
| Perfil por sesiones (`user_generation_preferences/xabi05`) | `session_feedback_count` | `29` |
| Perfil por sesiones (`user_generation_preferences/xabi05`) | `session_positive_feedback_count` | `28` |
| Perfil por sesiones (`user_generation_preferences/xabi05`) | `session_negative_feedback_count` | `1` |
| Dataset supervisado (`training_session_examples`) | ejemplos reales del modelo | `29` |
| Materialización funcional (`generated_playlists`) | playlists creadas | `29` |

### Tabla L. Señales aprendidas mostradas en la interfaz

| Señal | Firestore | Lectura visual |
|---|---:|---|
| `preferred_valence` | `0.5192` | tono emocional `52%` |
| `preferred_energy` | `0.5026` | energía `50%` |
| `preferred_danceability` | `0.4197` | ritmo `42%` |

### Tabla M. Distribución real del dataset supervisado

| Dimensión | Resultado |
|---|---|
| Total ejemplos | `29` |
| Positivos | `28` |
| Negativos | `1` |
| `model_gate_passed` | `False` |
| `model_readiness_reason` | `insufficient_total_examples` |
| `readiness_reason` | `insufficient_class_coverage_for_cv` |
| `quality_score` global | `0.0` |
| `cv_folds` | `1` |

### Tabla N. Cobertura real por mood en `training_session_examples`

| Mood | Positivos | Negativos | Lectura |
|---|---:|---:|---|
| `triste` | `9` | `0` | Muy cubierto en positivo, nada tensionado |
| `estresado` | `6` | `0` | Buena señal positiva, sin contraejemplos |
| `cansado` | `7` | `1` | Único mood con algo de balance real |
| `neutral` | `5` | `0` | Perfil estable, pero unilateral |
| `feliz` | `1` | `0` | Testimonio insuficiente |

### Tabla O. Cobertura real por combinación `goal + mood`

| Combinación | Conteo | Lectura |
|---|---:|---|
| `energia + triste` | `8` positivas | Bloque dominante y ya muy explotado |
| `relajacion + estresado` | `4` positivas | Bloque fuerte y defendible |
| `energia + cansado` | `3` positivas | Bien encaminado |
| `relajacion + cansado` | `2` positivas, `1` negativa | Combinación más informativa del dataset |
| `foco + estresado` | `2` positivas | Aún necesita más tensión |
| `foco + cansado` | `2` positivas | Aún necesita más tensión |
| `relajacion + neutral` | `2` positivas | Estable, pero unilateral |
| `relajacion + triste` | `1` positiva | Muy débil |
| `energia + neutral` | `1` positiva | Muy débil |
| `relajacion + feliz` | `1` positiva | Muy débil |
| `energia + estresado` | `0` | Ausente |
| `foco + triste` | `0` | Ausente |
| `foco + feliz` | `0` | Ausente |
| `energia + feliz` | `0` | Ausente |

## Lectura diagnóstica final de esta actualización

- La app sí muestra un aprendizaje acumulado fuerte a nivel de perfil visible.
- El perfil aprendido mostrado al usuario no debe confundirse con la madurez del
  modelo supervisado.
- La prioridad ya no es “más sesiones positivas”, sino:
  - más cobertura de combinaciones ausentes
  - más ejemplos frontera
  - más negativos honestos
- La siguiente fase de recogida debe evaluarse con el dataset de
  `training_session_examples`, no con el contador visible `57 / 56 / 1`.

## Actualización corroborada con Firebase (`2026-05-14`)

La nueva tanda confirma progreso funcional importante del perfil, pero todavía
no resuelve el cuello de botella del modelo supervisado global.

### Tabla P. Estado real actualizado del perfil y del dataset

| Nivel | Métrica | Valor |
|---|---|---:|
| Perfil visible (`user_generation_preferences/xabi05`) | `feedback_count` | `71` |
| Perfil visible (`user_generation_preferences/xabi05`) | `positive_feedback_count` | `70` |
| Perfil visible (`user_generation_preferences/xabi05`) | `negative_feedback_count` | `1` |
| Perfil por sesiones (`user_generation_preferences/xabi05`) | `session_feedback_count` | `36` |
| Perfil por sesiones (`user_generation_preferences/xabi05`) | `session_positive_feedback_count` | `35` |
| Perfil por sesiones (`user_generation_preferences/xabi05`) | `session_negative_feedback_count` | `1` |
| Dataset supervisado (`training_session_examples`) | ejemplos reales del modelo | `36` |
| Colección `feedback` | feedback totales persistidos | `131` |

### Tabla Q. Señales visibles actuales del perfil

| Señal | Firestore | Lectura visible aproximada |
|---|---:|---|
| `preferred_valence` | `0.5194` | tono emocional `52%` |
| `preferred_energy` | `0.5033` | energía `50%` |
| `preferred_danceability` | `0.4334` | ritmo `43%` |

### Tabla R. Estado real actualizado del modelo supervisado

| Métrica | Valor |
|---|---:|
| `total_examples` | `36` |
| Positivos | `35` |
| Negativos | `1` |
| `data_gate_passed` | `False` |
| `model_gate_passed` | `False` |
| `model_readiness_reason` | `insufficient_total_examples` |
| `readiness_reason` | `insufficient_class_coverage_for_cv` |
| `quality_score` global | `0.0` |
| `cv_folds` | `1` |
| `mood_coverage_quality` global | `32.81` |

### Tabla S. Cobertura real por mood en `training_session_examples`

| Mood | Positivos | Negativos | Quality por mood | Gate | Lectura |
|---|---:|---:|---:|---|---|
| `triste` | `11` | `0` | `49.41` | `FAIL` | Muy cubierto en positivo, sin tensión negativa |
| `estresado` | `8` | `0` | `48.88` | `FAIL` | Mejor cobertura estructural, pero unilateral |
| `cansado` | `8` | `1` | `58.27` | `FAIL` | Sigue siendo el mood más informativo del dataset |
| `neutral` | `7` | `0` | `49.16` | `FAIL` | Bastante estable, pero sin contraejemplos |
| `feliz` | `1` | `0` | `15.98` | `FAIL` | Testimonial |

### Tabla T. Cobertura real por combinación `goal + mood`

| Combinación | Conteo | Lectura |
|---|---:|---|
| `energia + triste` | `10` positivas | Sigue siendo el bloque dominante |
| `relajacion + estresado` | `5` positivas | Muy defendible a nivel funcional |
| `energia + cansado` | `3` positivas | Cobertura razonable |
| `foco + cansado` | `3` positivas | Ya deja de ser un caso marginal |
| `relajacion + neutral` | `3` positivas | Estable, pero unilateral |
| `energia + neutral` | `2` positivas | Ya no es un caso aislado |
| `foco + estresado` | `2` positivas | Aún necesita más tensión |
| `relajacion + cansado` | `2` positivas, `1` negativa | Sigue siendo la combinación más informativa |
| `foco + neutral` | `2` positivas | Cobertura básica |
| `relajacion + triste` | `1` positiva | Débil |
| `relajacion + feliz` | `1` positiva | Muy débil |
| `energia + estresado` | `1` positiva | Ya existe, pero aún sin masa crítica |

### Tabla U. Nueva tanda observada y su valor documental

| Caso | Combinación | Resultado principal | Valor documental |
|---|---|---|---|
| `L` | `energia + triste` | `quality = 81.03`, modo final `alta` | Refuerza el extremo energético del mood más maduro |
| `M` | `energia + triste` | `quality = 82.82`, `env=on` | Consolida madurez muy alta de `triste` |
| `N` | `foco + cansado` | `quality = 76.76`, modo final `media` | Fortalece una combinación útil menos dominante |
| `O` | `relajacion + estresado` | `quality = 71.92`, modo final `media` | Suma una variante adicional ya defendible |
| `P` | `energia + neutral` | `quality = 73.41`, modo final `alta` | Refuerza una combinación antes débil |
| `Q` | `energia + estresado` | `quality = 75.27`, modo final `media` | Cubre una ausencia importante del plan anterior |

### Tabla V. Evidencia sobre el clasificador de entorno

Consulta real sobre `checkins` almacenados:

| `environment_context` | Conteo |
|---|---:|
| `Sin medir` | `102` |
| `Silencio estable` | `37` |
| `Ruido continuo intenso` | `22` |
| `Ruido de fondo suave` | `3` |
| `Actividad sonora moderada` | `1` |

Lectura:

- El sistema no está fijado a `Silencio estable`.
- Sí existe un sesgo conservador hacia contextos silenciosos cuando:
  - el nivel medio es bajo
  - la desviación es pequeña
  - y los picos son poco persistentes
- Esto encaja con la lógica actual del cliente, que suaviza muestras y recorta
  extremos antes de clasificar.

## Lectura diagnóstica consolidada (`2026-05-14`)

- A nivel de aprendizaje individual, Harmony Hub ya muestra una madurez fuerte
  en varios moods y no solo en uno.
- A nivel de cobertura del dataset, la situación mejora:
  - `energia + estresado` deja de estar ausente
  - `energia + neutral` gana masa
  - `foco + cansado` gana masa
- A nivel del modelo supervisado global, la debilidad central sigue siendo la
  misma:
  - demasiados positivos
  - casi ningún negativo
  - sin cobertura suficiente para validación cruzada real
- La conclusión correcta para memoria y defensa no es “el ML global ya decide”,
  sino:
  - el aprendizaje individual ya es sólido y observable
  - el modelo supervisado global existe, se reentrena y se audita
  - pero todavía permanece conservadoramente desactivado por madurez

## Nueva ampliación observada (`2026-05-15`)

La nueva tanda sube el dataset desde `36` a `45` ejemplos etiquetados y cierra
casi por completo la checklist ambiciosa. Su valor principal no es solo sumar
volumen, sino mejorar la cobertura de combinaciones hasta ahora débiles.

### Tabla W. Casos nuevos y lectura documental

| Caso | Combinación | Resultado principal | Valor documental |
|---|---|---|---|
| `R` | `energia + estresado` | `quality = 79.45`, variante final `suave` | Consolida una combinación que hasta hace poco estaba ausente |
| `S` | `foco + triste` | `quality = 84.30`, `stable_weighted` | Abre por fin esta combinación con una señal fuerte |
| `T` | `foco + triste` | `quality = 86.13`, `env=on` | Segunda evidencia consistente para la misma combinación |
| `U` | `foco + feliz` | `quality = 31.01`, `gate = False`, `factor = 0.0` | Primer caso claro de mood inmaduro que sigue en abstención |
| `V` | `energia + feliz` | `quality = 31.01`, `gate = False`, `factor = 0.0` | Confirma que el problema es el mood `feliz`, no la combinación concreta |
| `W` | `relajacion + estresado` | `quality = 82.03`, pesos altos | Refuerza uno de los bloques más maduros del sistema |
| `X` | `energia + cansado` | `quality = 79.85`, modo final estable | Consolida una combinación ya útil y repetible |
| `Y` | `relajacion + cansado` | `quality = 82.03`, pesos altos | Refuerza la rama más informativa del dataset |
| `Z` | `relajacion + triste` | `quality = 86.13`, modo final `suave` | Hace que esta combinación deje de ser testimonial |

### Tabla X. Cobertura incremental observada a partir de la nueva tanda

Esta tabla no reemplaza el recuento exacto en Firebase, pero sí resume la
aportación directa de las nuevas sesiones observadas.

| Combinación | Incremento observado | Lectura |
|---|---:|---|
| `energia + estresado` | `+1` | Ya no es una cobertura anecdótica |
| `foco + triste` | `+2` | Pasa de ausente a defendible |
| `foco + feliz` | `+1` | Deja de estar ausente, aunque sigue inmadura |
| `energia + feliz` | `+1` | Deja de estar ausente, aunque sigue inmadura |
| `relajacion + estresado` | `+1` | Bloque cada vez más robusto |
| `energia + cansado` | `+1` | Refuerzo incremental consistente |
| `relajacion + cansado` | `+1` | Sigue siendo una combinación muy útil para análisis |
| `relajacion + triste` | `+1` | Deja de ser un caso aislado |

### Tabla Y. Lectura del mood `feliz`

| Métrica | `foco + feliz` | `energia + feliz` | Lectura |
|---|---:|---:|---|
| `mood_gate_passed` | `False` | `False` | El gate sigue cerrado |
| `mood_quality_score` | `31.01` | `31.01` | Muy por debajo de los moods maduros |
| `mood_application_factor` | `0.0` | `0.0` | El aprendizaje individual no se aplica |
| `session_weight` | `0.0` | `0.0` | Sin base reciente útil |
| `stable_weight` | `0.053` | `0.074` | Solo una memoria muy débil y prudente |

### Tabla Z. Estado consolidado tras alcanzar `45` ejemplos

| Señal | Lectura |
|---|---|
| `total_examples` | `45` |
| Selección de sesión | Sigue en `ml_enabled = False` |
| Aprendizaje individual por mood | Muy fuerte en `triste`, `estresado`, `cansado` |
| Cobertura de `neutral` | Ya razonable por la tanda previa |
| Cobertura de `feliz` | Ya no ausente, pero aún inmadura |
| Modelo supervisado global | Todavía no puede considerarse activado |

## Lectura diagnóstica consolidada (`2026-05-15`)

- El sistema ya cubre de forma creíble muchos más recorridos de uso reales.
- El aprendizaje individual no solo se ve en los casos fuertes, sino también en
  la capacidad del sistema para abstenerse cuando un mood aún no ha madurado.
- Esta última propiedad mejora mucho la defensa académica del proyecto:
  - Harmony Hub no presenta un aprendizaje homogéneo artificial
  - distingue entre estados ya consolidados y estados todavía inmaduros
- La lectura correcta del estado actual es:
  - el aprendizaje individual ya es sólido y observable en varios moods
  - el modelo supervisado global sigue sin estar listo para gobernar la
    selección por sí mismo
  - pero el conjunto del sistema híbrido es cada vez más defendible y completo

## Ampliación complementaria (`2026-05-15`, cierre del día)

La última tanda del día no añade tantas combinaciones nuevas como la anterior,
pero sí aporta un matiz importante: el mood `feliz` empieza a moverse desde la
abstención total hacia una aplicación prudente del aprendizaje.

### Tabla AA. Casos realmente nuevos de esta ampliación

| Caso | Combinación | Resultado principal | Valor documental |
|---|---|---|---|
| `AA` | `energia + feliz` | `quality = 47.36`, `factor = 0.25`, `gate = False` | `feliz` deja de estar totalmente congelado |
| `AB` | `relajacion + feliz` | `quality = 56.39`, `factor = 0.55`, `gate = False` | primera señal clara de aprendizaje prudente en `feliz` |
| `AC` | `energia + triste` | `quality = 87.16`, `factor = 1.0`, `gate = True` | refuerzo adicional del mood más maduro |

### Tabla AB. Evolución fina del mood `feliz`

| Etapa | Combinación | `quality` | `factor` | `gate` | Lectura |
|---|---|---:|---:|---|---|
| Primera observación | `foco + feliz` | `31.01` | `0.0` | `False` | abstención total |
| Primera observación | `energia + feliz` | `31.01` | `0.0` | `False` | abstención total |
| Nueva observación | `energia + feliz` | `47.36` | `0.25` | `False` | entrada en aprendizaje prudente |
| Nueva observación | `relajacion + feliz` | `56.39` | `0.55` | `False` | fase intermedia claramente visible |

### Tabla AC. Estado consolidado tras alcanzar `48` ejemplos

| Señal | Lectura |
|---|---|
| `total_examples` | `48` |
| `feliz` | ya no ausente y en transición |
| `triste` | muy maduro (`quality` por encima de `87`) |
| `estresado` | bloque estable y defendible |
| `cansado` | bloque estable y defendible |
| Modelo global | sigue sin activarse como selector real |

## Lectura diagnóstica consolidada (`2026-05-15`, final del día)

- El proyecto ya muestra tres estados distintos del aprendizaje por mood:
  - maduro y plenamente aplicado
  - inmaduro pero en transición prudente
  - todavía insuficiente para pasar gate
- Eso fortalece bastante la explicación académica del sistema.
- El caso más interesante ahora mismo ya no es `triste`, sino `feliz`, porque
  permite documentar la transición entre no tener base y empezar a construirla.

## Actualización final del día (`2026-05-15`, `feliz` madura)

La última tanda corrige la lectura previa: `feliz` ya no debe documentarse
como mood todavía inmaduro. Con dos sesiones más, el sistema ya lo trata como
un mood con gate superado y aprendizaje plenamente aplicado.

### Tabla AD. Casos que cambian la lectura de `feliz`

| Caso | Combinación | Resultado principal | Valor documental |
|---|---|---|---|
| `AD` | `relajacion + feliz` | `quality = 63.86`, `factor = 1.0`, `gate = True` | `feliz` cruza el gate en una rama calmada |
| `AE` | `energia + feliz` | `quality = 69.20`, `factor = 1.0`, `gate = True` | `feliz` cruza el gate también en una rama energética |

### Tabla AE. Trayectoria completa observada para `feliz`

| Etapa | Combinación | `quality` | `factor` | `gate` | `profile_mode` | Lectura |
|---|---|---:|---:|---|---|---|
| Inicio | `foco + feliz` | `31.01` | `0.0` | `False` | `progressive_contextual` | abstención total |
| Inicio | `energia + feliz` | `31.01` | `0.0` | `False` | `progressive_contextual` | abstención total |
| Transición | `energia + feliz` | `47.36` | `0.25` | `False` | `progressive_contextual` | aprendizaje prudente |
| Transición | `relajacion + feliz` | `56.39` | `0.55` | `False` | `progressive_contextual` | aprendizaje prudente reforzado |
| Madurez | `relajacion + feliz` | `63.86` | `1.0` | `True` | `stable_weighted` | aprendizaje plenamente aplicado |
| Madurez | `energia + feliz` | `69.20` | `1.0` | `True` | `stable_weighted` | aprendizaje plenamente aplicado |

### Tabla AF. Estado consolidado tras alcanzar `50` ejemplos

| Señal | Lectura |
|---|---|
| `total_examples` | `50` |
| `feliz` | ya maduro a nivel de aprendizaje individual |
| `triste` | muy maduro |
| `estresado` | muy maduro |
| `cansado` | muy maduro |
| `neutral` | estable y cubierto |
| Modelo global | sigue sin activarse como selector real en los logs observados |

## Lectura diagnóstica consolidada (`2026-05-15`, cierre real)

- Harmony Hub ya permite documentar el ciclo completo de maduración de un mood.
- `feliz` es especialmente valioso porque ha recorrido, dentro del mismo
  dataset, estas fases:
  - ausencia
  - inmadurez
  - prudencia
  - madurez
- Eso mejora mucho la defensa del sistema híbrido:
  - no se limita a acumular sesiones
  - muestra transición real del aprendizaje
  - y mantiene el clasificador global desactivado mientras la señal global no
    sea todavía suficiente

## Sexta actualización observada (`2026-05-18`, tanda negativa útil)

La nueva tanda no aporta solo más sesiones, sino un cambio estructural en el
estado del clasificador supervisado. Por primera vez, el conjunto ya cumple la
puerta mínima de datos por volumen y por balance entre clases, de modo que el
bloqueo de `ml_enabled` deja de estar en la falta de negativos y pasa a
desplazarse hacia la cobertura restante por mood y hacia la calidad global del
modelo.

### Tabla AG. Estado real actualizado tras `55` ejemplos

| Métrica | Valor |
|---|---:|
| `total_examples` | `55` |
| Positivos | `47` |
| Negativos | `8` |
| `data_gate_passed` | `True` |
| `model_gate_passed` | `False` |
| `model_readiness_reason` | `insufficient_mood_coverage` |
| `quality_score` global | `55.85` |
| `balanced_accuracy_mean` | `0.4922` |
| `roc_auc_mean` | `0.50` |
| `moods_ready` | `3 / 5` |
| `readiness_reason` | `quality_below_threshold` |

### Tabla AH. Cobertura real por mood tras la tanda negativa

| Mood | Positivos | Negativos | Quality por mood | Gate | Lectura |
|---|---:|---:|---:|---|---|
| `cansado` | `10` | `2` | `65.68` | `PASS` | ya aporta contraste suficiente |
| `estresado` | `10` | `2` | `69.20` | `PASS` | pasa a ser un mood listo para el clasificador |
| `neutral` | `7` | `2` | `68.25` | `PASS` | deja de ser unilateral |
| `feliz` | `6` | `1` | `59.16` | `FAIL` | sigue muy cerca, pero aún no pasa |
| `triste` | `14` | `1` | `63.00` | `FAIL` | mucho volumen, pero todavía poco contraste |

### Tabla AI. Qué cambia respecto al estado anterior

| Señal | Antes | Ahora | Lectura |
|---|---:|---:|---|
| Ejemplos negativos | `3` | `8` | se abre el `data_gate` |
| `data_gate_passed` | `False` | `True` | ya no falta volumen ni mínimo por clase |
| `moods_ready` | `0 / 5` | `3 / 5` | mejora clara de cobertura específica |
| `quality_score` | `44.83` | `55.85` | mejora real, aunque aún insuficiente |
| `roc_auc_mean` | `0.1458` | `0.50` | mejora sustancial en capacidad discriminativa |
| Motivo de bloqueo | `insufficient_class_balance` | `insufficient_mood_coverage` | el cuello de botella cambia |

### Tabla AJ. Tanda negativa realmente observada

| Caso | Combinación | Resultado principal | Valor documental |
|---|---|---|---|
| `AF` | `energia + estresado` | modo final `alta`, `quality = 83.82` | añade contraste negativo en un mood ya fuerte |
| `AG` | `energia + neutral` | modo final `media`, `quality = 76.76` | refuerza el contraste que le faltaba a `neutral` |
| `AH` | `foco + estresado` | modo final `media`, `quality = 83.82` | amplía diversidad de modo en `estresado` |
| `AI` | `relajacion + neutral` | modo final `suave`, `quality = 76.76` | consolida `neutral` como mood ya listo |
| `AJ` | `energia + cansado` | modo final `media`, `quality = 83.82` | añade una segunda negativa en `cansado` |

### Lectura diagnóstica consolidada (`2026-05-18`)

- La tanda negativa ha sido útil de verdad.
- El clasificador global sigue sin activarse, pero ahora por una razón mejor:
  - ya no falta balance mínimo de clases
  - faltan calidad global y cobertura completa por mood
- Esto mejora mucho la defensa técnica del proyecto, porque permite afirmar que:
  - el sistema ya ha superado la fase de bloqueo por desbalance extremo
  - tres moods (`cansado`, `estresado`, `neutral`) ya pasan su gate específico
  - el siguiente foco lógico está en `triste` y `feliz`
- La lectura correcta del estado actual ya no es “el ML sigue apagado sin
  cambios”, sino:
  - el `data_gate` ya está abierto
  - el clasificador mejora de forma medible
  - pero todavía no alcanza la calidad global ni la cobertura total necesarias
    para dejar que `ml_enabled` gobierne la selección en runtime

## Séptima actualización observada (`2026-05-18`, cierre de cobertura por mood)

Las dos sesiones finales añaden un cambio decisivo: el clasificador deja de
estar bloqueado por cobertura específica y pasa a quedar frenado únicamente por
calidad global. Dicho de otro modo, el sistema ya dispone de ejemplos
suficientes en los cinco moods observados, pero la validación cruzada todavía no
ofrece rendimiento bastante alto como para autorizar el uso de `ml_enabled` en
runtime.

### Tabla AK. Estado real actualizado tras `57` ejemplos

| Métrica | Valor |
|---|---:|
| `total_examples` | `57` |
| Positivos | `47` |
| Negativos | `10` |
| `data_gate_passed` | `True` |
| `mood_quality_gate_passed` | `True` |
| `model_gate_passed` | `False` |
| `model_readiness_reason` | `quality_below_threshold` |
| `quality_score` global | `58.91` |
| `balanced_accuracy_mean` | `0.5033` |
| `roc_auc_mean` | `0.5711` |
| `moods_ready` | `5 / 5` |
| `readiness_reason` | `quality_below_threshold` |

### Tabla AL. Cobertura real por mood tras el cierre de `triste` y `feliz`

| Mood | Positivos | Negativos | Quality por mood | Gate | Lectura |
|---|---:|---:|---:|---|---|
| `cansado` | `10` | `2` | `65.68` | `PASS` | estable y ya listo |
| `estresado` | `10` | `2` | `69.20` | `PASS` | bien cubierto |
| `feliz` | `6` | `2` | `69.90` | `PASS` | deja de ser el mood más frágil |
| `neutral` | `7` | `2` | `68.25` | `PASS` | cobertura suficiente |
| `triste` | `14` | `2` | `67.59` | `PASS` | gana contraste suficiente |

### Tabla AM. Qué cambia respecto al estado de `55` ejemplos

| Señal | Antes | Ahora | Lectura |
|---|---:|---:|---|
| Ejemplos negativos | `8` | `10` | se consolida el contraste |
| `moods_ready` | `3 / 5` | `5 / 5` | cobertura completa por mood |
| `mood_quality_gate_passed` | `False` | `True` | desaparece el bloqueo por cobertura |
| `quality_score` | `55.85` | `58.91` | mejora, pero aún por debajo de `60` |
| `roc_auc_mean` | `0.50` | `0.5711` | más cerca del umbral |
| Motivo de bloqueo | `insufficient_mood_coverage` | `quality_below_threshold` | el problema pasa a ser puramente de calidad global |

### Tabla AN. Dos sesiones finales ejecutadas

| Caso | Combinación | Resultado principal | Valor documental |
|---|---|---|---|
| `AK` | `energia + triste` | modo final `media`, `quality = 88.04` | añade el segundo negativo de `triste` y cierra su gate específico |
| `AL` | `foco + feliz` | modo final `media`, `quality = 73.41` | añade el segundo negativo de `feliz` y completa la cobertura global |

### Lectura diagnóstica consolidada (`2026-05-18`, estado actual)

- El conjunto ya no está bloqueado por:
  - volumen total
  - balance mínimo entre clases
  - cobertura por mood
- Los cinco moods observados ya pasan su puerta específica.
- `ml_enabled` sigue en `False`, pero ahora por una razón mucho más concreta:
  - `quality_score = 58.91 < 60`
  - `balanced_accuracy_mean = 0.5033 < 0.58`
  - `roc_auc_mean = 0.5711 < 0.62`
- La lectura correcta del estado final ya no es “el ML no arranca”, sino:
  - el aprendizaje individual ya está consolidado
  - el clasificador supervisado global está muy cerca
  - pero sigue manteniéndose en abstención prudente por rendimiento global aún
    insuficiente
