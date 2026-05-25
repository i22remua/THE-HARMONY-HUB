# Guía rápida para rellenar la plantilla del TFG

Esta versión de la plantilla está estructurada principalmente para un TFG de tipo **b) Análisis y resolución de casos prácticos reales en el ámbito de la ingeniería**, que suele encajar con el desarrollo de una aplicación, plataforma, sistema software o solución tipo "llave en mano".

## 1. Archivos que debes rellenar primero

1. `_datos_proyecto.tex`: título, autor/a, DNI, tutor/a/es/as, tipo de TFG y curso académico.
2. `0_resumen_y_abstract.tex`: resumen en español, abstract en inglés y palabras clave.
3. Capítulos `1_...tex` a `9_...tex`: memoria principal.
4. `referencias.bib`: bibliografía citada en la memoria.
5. `anexo_manual_usuario.tex` y `anexo_codigo.tex`: anexos si proceden.

El archivo que se compila es `__memoria.tex`.

## 2. Índice principal preparado en `__memoria.tex`

La memoria queda organizada así:

1. Introducción y contexto
2. Objetivos
3. Antecedentes y soluciones existentes
4. Análisis del problema y requisitos
5. Diseño de la solución
6. Desarrollo e implementación
7. Pruebas y validación
8. Planificación, recursos y presupuesto
9. Conclusiones y trabajos futuros
10. Bibliografía
11. Anexos
    - Manual de usuario
    - Manual de código y repositorio

Los capítulos 1, 2, 3, 4, 5, 9, la bibliografía y los anexos de usuario/código cubren la estructura mínima indicada por la guía para el tipo b. Los capítulos 6, 7 y 8 se han añadido como refuerzo para documentar el desarrollo real, la validación y la planificación del proyecto.

## 3. Qué poner en cada capítulo

### 1. Introducción y contexto
Explica el contexto, la motivación, el problema abordado, el alcance del TFG y la estructura de la memoria.

### 2. Objetivos
Incluye objetivo general, objetivos específicos y cómo vas a comprobar su cumplimiento.

### 3. Antecedentes y soluciones existentes
Analiza soluciones previas o similares, compáralas y justifica tu propuesta.

### 4. Análisis del problema y requisitos
Define actores, requisitos funcionales, requisitos no funcionales, casos de uso, restricciones y riesgos.

### 5. Diseño de la solución
Describe arquitectura, modelo de datos, interfaz, diseño funcional, diseño de pruebas y decisiones técnicas.

### 6. Desarrollo e implementación
Documenta tecnologías, entorno, módulos principales, integraciones, seguridad, privacidad y despliegue.

### 7. Pruebas y validación
Incluye plan de pruebas, pruebas funcionales, no funcionales, validación con usuarios o casos reales, resultados y correcciones.

### 8. Planificación, recursos y presupuesto
Incluye fases, cronograma, recursos y estimación de costes. Si tu tutor/a no lo ve necesario, puedes comentar este capítulo en `__memoria.tex`.

### 9. Conclusiones y trabajos futuros
Resume logros, cumplimiento de objetivos, limitaciones y mejoras futuras.

## 10. Recomendaciones prácticas
- No dejes textos entre corchetes en la versión final.
- Cada afirmación técnica basada en fuentes externas debe tener una cita bibliográfica.
- Usa figuras y tablas solo cuando ayuden a explicar el proyecto.
- Mantén los anexos para información extensa: manuales, capturas detalladas, código, configuraciones, resultados completos, etc.
- Antes de entregar, revisa que el índice generado coincide con la estructura acordada con tu tutor/a.
