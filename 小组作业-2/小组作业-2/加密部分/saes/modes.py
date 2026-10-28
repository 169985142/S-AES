"""在教学模式之上的三种加密封装。

- ASCII：把字符串按 2 字节一组转换为 16 bit 分组；
- 双重：32 bit 密钥拆成 K1、K2，执行两次单分组加密；
- 三重：48 bit 密钥拆成 K1、K2、K3，执行三次单分组加密（EEE）。

本模块不提供解密，也不做填充移除；填充规则在结果对象中显式记录，
避免把“补零”伪装成无损编码。
"""

from dataclasses import dataclass

from .core import encrypt_block
from .validators import validate_ascii


@dataclass(frozen=True)
class AsciiBlock:
    """ASCII 加密中的一个 16 bit 分组。"""

    index: int
    plaintext_bytes: bytes
    ciphertext: int
    padded: bool

    @property
    def plaintext_hex(self) -> str:
        return self.plaintext_bytes.hex().upper()

    @property
    def ciphertext_hex(self) -> str:
        return f"{self.ciphertext:04X}"


@dataclass(frozen=True)
class AsciiEncryptionResult:
    """ASCII 字符串加密结果。"""

    original_length: int
    padding_length: int
    blocks: tuple[AsciiBlock, ...]
    ciphertext: bytes

    @property
    def ciphertext_hex(self) -> str:
        return self.ciphertext.hex().upper()

    @property
    def ciphertext_hex_spaced(self) -> str:
        return " ".join(
            self.ciphertext.hex().upper()[index : index + 4]
            for index in range(0, len(self.ciphertext) * 2, 4)
        )


@dataclass(frozen=True)
class MultiEncryptionResult:
    """双重或三重加密结果。"""

    mode: str
    key_parts: tuple[int, ...]
    stage_ciphertexts: tuple[int, ...]
    ciphertext: int

    @property
    def ciphertext_hex(self) -> str:
        return f"{self.ciphertext:04X}"

    @property
    def stage_labels(self) -> tuple[str, ...]:
        if self.mode == "double":
            return ("E_K1(P)", "E_K2(E_K1(P))")
        return ("E_K1(P)", "E_K2(E_K1(P))", "E_K3(E_K2(E_K1(P)))")


def encrypt_ascii(text: str, key: int) -> AsciiEncryptionResult:
    """按每 2 个字节一组加密 ASCII 字符串。

    字节序为大端：``b0 << 8 | b1``。如果字节数为奇数，末尾补一个
    ``0x00``，并在结果中记录 ``padding_length``。
    """

    if not isinstance(text, str):
        raise TypeError("ASCII 明文必须是字符串")
    if not text:
        raise ValueError("请输入至少 1 个 ASCII 字符。")
    validate_ascii(text)

    data = text.encode("ascii")
    padding_length = len(data) % 2
    padded = data + (b"\x00" * padding_length)
    blocks: list[AsciiBlock] = []
    ciphertext = bytearray()

    for offset in range(0, len(padded), 2):
        chunk = padded[offset : offset + 2]
        block_value = (chunk[0] << 8) | chunk[1]
        encrypted = encrypt_block(block_value, key)
        ciphertext.extend(encrypted.to_bytes(2, "big"))
        blocks.append(
            AsciiBlock(
                index=offset // 2,
                plaintext_bytes=chunk,
                ciphertext=encrypted,
                padded=padding_length == 1 and offset + 2 == len(padded),
            )
        )

    return AsciiEncryptionResult(
        original_length=len(data),
        padding_length=padding_length,
        blocks=tuple(blocks),
        ciphertext=bytes(ciphertext),
    )


def double_encrypt(plaintext: int, key: int) -> MultiEncryptionResult:
    """双重加密：C = E_K2(E_K1(P))，密钥为 K1||K2。"""

    _require_range(key, 32, "双重加密密钥")
    k1 = (key >> 16) & 0xFFFF
    k2 = key & 0xFFFF
    first = encrypt_block(plaintext, k1)
    second = encrypt_block(first, k2)
    return MultiEncryptionResult(
        mode="double",
        key_parts=(k1, k2),
        stage_ciphertexts=(first, second),
        ciphertext=second,
    )


def triple_encrypt(plaintext: int, key: int) -> MultiEncryptionResult:
    """三重加密：C = E_K3(E_K2(E_K1(P)))，密钥为 K1||K2||K3。"""

    _require_range(key, 48, "三重加密密钥")
    k1 = (key >> 32) & 0xFFFF
    k2 = (key >> 16) & 0xFFFF
    k3 = key & 0xFFFF
    first = encrypt_block(plaintext, k1)
    second = encrypt_block(first, k2)
    third = encrypt_block(second, k3)
    return MultiEncryptionResult(
        mode="triple",
        key_parts=(k1, k2, k3),
        stage_ciphertexts=(first, second, third),
        ciphertext=third,
    )


def escape_bytes(data: bytes) -> str:
    """把任意字节转成适合界面展示的单行转义文本。

    可打印 ASCII 原样保留；反斜杠写成 ``\\\\``；其余字节写成
    ``\\xNN``。这样即使密文是乱码，也不会把控制字符直接送进 Qt 控件。
    """

    parts: list[str] = []
    for byte in data:
        if byte == 0x5C:
            parts.append("\\\\")
        elif 0x20 <= byte <= 0x7E:
            parts.append(chr(byte))
        else:
            parts.append(f"\\x{byte:02X}")
    return "".join(parts)


def _require_range(value: int, bits: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name}必须是整数")
    if not 0 <= value < (1 << bits):
        raise ValueError(f"{name}必须在 0..0x{(1 << bits) - 1:X} 之间")
