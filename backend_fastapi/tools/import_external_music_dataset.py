from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable
from urllib.parse import urlparse
from urllib.request import urlretrieve

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import MSD_CATALOG_PATH, MSD_TRACKS_COLLECTION
from app.services.catalog_bootstrap_service import build_bootstrap_catalog_track
from app.services.firestore_service import get_firestore_client
from app.services.msd_catalog_service import load_catalog_tracks, normalize_text


PRESET_FIELDS: dict[str, dict[str, str]] = {
    "spotify_tracks_csv": {
        "track_id": "track_id",
        "title": "track_name",
        "artist_name": "artists",
        "genre": "track_genre",
        "popularity": "popularity",
        "duration_ms": "duration_ms",
        "explicit": "explicit",
        "danceability": "danceability",
        "energy": "energy",
        "acousticness": "acousticness",
        "instrumentalness": "instrumentalness",
        "liveness": "liveness",
        "speechiness": "speechiness",
        "valence": "valence",
        "tempo": "tempo",
    },
    "generic_audio_features_csv": {
        "track_id": "track_id",
        "title": "title",
        "artist_name": "artist_name",
        "genre": "genre",
        "popularity": "popularity",
        "duration_ms": "duration_ms",
        "explicit": "explicit",
        "danceability": "danceability",
        "energy": "energy",
        "acousticness": "acousticness",
        "instrumentalness": "instrumentalness",
        "liveness": "liveness",
        "speechiness": "speechiness",
        "valence": "valence",
        "tempo": "tempo",
    },
}


def _identity_key(track: dict[str, Any]) -> str:
    title = normalize_text(track.get("name") or track.get("title"))
    artists = track.get("artists", []) or []
    artist = normalize_text(track.get("artist_name") or (artists[0] if artists else ""))
    return f"{title}::{artist}"


def _load_existing_catalog_sets() -> tuple[set[str], set[str]]:
    merged = load_catalog_tracks(limit=None)
    ids = {
        str(track.get("catalog_track_id")).strip()
        for track in merged
        if str(track.get("catalog_track_id") or "").strip()
    }
    identities = {_identity_key(track) for track in merged}
    return ids, identities


def _append_jsonl(path: Path, tracks: list[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        for track in tracks:
            fh.write(json.dumps(track, ensure_ascii=False) + "\n")


def _write_firestore(collection_name: str, tracks: list[dict[str, Any]]) -> int:
    if not tracks:
        return 0

    db = get_firestore_client()
    batch = db.batch()
    written = 0
    for track in tracks:
        doc_id = str(track.get("catalog_track_id"))
        batch.set(
            db.collection(collection_name).document(doc_id),
            track,
            merge=True,
        )
        written += 1
        if written % 400 == 0:
            batch.commit()
            batch = db.batch()

    if written % 400 != 0:
        batch.commit()
    return written


def _iter_json_payload(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
    elif isinstance(payload, dict):
        items = payload.get("items") or payload.get("tracks") or payload.get("data") or []
        for item in items:
            if isinstance(item, dict):
                yield item


def _iter_jsonl_payload(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            item = json.loads(text)
            if isinstance(item, dict):
                yield item


def _iter_csv_payload(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield dict(row)


def _iter_records(path: Path) -> Iterable[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        yield from _iter_jsonl_payload(path)
        return
    if suffix == ".json":
        yield from _iter_json_payload(path)
        return
    if suffix == ".csv":
        yield from _iter_csv_payload(path)
        return
    raise SystemExit(f"Formato no soportado para importacion: {path.suffix}")


def _download_if_needed(url: str) -> Path:
    parsed = urlparse(url)
    name = Path(parsed.path).name or "external_music_dataset.tmp"
    tmp_dir = Path(tempfile.mkdtemp(prefix="hh_external_catalog_"))
    target = tmp_dir / name
    urlretrieve(url, target)
    return target


def _split_artists(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    separators = [";", ",", "|"]
    for sep in separators:
        if sep in text:
            return [part.strip() for part in text.split(sep) if part.strip()]
    return [text]


def _map_row(raw: dict[str, Any], preset: str) -> dict[str, Any]:
    mapping = PRESET_FIELDS[preset]

    artist_value = raw.get(mapping["artist_name"])
    artists = _split_artists(artist_value)
    primary_artist = artists[0] if artists else str(artist_value or "").strip()
    genre = raw.get(mapping["genre"])

    return {
        "track_id": raw.get(mapping["track_id"]),
        "title": raw.get(mapping["title"]),
        "artist_name": primary_artist,
        "artists": artists,
        "genre": genre,
        "track_genre": genre,
        "labels": [genre] if genre else [],
        "popularity": raw.get(mapping["popularity"]),
        "duration_ms": raw.get(mapping["duration_ms"]),
        "explicit": raw.get(mapping["explicit"]),
        "danceability": raw.get(mapping["danceability"]),
        "energy": raw.get(mapping["energy"]),
        "acousticness": raw.get(mapping["acousticness"]),
        "instrumentalness": raw.get(mapping["instrumentalness"]),
        "liveness": raw.get(mapping["liveness"]),
        "speechiness": raw.get(mapping["speechiness"]),
        "valence": raw.get(mapping["valence"]),
        "tempo": raw.get(mapping["tempo"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa datasets externos grandes al formato msd_tracks.",
    )
    parser.add_argument("--input", help="Ruta local a CSV, JSON o JSONL")
    parser.add_argument("--url", help="URL publica del dataset a descargar antes de importar")
    parser.add_argument(
        "--preset",
        choices=sorted(PRESET_FIELDS.keys()),
        required=True,
        help="Preset de mapeo para el dataset externo",
    )
    parser.add_argument("--limit", type=int, default=0, help="Maximo de filas a procesar")
    parser.add_argument(
        "--max-per-genre",
        type=int,
        default=0,
        help="Maximo de tracks nuevas por genero normalizado",
    )
    parser.add_argument("--write-local", action="store_true", help="Añade las nuevas entradas al JSONL local")
    parser.add_argument("--write-firestore", action="store_true", help="Escribe las nuevas entradas en la colección msd_tracks")
    parser.add_argument("--jsonl-path", default=MSD_CATALOG_PATH, help="Ruta del JSONL local a ampliar")
    parser.add_argument("--collection", default=MSD_TRACKS_COLLECTION, help="Colección Firestore destino")
    args = parser.parse_args()

    if not args.input and not args.url:
        raise SystemExit("Debes indicar --input o --url")

    source_path = Path(args.input) if args.input else _download_if_needed(args.url)
    if not source_path.exists():
        raise SystemExit(f"No existe la fuente de datos: {source_path}")

    existing_ids, existing_identities = _load_existing_catalog_sets()
    generated: list[dict[str, Any]] = []
    skipped_existing = 0
    skipped_invalid = 0
    processed = 0
    genre_counts: Counter[str] = Counter()

    for raw in _iter_records(source_path):
        processed += 1
        mapped = _map_row(raw, args.preset)
        genre_key = normalize_text(mapped.get("genre") or mapped.get("track_genre"))
        if args.max_per_genre and genre_key and genre_counts[genre_key] >= args.max_per_genre:
            if args.limit and processed >= args.limit:
                break
            continue

        candidate = build_bootstrap_catalog_track(
            mapped,
            source=f"external_dataset:{args.preset}",
        )
        if candidate is None:
            skipped_invalid += 1
            if args.limit and processed >= args.limit:
                break
            continue

        catalog_id = str(candidate.get("catalog_track_id") or "").strip()
        identity = _identity_key(candidate)
        if catalog_id in existing_ids or identity in existing_identities:
            skipped_existing += 1
            if args.limit and processed >= args.limit:
                break
            continue

        existing_ids.add(catalog_id)
        existing_identities.add(identity)
        generated.append(candidate)
        if genre_key:
            genre_counts[genre_key] += 1

        if args.limit and processed >= args.limit:
            break

    print(
        "External candidates generated:",
        len(generated),
        "| processed:",
        processed,
        "| skipped_existing:",
        skipped_existing,
        "| skipped_invalid:",
        skipped_invalid,
        "| distinct_genres:",
        len(genre_counts),
    )

    if args.write_local:
        jsonl_path = Path(args.jsonl_path)
        _append_jsonl(jsonl_path, generated)
        print(f"Appended to local catalog: {jsonl_path} | tracks={len(generated)}")

    if args.write_firestore:
        written = _write_firestore(args.collection, generated)
        print(f"Written to Firestore collection '{args.collection}': {written}")


if __name__ == "__main__":
    main()
