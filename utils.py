import hashlib
import math
import collections
import magic
import base64
import random
from typing import Optional

def get_mime_type(file_path: str) -> Optional[str]:
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except magic.MagicException as e:
        print(f"Warning: MIME type detection failed for {file_path}. Error: {e}")
        return None

def is_image_file(file_path: str) -> bool:
    mime_type = get_mime_type(file_path)
    return mime_type.startswith('image/')

def read_file_bytes(file_path: str) -> bytes:
    with open(file_path, 'rb') as f:
        return f.read()

def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = collections.Counter(data)
    total_bytes = len(data)
    entropy = 0.0
    for count in counts.values():
        probability = count / total_bytes
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy

def inject_bit_errors(bit_str: str, error_percentage: float) -> tuple[str, int]:
    if error_percentage == 0:
        return bit_str, 0

    total_bits = len(bit_str)
    num_errors = int(total_bits * error_percentage / 100.0)
    if num_errors == 0 and error_percentage > 0 and total_bits > 0:
        num_errors = 1
    if num_errors > total_bits:
        num_errors = total_bits

    bit_list = list(bit_str)
    error_indices = random.sample(range(total_bits), num_errors)

    for index in error_indices:
        bit_list[index] = '1' if bit_list[index] == '0' else '0'

    return "".join(bit_list), num_errors

def to_base64(data_bytes: bytes) -> str:
    return base64.b64encode(data_bytes).decode('ascii')

def from_base64(b64_string: str) -> bytes:
    return base64.b64decode(b64_string.encode('ascii'))