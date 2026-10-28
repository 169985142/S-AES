"""S-AES 单分组加密与密钥扩展。

设计说明：
- 对外只公开 ``encrypt_block``、``encrypt_block_with_trace`` 和
  ``expand_key``；
- 所有内部变换都接收/返回 16 bit 整数，避免 GUI 与算法层共享字符串格式；
- 追踪版本与普通版本共用同一套变换，保证界面展示的中间状态就是
  实际加密使用的状态，而不是另写一份“演示逻辑”。
"""

from dataclasses import dataclass

from .constants import BLOCK_BITS, ROUND_CONSTANTS, S_BOX
from .gf import gf_mul


@dataclass(frozen=True)
class KeySchedule:
    """16 bit 主密钥扩展后的 6 个字与 3 个轮密钥。"""

    words: tuple[int, int, int, int, int, int]
    round_keys: tuple[int, int, int]

    @property
    def w0(self) -> int:
        return self.words[0]

    @property
    def w1(self) -> int:
        return self.words[1]

    @property
    def w2(self) -> int:
        return self.words[2]

    @property
    def w3(self) -> int:
        return self.words[3]

    @property
    def w4(self) -> int:
        return self.words[4]

    @property
    def w5(self) -> int:
        return self.words[5]


@dataclass(frozen=True)
class TraceStep:
    """一个可展示的中间状态。"""

    label: str
    value: int

    @property
    def hex_value(self) -> str:
        return f"{self.value:04X}"

    @property
    def binary_value(self) -> str:
        return f"{self.value:016b}"


@dataclass(frozen=True)
class EncryptionTrace:
    """一次完整加密的输入、密钥编排、中间状态和输出。"""

    plaintext: int
    key: int
    schedule: KeySchedule
    steps: tuple[TraceStep, ...]
    ciphertext: int

    @property
    def plaintext_hex(self) -> str:
        return f"{self.plaintext:04X}"

    @property
    def key_hex(self) -> str:
        return f"{self.key:04X}"

    @property
    def ciphertext_hex(self) -> str:
        return f"{self.ciphertext:04X}"


def _require_16bit(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} 必须是整数")
    if not 0 <= value < (1 << BLOCK_BITS):
        raise ValueError(f"{name} 必须在 0..0xFFFF 之间")


def _sub_nibbles(value: int) -> int:
    """对 16 bit 中的 4 个半字节分别查 S 盒。"""

    return (
        (S_BOX[(value >> 12) & 0xF] << 12)
        | (S_BOX[(value >> 8) & 0xF] << 8)
        | (S_BOX[(value >> 4) & 0xF] << 4)
        | S_BOX[value & 0xF]
    )


def _shift_rows(value: int) -> int:
    """交换状态矩阵第二行的两个半字节。

    16 bit 按“列优先”放入 2x2 状态矩阵：
        n0 n2
        n1 n3
    第二行左移一位后变成 n3 n1，因此整数层面的半字节顺序为
    n0 n3 n2 n1，即交换第 2 和第 4 个半字节。
    """

    n0 = (value >> 12) & 0xF
    n1 = (value >> 8) & 0xF
    n2 = (value >> 4) & 0xF
    n3 = value & 0xF
    return (n0 << 12) | (n3 << 8) | (n2 << 4) | n1


def _mix_columns(value: int) -> int:
    """对两个列分别左乘 S-AES 的列混合矩阵 [[1, 4], [4, 1]]。"""

    n0 = (value >> 12) & 0xF
    n1 = (value >> 8) & 0xF
    n2 = (value >> 4) & 0xF
    n3 = value & 0xF

    # 第一列 [n0, n1]；第二列 [n2, n3]。
    m0 = n0 ^ gf_mul(4, n1)
    m1 = gf_mul(4, n0) ^ n1
    m2 = n2 ^ gf_mul(4, n3)
    m3 = gf_mul(4, n2) ^ n3
    return (m0 << 12) | (m1 << 8) | (m2 << 4) | m3


def _rot_nibble(byte: int) -> int:
    """交换一个字节内的高、低半字节。"""

    return ((byte & 0x0F) << 4) | ((byte & 0xF0) >> 4)


def _sub_nibble_byte(byte: int) -> int:
    """对一个字节的高、低半字节分别做 S 盒替换。"""

    return (S_BOX[(byte >> 4) & 0xF] << 4) | S_BOX[byte & 0xF]


def _g(word: int, round_constant: int) -> int:
    """密钥扩展的 g 函数：RotNib → SubNib → XOR Rcon。"""

    return _sub_nibble_byte(_rot_nibble(word)) ^ round_constant


def expand_key(key: int) -> KeySchedule:
    """把 16 bit 主密钥扩展为 6 个 8 bit 字和 3 个轮密钥。"""

    _require_16bit(key, "密钥")
    w0 = (key >> 8) & 0xFF
    w1 = key & 0xFF
    w2 = w0 ^ _g(w1, ROUND_CONSTANTS[0])
    w3 = w2 ^ w1
    w4 = w2 ^ _g(w3, ROUND_CONSTANTS[1])
    w5 = w4 ^ w3
    words = (w0, w1, w2, w3, w4, w5)
    round_keys = (
        (w0 << 8) | w1,
        (w2 << 8) | w3,
        (w4 << 8) | w5,
    )
    return KeySchedule(words=words, round_keys=round_keys)


def encrypt_block_with_trace(plaintext: int, key: int) -> EncryptionTrace:
    """加密一个 16 bit 分组，并记录每个变换后的状态。

    加密结构：
        AddRoundKey(K0)
        SubNibbles → ShiftRows → MixColumns → AddRoundKey(K1)
        SubNibbles → ShiftRows → AddRoundKey(K2)

    最后一轮不执行 MixColumns，这是 S-AES 为了简化解密而采用的结构。
    """

    _require_16bit(plaintext, "明文")
    _require_16bit(key, "密钥")
    schedule = expand_key(key)
    k0, k1, k2 = schedule.round_keys
    steps: list[TraceStep] = []

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

    return EncryptionTrace(
        plaintext=plaintext,
        key=key,
        schedule=schedule,
        steps=tuple(steps),
        ciphertext=state,
    )


def encrypt_block(plaintext: int, key: int) -> int:
    """加密一个 16 bit 分组并返回 16 bit 密文。"""

    return encrypt_block_with_trace(plaintext, key).ciphertext
