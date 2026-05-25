# Harmony Hub Final Delivery Checklist

Checklist final para dejar Harmony Hub en estado de entrega, demo y evaluación.

## 1. Seguridad y secretos

- [ ] Confirmar que no se entregan credenciales reales innecesarias.
- [ ] Revisar [firebase-service-account.json](/Users/alvaroredondo/harmony-hub/backend_fastapi/firebase-service-account.json) y decidir:
  - mantenerlo fuera del paquete final, o
  - sustituirlo por un ejemplo/instrucción de configuración.
- [ ] Confirmar que `client_id`, tokens, claves o correos sensibles no aparecen hardcodeados en documentación o capturas.
- [ ] Añadir un fichero de ejemplo de variables si hace falta (`.env.example` o documento equivalente).

## 2. Estructura del proyecto

- [ ] Mantener `backend_fastapi/app/` solo para runtime.
- [ ] Mantener `backend_fastapi/tools/` solo para scripts manuales o de mantenimiento.
- [ ] Mantener `backend_fastapi/tests/` para validación automática.
- [ ] Mantener `backend_fastapi/app/ml/models/` para artefactos reales del modelo.
- [ ] Eliminar archivos temporales, zips viejos o restos locales no necesarios para la entrega.

## 3. Backend reproducible

- [ ] Verificar que [requirements.txt](/Users/alvaroredondo/harmony-hub/backend_fastapi/requirements.txt) está actualizado.
- [ ] Verificar que el backend arranca con el comando documentado.
- [ ] Comprobar que Firestore Rules desplegadas coinciden con [firestore.rules](/Users/alvaroredondo/harmony-hub/firestore.rules).
- [ ] Comprobar que el flujo de mantenimiento automático del modelo sigue activo tras `feedback`.

Comandos recomendados:

```bash
cd backend_fastapi
./.venv/bin/python -m unittest discover -s tests
./.venv/bin/python -m py_compile app/services/session_mode_ml_automation_service.py app/services/session_mode_ml_audit_service.py tools/*.py
./.venv/bin/python -m uvicorn app.main:app --reload
```

## 4. App Flutter reproducible

- [ ] Verificar que `flutter pub get` funciona sin intervención manual extraña.
- [ ] Verificar que `dart analyze` no devuelve errores.
- [ ] Verificar que `flutter test` pasa.
- [ ] Comprobar login, check-in, recomendación, playlist e histórico en un dispositivo real o emulador estable.

Comandos recomendados:

```bash
cd harmonyhub
flutter pub get
dart analyze
flutter test
```

## 5. Flujo funcional mínimo de entrega

- [ ] Login Spotify correcto.
- [ ] Creación de check-in correcta.
- [ ] Generación de recomendación correcta.
- [ ] Generación de playlist correcta.
- [ ] Envío de feedback correcto.
- [ ] Reentrenado automático correcto después del feedback.

Evidencia mínima que conviene guardar:

- [ ] captura del check-in
- [ ] captura de la recomendación
- [ ] captura de la playlist
- [ ] log del backend con `LEARNING`, `CATALOG`, `MATERIALIZATION` y `ML MAINTENANCE`

## 6. Estado del ML y recomendación

- [ ] Confirmar que el modelo y su metadata existen:
  - [session_mode_model.joblib](/Users/alvaroredondo/harmony-hub/backend_fastapi/app/ml/models/session_mode_model.joblib)
  - [session_mode_model_metadata.json](/Users/alvaroredondo/harmony-hub/backend_fastapi/app/ml/models/session_mode_model_metadata.json)
  - [session_mode_model_audit.json](/Users/alvaroredondo/harmony-hub/backend_fastapi/app/ml/models/session_mode_model_audit.json)
- [ ] Confirmar que el usuario de prueba ya tiene un caso donde el aprendizaje se ve de forma clara.
- [ ] Confirmar que el flujo con `msd_tracks` materializa canciones correctamente en Spotify.
- [ ] Documentar explícitamente que Spotify puede introducir `429` o timeouts externos.

## 7. Documentación final

- [ ] Revisar README general del proyecto.
- [ ] Revisar documentación del backend.
- [ ] Revisar memoria LaTeX y comprobar que refleja:
  - arquitectura híbrida
  - uso de `msd_tracks`
  - aprendizaje progresivo por `mood`
  - automatización de auditoría y reentrenado
  - limitaciones reales del sistema
- [ ] Comprobar que no quedan descripciones antiguas del pipeline previo.

## 8. Demo preparada

- [ ] Preparar una cuenta o caso de prueba estable.
- [ ] Preparar un recorrido corto de demo de 3 a 5 minutos.
- [ ] Preparar un caso donde el aprendizaje ya esté visible en la UI.
- [ ] Tener capturas de respaldo por si Spotify falla en directo.

Recorrido recomendado:

1. Login y conexión con Spotify.
2. Check-in breve.
3. Recomendación con explicación de contexto.
4. Generación de playlist real.
5. Feedback del usuario.
6. Explicación del aprendizaje acumulado.

## 9. Limitaciones que conviene declarar

- [ ] Dependencia de Firestore y configuración externa.
- [ ] Dependencia de Spotify para la materialización final.
- [ ] Posibles `429` o timeouts de Spotify.
- [ ] Aplicación progresiva del aprendizaje por `mood`.
- [ ] Posible abstención del modelo global si no supera gates de calidad o cobertura.

## 10. Cierre de entrega

- [ ] No añadir nuevas features a partir de este punto.
- [ ] Aceptar solo correcciones críticas.
- [ ] Verificar una última vez backend + Flutter + flujo real.
- [ ] Congelar el estado final que se va a entregar.

## Estado recomendado para darlo por entregable

Puedes considerar Harmony Hub listo para entrega cuando:

- backend tests: OK
- Flutter analyze/test: OK
- un flujo end-to-end real: OK
- documentación actualizada: OK
- sin secretos expuestos innecesariamente: OK
- demo preparada: OK
