# User Learning Input Plan

Tabla de trabajo para entrenar mejor el perfil del usuario y evidenciar la
evolución del aprendizaje en el sistema.

## Sesiones propuestas

| Sesión | Goal | Mood | Stress | Energy | Vocal | Intensity | Exploration | Popularity | Duration | Desired outcome | Env | Helpful | Effect | Post-session state | Observaciones |
|---|---|---:|---:|---:|---|---|---|---|---:|---|---|---|---|---|---|
| 1 | energia | triste | 4 | 2 | con_voz | suave | familiar | mainstream | 30 | mas_acompanado | false |  |  |  |  |
| 2 | energia | triste | 4 | 2 | con_voz | suave | familiar | mainstream | 30 | mas_despierto | false |  |  |  |  |
| 3 | energia | triste | 5 | 1 | con_voz | media | familiar | mixta | 30 | mas_despierto | true |  |  |  |  |
| 4 | energia | triste | 4 | 2 | indistinto | media | equilibrado | mixta | 20 | mas_acompanado | false |  |  |  |  |
| 5 | relajacion | estresado | 5 | 2 | instrumental | suave | familiar | mainstream | 30 | mas_calmado | true |  |  |  |  |
| 6 | relajacion | estresado | 5 | 2 | indistinto | suave | equilibrado | mixta | 30 | mas_calmado | false |  |  |  |  |
| 7 | relajacion | estresado | 4 | 1 | con_voz | suave | descubrir | alternativa | 20 | mas_acompanado | false |  |  |  |  |
| 8 | foco | cansado | 3 | 2 | instrumental | suave | familiar | mixta | 30 | mas_centrado | true |  |  |  |  |
| 9 | foco | cansado | 3 | 2 | instrumental | media | equilibrado | mixta | 40 | mas_centrado | false |  |  |  |  |
| 10 | energia | cansado | 4 | 1 | indistinto | suave | familiar | mixta | 30 | mas_despierto | false |  |  |  |  |
| 11 | foco | neutral | 3 | 3 | instrumental | media | familiar | mixta | 25 | mas_centrado | true |  |  |  |  |
| 12 | energia | neutral | 2 | 3 | con_voz | media | equilibrado | mixta | 20 | mas_despierto | true |  |  |  |  |
| 13 | relajacion | neutral | 3 | 2 | instrumental | suave | equilibrado | mixta | 30 | mas_calmado | true |  |  |  |  |

## Cómo usarla

- Rellena `Helpful` con `true` o `false`.
- Rellena `Effect` con `mejoro`, `igual` o `empeoro`.
- Rellena `Post-session state` con el estado percibido tras la sesión.
- Usa `Observaciones` para anotar si la playlist fue demasiado intensa, plana,
  repetitiva, conocida, acertada, etc.

## Orden recomendado

1. Sesiones `1-4`
2. Sesiones `5-7`
3. Sesiones `8-10`
4. Sesiones `11-13`

## Evidencia recomendable por sesión

- captura de la recomendación
- captura de la playlist
- log con:
  - `mood_learning_quality_score`
  - `mood_learning_application_factor`
  - `session_taste_weight`
  - `stable_taste_weight`
  - `taste_profile_mode`

## Checkpoints prácticos

Cuando completes un bloque razonable de sesiones, conviene revisar:

- `quality_score`
- `mood_coverage`
- `mood_learning_quality_score`
- `mood_learning_application_factor`
- si suben `session_taste_weight` y `stable_taste_weight`

Interpretación rápida:

- si el sistema todavía no supera la gate global, sigue recogiendo ejemplos
- si supera la gate global pero no la del `mood`, sigue reforzando ese estado emocional
- si supera ambas, ya tienes una evidencia defendible de aprendizaje aplicado

## Plantilla mínima de registro

```text
Sesion:
Inputs:
Recommended mode:
Selection source:
Mode probability:
Session taste weight:
Stable taste weight:
Playlist id:
Top tracks:
Helpful:
Effect:
Post-session state:
Nota:
```

## Objetivo

La tabla está pensada para:

- reforzar `triste`, `estresado` y `cansado`
- consolidar sesiones con `exploration_preference = familiar`
- y hacer visible en la documentación cómo el sistema incrementa el peso del
  aprendizaje a medida que madura cada `mood`

## Evidencia real recogida

### Bloque `triste + energia`

Los siguientes registros corresponden al primer bloque del plan y muestran que
el mood `triste` ya ha madurado con evidencia suficiente como para activar el
aprendizaje al `100%`.

| Caso | Correspondencia con plan | Inputs clave | Recommended mode | Taste profile mode | Session weight | Stable weight | Mood gate | Mood quality score | Application factor | Entorno | Playlist creada |
|---|---|---|---|---|---:|---:|---|---:|---:|---|---|
| A | Sesión `1` | `energia`, `triste`, `4/2`, `con_voz`, `suave`, `familiar`, `mainstream`, `mas_acompanado` | `energia_triste_suave` | `stable_weighted` | `0.288` | `0.318` | `True` | `68.61` | `1.0` | `No` | `Sí` |
| B | Sesión `2` | `energia`, `triste`, `4/2`, `con_voz`, `suave`, `familiar`, `mainstream`, `mas_despierto` | `energia_triste_suave` | `stable_weighted` | `0.290` | `0.319` | `True` | `72.81` | `1.0` | `No` | `Sí` |
| C | Sesión `3` | `energia`, `triste`, `5/1`, `con_voz`, `media`, `familiar`, `mixta`, `mas_despierto` | `energia_triste_media` | `stable_weighted` | `0.292` | `0.320` | `True` | `76.16` | `1.0` | `Sí`, `Silencio estable` | `Sí` |
| D | Sesión `4` | `energia`, `triste`, `4/2`, `indistinto`, `media`, `equilibrado`, `mixta`, `mas_acompanado` | `energia_triste_media` | `stable_weighted` | `0.261` | `0.284` | `True` | `78.85` | `1.0` | `Sí`, `Silencio estable` | `Sí` |

### Lectura técnica del bloque

- El `mood_learning_gate_passed` ya aparece en `True` en los cuatro casos.
- El `mood_learning_application_factor` se mantiene en `1.0`, por lo que el
  aprendizaje ya no se está aplicando de forma prudente o parcial, sino
  completa.
- El `mood_learning_quality_score` sube de `68.61` a `78.85`, lo que evidencia
  maduración del mood `triste` a medida que se acumulan sesiones útiles.
- Los pesos aprendidos se mantienen altos y estables:
  - `session_taste_weight`: `0.288 -> 0.290 -> 0.292 -> 0.261`
  - `stable_taste_weight`: `0.318 -> 0.319 -> 0.320 -> 0.284`
- La ligera bajada del cuarto caso es coherente con el cambio de
  `exploration_preference` de `familiar` a `equilibrado`, no con una pérdida de
  madurez del modelo.
- En los cuatro casos la playlist se llega a materializar correctamente en
  Spotify y el mantenimiento automático del modelo detecta nuevos ejemplos
  etiquetados:
  - `18 -> 19 -> 20 -> 21`
  - `train | reason=new_labeled_examples_detected`

### Conclusión del bloque

- El bloque `1-4` puede darse por completado.
- El mood `triste` ya dispone de una base madura y defendible.
- La siguiente fase recomendada del plan es pasar a `5-7`
  (`estresado + relajacion`).

### Nota de trazabilidad

En los logs aportados no aparece el contenido exacto del feedback textual
(`helpful`, `effect`, `post_session_state`), así que esta sección documenta la
parte observable del aprendizaje a partir de:

- inputs de sesión
- recomendación generada
- pesos aplicados
- quality gate del mood
- materialización final
- y reentrenado automático posterior

## Nueva tanda ambiciosa observada (`2026-05-14`)

La siguiente tanda amplía la cobertura del plan con combinaciones menos
dominantes y sirve mejor para documentar una fase más ambiciosa del perfil.

| Caso | Relación con checklist | Inputs clave | Recomendación previa | Modo en generación | Profile mode | Session weight | Stable weight | Mood gate | Mood quality | Factor | Playlist | Observación |
|---|---|---|---|---|---|---:|---:|---|---:|---:|---|---|
| `L` | `A1` | `energia`, `triste`, `4/2`, `indistinto`, `alta`, `descubrir`, `alternativa`, `mas_despierto`, `env=off` | `energia_triste_media` | `energia_triste_alta` | `stable_weighted` | `0.197` | `0.209` | `True` | `81.03` | `1.0` | `1gFKaxaIwUExlTC50eKDHm` | Paso claro hacia una variante más intensa del mismo mood |
| `M` | `A2` | `energia`, `triste`, `4/2`, `instrumental`, `media`, `equilibrado`, `alternativa`, `mas_acompanado`, `env=on` | `energia_triste_media` | `energia_triste_media` | `stable_weighted` | `0.273` | `0.290` | `True` | `82.82` | `1.0` | `4O6mW34AUsy5KixBMsM45O` | Mood muy maduro; solo se materializan `3` tracks |
| `N` | `A4` | `foco`, `cansado`, `3/2`, `con_voz`, `media`, `descubrir`, `alternativa`, `mas_centrado`, `env=on` | `foco_cansado_suave` | `foco_cansado_media` | `stable_weighted` | `0.198` | `0.210` | `True` | `76.76` | `1.0` | `73yCqpjglLmY7Wq6A2LQrH` | La generación final empuja hacia una variante más activa |
| `O` | `A3` variante | `relajacion`, `estresado`, `5/2`, `con_voz`, `media`, `equilibrado`, `mainstream`, `mas_calmado`, `env=off` | `relajacion_estresado_suave` | `relajacion_estresado_media` | `stable_weighted` | `0.275` | `0.290` | `True` | `71.92` | `1.0` | `5Ubr1QQKNzBrYsqwdHrp0o` | Variante útil aunque no replica exactamente el caso con entorno |
| `P` | `A6` | `energia`, `neutral`, `3/2`, `instrumental`, `alta`, `descubrir`, `alternativa`, `mas_despierto`, `env=on` | `energia_neutral_media` | `energia_neutral_alta` | `stable_weighted` | `0.200` | `0.211` | `True` | `73.41` | `1.0` | `5FxF3QGc3xF1vQf7hSdkTC` | Refuerza una combinación antes débil (`energia + neutral`) |
| `Q` | `B1` | `energia`, `estresado`, `5/2`, `instrumental`, `media`, `familiar`, `mixta`, `mas_despierto`, `env=on` | `energia_estresado_media` | `energia_estresado_media` | `stable_weighted` | `0.310` | `0.326` | `True` | `75.27` | `1.0` | `2gSEc0f4CrLB0qyCYhA3SV` | Primer caso fuerte de `energia + estresado` |

### Lectura técnica de la nueva tanda

- El conjunto refuerza la idea de que el aprendizaje por `mood` ya está en una
  fase madura para `triste`, `cansado`, `estresado` y `neutral`.
- En todos los casos observados:
  - `mood_learning_gate_passed = True`
  - `mood_learning_application_factor = 1.0`
- La `mood_quality_score` se mantiene alta en todo el bloque:
  - `81.03` y `82.82` en `triste`
  - `76.76` en `cansado`
  - `71.92` en `estresado`
  - `73.41` en `neutral`
- El mantenimiento automático sigue detectando ejemplos nuevos tras cada
  feedback:
  - `30 -> 31 -> 32 -> 33 -> 35 -> 36`
- También se observa un patrón interesante: la recomendación previa y el modo
  usado al generar la playlist no siempre coinciden exactamente. En varios
  casos la generación final desplaza la intensidad hacia una variante `media` o
  `alta`, lo cual merece documentarse como parte normal del pipeline y no como
  inconsistencia.

### Qué demuestra esta tanda y qué no

- Sí demuestra:
  - mejor cobertura de combinaciones antes débiles
  - madurez funcional del aprendizaje individual
  - capacidad del sistema para sostener playlists reales sin rate limit
- No demuestra todavía:
  - equilibrio suficiente del dataset supervisado global
  - activación del clasificador global

Aunque el usuario visible ya muestra una afinidad muy consolidada, esta tanda
sigue añadiendo sobre todo ejemplos positivos, no contraejemplos.

## Observación técnica sobre el entorno

En esta fase apareció repetidamente `Silencio estable`, lo que puede inducir a
pensar que el clasificador ambiental está fijado a ese contexto. No es así.

La lógica actual del cliente:

- suaviza la serie de decibelios
- recorta extremos
- ignora el calentamiento inicial del micro
- y toma decisiones principalmente a partir del nivel medio y la estabilidad

Por eso, si el ruido es breve, lejano o poco persistente, la lectura puede
seguir cayendo en `Silencio estable` aunque subjetivamente el usuario perciba
algo de ruido.

Para documentación conviene explicarlo así:

- el entorno sí influye
- pero el clasificador es deliberadamente conservador
- y prioriza señales sostenidas frente a picos aislados

## Tercera tanda ambiciosa observada (`2026-05-15`)

Esta nueva tanda cierra prácticamente todos los casos pendientes de la checklist
operativa y aporta valor en tres frentes:

- consolida combinaciones ya fuertes (`relajacion + estresado`,
  `energia + cansado`)
- cubre huecos que aún faltaban (`foco + triste`, `foco + feliz`,
  `energia + feliz`, `relajacion + triste`)
- y confirma que el mood `feliz` sigue claramente inmaduro frente al resto

| Caso | Relación con checklist | Inputs clave | Recomendación previa | Modo en generación | Profile mode | Session weight | Stable weight | Mood gate | Mood quality | Factor | Playlist | Observación |
|---|---|---|---|---|---|---:|---:|---|---:|---:|---|---|
| `R` | `B2` | `energia`, `estresado`, `4/2`, `con_voz`, `suave`, `equilibrado`, `mainstream`, `mas_acompanado`, `env=off` | `energia_estresado_suave` | `energia_estresado_suave` | `stable_weighted` | `0.278` | `0.291` | `True` | `79.45` | `1.0` | `1AxAxVKvT2x8NYsNAs23Yq` | Refuerza `energia + estresado` también en variante suave |
| `S` | `B3` | `foco`, `triste`, `4/2`, `instrumental`, `suave`, `familiar`, `mixta`, `mas_centrado`, `env=off` | `foco_triste_suave` | `foco_triste_suave` | `stable_weighted` | `0.312` | `0.327` | `True` | `84.30` | `1.0` | `7eEmk0vjx119GVvXlUxiDe` | Primera cobertura fuerte de `foco + triste` |
| `T` | `B4` | `foco`, `triste`, `4/2`, `indistinto`, `media`, `equilibrado`, `alternativa`, `mas_centrado`, `env=on` | `foco_triste_media` | `foco_triste_media` | `stable_weighted` | `0.279` | `0.292` | `True` | `86.13` | `1.0` | `2BKeQf251DiZHqPoivV715` | Segunda cobertura de `foco + triste`, además con entorno |
| `U` | `B5` | `foco`, `feliz`, `2/4`, `instrumental`, `media`, `descubrir`, `alternativa`, `mas_centrado`, `env=off` | `foco_feliz_suave` | `foco_feliz_media` | `progressive_contextual` | `0.000` | `0.053` | `False` | `31.01` | `0.0` | `7gYwOvUKdp6GB0mAEnPNih` | El mood `feliz` sigue sin base suficiente |
| `V` | `B6` | `energia`, `feliz`, `2/4`, `con_voz`, `media`, `equilibrado`, `mainstream`, `mas_despierto`, `env=on` | `energia_feliz_alta` | `energia_feliz_media` | `progressive_contextual` | `0.000` | `0.074` | `False` | `31.01` | `0.0` | `0smPbsSkadKWknUQnZhP05` | Segunda prueba de `feliz`; sigue en abstención |
| `W` | `C1` | `relajacion`, `estresado`, `5/2`, `instrumental`, `suave`, `familiar`, `mainstream`, `mas_calmado`, `env=off` | `relajacion_estresado_suave` | `relajacion_estresado_suave` | `stable_weighted` | `0.297` | `0.335` | `True` | `82.03` | `1.0` | `3yOcKBaYmRmOecZ3vljbVB` | Refuerza uno de los bloques más maduros del sistema |
| `X` | `C2` | `energia`, `cansado`, `4/1`, `indistinto`, `media`, `equilibrado`, `mixta`, `mas_despierto`, `env=off` | `energia_cansado_media` | `energia_cansado_media` | `stable_weighted` | `0.265` | `0.298` | `True` | `79.85` | `1.0` | `74Kf27paGK2dCG2Kl2KO2s` | Mantiene estable una combinación ya útil |
| `Y` | `C3` | `relajacion`, `cansado`, `3/2`, `instrumental`, `suave`, `equilibrado`, `mixta`, `mas_calmado`, `env=off` | `relajacion_cansado_suave` | `relajacion_cansado_suave` | `stable_weighted` | `0.266` | `0.298` | `True` | `82.03` | `1.0` | `5dRP9MDgqesBVcPasuKh6T` | Sigue reforzando la rama más informativa del dataset |
| `Z` | `C4` | `relajacion`, `triste`, `4/2`, `con_voz`, `suave`, `descubrir`, `alternativa`, `mas_acompanado`, `env=off` | `relajacion_triste_suave` | `relajacion_triste_suave` | `stable_weighted` | `0.193` | `0.216` | `True` | `86.13` | `1.0` | `2a6lfcHkdxm21EqhWQcvBR` | `relajacion + triste` deja de ser testimonial |

### Lectura técnica de la tercera tanda

- El sistema alcanza `45` ejemplos etiquetados:
  - `36 -> 45`
- En todos los casos salvo los de `feliz`:
  - `mood_learning_gate_passed = True`
  - `mood_learning_application_factor = 1.0`
- Las `mood_quality_score` siguen creciendo o se mantienen muy altas:
  - `79.45` en `energia + estresado`
  - `84.30` y `86.13` en `foco + triste`
  - `82.03` en `relajacion + estresado`
  - `79.85` en `energia + cansado`
  - `82.03` en `relajacion + cansado`
  - `86.13` en `relajacion + triste`
- El mood `feliz` queda claramente identificado como inmaduro:
  - `mood_gate = False`
  - `mood_quality_score = 31.01`
  - `application_factor = 0.0`
  - `profile_mode = progressive_contextual`
  - `session_weight = 0.0`

### Qué demuestra esta tanda

- Sí demuestra:
  - cierre casi completo de la checklist ambiciosa
  - cobertura funcional mucho mejor de `foco + triste`
  - entrada real de los primeros casos útiles de `feliz`
  - consolidación fuerte de `relajacion + estresado`,
    `relajacion + cansado` y `energia + cansado`
- También demuestra algo muy útil para la memoria:
  - el sistema no “finge” aprender igual en todos los moods
  - cuando no hay base suficiente, como en `feliz`, se mantiene prudente y no
    aplica aprendizaje individual fuerte

### Conclusión de esta fase

- A nivel de aprendizaje individual, `triste`, `estresado` y `cansado` quedan
  ya muy maduros y defendibles.
- `neutral` ya estaba razonablemente estable en la tanda anterior.
- `feliz` pasa a estar cubierto, pero todavía no maduro.
- La narrativa del proyecto se vuelve más rica porque ya no solo muestra
  “aprendizaje exitoso”, sino también un caso donde el sistema reconoce que aún
  no debe aplicar memoria aprendida de forma intensa.

## Cuarta tanda complementaria observada (`2026-05-15`, ampliación)

Una parte de los logs aportados repite sesiones ya documentadas
(`energia + cansado`, `relajacion + cansado`, `relajacion + triste`). La parte
nueva y verdaderamente relevante es esta:

- una nueva variante de `energia + feliz`
- una primera variante explícita de `relajacion + feliz`
- y un refuerzo adicional del bloque maduro `energia + triste`

| Caso | Naturaleza | Inputs clave | Modo en generación | Profile mode | Session weight | Stable weight | Mood gate | Mood quality | Factor | Playlist | Lectura |
|---|---|---|---|---|---:|---:|---|---:|---:|---|---|
| `AA` | nueva sesión | `energia`, `feliz`, `2/4`, `indistinto`, `alta`, `equilibrado`, `mixta`, `mas_despierto`, `env=off` | `energia_feliz_alta` | `progressive_contextual` | `0.067` | `0.074` | `False` | `47.36` | `0.25` | `5gv2p3tWj7puVILeMJSs8q` | `feliz` sigue inmaduro, pero deja de estar completamente a cero |
| `AB` | nueva sesión | `relajacion`, `feliz`, `2/4`, `instrumental`, `suave`, `equilibrado`, `alternativa`, `mas_calmado`, `env=off` | `relajacion_feliz_suave` | `progressive_contextual` | `0.147` | `0.164` | `False` | `56.39` | `0.55` | `1ZbS2BsUCnteAIaoynWLQX` | Primera señal de aprendizaje prudente en `feliz` |
| `AC` | refuerzo | `energia`, `triste`, `4/2`, `con_voz`, `alta`, `descubrir`, `alternativa`, `mas_despierto`, `env=off` | `energia_triste_alta` | `stable_weighted` | `0.195` | `0.216` | `True` | `87.16` | `1.0` | `4Z7Q6tf7dsWMVU0axkYICD` | El mood `triste` se reafirma como el más maduro |

### Lectura técnica de esta ampliación

- El dataset alcanza `48` ejemplos etiquetados:
  - `45 -> 48`
- El mood `feliz` sigue sin pasar gate, pero ya no se comporta igual que en la
  tanda anterior:
  - antes: `quality = 31.01`, `factor = 0.0`
  - ahora:
    - `energia + feliz`: `quality = 47.36`, `factor = 0.25`
    - `relajacion + feliz`: `quality = 56.39`, `factor = 0.55`
- Esto indica que `feliz` sigue inmaduro, pero empieza a entrar en una fase de
  aprendizaje prudente, no de abstención absoluta.
- `triste` refuerza aún más su madurez con `quality = 87.16`.

### Qué aporta esta ampliación

- Para memoria:
  - permite enseñar una evolución intermedia del mood `feliz`
  - ya no solo existe el contraste binario “maduro / no maduro”
  - ahora aparece una fase de transición con aplicación parcial
- Para el sistema:
  - confirma que el `application_factor` puede crecer antes de que el
    `mood_gate` pase completamente
  - y eso hace la lógica más interesante y más creíble

### Conclusión práctica

- `feliz` sigue sin ser un mood maduro, pero ya no está en estado embrionario.
- `triste`, `estresado` y `cansado` se mantienen muy consolidados.
- La siguiente mejora de más valor ya no es añadir más positivos de `triste`,
  sino:
  - conseguir algún caso menos positivo o ambiguo
  - y seguir empujando `feliz` hasta ver si llega a pasar gate.

## Quinta tanda de cierre observada (`2026-05-15`, `feliz` cruza el gate)

La nueva evidencia cambia la lectura anterior: el mood `feliz` ya no está solo
en transición prudente. En esta tanda pasa el gate y entra en aplicación
completa del aprendizaje individual.

| Caso | Naturaleza | Inputs clave | Modo en generación | Profile mode | Session weight | Stable weight | Mood gate | Mood quality | Factor | Playlist | Lectura |
|---|---|---|---|---|---:|---:|---|---:|---:|---|---|
| `AD` | nueva sesión | `relajacion`, `feliz`, `2/4`, `instrumental`, `suave`, `familiar`, `mixta`, `mas_calmado`, `env=off` | `relajacion_feliz_suave` | `stable_weighted` | `0.302` | `0.335` | `True` | `63.86` | `1.0` | `5WcLNzZiCgY6hgHQjCRZQV` | `feliz` pasa a una fase plenamente aplicada en relajación |
| `AE` | nueva sesión | `energia`, `feliz`, `2/4`, `con_voz`, `alta`, `familiar`, `mainstream`, `mas_despierto`, `env=off` | `energia_feliz_alta` | `stable_weighted` | `0.303` | `0.335` | `True` | `69.20` | `1.0` | `3dibTH630A6yXeE36FHKEt` | `feliz` también cruza el gate en energía |

### Lectura técnica de esta tanda final

- El dataset alcanza `50` ejemplos etiquetados:
  - `48 -> 50`
- `feliz` pasa de:
  - `quality = 31.01`, `factor = 0.0`
  - luego `47.36 / 0.25`
  - después `56.39 / 0.55`
  - y finalmente:
    - `63.86 / 1.0` en `relajacion + feliz`
    - `69.20 / 1.0` en `energia + feliz`
- El `profile_mode` cambia de `progressive_contextual` a `stable_weighted`,
  señal muy coherente con la maduración del mood.
- Los pesos dejan de ser testimoniales:
  - `session_weight` pasa a `0.302` y `0.303`
  - `stable_weight` sube a `0.335`

### Qué demuestra esta tanda

- El sistema no solo identifica moods maduros desde el principio, sino que
  puede mostrar la trayectoria completa:
  - abstención total
  - aprendizaje prudente
  - aprendizaje plenamente aplicado
- `feliz` deja de ser el contraejemplo inmaduro y pasa a integrarse en el grupo
  de moods ya maduros.

### Conclusión actualizada del estado del perfil

- `triste`, `estresado`, `cansado`, `neutral` y ahora también `feliz` cuentan
  ya con evidencia funcional de aprendizaje individual maduro.
- El volumen objetivo de esta fase (`45-50` ejemplos) se ha alcanzado.
- La historia que mejor representa Harmony Hub a día de hoy es:
  - aprendizaje individual fuerte y observable
  - transición gradual por mood cuando aún no hay suficiente evidencia
  - y activación prudente solo cuando el mood realmente madura
