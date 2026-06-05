import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from app.core.config import settings
from app.schemas.faceid import FaceIDUpdate

router = APIRouter()

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "faceid"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = UPLOAD_ROOT / "manifest.json"
IMAGE_EXTS = ("jpg", "jpeg", "png", "gif", "webp")
FACE_MATCH_THRESHOLD = 0.7
FACEPP_COMPARE_URL = "https://api-us.faceplusplus.com/facepp/v3/compare"
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _load_manifest() -> dict[str, dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _save_manifest(data: dict[str, dict[str, Any]]) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(data, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _find_face_image(faceid_id: str) -> Path | None:
    for ext in IMAGE_EXTS:
        candidate = UPLOAD_ROOT / f"{faceid_id}.{ext}"
        if candidate.exists():
            return candidate
    return None


def _build_photo_url(request: Request, file_name: str) -> str:
    base_url = str(request.base_url)
    return f"{base_url}static/faceid/{file_name}"


def _to_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


async def _compare_faces(image_a: bytes, image_b: bytes) -> float | None:
    env_values = dotenv_values(ENV_PATH)
    api_key = env_values.get("FACEPP_API_KEY") or settings.FACEPP_API_KEY
    api_secret = env_values.get("FACEPP_API_SECRET") or settings.FACEPP_API_SECRET
    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="Face++ API not configured")

    data = {
        "api_key": api_key,
        "api_secret": api_secret,
    }
    files = {
        "image_file1": ("capture.jpg", image_a, "image/jpeg"),
        "image_file2": ("stored.jpg", image_b, "image/jpeg"),
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(FACEPP_COMPARE_URL, data=data, files=files)
        response.raise_for_status()
        payload = response.json()

    confidence = payload.get("confidence")
    if isinstance(confidence, (int, float)):
        return float(confidence)
    return None


@router.get("")
def get_faceids(request: Request):
    try:
        manifest = _load_manifest()
        faceids = []

        for image_path in sorted(UPLOAD_ROOT.iterdir()):
            if not image_path.is_file():
                continue
            if image_path.suffix.lower().lstrip(".") not in IMAGE_EXTS:
                continue

            faceid_id = image_path.stem
            meta = manifest.get(faceid_id, {})
            is_active = bool(meta.get("is_active", True))
            full_name = meta.get("full_name") or faceid_id

            faceids.append({
                "id": faceid_id,
                "is_active": is_active,
                "created_at": _to_iso(image_path.stat().st_mtime),
                "full_name": full_name,
                "photo_url": _build_photo_url(request, image_path.name),
            })

        return faceids

    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("")
def update_status(faceid: FaceIDUpdate):
    try:
        image_path = _find_face_image(faceid.id)
        if not image_path:
            raise HTTPException(status_code=404, detail="Face image not found")

        manifest = _load_manifest()
        meta = manifest.get(faceid.id, {})
        meta["is_active"] = faceid.is_active
        manifest[faceid.id] = meta
        _save_manifest(manifest)

        return {
            "id": faceid.id,
            "is_active": faceid.is_active,
        }

    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_face(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty image file")

        manifest = _load_manifest()
        best_match = {"confidence": 0.0, "face_id": None}
        matched_any = False

        for image_path in UPLOAD_ROOT.iterdir():
            if not image_path.is_file():
                continue
            if image_path.suffix.lower().lstrip(".") not in IMAGE_EXTS:
                continue

            face_id = image_path.stem
            meta = manifest.get(face_id, {})
            if meta.get("is_active") is False:
                continue

            stored_bytes = image_path.read_bytes()
            confidence = await _compare_faces(image_bytes, stored_bytes)
            if confidence is None:
                continue
            matched_any = True
            if confidence > best_match["confidence"]:
                best_match = {"confidence": confidence, "face_id": face_id}

        if not matched_any:
            return {
                "matched": False,
                "confidence": 0.0,
                "face_id": None,
            }

        normalized = best_match["confidence"] / 100.0
        matched = normalized >= FACE_MATCH_THRESHOLD
        return {
            "matched": matched,
            "confidence": normalized,
            "face_id": best_match["face_id"],
        }

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
