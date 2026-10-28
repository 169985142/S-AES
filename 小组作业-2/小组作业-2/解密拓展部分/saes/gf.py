"""GF(2^4) 上的乘法。

S-AES 的列混合矩阵使用 1 和 4 两个系数，其中 4 表示多项式 x^2。
这里实现通用的 4 bit 有限域乘法，既服务列混合，也方便在开发手册中
解释“乘法不是普通整数乘法”。
"""

from .constants import GF_MODULUS


def gf_mul(left: int, right: int) -> int:
    """返回两个 GF(2^4) 元素的乘积。

    参数必须是 0..15 的整数。乘法采用“移位 + 条件异或”的俄式农民乘法：
    每轮根据 right 的最低位决定是否累加 left，然后对 left 做一次
    x 乘法；若 x 乘法溢出 4 bit，则异或本原多项式 0x3 进行约减。
    """

    if not isinstance(left, int) or not isinstance(right, int):
        raise TypeError("GF(2^4) 乘法的两个操作数都必须是整数")
    if not 0 <= left <= 0xF or not 0 <= right <= 0xF:
        raise ValueError("GF(2^4) 乘法的操作数必须在 0..15 之间")

    product = 0
    a, b = left, right
    for _ in range(4):
        if b & 1:
            product ^= a
        carry = a & 0x8
        a = (a << 1) & 0xF
        if carry:
            a ^= GF_MODULUS
        b >>= 1
    return product