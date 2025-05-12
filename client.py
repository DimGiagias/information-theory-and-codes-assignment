import argparse
import os
import magic
import json
from typing import Optional
from utils import ProcessedData, calculate_sha256, calculate_entropy, apply_pkcs7_padding
from huffman import HuffmanCodec
from linear import linear_encode

def process_file(filepath: str) -> Optional[ProcessedData]:
    """
    Reads a file, checks if it's an image, and calculates its SHA256 and entropy.
    """
    if not os.path.isfile(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    print(f"Processing file: {filepath}")
    
    try:
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
    except IOError as e:
        print(f"Error: Could not read file {filepath}. IO Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return None

    processed_data = ProcessedData(original_image_path=filepath)

    try:
        mime = magic.Magic(mime=True)
        processed_data.mime_type = mime.from_buffer(file_bytes)
        print(f"Detected MIME type: {processed_data.mime_type}")
    except magic.MagicException as e:
        print(f"Error: MIME type detection failed. Is libmagic installed correctly? Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during MIME type detection: {e}")
        return None

    if processed_data.mime_type and processed_data.mime_type.startswith('image/'):
        processed_data.is_image = True
        print("File is identified as an image.")

        # Claculate sha256
        processed_data.sha256 = calculate_sha256(file_bytes)
        
        #Calculate entropy
        processed_data.entropy = calculate_entropy(file_bytes)
        
        # Huffman Compression
        codec = HuffmanCodec(file_bytes)
        bit_string, freq_map = codec.compress()
        processed_data.encoded_message = bit_string
        processed_data.frequency_map = freq_map
        print(f"Huffman bit length: {len(bit_string)}")
        
        # PKCS7 padding
        padded_bit_string = apply_pkcs7_padding(bit_string)
        print(f"Padded to {len(padded_bit_string)} bits")
        
        # Linear encoding
        encoded_linear, params = linear_encode(padded_bit_string)
        processed_data.encoded_message = encoded_linear
        processed_data.encoding_parameters = params
        print(f"Linear encoded length: {len(encoded_linear)} bits, parameters: {params}")

    else:
        processed_data.is_image = False
        print("Stopping processing as file is not an image.")
        return None

    return processed_data

def build_payload(processed_data: ProcessedData, errors: int = 0) -> str:
    payload = {
        "encoded_message": processed_data.encoded_message,
        "compression_algorithm": processed_data.compression_algorithm,
        "errors": errors,
        "SHA256": processed_data.sha256,
        "entropy": processed_data.entropy
    }
    return json.dumps(payload)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to the file to process.")
    parser.add_argument("--errors", type=int, default=0, help="Error injection rate percentage.")

    args = parser.parse_args()

    processed_info = process_file(args.filepath)

    if processed_info:
        payload = build_payload(processed_info, errors=args.errors)
        print("\n--- JSON Payload ---")
        #print(payload)
    else:
        print("\nProcessing Failed.")
        exit(1)