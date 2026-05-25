from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.firestore_service import get_firestore_client
from app.services.msd_catalog_service import normalize_catalog_track


def _iter_records(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                text = line.strip()
                if not text:
                    continue
                yield json.loads(text)
        return

    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
        return

    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("tracks") or []
        for item in items:
            if isinstance(item, dict):
                yield item


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa un catálogo derivado de MSD a Firestore.",
    )
    parser.add_argument("--input", required=True, help="Ruta a JSON o JSONL normalizado")
    parser.add_argument("--collection", default="msd_tracks", help="Colección destino")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de registros")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"No existe el fichero: {input_path}")

    db = get_firestore_client()
    batch = db.batch()
    written = 0

    for index, raw in enumerate(_iter_records(input_path), start=1):
        normalized = normalize_catalog_track(raw, source="firestore")
        doc_id = normalized.get("catalog_track_id")
        if not doc_id:
            continue

        ref = db.collection(args.collection).document(str(doc_id))
        batch.set(
            ref,
            {
                **normalized,
                "_catalog_search_text": normalized.get("_catalog_search_text"),
            },
            merge=True,
        )
        written += 1

        if written % 400 == 0:
            batch.commit()
            batch = db.batch()
            print(f"Importados {written} tracks...")

        if args.limit and written >= args.limit:
            break

    if written % 400 != 0:
        batch.commit()

    print(f"Importación completada. Tracks escritos: {written}")


if __name__ == "__main__":
    main()
