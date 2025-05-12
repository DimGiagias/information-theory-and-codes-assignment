from typing import Dict, Any

def linear_encode(bit_string: str, block_size: int = 128) -> tuple[str, Dict[str, Any]]:
    """
    Encodes the given bit string using a simple single-parity-bit linear block code.

    Args:
        bit_string: The padded bit string to encode.
        block_size: Number of data bits per block (excluding parity bit).

    Returns:
        A tuple of (encoded_bit_string, parameters), where encoded_bit_string
        has one parity bit appended after each block, and parameters is a dict
        containing the block_size used.
    """
    encoded = []
    for i in range(0, len(bit_string), block_size):
        block = bit_string[i:i + block_size]
        parity = str(block.count('1') % 2)
        encoded.append(block + parity)
    encoded_bit_string = ''.join(encoded)
    parameters = {'block_size': block_size}
    return encoded_bit_string, parameters


def linear_decode(encoded_string: str, block_size: int = 128) -> tuple[str, int]:
    """
    Decodes a bit string encoded with the linear_encode, checking and counting parity errors.

    Args:
        encoded_string: The received bit string with parity bits.
        block_size: Number of data bits per block (excluding parity bit).

    Returns:
        A tuple of (decoded_bit_string, corrected_errors_count), where decoded_bit_string
        is the concatenated data bits (without parity), and corrected_errors_count
        is the number of blocks in which parity mismatched.
    """
    decoded = []
    error_count = 0
    step = block_size + 1
    for i in range(0, len(encoded_string), step):
        segment = encoded_string[i:i + step]
        if len(segment) < step:
            break
        data_bits = segment[:block_size]
        received_parity = segment[block_size]
        expected_parity = str(data_bits.count('1') % 2)
        if received_parity != expected_parity:
            error_count += 1
        decoded.append(data_bits)
    decoded_bit_string = ''.join(decoded)
    return decoded_bit_string, error_count