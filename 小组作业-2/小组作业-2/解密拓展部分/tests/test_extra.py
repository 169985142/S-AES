import pytest
from saes import (
    encrypt_block, decrypt_block,
    cbc_encrypt, cbc_decrypt, meet_in_the_middle_attack,
    double_encrypt
)

def test_decrypt_standard_vector():
    assert decrypt_block(0x0738, 0xA73B) == 0x6F6B
    assert decrypt_block(encrypt_block(0x1234, 0xABCD), 0xABCD) == 0x1234

def test_cbc_mode():
    key, iv = 0xA73B, 0x1234
    plaintext = b"okhello!" # 8字节
    enc = cbc_encrypt(plaintext, key, iv)
    dec = cbc_decrypt(enc.final_ciphertext, key, iv)
    dec_bytes = b"".join(p.to_bytes(2, 'big') for _, p in dec.blocks)
    assert dec_bytes == plaintext

def test_cbc_tampering():
    key, iv = 0xA73B, 0x0000
    plaintext = b"abcdefgh"
    enc = cbc_encrypt(plaintext, key, iv)
    # 篡改第 0 个分组（最低位异或），解密后第 0 组内容改变，第 1 组也受影响
    dec = cbc_decrypt(enc.final_ciphertext, key, iv, tamper_index=0)
    dec_bytes = b"".join(p.to_bytes(2, 'big') for _, p in dec.blocks)
    assert dec_bytes != plaintext

def test_mitm_attack():
    k1, k2 = 0x2D55, 0xA73B
    p = 0x6F6B
    c = double_encrypt(p, (k1 << 16) | k2).ciphertext
    res = meet_in_the_middle_attack(p, c)


def test_mitm_attack():
    k1, k2 = 0x2D55, 0xA73B
    p = 0x6F6B
    c = double_encrypt(p, (k1 << 16) | k2).ciphertext
    res = meet_in_the_middle_attack(p, c)

    assert res is not None
    # 修改这里：验证破解出来的 K1, K2 能成功将明文加密为密文即可
    forged_k1, forged_k2 = res
    assert double_encrypt(p, (forged_k1 << 16) | forged_k2).ciphertext == c