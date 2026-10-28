"""S-AES 教学实现（仅加密方向）。

公开 API::

    from saes import encrypt_block, encrypt_ascii, double_encrypt, triple_encrypt

所有分组都是 16 bit 整数；ASCII 结果通过 ``AsciiEncryptionResult``
返回分组明细和补零信息。
"""

from .core import (
    EncryptionTrace,
    KeySchedule,
    TraceStep,
    encrypt_block,
    encrypt_block_with_trace,
    expand_key,
)
from .modes import (
    AsciiBlock,
    AsciiEncryptionResult,
    MultiEncryptionResult,
    double_encrypt,
    encrypt_ascii,
    escape_bytes,
    triple_encrypt,
)

__version__ = "1.0.0"

__all__ = [
    "AsciiBlock",
    "AsciiEncryptionResult",
    "EncryptionTrace",
    "KeySchedule",
    "MultiEncryptionResult",
    "TraceStep",
    "double_encrypt",
    "encrypt_ascii",
    "encrypt_block",
    "encrypt_block_with_trace",
    "escape_bytes",
    "expand_key",
    "triple_encrypt",
]
