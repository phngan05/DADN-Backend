Place face images here.

Rules:
- Filename (without extension) is used as the FaceID id.
- Supported extensions: .jpg, .jpeg, .png, .gif, .webp
- Example: 123e4567-e89b-12d3-a456-426614174000.jpg

Optional manifest:
- app/uploads/faceid/manifest.json can store per-id settings.
- Example:
{
  "123e4567-e89b-12d3-a456-426614174000": {
    "full_name": "Nguyen Van A",
    "is_active": true
  }
}
