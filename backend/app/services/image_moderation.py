"""
Image moderation service — NetSentinel.

Uses two AI models in sequence:
  1. NudeNet      — fast ONNX-based detector for exposed body parts (primary)
  2. Falconsai NSFW ViT — HuggingFace classifier as broader NSFW fallback

Only images that test positive on either model are blurred.
Safe images pass through completely untouched.

If both models fail (import error, download error, corrupt image),
the image is returned as-is so normal content is never accidentally censored.
"""

from __future__ import annotations

import os
import tempfile
from io import BytesIO
from typing import Optional, Tuple

from PIL import Image, ImageFilter

# ── Lazy singletons ────────────────────────────────────────────
# Models are loaded on first use so the backend starts instantly.
# Subsequent calls reuse the cached instance.

_nudenet_detector = None
_hf_model         = None
_hf_processor     = None


def _get_nudenet():
    """Return a cached NudeDetector, or None if nudenet is not installed."""
    global _nudenet_detector
    if _nudenet_detector is not None:
        return _nudenet_detector
    try:
        from nudenet import NudeDetector
        _nudenet_detector = NudeDetector()
    except Exception:
        _nudenet_detector = None
    return _nudenet_detector


def _get_hf_classifier():
    """Return (model, processor) tuple, or (None, None) if not available."""
    global _hf_model, _hf_processor
    if _hf_model is not None:
        return _hf_model, _hf_processor
    try:
        from transformers import AutoModelForImageClassification, ViTImageProcessor
        _hf_model     = AutoModelForImageClassification.from_pretrained(
            "Falconsai/nsfw_image_detection"
        )
        _hf_processor = ViTImageProcessor.from_pretrained(
            "Falconsai/nsfw_image_detection"
        )
    except Exception:
        _hf_model     = None
        _hf_processor = None
    return _hf_model, _hf_processor


# ── Detection helpers ──────────────────────────────────────────

# Body-part classes that NudeNet flags as explicit
_UNSAFE_CLASSES = {
    "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
}


def _is_nude_by_detector(detections: list, threshold: float) -> bool:
    """Return True if any detection exceeds the confidence threshold."""
    for d in detections:
        label = (d.get("class") or d.get("label") or "").upper()
        score = float(d.get("score", 0.0))
        if score >= threshold and any(u in label for u in _UNSAFE_CLASSES):
            return True
    return False


def _nudenet_is_explicit(image_bytes: bytes, threshold: float) -> bool:
    """
    Run NudeNet on the image bytes.
    Handles both older API (accepts bytes) and newer API (requires file path).
    Returns False on any error so safe images are never blocked by a crash.
    """
    detector = _get_nudenet()
    if detector is None:
        return False

    try:
        # Older NudeNet versions accept raw bytes directly
        detections = detector.detect(image_bytes)
        return _is_nude_by_detector(detections, threshold)
    except TypeError:
        pass  # Newer versions need a file path — fall through
    except Exception:
        return False

    # Newer NudeNet: write to a temp file and pass the path
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        detections = detector.detect(tmp_path)
        return _is_nude_by_detector(detections, threshold)
    except Exception:
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _hf_is_explicit(image_bytes: bytes) -> bool:
    """
    Run the HuggingFace ViT NSFW classifier.
    Returns False on any error.
    """
    model, processor = _get_hf_classifier()
    if model is None or processor is None:
        return False

    try:
        import torch
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
        label = model.config.id2label[logits.argmax(-1).item()]
        return label.lower() == "nsfw"
    except Exception:
        return False


# ── Blur rendering ─────────────────────────────────────────────

def _blur_image(image_bytes: bytes) -> bytes:
    """Apply a strong Gaussian blur. Returns original bytes on failure."""
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.filter(ImageFilter.GaussianBlur(radius=20))
        out = BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue()
    except Exception:
        return image_bytes


# ── Public API ─────────────────────────────────────────────────

def censor_if_needed(
    image_bytes: bytes,
    threshold: float = 0.5,
) -> Tuple[bytes, bool]:
    """
    Analyse image_bytes with AI models and blur if explicit content is detected.

    Returns:
        (final_bytes, was_censored)

    Detection order:
      1. NudeNet  — fast body-part detector (primary)
      2. HuggingFace ViT  — broader NSFW classifier (fallback)

    If both models are unavailable or both raise exceptions the original
    image is returned untouched (fail-open for safety of normal content).

    Args:
        image_bytes: Raw image bytes fetched from the remote URL.
        threshold:   Minimum confidence score for NudeNet to trigger blur.
                     0.6 for strict mode, 0.8 for moderate mode.
    """
    # Primary: NudeNet body-part detector
    try:
        if _nudenet_is_explicit(image_bytes, threshold):
            return _blur_image(image_bytes), True
    except Exception:
        pass

    # Fallback: HuggingFace NSFW classifier
    try:
        if _hf_is_explicit(image_bytes):
            return _blur_image(image_bytes), True
    except Exception:
        pass

    # Image is clean — return original untouched
    return image_bytes, False