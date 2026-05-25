import asyncio
import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import httpx

from app.core.config import SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI, SPOTIFY_SCOPES

# Endpoints principales de la Web API de Spotify que usamos en la app.
AUTH_BASE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
ME_URL = "https://api.spotify.com/v1/me"

# Almacenamiento efímero del flujo PKCE.
# Clave: `state` enviado al cliente.
# Valor: `code_verifier` necesario para intercambiar luego el `code` por token.
spotify_pkce_store: dict[str, dict] = {}

spotify_recommendations_available: bool | None = None
SPOTIFY_RETRY_AFTER_CAP_SECONDS = 3.0


class SpotifyRateLimitError(RuntimeError):
    def __init__(self, *, query: str, retry_after_seconds: float | None = None):
        self.query = query
        self.retry_after_seconds = retry_after_seconds
        retry_fragment = (
            f" retry_after={retry_after_seconds:.1f}s"
            if retry_after_seconds is not None
            else ""
        )
        super().__init__(f"Spotify search rate limited for query '{query}'.{retry_fragment}")


def _parse_retry_after_seconds(retry_after: str | None, default_seconds: float) -> float:
    try:
        return max(1.0, float(retry_after)) if retry_after else default_seconds
    except Exception:
        return default_seconds


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)[:96]


def _generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return _base64url(digest)


def _normalize_track_item(item: dict) -> dict:
    """
    Reduce la respuesta cruda de Spotify a la forma que consume el ranking.

    La idea es unificar los campos mínimos que necesita el resto del backend
    sin arrastrar toda la estructura original de la Web API.
    """
    artists_full = [
        {
            "id": artist.get("id"),
            "name": artist.get("name"),
        }
        for artist in item.get("artists", [])
        if artist.get("name")
    ]

    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "uri": item.get("uri"),
        "artists": [artist.get("name") for artist in item.get("artists", [])],
        "artists_full": artists_full,
        "spotify_url": item.get("external_urls", {}).get("spotify"),
        "popularity": item.get("popularity", 0),
        "duration_ms": item.get("duration_ms", 0),
        "explicit": item.get("explicit", False),
        "album_name": item.get("album", {}).get("name"),
        "album_id": item.get("album", {}).get("id"),
    }


def create_authorize_url() -> dict:
    """
    Inicia el flujo OAuth de Spotify con PKCE.

    Devuelve:
    - `authorize_url`: URL que el cliente móvil abrirá en el navegador
    - `state`: valor anti-CSRF que luego se validará al volver de Spotify
    """
    if not SPOTIFY_CLIENT_ID:
        raise ValueError("SPOTIFY_CLIENT_ID no configurado")

    state = secrets.token_urlsafe(24)
    verifier = _generate_code_verifier()
    challenge = _generate_code_challenge(verifier)

    spotify_pkce_store[state] = {
        "code_verifier": verifier,
        "created_at": time.time(),
    }

    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SPOTIFY_SCOPES,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "show_dialog": "true",
    }

    return {
        "authorize_url": f"{AUTH_BASE_URL}?{urlencode(params)}",
        "state": state,
    }


async def exchange_code_for_token(code: str, state: str) -> dict:
    """
    Intercambia el `authorization code` por un `access_token`.

    Solo funciona si el `state` existe en `spotify_pkce_store`, porque de ahí
    recuperamos el `code_verifier` del flujo PKCE.
    """
    print("\n[AUTH] exchange_code_for_token")
    print("state:", state)

    entry = spotify_pkce_store.get(state)
    if not entry:
        raise ValueError("state inválido o expirado")

    code_verifier = entry["code_verifier"]

    data = {
        "client_id": SPOTIFY_CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "code_verifier": code_verifier,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise ValueError(f"Error token Spotify: {response.status_code} {response.text}")

    token_data = response.json()
    spotify_pkce_store.pop(state, None)

    print("[AUTH] token received")
    print("scope:", token_data.get("scope"))
    print("expires_in:", token_data.get("expires_in"))

    return token_data


async def refresh_access_token(refresh_token: str) -> dict:
    """
    Obtiene un nuevo `access_token` de Spotify usando un `refresh_token`.

    Este flujo evita forzar al usuario a reconectar manualmente Spotify cuando
    el token de acceso caduca durante una sesión larga de pruebas o de uso real.
    """
    if not refresh_token:
        raise ValueError("refresh_token ausente")

    data = {
        "client_id": SPOTIFY_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise ValueError(
            f"Error refresh Spotify: {response.status_code} {response.text}"
        )

    token_data = response.json()

    print("\n[AUTH] refresh_access_token")
    print(
        "access_token (primeros 20):",
        token_data.get("access_token", "")[:20],
    )
    print("scope:", token_data.get("scope"))
    print("expires_in:", token_data.get("expires_in"))

    return token_data


async def get_spotify_profile(access_token: str) -> dict:
    """
    Recupera el perfil básico del usuario autenticado en Spotify.

    Se usa para validar el token y para obtener el `spotify_user_id` que luego
    enlaza playlists, feedback y aprendizaje.
    """
    print("\n[PROFILE] get_spotify_profile")
    print("token primeros 20:", access_token[:20] if access_token else None)

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        raise ValueError(f"Error perfil Spotify: {response.status_code} {response.text}")

    return response.json()


async def get_user_playlists(access_token: str) -> list[dict]:
    """
    Lista las playlists del usuario ya autenticado.

    La respuesta se simplifica a un formato ligero para que el frontend pueda
    mostrarla sin depender de la estructura completa de Spotify.
    """
    playlists_url = "https://api.spotify.com/v1/me/playlists?limit=50"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            playlists_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        raise ValueError(f"Error playlists Spotify: {response.status_code} {response.text}")

    data = response.json()
    items = data.get("items", [])

    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "description": item.get("description"),
            "url": item.get("external_urls", {}).get("spotify"),
            "tracks_total": item.get("tracks", {}).get("total", 0),
        }
        for item in items
    ]


async def get_user_top_items(
    access_token: str,
    item_type: str,
    time_range: str = "medium_term",
    limit: int = 20,
) -> list[dict]:
    """
    Recupera top tracks o top artists del usuario.

    Esta llamada alimenta la capa de personalización: afinidad por artistas,
    top tracks recientes y candidatos personalizados para la playlist final.
    """
    if item_type not in {"artists", "tracks"}:
        raise ValueError("item_type debe ser 'artists' o 'tracks'")

    url = f"https://api.spotify.com/v1/me/top/{item_type}"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            url,
            params={
                "time_range": time_range,
                "limit": limit,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        raise ValueError(
            f"Error top items Spotify: {response.status_code} {response.text}"
        )

    items = response.json().get("items", [])

    if item_type == "artists":
        return [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "genres": item.get("genres", []),
                "popularity": item.get("popularity", 0),
                "spotify_url": item.get("external_urls", {}).get("spotify"),
                "uri": item.get("uri"),
            }
            for item in items
        ]

    return [_normalize_track_item(item) for item in items]


async def search_tracks(
    access_token: str,
    query: str,
    limit: int = 10,
    market: str = "ES",
) -> list[dict]:
    """
    Busca tracks por texto libre.

    Es la base del fallback semántico: el generador crea queries como
    `deep focus instrumental` o `uplifting indie pop` y Spotify devuelve
    candidatos que luego el sistema filtra y rankea.
    """
    search_url = "https://api.spotify.com/v1/search"

    async with httpx.AsyncClient(timeout=20) as client:
        retries = 2
        response = None

        for attempt in range(retries + 1):
            response = await client.get(
                search_url,
                params={
                    "q": query,
                    "type": "track",
                    "limit": limit,
                    "market": market,
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 429:
                break

            if attempt == retries:
                break

            retry_after = response.headers.get("Retry-After")
            wait_seconds = _parse_retry_after_seconds(retry_after, default_seconds=1.5)

            if wait_seconds > SPOTIFY_RETRY_AFTER_CAP_SECONDS:
                print(
                    f"[SPOTIFY SEARCH] 429 en query '{query}'. "
                    f"Retry-After={wait_seconds:.1f}s supera el cap local de "
                    f"{SPOTIFY_RETRY_AFTER_CAP_SECONDS:.1f}s; se aborta la búsqueda."
                )
                raise SpotifyRateLimitError(
                    query=query,
                    retry_after_seconds=wait_seconds,
                )

            print(
                f"[SPOTIFY SEARCH] 429 en query '{query}'. retry in {wait_seconds:.1f}s "
                f"(attempt {attempt + 1}/{retries + 1})"
            )
            await asyncio.sleep(wait_seconds)

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After") if response else None
        raise SpotifyRateLimitError(
            query=query,
            retry_after_seconds=_parse_retry_after_seconds(retry_after, default_seconds=1.5),
        )

    if response.status_code != 200:
        raise ValueError(f"Error search Spotify: {response.status_code} {response.text}")

    data = response.json()
    items = data.get("tracks", {}).get("items", [])

    return [_normalize_track_item(item) for item in items]


async def search_tracks_by_artist(
    access_token: str,
    artist_name: str,
    limit: int = 12,
    market: str = "ES",
) -> list[dict]:
    """
    Busca canciones restringiendo la consulta a un artista.

    Se usa sobre todo en la construcción de candidatos personalizados cuando
    queremos expandir artistas afines del historial del usuario.
    """
    search_url = "https://api.spotify.com/v1/search"
    query = f'artist:"{artist_name}"'

    async with httpx.AsyncClient(timeout=20) as client:
        retries = 1
        response = None

        for attempt in range(retries + 1):
            response = await client.get(
                search_url,
                params={
                    "q": query,
                    "type": "track",
                    "limit": limit,
                    "market": market,
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 429:
                break

            if attempt == retries:
                break

            retry_after = response.headers.get("Retry-After")
            wait_seconds = _parse_retry_after_seconds(retry_after, default_seconds=1.0)

            if wait_seconds > SPOTIFY_RETRY_AFTER_CAP_SECONDS:
                print(
                    f"[SPOTIFY SEARCH] 429 en artist search '{artist_name}'. "
                    f"Retry-After={wait_seconds:.1f}s supera el cap local de "
                    f"{SPOTIFY_RETRY_AFTER_CAP_SECONDS:.1f}s; se aborta la búsqueda."
                )
                raise SpotifyRateLimitError(
                    query=query,
                    retry_after_seconds=wait_seconds,
                )

            print(
                f"[SPOTIFY SEARCH] 429 en artist search '{artist_name}'. "
                f"retry in {wait_seconds:.1f}s"
            )
            await asyncio.sleep(wait_seconds)

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After") if response else None
        raise SpotifyRateLimitError(
            query=query,
            retry_after_seconds=_parse_retry_after_seconds(retry_after, default_seconds=1.0),
        )

    if response.status_code != 200:
        raise ValueError(
            f"Error search by artist Spotify: {response.status_code} {response.text}"
        )

    data = response.json()
    items = data.get("tracks", {}).get("items", [])

    return [_normalize_track_item(item) for item in items]




async def get_recommendations(
    access_token: str,
    seed_genres: list[str],
    target_valence: float,
    target_energy: float,
    target_danceability: float,
    min_valence: float = 0.0,
    max_valence: float = 1.0,
    min_energy: float = 0.0,
    max_energy: float = 1.0,
    limit: int = 30,
    market: str = "ES",
) -> list[dict]:
    """
    Llama al endpoint de recomendaciones de Spotify.

    Esta es la segunda gran fuente de candidatos, basada en géneros semilla y
    targets musicales (valence, energy, danceability) calculados por el modelo
    de generación de la sesión.
    """
    global spotify_recommendations_available

    if spotify_recommendations_available is False:
        return []

    url = "https://api.spotify.com/v1/recommendations"

    params = {
        "limit": limit,
        "seed_genres": ",".join(seed_genres[:5]),
        "target_valence": target_valence,
        "target_energy": target_energy,
        "target_danceability": target_danceability,
        "min_valence": min_valence,
        "max_valence": max_valence,
        "min_energy": min_energy,
        "max_energy": max_energy,
        "market": market,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code in {403, 404}:
        spotify_recommendations_available = False
        print(
            "[SPOTIFY RECOMMENDATIONS] endpoint no disponible para esta "
            "app/token en el modo actual. Se desactiva esta fuente y la "
            "generación seguirá con search + top items + afinidad."
        )
        return []

    if response.status_code != 200:
        print("[CATALOG ERROR] recommendations params:", params)
        print("[CATALOG ERROR] recommendations body:", response.text)
        raise ValueError(
            f"Error recommendations Spotify: {response.status_code} {response.text}"
        )

    spotify_recommendations_available = True
    data = response.json()
    items = data.get("tracks", [])

    return [_normalize_track_item(item) for item in items]


async def create_playlist(
    access_token: str,
    name: str,
    description: str,
    public: bool = False,
) -> dict:
    """
    Crea una playlist vacía en la cuenta del usuario autenticado.

    El servicio devuelve el objeto completo de Spotify porque luego el backend
    necesita su `id` y la URL pública para responder al frontend.
    """
    url = "https://api.spotify.com/v1/me/playlists"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            url,
            json={
                "name": name,
                "description": description,
                "public": public,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code not in (200, 201):
        raise ValueError(f"Error creating playlist: {response.status_code} {response.text}")

    return response.json()


async def add_items_to_playlist(
    access_token: str,
    playlist_id: str,
    uris: list[str],
) -> dict:
    """
    Inserta las canciones seleccionadas en la playlist ya creada.

    Este es el último paso del flujo Spotify: el ranking del backend ya decidió
    el orden y aquí solo se materializa la playlist dentro de la cuenta real.
    """
    print("\n[MATERIALIZATION] add_items_to_playlist")
    print("playlist_id:", playlist_id)
    print("uris_count:", len(uris))

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            url,
            json={"uris": uris},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code not in (200, 201):
        print("[MATERIALIZATION ERROR] add_items_to_playlist status:", response.status_code)
        print("[MATERIALIZATION ERROR] add_items_to_playlist body:", response.text)
        raise ValueError(
            f"Error adding items to playlist: {response.status_code} {response.text}"
        )

    return response.json()
