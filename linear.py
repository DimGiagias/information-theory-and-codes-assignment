import numpy as np
from typing import Dict, Any, Optional, Tuple, List

class LinearCodec:
    def __init__(self, n: int = 128, k: int = 120):
        if k >= n:
            raise ValueError("Message length k must be less than codeword length n")
            
        self.n = n
        self.k = k
        self.parity_bits = n - k
        
        self.G_matrix: Optional[np.ndarray] = None
        self.H_matrix: Optional[np.ndarray] = None
        self._syndrome_table: Dict[Tuple[int, ...], int] = {}
        
        self._initialize_matrices()
        
    def _initialize_matrices(self) -> None:
        p = self.parity_bits
        k = self.k
        
        I_p = np.identity(p, dtype=np.uint8)
        
        P_cols = self._generate_P_matrix_columns(I_p)
        P_matrix = np.array(P_cols).T
        
        self.H_matrix = np.hstack((P_matrix, I_p))
        self.G_matrix = np.hstack((np.identity(k, dtype=np.uint8), P_matrix.T))
        
        self._build_syndrome_table()
        
    def _generate_P_matrix_columns(self, I_p: np.ndarray) -> List[np.ndarray]:
        p = self.parity_bits
        id_cols = {tuple(I_p[:, i]) for i in range(p)}
        P_cols = []
        
        for i in range(1, 2 ** p):
            col = np.array([int(bit) for bit in format(i, f'0{p}b')], dtype=np.uint8)
            if tuple(col) not in id_cols:
                P_cols.append(col)
                if len(P_cols) == self.k:
                    break
                    
        return P_cols

    def _build_syndrome_table(self) -> None:
        self._syndrome_table.clear()
        
        if self.H_matrix is None:
            return
            
        for pos in range(self.n):
            error = np.zeros(self.n, dtype=np.uint8)
            error[pos] = 1
            syndrome = tuple((self.H_matrix @ error) % 2)
            
            if any(syndrome) and syndrome not in self._syndrome_table:
                self._syndrome_table[syndrome] = pos

    def encode(self, message: str) -> str:
        if not self.G_matrix is not None:
            raise RuntimeError("Generator matrix not initialized")
        if len(message) != self.k:
            raise ValueError(f"Message must be {self.k} bits, got {len(message)}")
            
        message_vector = np.array([int(bit) for bit in message], dtype=np.uint8)
        codeword = (message_vector @ self.G_matrix) % 2
        return ''.join(map(str, codeword))

    def decode(self, received: str) -> Tuple[str, int]:
        if self.H_matrix is None:
            raise RuntimeError("Parity check matrix not initialized")
        if len(received) != self.n:
            raise ValueError(f"Received word must be {self.n} bits, got {len(received)}")
            
        received_vector = np.array([int(bit) for bit in received], dtype=np.uint8)
        syndrome = tuple((received_vector @ self.H_matrix.T) % 2)
        
        errors_corrected = 0
        corrected_vector = received_vector.copy()
        
        if any(syndrome) and syndrome in self._syndrome_table:
            error_pos = self._syndrome_table[syndrome]
            corrected_vector[error_pos] ^= 1
            errors_corrected = 1
            
        message = corrected_vector[:self.k]
        return ''.join(map(str, message)), errors_corrected

    def get_parameters(self) -> Dict[str, Any]:
        if self.H_matrix is None:
            self._initialize_matrices()
        return {
            "n": self.n,
            "k": self.k,
            "H_matrix_list": self.H_matrix.tolist()
        }

    @classmethod
    def from_parameters(cls, params: Dict[str, Any]) -> 'LinearCodec':
        codec = cls(params["n"], params["k"])
        codec.H_matrix = np.array(params["H_matrix_list"], dtype=np.uint8)
        codec.G_matrix = None
        codec._build_syndrome_table()
        return codec