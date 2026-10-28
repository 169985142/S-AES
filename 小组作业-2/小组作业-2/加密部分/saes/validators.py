"""输入解析与校验。

GUI 收到的都是字符串，算法层只接受整数。本模块负责把用户输入
规范化，并把错误转成可以直接展示给用户的中文消息。
"""

import re
import string


_HEX_CHARS = set(string.hexdigits)
_SEPARATOR_PATTERN = re.compile(r"[\s_:\-]+")
_PREFIX_PATTERN = re.compile(r"^0[xX]")


def parse_hex(text: str, digits: int, field_name: str) -> int:
    """把十六进制字符串解析为整数。

    允许空格、下划线、冒号、短横线和 ``0x`` 前缀，例如：
    ``6F6B``、``0x6F6B``、``6F 6B`` 都表示同一个 16 bit 值。

    参数:
        text: 用户输入的原始字符串。
        digits: 要求的十六进制位数（4/8/12）。
        field_name: 错误消息中使用的字段名。

    异常:
        ValueError: 输入为空、位数不符或包含非法字符。
    """

    if text is None:
        raise ValueError(f"{field_name}不能为空。")

    normalized = _SEPARATOR_PATTERN.sub("", text.strip())
    normalized = _PREFIX_PATTERN.sub("", normalized)

    if not normalized:
        raise ValueError(f"{field_name}不能为空。")
    if len(normalized) != digits:
        raise ValueError(
            f"{field_name}必须是 {digits} 位十六进制数，"
            f"当前为 {len(normalized)} 位：{_safe_preview(text)}"
        )
    if any(char not in _HEX_CHARS for char in normalized):
        raise ValueError(
            f"{field_name}只能包含 0-9、A-F，当前输入为：{_safe_preview(text)}"
        )
    return int(normalized, 16)


def validate_ascii(text: str) -> None:
    """检查文本是否全部位于 ASCII 范围（0x00..0x7F）。"""

    for index, char in enumerate(text):
        if ord(char) > 0x7F:
            raise ValueError(
                f"第 {index + 1} 个字符“{char}”不是 ASCII 字符；"
                "本关只支持 0x00–0x7F 范围内的字符。"
            )


def _safe_preview(text: str, limit: int = 32) -> str:
    """生成短预览，避免用户粘贴超长内容时错误消息撑破界面。"""

    compact = text.strip()
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "…"
