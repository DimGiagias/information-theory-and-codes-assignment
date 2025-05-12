try:
    from huffman import HuffmanCodec
except ImportError:
    print("ERROR: Make sure the HuffmanCodec class is defined in huffman.py")
    exit()
import traceback

def run_huffman_codec_tests():
    """Runs a series of tests for the provided HuffmanCodec class."""
    test_suite_name = "HuffmanCodec Test Suite (Class Version)"
    print(f"--- Running {test_suite_name} ---")
    tests_passed = 0
    tests_failed = 0

    test_cases = [
        ("Test Case 1: Single character repeated", b"AAAAA"),
        ("Test Case 2: A common example string", b"ABRACADABRA"),
        ("Test Case 3: String with spaces and varying frequencies", b"MISSISSIPPI MUD PIE"),
        ("Test Case 4: All unique characters, equal frequency", b"abcdef"),
        ("Test Case 5: Empty string", b""),
        ("Test Case 6: Single character string", b"A"),
        ("Test Case 7: Byte data with nulls", b"\x00\x01\x00\x02\x00\x01\x00"),
        ("Test Case 8: Two unique characters", b"AB"),
        ("Test Case 9: A longer sentence", b"This is a test string for Huffman coding."),
        ("Test Case 10: Simple byte string for clear code checking", b"aaabbc"),
        ("Test Case 11: Non-ASCII Bytes", bytes([128, 129, 128, 130, 128])),
    ]

    for i, (description, original_data_bytes) in enumerate(test_cases):
        print(f"\n--- Test {i+1}: {description} ---")
        test_passed_flag = False

        codec = HuffmanCodec()

        try:
            print(f"Original Data: {original_data_bytes!r}")
            original_len = len(original_data_bytes)
            print(f"Original Length (bytes): {original_len}")

            compressed_bits, freq_map_used = codec.compress(original_data_bytes)

            # --- Compression Checks ---
            if original_len == 0:
                if compressed_bits == "" and not freq_map_used:
                    print("Compression check: PASSED (Correct empty output for empty input)")
                else:
                    print(f"Compression check: FAILED (Expected ('', {{}}), got ({compressed_bits!r}, {freq_map_used!r}))")
                    tests_failed += 1
                    continue
            elif not freq_map_used:
                print("Compression check: FAILED (Returned empty frequency map for non-empty data)")
                tests_failed += 1
                continue
            elif not isinstance(compressed_bits, str):
                 print(f"Compression check: FAILED (Compressed data is not a string: {type(compressed_bits)})")
                 tests_failed += 1
                 continue
            else:
                 print(f"Frequency Map: {freq_map_used}")
                 print(f"Compressed Bit String (len {len(compressed_bits)}): {compressed_bits[:100]}{'...' if len(compressed_bits)>100 else ''}")
        
        
            # --- Decompression Checks ---
            decoder = HuffmanCodec()
            decompressed_data_bytes = decoder.decompress(compressed_bits, freq_map_used)
            
            if not isinstance(decompressed_data_bytes, bytes):
                print(f"Decompression check: FAILED (Did not return bytes: {type(decompressed_data_bytes)})")
            elif decompressed_data_bytes == original_data_bytes:
                print("Decompression check: PASSED (Data matches original)")
                test_passed_flag = True
            else:
                print("Decompression check: FAILED (Decompressed data does not match original)")
                print(f"  Original (hex): {original_data_bytes.hex()}")
                print(f"  Decompressed (hex): {decompressed_data_bytes.hex()}")
                try:
                    print(f"  Original (decoded): {original_data_bytes.decode('utf-8', errors='replace')}")
                    print(f"  Decompressed (decoded): {decompressed_data_bytes.decode('utf-8', errors='replace')}")
                except Exception:
                    pass

        except Exception as e:
            print(f"\nERROR: An unexpected exception occurred during test '{description}': {e}")
            traceback.print_exc()

        if test_passed_flag:
            tests_passed += 1
        else:
            if original_len == 0 and (compressed_bits != "" or freq_map_used):
                pass
            elif original_len !=0 and (not freq_map_used or not isinstance(compressed_bits, str)):
                 pass
            else:
                 tests_failed += 1


    # --- Final Summary ---
    print(f"\n--- {test_suite_name} Summary ---")
    total_tests = len(test_cases)
    print(f"Total Tests Run: {total_tests}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print("--- Testing Finished ---")
    return tests_failed == 0

if __name__ == '__main__':
    all_passed = run_huffman_codec_tests()
    if all_passed:
        print("\nAll HuffmanCodec tests passed successfully!")
    else:
        print("\nSome HuffmanCodec tests FAILED.")