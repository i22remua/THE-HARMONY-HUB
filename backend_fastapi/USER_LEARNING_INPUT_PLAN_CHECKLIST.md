# User Learning Input Plan Checklist

Versión ligera y operativa de la planificación de entrenamiento del perfil.
Está pensada para abrirla rápido mientras generas playlists y guardas logs.

## Objetivo de esta tanda

- subir `training_session_examples` de `29` a `45-50`
- añadir `6-8` sesiones honestamente no positivas o ambiguas
- cubrir combinaciones ausentes o casi ausentes
- reducir el peso excesivo de `energia + triste`

## Estado real del gate ML

Situación observada en `session_mode_model_metadata.json`:

- `total_examples = 57`
- `class_counts = 47` útiles / `10` no útiles
- `data_gate_passed = true`
- `mood_quality_gate_passed = true`
- `model_gate_passed = false`
- `model_readiness_reason = quality_below_threshold`
- `quality_score = 58.91`
- `readiness_reason = quality_below_threshold`
- `moods_ready = 5 / 5`

### Qué falta exactamente para desbloquear `ml_enabled`

| Condición | Umbral exigido | Estado actual | Falta mínima observable | Lectura práctica |
|---|---:|---:|---:|---|
| Volumen total | `>= 40` ejemplos | `57` | `0` | ya cumplido |
| Ejemplos positivos | `>= 8` | `47` | `0` | ya cumplido |
| Ejemplos negativos | `>= 8` | `10` | `0` | ya cumplido y reforzado |
| `quality_score` global | `>= 60` | `58.91` | `+1.09` | el bloqueo ya es casi exclusivamente de calidad global |
| `balanced_accuracy_mean` | `>= 0.58` | `0.5033` | `+0.0767` | mejora leve, aún insuficiente |
| `roc_auc_mean` | `>= 0.62` | `0.5711` | `+0.0489` | ya está cerca del umbral |
| `moods_ready` | al menos el mood actual con gate `true` | `5 / 5` | `0` | cobertura completa por mood ya conseguida |

### Traducción directa

- los `5` negativos ya han servido para abrir el `data_gate`
- las `2` sesiones finales han cerrado además la cobertura restante por mood
- eso **todavía no ha bastado** para activar `ml_enabled`
- ahora el cuello de botella ya no es:
  - ni el balance mínimo de clases
  - ni la cobertura específica por mood
- ahora el bloqueo es, sobre todo, la calidad global del modelo

### Dónde conviene meter los siguientes negativos

| Mood | Estado actual | Prioridad | Motivo |
|---|---|---|---|
| `triste` | `14` positivos / `2` negativos | media | ya pasa gate; ahora solo suma si mejora discriminación |
| `feliz` | `6` positivos / `2` negativos | media | ya pasa gate; el retorno marginal baja bastante |
| `estresado` | `10` positivos / `2` negativos | baja | ya pasa gate de mood |
| `neutral` | `7` positivos / `2` negativos | baja | ya pasa gate de mood |
| `cansado` | `10` positivos / `2` negativos | baja | ya pasa gate de mood |

### Objetivo operativo más realista

No pensar en “activar ya el ML” solo por llegar a `50+`, sino en esta secuencia:

1. volver a auditar `quality_score`, `balanced_accuracy` y `roc_auc`
2. buscar negativos que mejoren poder discriminativo, no solo conteo bruto
3. priorizar combinaciones frontera si se hace una tanda adicional
4. comprobar si el `quality_score` global supera `60`

### Dos sesiones finales más rentables ahora mismo

Si se quiere hacer una última tanda muy corta, estas son las dos sesiones con
mejor retorno marginal para intentar desbloquear el tramo final del modelo:

| Caso | Goal | Mood | Stress | Energy | Vocal | Intensity | Exploration | Popularity | Env | Desired outcome | Qué tensiona | Señal útil si sale mal |
|---|---|---|---:|---:|---|---|---|---|---|---|---|---|
| `F1` | `energia` | `triste` | `4` | `2` | `con_voz` | `alta` | `descubrir` | `mainstream` | `off` | `mas_despierto` | un mood muy maduro, pero con una variante más expuesta y menos contenida | si la playlist acelera demasiado o acompaña mal, el negativo mejora contraste en `triste` |
| `F2` | `foco` | `feliz` | `2` | `4` | `con_voz` | `media` | `descubrir` | `mainstream` | `off` | `mas_centrado` | el mood más frágil con una combinación proclive a distraer | si la sesión dispersa o acompaña peor de lo esperado, el negativo fortalece `feliz` |

#### Cómo leer esta mini tanda

- `F1` no busca volumen, sino romper la homogeneidad excesiva de `triste`
- `F2` no busca confirmar que `feliz` funciona, sino comprobar si el contraste
  sigue siendo insuficiente en un caso frontera de foco
- si ambas salen claramente positivas, también aportan información, pero el
  retorno para desbloquear `ml_enabled` será menor que si generan feedback
  ambiguo o no positivo

## Resultado real tras la tanda de cinco negativas

Impacto observado en metadatos:

- `total_examples`: `50 -> 55`
- negativos: `3 -> 8`
- `data_gate_passed`: `False -> True`
- `moods_ready`: `0 / 5 -> 3 / 5`
- moods que ya pasan gate específico:
  - `cansado`
  - `estresado`
  - `neutral`
- `quality_score`: `44.83 -> 55.85`
- `roc_auc_mean`: `0.1458 -> 0.50`

### Lo que todavía impide `ml_enabled`

- `model_gate_passed` sigue en `False`
- motivo principal actual:
  - `insufficient_mood_coverage`
- además sigue fallando la calidad global:
  - `quality_score < 60`
  - `balanced_accuracy_mean < 0.58`
  - `roc_auc_mean < 0.62`

### Lectura importante

La tanda ha sido útil de verdad.

- No se ha quedado en “más volumen”.
- Ha abierto el `data_gate`.
- Ha hecho que el problema cambie de naturaleza:
  - antes el bloqueo era `insufficient_class_balance`
  - ahora el bloqueo es cobertura/calidad restante

### Observación de trazas

En el primer caso (`energia + estresado`) aparecen varias materializaciones con
el mismo `recommendation_id` antes del feedback final. Eso no parece haber
creado ejemplos supervisados duplicados, porque el contador solo sube una vez:

- `50 -> 51`

La lectura más probable es:

- hubo varios intentos de generación de playlist sobre la misma recomendación
- pero solo un cierre efectivo con feedback etiquetado

## Resultado adicional tras las dos sesiones finales

Impacto observado en metadatos:

- `total_examples`: `55 -> 57`
- negativos: `8 -> 10`
- `mood_quality_gate_passed`: `False -> True`
- `moods_ready`: `3 / 5 -> 5 / 5`
- `quality_score`: `55.85 -> 58.91`
- `balanced_accuracy_mean`: `0.4922 -> 0.5033`
- `roc_auc_mean`: `0.50 -> 0.5711`

### Lo que ahora sí queda claro

- `triste` ya pasa gate específico:
  - `16` ejemplos
  - `14` positivos
  - `2` negativos
  - `quality_score = 67.59`
- `feliz` ya pasa gate específico:
  - `8` ejemplos
  - `6` positivos
  - `2` negativos
  - `quality_score = 69.90`
- con eso, los `5` moods del sistema ya tienen `quality_gate_passed = true`

### Lo único que sigue impidiendo `ml_enabled`

- `model_gate_passed` sigue en `False`
- `model_readiness_reason` ya no es `insufficient_mood_coverage`
- ahora el motivo directo pasa a ser:
  - `quality_below_threshold`

### Traducción práctica final

Con `57` ejemplos, `10` negativos y cobertura completa por mood, el sistema ya
ha resuelto casi todos los bloqueos estructurales del clasificador supervisado.
Lo que falta para ver `ml_enabled = True` ya no es cobertura, sino rendimiento
global suficiente en validación cruzada.

## Siguiente tanda de máxima ganancia estadística

Tras ejecutar `G1` y `G2`, esta es la tanda más sensata para seguir empujando
el gate global. No busca solo añadir ejemplos, sino mejorar la separación entre
casos claramente útiles y claramente no útiles.

| Caso | Goal | Mood | Stress | Energy | Vocal | Intensity | Exploration | Popularity | Env | Desired outcome | Qué pone a competir | Qué conviene marcar si no encaja |
|---|---|---|---:|---:|---|---|---|---|---|---|---|---|
| `G3` | `relajacion` | `neutral` | `3` | `3` | `con_voz` | `alta` | `descubrir` | `mainstream` | `on` | `mas_calmado` | relajación frente a un perfil más activo e inestable | `helpful = false` si no calma o rompe coherencia |
| `H1` | `energia` | `neutral` | `3` | `2` | `instrumental` | `suave` | `descubrir` | `alternativa` | `off` | `mas_despierto` | despertar con una configuración aún más contenida de lo razonable | `helpful = false` si no activa o se queda plana |
| `H2` | `foco` | `estresado` | `5` | `3` | `con_voz` | `alta` | `descubrir` | `mainstream` | `on` | `mas_centrado` | concentración bajo estrés con rasgos que tienden a sobrecargar | `helpful = false` si distrae o rompe foco |

### Por qué estas tres y no otras

- `G3` busca un caso frontera entre relajación y energía residual, útil para
  subir `roc_auc` si el feedback es nítido
- `H1` fuerza una separación muy útil entre `energia` real y acompañamiento
  simplemente agradable
- `H2` reabre una frontera exigente en `foco + estresado`, donde la combinación
  de estrés alto, voz e intensidad puede ayudar o perjudicar con mucha claridad

### Cómo sacarles el máximo valor

- si salen claramente bien, márcalos como positivos sin ambigüedad
- si salen regular, no los salves como “más o menos útiles”
- prioriza feedback binario claro y una nota corta sobre:
  - distracción
  - falta de activación
  - exceso de intensidad
  - poca coherencia con el objetivo

### Orden recomendado

1. `G3`
2. `H1`
3. `H2`

## Microbatería para generar negativos útiles

Estas sesiones no buscan “que salga bien”, sino provocar casos frontera o
desajustes razonables para que el clasificador vea contraste real entre
contextos útiles y no útiles.

| Caso | Goal | Mood | Stress | Energy | Vocal | Intensity | Exploration | Popularity | Env | Desired outcome | Qué forzar | Negativo esperado |
|---|---|---|---:|---:|---|---|---|---|---|---|---|---|
| N1 | energia | estresado | 5 | 2 | con_voz | alta | descubrir | mainstream | off | mas_despierto | subir intensidad en un mood que suele responder mejor a energía más contenida | playlist demasiado invasiva o poco reguladora |
| N2 | foco | estresado | 5 | 3 | con_voz | alta | descubrir | mixta | on | mas_centrado | combinar estrés alto con voz y alta intensidad para dificultar la concentración | sensación de distracción o sobreestimulación |
| N3 | energia | neutral | 3 | 2 | instrumental | suave | familiar | alternativa | off | mas_despierto | pedir despertar con una configuración deliberadamente demasiado suave | sesión insuficiente para activar energía |
| N4 | relajacion | neutral | 3 | 3 | con_voz | alta | descubrir | mainstream | on | mas_calmado | mezclar relajación con energía e intensidad poco compatibles | playlist poco calmante o demasiado activa |
| N5 | energia | cansado | 4 | 1 | con_voz | alta | descubrir | alternativa | on | mas_despierto | exagerar la activación en un estado cansado con muy baja energía de partida | salto demasiado brusco o falta de encaje progresivo |

### Cómo marcar estos casos si salen “regular”

- si no te ayudan claramente, marca `helpful = false`
- si ayudan a medias, usa una nota explícita en `Effect` o `Nota`
- si el problema fue:
  - exceso de intensidad
  - falta de energía
  - distracción
  - poca coherencia con el objetivo
  deja ese matiz escrito, porque añade valor interpretativo aunque el label sea binario

### Prioridad recomendada

1. `N1`
2. `N3`
3. `N2`
4. `N4`
5. `N5`

### Señal de éxito de esta microbatería

El objetivo no es que estas cinco sesiones salgan mal por completo, sino que al
menos `3` de ellas aporten contraste honesto, por ejemplo:

- `helpful = false`
- o feedback ambiguo pero razonado
- o una combinación que obligue a reconocer que el modo elegido no encajó tan bien como en los casos positivos maduros

## Checklist operativa (`16` sesiones)

| Caso | Estado | Goal | Mood | Stress | Energy | Vocal | Intensity | Exploration | Popularity | Env | Desired outcome | Recommended mode | Profile mode | Mood gate | Mood quality | App factor | Session weight | Stable weight | Helpful | Effect | Post-session state | Playlist id | Nota corta |
|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| A1 | ejecutada | energia | triste | 4 | 2 | indistinto | alta | descubrir | alternativa | off | mas_despierto | energia_triste_alta | stable_weighted | True | 81.03 | 1.0 | 0.197 | 0.209 |  |  |  | 1gFKaxaIwUExlTC50eKDHm | recomendacion previa en `media`, generacion final en `alta` |
| A2 | ejecutada | energia | triste | 4 | 2 | instrumental | media | equilibrado | alternativa | on | mas_acompanado | energia_triste_media | stable_weighted | True | 82.82 | 1.0 | 0.273 | 0.290 |  |  |  | 4O6mW34AUsy5KixBMsM45O | solo 3 tracks materializados; `failed=5` |
| A3 | ejecutada (variante) | relajacion | estresado | 5 | 2 | con_voz | media | equilibrado | mainstream | on | mas_calmado | relajacion_estresado_media | stable_weighted | True | 71.92 | 1.0 | 0.275 | 0.290 |  |  |  | 5Ubr1QQKNzBrYsqwdHrp0o | ejecutada con `env=off`; recomendacion previa en `suave` |
| A4 | ejecutada | foco | cansado | 3 | 2 | con_voz | media | descubrir | alternativa | on | mas_centrado | foco_cansado_media | stable_weighted | True | 76.76 | 1.0 | 0.198 | 0.210 |  |  |  | 73yCqpjglLmY7Wq6A2LQrH | recomendacion previa en `suave`, playlist final en `media` |
| A5 | pendiente | relajacion | neutral | 3 | 2 | con_voz | media | descubrir | alternativa | off | mas_calmado |  |  |  |  |  |  |  |  |  |  |  |  |
| A6 | ejecutada | energia | neutral | 3 | 2 | instrumental | alta | descubrir | alternativa | on | mas_despierto | energia_neutral_alta | stable_weighted | True | 73.41 | 1.0 | 0.200 | 0.211 |  |  |  | 5FxF3QGc3xF1vQf7hSdkTC | recomendacion previa en `media`, playlist final en `alta` |
| B1 | ejecutada | energia | estresado | 5 | 2 | instrumental | media | familiar | mixta | on | mas_despierto | energia_estresado_media | stable_weighted | True | 75.27 | 1.0 | 0.310 | 0.326 |  |  |  | 2gSEc0f4CrLB0qyCYhA3SV | primera cobertura positiva real de `energia + estresado` |
| B2 | ejecutada | energia | estresado | 4 | 2 | con_voz | suave | equilibrado | mainstream | off | mas_acompanado | energia_estresado_suave | stable_weighted | True | 79.45 | 1.0 | 0.278 | 0.291 |  |  |  | 1AxAxVKvT2x8NYsNAs23Yq | consolida `energia + estresado` también en variante `suave` |
| B3 | ejecutada | foco | triste | 4 | 2 | instrumental | suave | familiar | mixta | off | mas_centrado | foco_triste_suave | stable_weighted | True | 84.30 | 1.0 | 0.312 | 0.327 |  |  |  | 7eEmk0vjx119GVvXlUxiDe | abre cobertura real de `foco + triste` |
| B4 | ejecutada | foco | triste | 4 | 2 | indistinto | media | equilibrado | alternativa | on | mas_centrado | foco_triste_media | stable_weighted | True | 86.13 | 1.0 | 0.279 | 0.292 |  |  |  | 2BKeQf251DiZHqPoivV715 | segunda sesión de `foco + triste`, con entorno activo |
| B5 | ejecutada | foco | feliz | 2 | 4 | instrumental | media | descubrir | alternativa | off | mas_centrado | foco_feliz_media | progressive_contextual | False | 31.01 | 0.0 | 0.0 | 0.053 |  |  |  | 7gYwOvUKdp6GB0mAEnPNih | mood `feliz` todavía inmaduro; gate cerrado |
| B6 | ejecutada | energia | feliz | 2 | 4 | con_voz | media | equilibrado | mainstream | on | mas_despierto | energia_feliz_media | progressive_contextual | False | 31.01 | 0.0 | 0.0 | 0.074 |  |  |  | 0smPbsSkadKWknUQnZhP05 | segunda prueba de `feliz`; sigue sin madurez |
| C1 | ejecutada | relajacion | estresado | 5 | 2 | instrumental | suave | familiar | mainstream | off | mas_calmado | relajacion_estresado_suave | stable_weighted | True | 82.03 | 1.0 | 0.297 | 0.335 |  |  |  | 3yOcKBaYmRmOecZ3vljbVB | refuerza mucho uno de los bloques más sólidos |
| C2 | ejecutada (variante) | energia | cansado | 4 | 1 | indistinto | media | equilibrado | mixta | on | mas_despierto | energia_cansado_media | stable_weighted | True | 79.85 | 1.0 | 0.265 | 0.298 |  |  |  | 74Kf27paGK2dCG2Kl2KO2s | ejecutada con `env=off`; mantiene consistencia |
| C3 | ejecutada | relajacion | cansado | 3 | 2 | instrumental | suave | equilibrado | mixta | off | mas_calmado | relajacion_cansado_suave | stable_weighted | True | 82.03 | 1.0 | 0.266 | 0.298 |  |  |  | 5dRP9MDgqesBVcPasuKh6T | refuerza la rama más informativa del dataset |
| C4 | ejecutada | relajacion | triste | 4 | 2 | con_voz | suave | descubrir | alternativa | off | mas_acompanado | relajacion_triste_suave | stable_weighted | True | 86.13 | 1.0 | 0.193 | 0.216 |  |  |  | 2a6lfcHkdxm21EqhWQcvBR | deja de ser una combinación testimonial |

## Sesiones complementarias fuera de checklist

Estas sesiones no eran necesarias para cerrar la matriz mínima, pero añaden
valor diagnóstico porque afinan la lectura del mood `feliz` y refuerzan el caso
maduro de `triste`.

| Caso | Estado | Goal | Mood | Stress | Energy | Vocal | Intensity | Exploration | Popularity | Env | Desired outcome | Recommended mode | Profile mode | Mood gate | Mood quality | App factor | Session weight | Stable weight | Playlist id | Nota corta |
|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---|---|
| D1 | ejecutada | energia | feliz | 2 | 4 | indistinto | alta | equilibrado | mixta | off | mas_despierto | energia_feliz_alta | progressive_contextual | False | 47.36 | 0.25 | 0.067 | 0.074 | 5gv2p3tWj7puVILeMJSs8q | `feliz` sigue inmaduro, pero deja de estar totalmente bloqueado |
| D2 | ejecutada | relajacion | feliz | 2 | 4 | instrumental | suave | equilibrado | alternativa | off | mas_calmado | relajacion_feliz_suave | progressive_contextual | False | 56.39 | 0.55 | 0.147 | 0.164 | 1ZbS2BsUCnteAIaoynWLQX | mejor señal para `feliz`, todavía sin gate completo |
| D3 | ejecutada | energia | triste | 4 | 2 | con_voz | alta | descubrir | alternativa | off | mas_despierto | energia_triste_alta | stable_weighted | True | 87.16 | 1.0 | 0.195 | 0.216 | 4Z7Q6tf7dsWMVU0axkYICD | refuerza aún más el mood más maduro del sistema |
| D4 | ejecutada | relajacion | feliz | 2 | 4 | instrumental | suave | familiar | mixta | off | mas_calmado | relajacion_feliz_suave | stable_weighted | True | 63.86 | 1.0 | 0.302 | 0.335 | 5WcLNzZiCgY6hgHQjCRZQV | `feliz` cruza gate en variante de relajación |
| D5 | ejecutada | energia | feliz | 2 | 4 | con_voz | alta | familiar | mainstream | off | mas_despierto | energia_feliz_alta | stable_weighted | True | 69.20 | 1.0 | 0.303 | 0.335 | 3dibTH630A6yXeE36FHKEt | `feliz` cruza gate también en variante energética |
| D6 | ejecutada | energia | triste | 4 | 2 | con_voz | media | descubrir | mainstream | off | mas_despierto | energia_triste_media | stable_weighted | True | 88.04 | 1.0 | 0.177 | 0.222 | 4eSwREyyPMx5ZbNn3aRcMM | añade el segundo negativo útil en `triste` y cierra su gate específico |
| D7 | ejecutada | foco | feliz | 2 | 4 | con_voz | media | descubrir | mainstream | off | mas_centrado | foco_feliz_media | stable_weighted | True | 73.41 | 1.0 | 0.174 | 0.223 | 5Bj0FDYXL6Q6lxCvOrRTsg | añade el segundo negativo útil en `feliz` y completa la cobertura por mood |

## Qué copiar del log

- `[SESSION] selected_mode`
- `[SESSION] selected_mode_scores`
- `[LEARNING] mood_gate_passed`
- `[LEARNING] mood_quality_score`
- `[LEARNING] mood_application_factor`
- `mode=... | subtype=... | curve=... | profile_mode=...`
- `session_weight`
- `stable_weight`
- `[CATALOG] ... top_track=... | top_score=...`
- `[PLAYLIST] created id=...`
- `[ML MAINTENANCE] start`
- `[ML MAINTENANCE] done`

## Plantilla corta

```text
Caso:
Recommendation id:
Goal / Mood:
Inputs:
Recommended mode:
Profile mode:
Mood gate:
Mood quality:
Application factor:
Session weight:
Stable weight:
Top track:
Playlist id:
Helpful:
Effect:
Post-session state:
Nota:
```

## Orden recomendado

1. `A1-A6`
2. `B1-B4`
3. `C1-C4`
4. `B5-B6`

## Regla rápida

- si una combinación ausente sale bien, ganas cobertura
- si una sesión frontera sale regular o mal, ganas balance
- si ves que se repite demasiado el mismo `recommended_mode`, cambia al
  siguiente caso del bloque
