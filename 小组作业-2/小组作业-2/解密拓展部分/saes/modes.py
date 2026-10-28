"""三种加密封装：ASCII、多重加密、CBC 模式。"""
from dataclasses import dataclass
from .core import encrypt_block, decrypt_block
from .validators import validate_ascii

@dataclass(frozen=True)
class AsciiBlock:
    index: int
    plaintext_bytes: bytes
    ciphertext: int
    padded: bool
    @property
    def plaintext_hex(self) -> str: return self.plaintext_bytes.hex().upper()
    @property
    def ciphertext_hex(self) -> str: return f"{self.ciphertext:04X}"

@dataclass(frozen=True)
class AsciiEncryptionResult:
    original_length: int
    padding_length: int
    blocks: tuple[AsciiBlock, ...]
    ciphertext: bytes
    @property
    def ciphertext_hex(self) -> str: return self.ciphertext.hex().upper()
    @property
    def ciphertext_hex_spaced(self) -> str:
        return " ".join(self.ciphertext.hex().upper()[i:i+4] for i in range(0, len(self.ciphertext)*2, 4))

@dataclass(frozen=True)
class MultiEncryptionResult:
    mode: str
    key_parts: tuple[int, ...]
    stage_ciphertexts: tuple[int, ...]
    ciphertext: int
    @property
    def ciphertext_hex(self) -> str: return f"{self.ciphertext:04X}"
    @property
    def stage_labels(self) -> tuple[str, ...]:
        if self.mode == "double": return ("E_K1(P)", "E_K2(E_K1(P))")
        return ("E_K1(P)", "E_K2(E_K1(P))", "E_K3(E_K2(E_K1(P)))")

@dataclass(frozen=True)
class CBCResult:
    mode: str
    iv: int
    blocks: tuple[tuple[int, int], ...]
    final_ciphertext: bytes

def encrypt_ascii(text: str, key: int) -> AsciiEncryptionResult:
    if not isinstance(text, str): raise TypeError("ASCII 明文必须是字符串")
    if not text: raise ValueError("请输入至少 1 个 ASCII 字符。")
    validate_ascii(text)
    data = text.encode("ascii")
    padding_length = len(data) % 2
    padded = data + (b"\x00" * padding_length)
    blocks, ciphertext = [], bytearray()
    for offset in range(0, len(padded), 2):
        chunk = padded[offset:offset+2]
        block_value = (chunk[0] << 8) | chunk[1]
        encrypted = encrypt_block(block_value, key)
        ciphertext.extend(encrypted.to_bytes(2, "big"))
        blocks.append(AsciiBlock(offset//2, chunk, encrypted, padding_length == 1 and offset+2 == len(padded)))
    return AsciiEncryptionResult(len(data), padding_length, tuple(blocks), bytes(ciphertext))

def double_encrypt(plaintext: int, key: int) -> MultiEncryptionResult:
    _require_range(key, 32, "双重加密密钥")
    k1, k2 = (key >> 16) & 0xFFFF, key & 0xFFFF
    first = encrypt_block(plaintext, k1)
    second = encrypt_block(first, k2)
    return MultiEncryptionResult("double", (k1, k2), (first, second), second)

def triple_encrypt(plaintext: int, key: int) -> MultiEncryptionResult:
    _require_range(key, 48, "三重加密密钥")
    k1, k2, k3 = (key >> 32) & 0xFFFF, (key >> 16) & 0xFFFF, key & 0xFFFF
    first = encrypt_block(plaintext, k1)
    second = encrypt_block(first, k2)
    third = encrypt_block(second, k3)
    return MultiEncryptionResult("triple", (k1, k2, k3), (first, second, third), third)

def escape_bytes(data: bytes) -> str:
    parts = []
    for byte in data:
        if byte == 0x5C: parts.append("\\\\")
        elif 0x20 <= byte <= 0x7E: parts.append(chr(byte))
        else: parts.append(f"\\x{byte:02X}")
    return "".join(parts)

def _require_range(value: int, bits: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int): raise TypeError(f"{name}必须是整数")
    if not 0 <= value < (1 << bits): raise ValueError(f"{name}必须在 0..0x{(1 << bits) - 1:X} 之间")

def cbc_encrypt(plaintext: bytes, key: int, iv: int) -> CBCResult:
    if len(plaintext) % 2 != 0: raise ValueError("CBC 模式需要字节长度为偶数。")
    blocks, prev_cipher, out_bytes = [], iv, bytearray()
    for i in range(0, len(plaintext), 2):
        p_block = (plaintext[i] << 8) | plaintext[i+1]
        c_block = encrypt_block(p_block ^ prev_cipher, key)
        out_bytes.extend(c_block.to_bytes(2, "big"))
        blocks.append((p_block, c_block))
        prev_cipher = c_block
    return CBCResult("CBC", iv, tuple(blocks), bytes(out_bytes))

def cbc_decrypt(ciphertext: bytes, key: int, iv: int, tamper_index: int = -1) -> CBCResult:
    if len(ciphertext) % 2 != 0: raise ValueError("CBC 模式密文长度必须为偶数。")
    blocks, prev_cipher, out_bytes = [], iv, bytearray()
    c_list = [((ciphertext[i] << 8) | ciphertext[i+1]) for i in range(0, len(ciphertext), 2)]
    if 0 <= tamper_index < len(c_list): c_list[tamper_index] ^= 0x0001
    for c_block in c_list:
        p_block = decrypt_block(c_block, key) ^ prev_cipher
        out_bytes.extend(p_block.to_bytes(2, "big"))
        blocks.append((c_block, p_block))
        prev_cipher = c_block
    return CBCResult("CBC", iv, tuple(blocks), bytes(out_bytes))

def meet_in_the_middle_attack(plaintext: int, ciphertext: int) -> tuple[int, int] | None:
    middle_table = {}
    for k1 in range(0x10000):
        middle_table[encrypt_block(plaintext, k1)] = k1
    for k2 in range(0x10000):
        intermediate = decrypt_block(ciphertext, k2)
        if intermediate in middle_table:
            return (middle_table[intermediate], k2)
    return None