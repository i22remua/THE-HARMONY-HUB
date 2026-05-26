Manual and maintenance scripts for the backend.

These files are intentionally kept outside `app/` because they are not part of
the normal request/response runtime flow. They are used for:

- ML audit and verification
- MSD catalog import
- external dataset import and catalog bootstrap

If a script needs shared business logic, that logic should live in `app/` and
the script should act only as a thin manual entrypoint.

Useful entrypoints:

- `tools/audit_session_mode_model.py`: inspect the current supervised dataset and model availability.
- `tools/verify_session_mode_ml.py`: run deterministic ML verification scenarios against the current backend logic.
- `tools/generate_catalog_summary.py`: generate a markdown and JSON summary of the current catalog.
- `tools/import_msd_tracks.py`: sync a normalized JSONL/JSON catalog into Firestore.
- `tools/expand_msd_tracks_from_track_features.py`: grow `msd_tracks` from `track_features`.
- `tools/import_external_music_dataset.py`: import large external CSV/JSON/JSONL datasets into the `msd_tracks` format.
