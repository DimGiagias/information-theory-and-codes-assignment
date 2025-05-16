from flask import Flask, request, jsonify
from typing import Dict
from utils import (
    calculate_sha256, calculate_entropy,
    bytes_to_bit_string,
    pkcs7_unpad_bit_string,
    from_base64,to_base64
)
from huffman import HuffmanCodec
from linear import LinearCodec

app = Flask(__name__)

N_HAMMING_DEFAULT = 128
K_HAMMING_DEFAULT = 120

@app.route('/', methods=['POST'])
def process_request():
    print("\n--- Server: Received new request ---")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

        b64_encoded_message = data.get("encoded_message")
        parameters = data.get("parameters", {})
        errors_introduced_by_client = data.get("errors", 0)
        original_image_sha256 = data.get("SHA256")

        if not all([b64_encoded_message, parameters, original_image_sha256 is not None]):
            missing = [field for field in ["encoded_message", "parameters", "SHA256"] if not data.get(field)]
            return jsonify({"status": "error", "message": f"Missing required fields: {', '.join(missing)}"}), 400

        freq_map_str = parameters.get("huffman_freq_map")
        
        original_huffman_bit_length = parameters.get("original_huffman_bit_length")
        
        padded_length = parameters.get("padded_length")
        linear_codec_params = parameters.get("linear_codec_params")

        if not all([freq_map_str,
                    original_huffman_bit_length is not None,
                    padded_length is not None,
                    linear_codec_params]):
            missing_params = []
            if not freq_map_str: missing_params.append("huffman_freq_map")
            if original_huffman_bit_length is None: missing_params.append("original_huffman_bit_length")
            if padded_length is None: missing_params.append(
                "padded_length")
            if not linear_codec_params: missing_params.append("linear_codec_params")
            return jsonify({"status": "error", "message": f"Missing parameters: {', '.join(missing_params)}"}), 400

        try:
            huffman_freq_map: Dict[int, int] = {int(k): v for k, v in freq_map_str.items()}
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid keys in huffman_freq_map."}), 400

        # Base64 Decoding
        errored_bytes_from_client = from_base64(b64_encoded_message)
        errored_bits = bytes_to_bit_string(errored_bytes_from_client)
        print(f"Received {len(errored_bits)} errored bits.")

        # Linear Decoding
        try:
            linear_decoder = LinearCodec.from_parameters(linear_codec_params)
            N_EFFECTIVE = linear_decoder.n
            K_EFFECTIVE = linear_decoder.k
        except Exception as e:
            print(f"Error reconstructing linear codec from parameters: {e}")
            return jsonify({"status": "error", "message": f"Invalid linear codec parameters: {e}"}), 400

        decoded_k_bit_chunks = []
        total_errors_corrected = 0

        num_n_bit_blocks_received = len(errored_bits) // N_EFFECTIVE
        processed_bit_len = num_n_bit_blocks_received * N_EFFECTIVE

        if len(errored_bits) % N_EFFECTIVE != 0:
            print(
                f"Warning: Length of received errored bits ({len(errored_bits)}) is not a multiple of N_EFFECTIVE ({N_EFFECTIVE}). Processing only full blocks.")

        for i in range(0, processed_bit_len, N_EFFECTIVE):
            chunk_n_bits = errored_bits[i: i + N_EFFECTIVE]
            message_chunk_k_bits, corrected_in_block = linear_decoder.decode(chunk_n_bits)
            decoded_k_bit_chunks.append(message_chunk_k_bits)
            total_errors_corrected += corrected_in_block

        bits_after_linear_decode = "".join(decoded_k_bit_chunks)
        print(f"Linearly decoded to {len(bits_after_linear_decode)} bits. Corrected {total_errors_corrected} errors.")

        # Check if length matches what client sent as padded_length
        if len(bits_after_linear_decode) != padded_length:
            print(f"CRITICAL LENGTH MISMATCH: After linear decode length is {len(bits_after_linear_decode)}, "
                  f"but client expected {padded_length} bits at this stage.")
            return jsonify({"status": "error", "message": "Length mismatch after linear decoding."}), 500

        # Removing PKCS#7 padding from bit string
        try:
            huffman_bits_to_decompress = pkcs7_unpad_bit_string(
                bits_after_linear_decode,
                target_unpad_block_size_bits=K_EFFECTIVE,
                original_significant_bit_length=original_huffman_bit_length
            )
        except ValueError as e:
            print(f"Error during PKCS#7 unpadding of bit string: {e}")
            return jsonify({"status": "error", "message": f"PKCS#7 Unpadding failed: {e}. Data likely corrupted."}), 400

        # The length after unpadding should be the original huffman bit length
        if len(huffman_bits_to_decompress) != original_huffman_bit_length:
            print(f"LENGTH MISMATCH AFTER UNPADDING: "
                  f"Unpadded length is {len(huffman_bits_to_decompress)}, "
                  f"expected original Huffman bit length {original_huffman_bit_length}.")
            return jsonify({"status": "error",
                            "message": "Length after PKCS#7 unpadding inconsistent with original Huffman length."}), 500

        # Huffman decompress
        huffman_decoder = HuffmanCodec()
        try:
            final_reconstructed_image_data = huffman_decoder.decompress_from_bit_string(
                huffman_bits_to_decompress,
                huffman_freq_map
            )
        except Exception as e:
            print(f"Error during Huffman decompression: {e}")
            return jsonify({"status": "error", "message": f"Huffman decompression failed: {e}"}), 500

        if final_reconstructed_image_data is None:
            return jsonify({"status": "error", "message": "Huffman decompression failed to produce data."}), 500

        reconstructed_sha256 = calculate_sha256(final_reconstructed_image_data)
        reconstructed_entropy = calculate_entropy(final_reconstructed_image_data)
        sha256_match = (reconstructed_sha256 == original_image_sha256)
        error_difference = errors_introduced_by_client - total_errors_corrected
        
        b64_final_reconstructed_image_data = to_base64(final_reconstructed_image_data)

        response_payload = {
            "status": "success",
            "decoded_image": b64_final_reconstructed_image_data,
            "server_calculated_sha256": reconstructed_sha256,
            "sha256_match": sha256_match,
            "errors_corrected": total_errors_corrected,
            "errors_difference_from_client_injected": error_difference,
            "final_entropy": reconstructed_entropy
        }
        print("--- Server: Processing finished successfully. ---")
        return jsonify(response_payload), 200

    except Exception as e:
        print(f"--- Server: UNEXPECTED ERROR: {e} ---")
        return jsonify({"status": "error", "message": f"An unexpected server error occurred: {e}"}), 500

if __name__ == '__main__':
    print("Starting server...")
    app.run(port=5000, debug=True)