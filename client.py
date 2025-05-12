import argparse
import os
import magic
from typing import Optional
from common_utils import ProcessedData, calculate_sha256, calculate_entropy

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

    client_data_obj = ProcessedData(original_image_path=filepath)

    try:
        mime = magic.Magic(mime=True)
        client_data_obj.mime_type = mime.from_buffer(file_bytes)
        print(f"Detected MIME type: {client_data_obj.mime_type}")
    except magic.MagicException as e:
        print(f"Error: MIME type detection failed. Is libmagic installed correctly? Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during MIME type detection: {e}")
        return None

    if client_data_obj.mime_type and client_data_obj.mime_type.startswith('image/'):
        client_data_obj.is_image = True
        print("File is identified as an image.")

        client_data_obj.sha256 = calculate_sha256(file_bytes)
        client_data_obj.entropy = calculate_entropy(file_bytes)
    else:
        client_data_obj.is_image = False
        print("Stopping processing as file is not an image.")
        return None

    return client_data_obj

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to the file to process.")

    args = parser.parse_args()

    processed_info = process_file(args.filepath)

    if processed_info:
        print("\n--- Processing Summary ---")
        print(f"File Path: {processed_info.original_image_path}")
        print(f"MIME Type: {processed_info.mime_type}")
        print(f"File is Image: {processed_info.is_image}")
        if processed_info.is_image:
            print(f"SHA256: {processed_info.sha256}")
            print(f"Entropy: {processed_info.entropy}")
    else:
        print("\nFile processing failed or file was not an image.") 