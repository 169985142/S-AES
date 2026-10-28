import sys
sys.path.append("..")
from saes import encrypt_block

def brute_force_saes(plain_hex, cipher_hex):
    plain = int(plain_hex, 16)
    target_cipher = int(cipher_hex, 16)
    found_keys = []
    print("===== 开始暴力破解 S-AES（16bit密钥，共65536种）=====")
    for key in range(0, 0xFFFF + 1):
        c = encrypt_block(plain, key)
        if c == target_cipher:
            found_keys.append(key)
            print(f"匹配成功！密钥十进制：{key:05d} | 16bit十六进制：{key:04X}")
    if len(found_keys) == 0:
        print("未找到匹配密钥")
    else:
        print(f"\n✅ 一共找到 {len(found_keys)} 个密钥（密钥碰撞）")
    return found_keys

if __name__ == "__main__":
    # 这里填UI上：明文(4位16进制)，密文(4位16进制)
    # 例子：brute_force_saes("6F6B", "XXXX")
    brute_force_saes("6F6B", "0738")
