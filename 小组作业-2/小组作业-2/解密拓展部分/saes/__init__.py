"""S-AES 教学实现。"""
from .core import (
    EncryptionTrace, KeySchedule, TraceStep,
    encrypt_block, encrypt_block_with_trace, decrypt_block, decrypt_block_with_trace,
    expand_key,
)
from .modes import (
    AsciiBlock, AsciiEncryptionResult, MultiEncryptionResult, CBCResult,
    double_encrypt, encrypt_ascii, escape_bytes, triple_encrypt,
    cbc_encrypt, cbc_decrypt, meet_in_the_middle_attack,
)

__version__ = "1.0.0"

__all__ = [
    "AsciiBlock", "AsciiEncryptionResult", "EncryptionTrace", "KeySchedule",
    "MultiEncryptionResult", "TraceStep", "CBCResult",
    "double_encrypt", "encrypt_ascii", "encrypt_block", "encrypt_block_with_trace",
    "escape_bytes", "expand_key", "triple_encrypt",
    "decrypt_block", "decrypt_block_with_trace", "cbc_encrypt", "cbc_decrypt",
    "meet_in_the_middle_attack"
]