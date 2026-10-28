"""S-AES 核心行为测试。

测试依据是教材标准向量和公开 API 契约，不依赖内部函数或中间变量。
"""

import pytest

from saes import encrypt_block, encrypt_block_with_trace, expand_key
from saes.validators import parse_hex


def test_standard_vector_a73b_6f6b_to_0738():
    """经典 ASCII 示例：E_A73B(6F6B) = 0738。"""

    assert encrypt_block(0x6F6B, 0xA73B) == 0x0738


def test_key_expansion_words_and_round_keys():
    """A73B 的六个字和三组轮密钥应与标准推导一致。"""

    schedule = expand_key(0xA73B)
    assert schedule.words == (0xA7, 0x3B, 0x1C, 0x27, 0x76, 0x51)
    assert schedule.round_keys == (0xA73B, 0x1C27, 0x7651)


def test_trace_ends_at_same_ciphertext_and_has_eight_steps():
    """追踪版与普通版必须产生相同结果，并覆盖 8 个标准步骤。"""

    trace = encrypt_block_with_trace(0x6F6B, 0xA73B)
    assert trace.ciphertext == 0x0738
    assert trace.ciphertext == encrypt_block(0x6F6B, 0xA73B)
    assert len(trace.steps) == 8
    assert trace.steps[0].value == 0x6F6B ^ 0xA73B
    assert trace.steps[-1].value == 0x0738


def test_encryption_is_deterministic():
    """同一输入和密钥重复执行必须得到相同密文。"""

    first = encrypt_block(0x1234, 0x5678)
    second = encrypt_block(0x1234, 0x5678)
    assert first == second


def test_single_bit_key_change_changes_ciphertext():
    """翻转密钥最低位应改变密文，避免把密钥参数忽略掉。"""

    base = encrypt_block(0x0000, 0x0000)
    changed = encrypt_block(0x0000, 0x0001)
    assert base != changed


@pytest.mark.parametrize("value", [-1, 0x10000])
def test_block_input_out_of_range_is_rejected(value):
    with pytest.raises(ValueError):
        encrypt_block(value, 0xA73B)


def test_parse_hex_accepts_common_formats():
    assert parse_hex("6F6B", 4, "明文") == 0x6F6B
    assert parse_hex("0x6F6B", 4, "明文") == 0x6F6B
    assert parse_hex("6F 6B", 4, "明文") == 0x6F6B
    assert parse_hex("6f-6b", 4, "明文") == 0x6F6B


@pytest.mark.parametrize("bad_value", ["", "6F6", "6F6B6", "GGGG"])
def test_parse_hex_rejects_invalid_values(bad_value):
    with pytest.raises(ValueError):
        parse_hex(bad_value, 4, "明文")
