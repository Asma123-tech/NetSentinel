"""
Image moderation service — NetSentinel.

Uses two AI models:
  1. NudeNet  — fast ONNX body-part detector (primary)
  2. Falconsai/nsfw_image_detection ViT — HuggingFace NSFW classifier (fallback)

Strict mode catches partial exposure (bikinis, suggestive poses) in addition
to full nudity by including BELLY_EXPOSED, ARMPITS_EXPOSED, and using a
lower confidence threshold (0.4 vs 0.6 for moderate).
"""

from __future__ import annotations

import os
import tempfile
from io import BytesIO
from typing import Optional, Tuple

from PIL import Image, ImageFilter

# ── Lazy singletons ────────────────────────────────────────────

_nudenet_detector = None
_hf_model         = None
_hf_processor     = None


def _get_nudenet():
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


# ── NudeNet class sets ─────────────────────────────────────────

# Strict mode: full nudity + partial exposure (bikinis, suggestive poses)
_UNSAFE_CLASSES_STRICT = {
    "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
    "BELLY_EXPOSED",        # catches bikinis and crop-top exposure
    "ARMPITS_EXPOSED",      # catches very suggestive poses
}

# Moderate mode: only full nudity
_UNSAFE_CLASSES_MODERATE = {
    "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
}


# ── Detection helpers ──────────────────────────────────────────

def _is_nude_by_detector(
    detections: list,
    threshold: float,
    unsafe_classes: set,
) -> bool:
    for d in detections:
        label = (d.get("class") or d.get("label") or "").upper()
        score = float(d.get("score", 0.0))
        if score >= threshold and any(u in label for u in unsafe_classes):
            return True
    return False


def _nudenet_is_explicit(
    image_bytes: bytes,
    threshold: float,
    unsafe_classes: set,
) -> bool:
    detector = _get_nudenet()
    if detector is None:
        return False

    try:
        detections = detector.detect(image_bytes)
        return _is_nude_by_detector(detections, threshold, unsafe_classes)
    except TypeError:
        pass
    except Exception:
        return False

    # Newer NudeNet requires file path
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        detections = detector.detect(tmp_path)
        return _is_nude_by_detector(detections, threshold, unsafe_classes)
    except Exception:
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _hf_is_explicit(image_bytes: bytes) -> bool:
    model, processor = _get_hf_classifier()
    if model is None or processor is None:
        return False
    try:
        import torch
        image  = Image.open(BytesIO(image_bytes)).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
        label = model.config.id2label[logits.argmax(-1).item()]
        return label.lower() == "nsfw"
    except Exception:
        return False


# ── Blur ──────────────────────────────────────────────────────

def _blur_image(image_bytes: bytes) -> bytes:
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
    strict: bool = True,
) -> Tuple[bytes, bool]:
    """
    Analyse image_bytes and blur if explicit content is detected.

    Args:
        image_bytes: Raw bytes of the image.
        threshold:   Confidence threshold for NudeNet detections.
                       strict mode  → 0.4  (catches partial exposure)
                       moderate mode → 0.6  (full nudity only)
        strict:      If True, uses the larger unsafe class set that
                     includes belly and armpit exposure.

    Returns:
        (final_bytes, was_censored)
    """
    unsafe_classes = _UNSAFE_CLASSES_STRICT if strict else _UNSAFE_CLASSES_MODERATE

    # Primary: NudeNet
    try:
        if _nudenet_is_explicit(image_bytes, threshold, unsafe_classes):
            return _blur_image(image_bytes), True
    except Exception:
        pass

    # Fallback: HuggingFace NSFW classifier
    try:
        if _hf_is_explicit(image_bytes):
            return _blur_image(image_bytes), True
    except Exception:
        pass

    return image_bytes, False