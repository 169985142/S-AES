"""S-AES 单分组加密、解密与密钥扩展。"""
from dataclasses import dataclass
from .constants import BLOCK_BITS, ROUND_CONSTANTS, S_BOX, INV_S_BOX
from .gf import gf_mul

@dataclass(frozen=True)
class KeySchedule:
    words: tuple[int, int, int, int, int, int]
    round_keys: tuple[int, int, int]

    @property
    def w0(self) -> int: return self.words[0]
    @property
    def w1(self) -> int: return self.words[1]
    @property
    def w2(self) -> int: return self.words[2]
    @property
    def w3(self) -> int: return self.words[3]
    @property
    def w4(self) -> int: return self.words[4]
    @property
    def w5(self) -> int: return self.words[5]

@dataclass(frozen=True)
class TraceStep:
    label: str
    value: int
    @property
    def hex_value(self) -> str: return f"{self.value:04X}"
    @property
    def binary_value(self) -> str: return f"{self.value:016b}"

@dataclass(frozen=True)
class EncryptionTrace:
    plaintext: int
    key: int
    schedule: KeySchedule
    steps: tuple[TraceStep, ...]
    ciphertext: int
    @property
    def plaintext_hex(self) -> str: return f"{self.plaintext:04X}"
    @property
    def key_hex(self) -> str: return f"{self.key:04X}"
    @property
    def ciphertext_hex(self) -> str: return f"{self.ciphertext:04X}"

def _require_16bit(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} 必须是整数")
    if not 0 <= value < (1 << BLOCK_BITS):
        raise ValueError(f"{name} 必须在 0..0xFFFF 之间")

def _sub_nibbles(value: int) -> int:
    return ((S_BOX[(value >> 12) & 0xF] << 12) | (S_BOX[(value >> 8) & 0xF] << 8)
            | (S_BOX[(value >> 4) & 0xF] << 4) | S_BOX[value & 0xF])

def _inv_sub_nibbles(value: int) -> int:
    return ((INV_S_BOX[(value >> 12) & 0xF] << 12) | (INV_S_BOX[(value >> 8) & 0xF] << 8)
            | (INV_S_BOX[(value >> 4) & 0xF] << 4) | INV_S_BOX[value & 0xF])

def _shift_rows(value: int) -> int:
    n0, n1, n2, n3 = (value >> 12) & 0xF, (value >> 8) & 0xF, (value >> 4) & 0xF, value & 0xF
    return (n0 << 12) | (n3 << 8) | (n2 << 4) | n1

def _inv_shift_rows(value: int) -> int:
    return _shift_rows(value)

def _mix_columns(value: int) -> int:
    n0, n1, n2, n3 = (value >> 12) & 0xF, (value >> 8) & 0xF, (value >> 4) & 0xF, value & 0xF
    m0, m1 = n0 ^ gf_mul(4, n1), gf_mul(4, n0) ^ n1
    m2, m3 = n2 ^ gf_mul(4, n3), gf_mul(4, n2) ^ n3
    return (m0 << 12) | (m1 << 8) | (m2 << 4) | m3

def _inv_mix_columns(value: int) -> int:
    n0, n1, n2, n3 = (value >> 12) & 0xF, (value >> 8) & 0xF, (value >> 4) & 0xF, value & 0xF
    m0, m1 = gf_mul(9, n0) ^ gf_mul(2, n1), gf_mul(2, n0) ^ gf_mul(9, n1)
    m2, m3 = gf_mul(9, n2) ^ gf_mul(2, n3), gf_mul(2, n2) ^ gf_mul(9, n3)
    return (m0 << 12) | (m1 << 8) | (m2 << 4) | m3

def _rot_nibble(byte: int) -> int: return ((byte & 0x0F) << 4) | ((byte & 0xF0) >> 4)
def _sub_nibble_byte(byte: int) -> int: return (S_BOX[(byte >> 4) & 0xF] << 4) | S_BOX[byte & 0xF]
def _g(word: int, round_constant: int) -> int: return _sub_nibble_byte(_rot_nibble(word)) ^ round_constant

def expand_key(key: int) -> KeySchedule:
    _require_16bit(key, "密钥")
    w0, w1 = (key >> 8) & 0xFF, key & 0xFF
    w2 = w0 ^ _g(w1, ROUND_CONSTANTS[0])
    w3 = w2 ^ w1
    w4 = w2 ^ _g(w3, ROUND_CONSTANTS[1])
    w5 = w4 ^ w3
    words = (w0, w1, w2, w3, w4, w5)
    round_keys = ((w0 << 8) | w1, (w2 << 8) | w3, (w4 << 8) | w5)
    return KeySchedule(words=words, round_keys=round_keys)

def encrypt_block_with_trace(plaintext: int, key: int) -> EncryptionTrace:
    _require_16bit(plaintext, "明文")
    _require_16bit(key, "密钥")
    schedule = expand_key(key)
    k0, k1, k2 = schedule.round_keys
    steps = []

    state = plaintext ^ k0
    steps.append(TraceStep("初始轮密钥加 (P ⊕ K0)", state))
    state = _sub_nibbles(state)
    steps.append(TraceStep("第 1 轮 · 半字节替换", state))
    state = _shift_rows(state)
    steps.append(TraceStep("第 1 轮 · 行移位", state))
    state = _mix_columns(state)
    steps.append(TraceStep("第 1 轮 · 列混合", state))
    state ^= k1
    steps.append(TraceStep("第 1 轮 · 轮密钥加 (⊕ K1)", state))
    state = _sub_nibbles(state)
    steps.append(TraceStep("第 2 轮 · 半字节替换", state))
    state = _shift_rows(state)
    steps.append(TraceStep("第 2 轮 · 行移位", state))
    state ^= k2
    steps.append(TraceStep("第 2 轮 · 轮密钥加 (⊕ K2)", state))

    return EncryptionTrace(plaintext=plaintext, key=key, schedule=schedule, steps=tuple(steps), ciphertext=state)

def encrypt_block(plaintext: int, key: int) -> int:
    return encrypt_block_with_trace(plaintext, key).ciphertext

def decrypt_block_with_trace(ciphertext: int, key: int) -> EncryptionTrace:
    _require_16bit(ciphertext, "密文")
    _require_16bit(key, "密钥")
    schedule = expand_key(key)
    k0, k1, k2 = schedule.round_keys
    steps = []

    state = ciphertext ^ k2
    steps.append(TraceStep("初始轮密钥加 (C ⊕ K2)", state))
    state = _inv_shift_rows(state)
    steps.append(TraceStep("第 1 轮 · 逆行移位", state))
    state = _inv_sub_nibbles(state)
    steps.append(TraceStep("第 1 轮 · 逆半字节替换", state))
    state ^= k1
    steps.append(TraceStep("第 1 轮 · 轮密钥加 (⊕ K1)", state))
    state = _inv_mix_columns(state)
    steps.append(TraceStep("第 1 轮 · 逆列混合", state))
    state = _inv_shift_rows(state)
    steps.append(TraceStep("第 2 轮 · 逆行移位", state))
    state = _inv_sub_nibbles(state)
    steps.append(TraceStep("第 2 轮 · 逆半字节替换", state))
    state ^= k0
    steps.append(TraceStep("第 2 轮 · 轮密钥加 (⊕ K0)", state))

    return EncryptionTrace(plaintext=ciphertext, key=key, schedule=schedule, steps=tuple(steps), ciphertext=state)

def decrypt_block(ciphertext: int, key: int) -> int:
    return decrypt_block_with_trace(ciphertext, key).ciphertext