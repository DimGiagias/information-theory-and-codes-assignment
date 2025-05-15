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
    return base64.b64encode(data_bytes).decode('utf-8')

def from_base64(b64_string: str) -> bytes:
    return base64.b64decode(b64_string.encode('utf-8'))

def bytes_to_bit_string(byte_data: bytes) -> str:
    return "".join(format(byte, '08b') for byte in byte_data)

def bit_string_to_bytes(bit_str: str) -> bytes:
    if not bit_str:
        return b''
    padded_bit_str = bit_str + '0' * ((8 - len(bit_str) % 8) % 8)
    byte_list = []
    for i in range(0, len(padded_bit_str), 8):
        byte_list.append(int(padded_bit_str[i:i + 8], 2))

    return bytes(byte_list)

def pkcs7_pad_bytes(data: bytes, block_size_bytes: int) -> bytes:
    if block_size_bytes < 1 or block_size_bytes > 255:
        raise ValueError("Block size must be between 1 and 255 for PKCS#7 byte values.")
    padding_len = block_size_bytes - (len(data) % block_size_bytes)
    padding = bytes([padding_len] * padding_len)

    return data + padding

def pkcs7_unpad_bytes(data: bytes, block_size_bytes: int) -> bytes:
    if not data:
        raise ValueError("Cannot unpad empty data.")
    padding_len = data[-1]
    if padding_len == 0 or padding_len > block_size_bytes:
        raise ValueError(f"Invalid PKCS#7 padding value: {padding_len} (block size was {block_size_bytes})")
    if padding_len > len(data):
        raise ValueError(f"Invalid PKCS#7 padding: padding length {padding_len} > data length {len(data)}")

    return data[:-padding_len]

def pkcs7_pad_bit_string(bit_str: str, block_size_bits: int) -> str:
    if block_size_bits <= 0 or block_size_bits % 8 != 0:
        raise ValueError("block_size_bits for PKCS#7 bit string padding must be a positive multiple of 8.")

    current_bytes = bit_string_to_bytes(bit_str)
    target_byte_block_size = block_size_bits // 8

    padded_bytes_for_k_multiple = pkcs7_pad_bytes(current_bytes, target_byte_block_size)
    final_padded_bit_string = bytes_to_bit_string(padded_bytes_for_k_multiple)
    return final_padded_bit_string

def pkcs7_unpad_bit_string(padded_bit_str: str, target_unpad_block_size_bits: int, original_significant_bit_length: int = None) -> str:
    if len(padded_bit_str) % 8 != 0:
        raise ValueError(
            f"Input bit string to pkcs7_unpad_bit_string (len {len(padded_bit_str)}) must have length multiple of 8.")
    if target_unpad_block_size_bits <= 0 or target_unpad_block_size_bits % 8 != 0:
        raise ValueError("target for unpadding must be a positive multiple of 8.")

    current_bytes = bit_string_to_bytes(padded_bit_str)
    byte_block_to_unpad_against = target_unpad_block_size_bits // 8

    unpadded_bytes = pkcs7_unpad_bytes(current_bytes, byte_block_to_unpad_against)
    unpadded_bit_str_from_bytes = bytes_to_bit_string(unpadded_bytes)

    if original_significant_bit_length is not None:
        if len(unpadded_bit_str_from_bytes) < original_significant_bit_length:
            raise ValueError(
                f"Unpadded bit string ({len(unpadded_bit_str_from_bytes)}) is shorter than expected original length ({original_significant_bit_length}). Padding value likely corrupted.")
        return unpadded_bit_str_from_bytes[:original_significant_bit_length]
    else:
        return unpadded_bit_str_from_bytes