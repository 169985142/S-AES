"""S-AES 的固定参数。

本模块只存放算法标准中不会变化的数据，避免把“魔法数字”散落在
加密流程和界面代码里。S 盒按 4 bit 输入索引直接查表。
"""

from typing import Final

# S-AES 的 16 项半字节替换表。索引 0x0..0xF 对应输出 0x9..0x7。
S_BOX: Final[tuple[int, ...]] = (
    0x9,
    0x4,
    0xA,
    0xB,
    0xD,
    0x1,
    0x8,
    0x5,
    0x6,
    0x2,
    0x0,
    0x3,
    0xC,
    0xE,
    0xF,
    0x7,
)

# 两轮密钥扩展使用的轮常量，分别对应 x^3 和 x^4 在 GF(2^4) 中的表示。
ROUND_CONSTANTS: Final[tuple[int, int]] = (0x80, 0x30)

BLOCK_BITS: Final[int] = 16
BLOCK_HEX_DIGITS: Final[int] = 4
DOUBLE_KEY_HEX_DIGITS: Final[int] = 8
TRIPLE_KEY_HEX_DIGITS: Final[int] = 12

# GF(2^4) 的本原多项式 x^4 + x + 1，低 4 位表示为 0x3。
GF_MODULUS: Final[int] = 0x3
