import hashlib
import math
import collections
from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class ProcessedData:
    original_image_path: Optional[str] = None
    mime_type: Optional[str] = None
    is_image: bool = False
    encoded_message: Optional[str] = None
    compression_algorithm: Optional[str] = "huffman"
    frequency_map: Dict[int, int] = field(default_factory=dict)
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

def apply_pkcs7_padding(bit_string: str, block_size: int = 128) -> str:
    """
    Applies PKCS#7 padding to a bit string so its length is a multiple of block_size bits.
    PKCS#7 pads whole bytes: compute required padding bytes, then append that many bytes of value = pad_len.
    """
    byte_len = (len(bit_string) + 7) // 8
    data_bytes = int(bit_string, 2).to_bytes(byte_len, byteorder='big')

    # Compute padding
    pad_len = block_size // 8 - (len(data_bytes) % (block_size // 8))
    if pad_len == 0:
        pad_len = block_size // 8
    padding = bytes([pad_len] * pad_len)

    padded = data_bytes + padding
    
    # Convert back to bit string
    padded_bit_string = bin(int.from_bytes(padded, 'big'))[2:]
    
    # Ensure leading zeros are kept
    total_bits = len(padded) * 8
    return padded_bit_string.zfill(total_bits)