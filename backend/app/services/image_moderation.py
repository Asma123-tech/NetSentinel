# app/services/image_moderation.py
"""
Image moderation service.
Uses Pillow (already in requirements.txt) to apply Gaussian blur to images
when the filter mode is strict or moderate.
No ML model required — blur is applied unconditionally in non-relaxed modes.
The media proxy decides WHETHER to blur; this module decides HOW.
"""
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageFilter


def censor_if_needed(
    image_bytes: bytes,
    threshold: float = 0.5,   # kept for API compatibility — not used with blur approach
) -> Tuple[bytes, bool]:
    """
    Apply Gaussian blur to the image.
    Returns (blurred_bytes, True) on success.
    Returns (original_bytes, False) if the image cannot be processed.

    The `threshold` parameter is kept so the call signature in media.py
    doesn't need to change.
    """
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")

        # Radius 20 gives a strong blur that obscures explicit content
        # while still showing the image exists (better UX than a broken img)
        blurred = image.filter(ImageFilter.GaussianBlur(radius=20))

        output = BytesIO()
        blurred.save(output, format="JPEG", quality=85)
        return output.getvalue(), True

    except Exception:
        # If Pillow can't open it (corrupt image, SVG, etc.) return original
        return image_bytes, False