# Tools del backend

Esta carpeta reune utilidades manuales de apoyo para mantenimiento tecnico del backend.

## Scripts disponibles

- `audit_session_mode_model.py`
  - revisa artefactos, metadatos y consistencia basica del modelo supervisado de sesion.
- `verify_session_mode_ml.py`
  - ejecuta comprobaciones de disponibilidad y estado del pipeline de seleccion de modo.
- `generate_catalog_summary.py`
  - genera el resumen estructurado del catalogo musical local.
- `import_msd_tracks.py`
  - importa pistas base al catalogo local desde el dataset preparado para el proyecto.
- `expand_msd_tracks_from_track_features.py`
  - amplia el catalogo local a partir de ficheros de caracteristicas adicionales.
- `import_external_music_dataset.py`
  - incorpora fuentes externas de catalogo para enriquecer la base musical local.

## Uso

Estos scripts no forman parte del flujo normal de ejecucion de la app movil ni del backend en produccion. Se usan como utilidades de:

- verificacion
- auditoria
- generacion de informes
- mantenimiento puntual del catalogo

## Nota

Antes de ejecutar cualquier script, conviene activar el entorno virtual del backend:

```bash
cd backend_fastapi
source .venv/bin/activate
```
