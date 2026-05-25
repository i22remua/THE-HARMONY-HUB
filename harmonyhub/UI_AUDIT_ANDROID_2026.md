# UI Audit · Harmony Hub vs Android Patterns (2026)

## Objetivo
Esta auditoría revisa Harmony Hub comparándola con patrones frecuentes en interfaces Android actuales, especialmente con Material 3, ayuda contextual visible y layouts adaptativos. No busca homogeneizar la app hasta volverla genérica, sino identificar dónde conviene simplificar, sistematizar o reforzar utilidad.

## Diagnóstico general

### Fortalezas
- La app tiene una identidad visual propia y más carácter que muchas interfaces Android estándar.
- El lenguaje editorial está bastante cohesionado: degradados, superficies curvas, tipografía amplia y bloques con intención.
- El flujo principal se entiende bien: check-in → recomendación → playlist → feedback.
- La poda de texto explicativo ya ha mejorado mucho la claridad general.

### Riesgos actuales
- Algunas pantallas siguen apoyándose demasiado en el hero superior frente al contenido funcional.
- Aún hay diferencias de densidad entre secciones: unas se sienten muy refinadas y otras más cercanas al estilo Flutter/Material por defecto.
- La interfaz es más “editorial” que “adaptativa”: en Android actual se espera mejor aprovechamiento del espacio y más consistencia en tamaños distintos.
- Faltan más estados de ayuda y vacío contextuales en puntos delicados del flujo.

## Prioridades altas

### 1. Reducir peso visual del hero en pantallas funcionales
Pantallas afectadas:
- `history_screen.dart`
- `profile_screen.dart`
- `preset_mode_detail_screen.dart`
- `generated_playlist_screen.dart`

Recomendación:
- bajar un poco la altura visual del hero
- usar más frecuencia de títulos funcionales y menos bloques de apertura grandes
- reservar heroes grandes para home, check-in y recommendation

Impacto:
- mejora sensación de agilidad
- acerca la app a patrones Android premium actuales

### 2. Unificar más los bloques secundarios
Se ven varios estilos de bloque conviviendo:
- `EditorialPanel`
- tarjetas blancas con borde
- chips suaves
- botones largos con distinto peso visual

Recomendación:
- fijar 3 niveles de superficie máximos:
  - hero
  - panel principal
  - chip / tarjeta de dato
- evitar variantes extra si no aportan jerarquía real

Impacto:
- la app se siente más madura y menos artesanal

### 3. Introducir más ayuda contextual y estados vacíos
La nueva FAQ y guía de perfil ayudan, pero el patrón debería extenderse a:
- Spotify no conectado
- historial sin resultados
- aprendizaje todavía inmaduro
- playlist no materializable
- feedback no enviado

Recomendación:
- bloques pequeños, muy concretos, cerca de la acción
- no tutoriales largos ni pantallas aparte

Impacto:
- reduce fricción sin recargar copy

## Revisión pantalla por pantalla

### Home
Estado:
- visualmente potente
- buena entrada emocional
- CTA principal claro

Mantendría:
- hero principal
- CTA de empezar check-in
- identidad de marca

Reduciría:
- cantidad de mini paneles secundarios si no empujan una acción inmediata

Mejoraría:
- una versión más adaptativa en pantallas grandes
- un bloque funcional más visible para “seguir donde lo dejaste”

### Check-in
Estado:
- probablemente la pantalla más sólida del producto
- flujo bien articulado
- el resumen final ya quedó más limpio

Mantendría:
- el estilo conversacional
- la progresión guiada
- la barra inferior de acciones

Mejoraría:
- dividir mejor visualmente “estado actual” y “acciones”
- compactar todavía algo más algunos resúmenes en móviles pequeños

### Recommendation
Estado:
- muy buena transición entre lectura emocional y propuesta
- visualmente coherente

Mantendría:
- el tono editorial
- el resumen del modo recomendado

Reduciría:
- cualquier repetición residual de aprendizaje / cierre / siguiente paso

Mejoraría:
- estados alternativos más claros:
  - recomendación rehecha
  - uso o no uso del entorno
  - ML prudente o más estable

### Generated playlist
Estado:
- ya está bastante limpia
- sigue contando bien el salto a Spotify

Mantendría:
- el bloque de aprendizaje
- el bloque de entorno
- las dos acciones finales

Mejoraría:
- más énfasis en el estado de materialización real
- mejor tratamiento de errores o limitaciones Spotify
- si la playlist se abrió o no, como estado visible

### Feedback
Estado:
- mucho más directa tras la limpieza
- buena estructura

Mantendría:
- preguntas secuenciales simples
- cierre de sesión claro

Mejoraría:
- reforzar visualmente qué campos son realmente clave para aprender
- usar una microconfirmación más cálida al guardar

### History
Estado:
- mejoró al eliminar la pantalla de detalle
- ahora se siente más utilitaria

Mantendría:
- filtros
- cards por tipo de registro

Mejoraría:
- una jerarquía más fuerte entre “filtros” y “resultados”
- estados vacíos por filtro
- posibilidad de resumir más el historial reciente y menos el completo

### Preset modes
Estado:
- mucho mejor tras quitar textos redundantes
- el detalle ya se comporta más como atajo

Mantendría:
- agrupación por intención
- guardar para luego
- acceso directo a Spotify

Mejoraría:
- un sistema más compacto de badges para objetivo / mood / salida
- menos separación visual entre tarjeta y detalle

### Profile
Estado:
- ha ganado mucho con guía rápida y FAQ
- ahora sí tiene valor funcional

Mantendría:
- tiles de Spotify / privacidad / ajustes
- guía visible
- FAQ expandible

Mejoraría:
- una zona superior algo más informativa:
  - cuenta
  - estado de Spotify
  - resumen corto de aprendizaje
- una arquitectura más tipo “hub”:
  - cuenta
  - conexión
  - ayuda
  - privacidad

### User learning
Estado:
- mejor tras quitar duplicación
- buena pantalla para explicar memoria del sistema

Mantendría:
- métricas claras
- lectura de afinidad y sesiones

Mejoraría:
- visualización más “dashboard”
- separar más claramente:
  - evidencia acumulada
  - peso aplicado hoy
  - fiabilidad de aprendizaje por mood

### Login / Splash / Spotify connect
Estado:
- más limpios que antes
- consistentes con el resto

Mantendría:
- el tono sereno
- continuidad visual

Mejoraría:
- aún menos altura hero en login y conexión
- más foco en la acción primaria
- mensajes de error y reconexión aún más claros

## Qué haría para acercarla más al mercado Android actual

### 1. Sistema de componentes más estricto
- un solo patrón de hero alto
- un solo patrón de panel informativo
- un solo patrón de chip
- un solo patrón de CTA primario

### 2. Adaptatividad real
- revisar tablet / landscape / pantallas altas
- cambiar algunas listas verticales por composiciones en dos columnas cuando haya espacio

### 3. Mejor comunicación de estados
Priorizar estados del sistema en:
- Spotify conectado / no conectado
- aprendizaje alto / prudente
- entorno usado / no usado
- playlist generada / no materializable

### 4. Más UX de utilidad y menos decoración en pantallas secundarias
Home, check-in y recommendation sí pueden sostener una capa emocional más fuerte.
History, profile, preset detail y settings deberían ser algo más funcionales.

### 5. Reforzar accesibilidad visual
- revisar contraste en algunos degradados
- validar tamaños con text scale factor alto
- comprobar chips y botones en móviles compactos

## Qué no tocaría
- no eliminaría la identidad editorial general
- no llevaría la app a un estilo Android genérico blanco y plano
- no reduciría todo a listas impersonales

La diferencia competitiva de Harmony Hub es precisamente que no parece una herramienta fría.

## Orden recomendado de mejora
1. Reducir peso visual en pantallas secundarias.
2. Unificar sistema de superficies y CTAs.
3. Mejorar estados vacíos / error / aprendizaje.
4. Hacer layout más adaptativo.
5. Afinar accesibilidad y consistencia fina.

## Conclusión
Harmony Hub ya tiene más personalidad que muchas apps Android actuales. El siguiente salto no pasa por “ponerle más diseño”, sino por hacerla más sistemática, más adaptativa y más clara en estados funcionales. Si consigues eso sin perder el tono editorial, la interfaz quedará bastante por encima de un MVP académico típico.
