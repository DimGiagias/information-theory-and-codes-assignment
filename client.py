import argparse
import os
import json
import io
import requests
from PIL import Image
from typing import Dict, Any
from huffman import HuffmanCodec
from linear import LinearCodec
from utils import (
    is_image_file, read_file_bytes,
    calculate_sha256, calculate_entropy,
    bit_string_to_bytes,
    pkcs7_pad_bit_string,
    inject_bit_errors,
    to_base64,from_base64
)

N_HAMMING = 128
K_HAMMING = 120

def process_and_send(filepath: str, error_rate: float, server_url: str):
    print(f"--- Client: Processing file '{filepath}' ---")

    if not os.path.isfile(filepath):
        print(f"Error: File not found: {filepath}")
        return
    if not is_image_file(filepath):
        print(f"Error: File is not a supported image type: {filepath}")
        return

    original_image_data = read_file_bytes(filepath)
    if not original_image_data:
        print(f"Error: Could not read or file is empty: {filepath}")
        return

    print(f"Original image size: {len(original_image_data)} bytes")

    # Calculate hash
    sha256 = calculate_sha256(original_image_data)
    print(f"Original SHA256: {sha256}")

    #Calculate entropy
    entropy = calculate_entropy(original_image_data)
    print(f"Original Entropy: {entropy}")

    # Compress with huffman
    huffman_coder = HuffmanCodec()
    huffman_compressed_bits, huffman_freq_map = huffman_coder.compress_to_bit_string(original_image_data)
    if not huffman_compressed_bits and original_image_data:
        print("Error: Huffman compression resulted in empty bit string for non-empty data.")
        return
    original_huffman_bit_length = len(huffman_compressed_bits)
    print(f"Huffman compressed to {original_huffman_bit_length} bits.")

    # Apply padding
    padded_bits = pkcs7_pad_bit_string(huffman_compressed_bits, block_size_bits=K_HAMMING)
    if len(padded_bits) % K_HAMMING != 0:
        print(f"Error: PKCS#7 padding failed. Length {len(padded_bits)} is not multiple of {K_HAMMING}.")
        return

    # Linear encoding
    linear_coder = LinearCodec(n=N_HAMMING, k=K_HAMMING)
    encoded_chunks = []
    for i in range(0, len(padded_bits), K_HAMMING):
        chunk_k_bits = padded_bits[i: i + K_HAMMING]
        encoded_chunk_n_bits = linear_coder.encode(chunk_k_bits)
        encoded_chunks.append(encoded_chunk_n_bits)
    linearly_encoded_bits = "".join(encoded_chunks)
    print(f"Linearly encoded to {len(linearly_encoded_bits)} bits (output blocks of {N_HAMMING}).")

    # Inject errors
    errored_bits, num_errors_injected = inject_bit_errors(linearly_encoded_bits, error_rate)
    print(f"Injected {num_errors_injected} errors.")

    # Base64 encode
    encoded_bytes = bit_string_to_bytes(errored_bits)
    b64_encoded_message = to_base64(encoded_bytes)

    payload_parameters: Dict[str, Any] = {
        "huffman_freq_map": huffman_freq_map,
        "original_huffman_bit_length": original_huffman_bit_length,
        "padded_length": len(padded_bits),
        "linear_codec_params": linear_coder.get_parameters()
    }

    # Build payload
    payload = {
        "encoded_message": b64_encoded_message,
        "compression_algorithm": "huffman",
        "encoding": "linear",
        "parameters": payload_parameters,
        "errors": num_errors_injected,
        "SHA256": sha256,
        "entropy": entropy
    }

    print(f"\n--- Sending JSON payload to {server_url} ---")
    #print(payload)

    try:
        response = requests.post(server_url, json=payload, timeout=30)
        response.raise_for_status()
        print("\n--- Server Response ---")
        response_data = response.json()
        
        display_data = dict(response_data)
        display_data["decoded_image"] = display_data["decoded_image"][:60] + "..." + display_data["decoded_image"][-60:]
        
        # Display response
        print(json.dumps(display_data, indent=2))
        
        if response_data.get("status") == "success":
            image_representation = response_data.get("decoded_image")

            if isinstance(image_representation, str):
                if not image_representation:
                    print("Received empty Base64 string from the server.")
            else:
                print("No image data received from server.")

            # Attempt to display decoded image
            if image_representation:
                image_bytes_from_server = from_base64(image_representation)
                if image_bytes_from_server:
                    try:
                        reconstructed_image = Image.open(io.BytesIO(image_bytes_from_server))
                        original_input_image_for_format = Image.open(filepath)
                        original_format = original_input_image_for_format.format

                        decoded_filename = f"decoded_client_{os.path.basename(filepath)}"
                        save_format = original_format if original_format and original_format.upper() in ["JPEG", "JPG", "PNG", "GIF", "BMP", "TIFF"] else "PNG"
                        if not decoded_filename.lower().endswith(f".{save_format.lower()}"):
                            base, _ = os.path.splitext(decoded_filename)
                            decoded_filename = f"{base}.{save_format.lower()}"
                        
                        reconstructed_image.save(decoded_filename, format=save_format)
                        print(f"Reconstructed image saved as: {decoded_filename} (Format: {save_format})")

                        original_input_image_for_format.show(title="Original Input Image")
                        reconstructed_image.show(title=f"Reconstructed Image")
                    except IOError as e:
                        print(f"Client Info: Failed to recognize image format from server data. The received data is likely corrupted and can't form a valid image file.")
                    except Exception as e:
                        print(f"Client Error handling reconstructed image: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to server: {e}")
    except json.JSONDecodeError:
        print(f"Error: Server did not return valid JSON. Response text: {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to the image file.")
    parser.add_argument("--errors", type=float, default=0.0,
                        help="Percentage of random bit errors to introduce (e.g., 1.5 for 1.5%%).")
    parser.add_argument("--url", default="http://127.0.0.1:5000/",
                        help="URL of the server endpoint.")

    args = parser.parse_args()

    if args.errors < 0 or args.errors > 100:
        print("Error: Error percentage must be between 0 and 100.")
    else:
        process_and_send(args.filepath, args.errors, args.url)