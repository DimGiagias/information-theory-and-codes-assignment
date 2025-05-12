import heapq
import collections
from typing import Dict, Optional, Tuple

class HuffmanNode:
    """
    Represents a node in the Huffman tree.
    Can be a leaf node (containing a character/byte) or an internal node.
    """
    __slots__ = ('symbol', 'frequency', 'left', 'right')

    def __init__(self, symbol: Optional[int], frequency: int):
        self.symbol: Optional[int] = symbol
        self.frequency: int = frequency
        self.left: Optional['HuffmanNode'] = None
        self.right: Optional['HuffmanNode'] = None

    def __lt__(self, other: 'HuffmanNode') -> bool:
        return self.frequency < other.frequency

    def __repr__(self) -> str:
        return f"HuffmanNode(symbol={self.symbol}, frequency={self.frequency})"

class HuffmanCodec:
    def __init__(self, data: Optional[bytes] = None):
        self.data: bytes = data or b""
        self.frequency_map: Dict[int, int] = {}
        self.root: Optional[HuffmanNode] = None
        self.code_map: Dict[int, str] = {}

    def build(self) -> None:
        """
        Builds the Huffman tree and code map from self.data.
        """
        self.frequency_map = dict(collections.Counter(self.data))
        self.root = self._build_tree(self.frequency_map)
        self.code_map = self._generate_codes(self.root)

    def compress(self, data: Optional[bytes] = None) -> Tuple[str, Dict[int, int]]:
        """
        Compresses the given data and returns a bit string plus frequency map.
        """
        input_data = data if data is not None else self.data
        if not input_data:
            return "", {}

        self.data = input_data
        if not self.code_map:
            self.build()

        bit_string = ''.join(self.code_map[b] for b in self.data)
        return bit_string, self.frequency_map

    def decompress(self, bit_string: str, frequency_map: Optional[Dict[int, int]] = None) -> bytes:
        """
        Decompresses a bit string using the provided frequency map.
        """
        if frequency_map is not None:
            self.frequency_map = frequency_map
        if not self.frequency_map:
            return b""

        if self.root is None or frequency_map is not None:
            self.root = self._build_tree(self.frequency_map)

        decoded_bytes = []
        node = self.root
        for bit in bit_string:
            node = node.left if bit == '0' else node.right
            if node.symbol is not None:
                decoded_bytes.append(node.symbol)
                node = self.root
        return bytes(decoded_bytes)

    def _build_tree(self, freq_map: Dict[int, int]) -> Optional[HuffmanNode]:
        if not freq_map:
            return None

        queue = [HuffmanNode(s, f) for s, f in freq_map.items()]
        heapq.heapify(queue)

        if len(queue) == 1:
            only_node = heapq.heappop(queue)
            wrapper = HuffmanNode(None, only_node.frequency)
            wrapper.left = only_node
            return wrapper

        while len(queue) > 1:
            left = heapq.heappop(queue)
            right = heapq.heappop(queue)
            merged = HuffmanNode(None, left.frequency + right.frequency)
            merged.left = left
            merged.right = right
            heapq.heappush(queue, merged)

        return queue[0]

    def _generate_codes(self, node: Optional[HuffmanNode], prefix: str = "", code_map: Optional[Dict[int, str]] = None) -> Dict[int, str]:
        code_map = code_map if code_map is not None else {}
        if node is None:
            return code_map

        if node.symbol is not None:
            code_map[node.symbol] = prefix or "0"
        else:
            if node.left:
                self._generate_codes(node.left, prefix + "0", code_map)
            if node.right:
                self._generate_codes(node.right, prefix + "1", code_map)

        return code_map