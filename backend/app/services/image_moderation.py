# app/services/image_moderation.py
# nudenet/torch/transformers disabled - not installed
from typing import Tuple

def censor_if_needed(image_bytes: bytes, threshold: float = 0.5) -> Tuple[bytes, bool]:
    return image_bytes, False