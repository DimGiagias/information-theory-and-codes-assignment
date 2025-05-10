import hashlib
import math
import collections
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProcessedData:
    original_image_path: Optional[str] = None
    mime_type: Optional[str] = None
    is_image: bool = False
    sha256: Optional[str] = None
    entropy: Optional[float] = None

@dataclass
class ServerResponse:
    status: str
    message: str

def calculate_sha256(data: bytes) -> str:
    """Calculates the SHA256 hash of byte data and returns it as a hex string."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.hexdigest()

def calculate_entropy(data: bytes) -> float:
    """
    Calculates the Shannon entropy of byte data.
    Entropy H(X) = - sum(p(x_i) * log2(p(x_i))) for all symbols x_i.
    For byte data, symbols are byte values (0-255).
    """
    if not data:
        return 0.0

    counts = collections.Counter(data)
    total_bytes = len(data)
    entropy = 0.0

    for byte_val in counts:
        probability = counts[byte_val] / total_bytes
        if probability > 0: # Avoid log(0)
            entropy -= probability * math.log2(probability)

    return entropy