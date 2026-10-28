"""ASCII、双重和三重加密的契约测试。"""

import pytest

from saes import (
    double_encrypt,
    encrypt_ascii,
    encrypt_block,
    escape_bytes,
    triple_encrypt,
)


def test_ascii_even_length_without_padding():
    result = encrypt_ascii("abcd", 0xA73B)
    assert result.original_length == 4
    assert result.padding_length == 0
    assert len(result.blocks) == 2
    assert all(not block.padded for block in result.blocks)
    assert result.ciphertext.hex().upper() == (
        f"{encrypt_block(0x6162, 0xA73B):04X}"
        f"{encrypt_block(0x6364, 0xA73B):04X}"
    )


def test_ascii_odd_length_pads_last_block_with_zero():
    result = encrypt_ascii("abc", 0xA73B)
    assert result.original_length == 3
    assert result.padding_length == 1
    assert len(result.blocks) == 2
    assert result.blocks[-1].plaintext_bytes == b"c\x00"
    assert result.blocks[-1].padded is True
    assert result.ciphertext.hex().upper() == (
        f"{encrypt_block(0x6162, 0xA73B):04X}"
        f"{encrypt_block(0x6300, 0xA73B):04X}"
    )


def test_ascii_example_ok_matches_standard_vector():
    result = encrypt_ascii("ok", 0xA73B)
    assert result.ciphertext_hex == "0738"


def test_ascii_rejects_empty_and_non_ascii():
    with pytest.raises(ValueError):
        encrypt_ascii("", 0xA73B)
    with pytest.raises(ValueError):
        encrypt_ascii("中", 0xA73B)


def test_double_encryption_is_two_sequential_blocks():
    key = 0x2D55A73B
    result = double_encrypt(0x6F6B, key)
    expected = encrypt_block(encrypt_block(0x6F6B, 0x2D55), 0xA73B)
    assert result.mode == "double"
    assert result.key_parts == (0x2D55, 0xA73B)
    assert result.ciphertext == expected
    assert result.stage_ciphertexts == (encrypt_block(0x6F6B, 0x2D55), expected)


def test_triple_encryption_is_three_sequential_blocks():
    key = 0x2D55A73B1C27
    result = triple_encrypt(0x6F6B, key)
    first = encrypt_block(0x6F6B, 0x2D55)
    second = encrypt_block(first, 0xA73B)
    third = encrypt_block(second, 0x1C27)
    assert result.mode == "triple"
    assert result.key_parts == (0x2D55, 0xA73B, 0x1C27)
    assert result.ciphertext == third
    assert result.stage_ciphertexts == (first, second, third)


def test_escape_bytes_handles_printable_and_control_bytes():
    assert escape_bytes(b"ok") == "ok"
    assert escape_bytes(b"\x00\xff\\") == "\\x00\\xFF\\\\"
