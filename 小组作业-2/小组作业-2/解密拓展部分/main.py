"""S-AES 加密实验台启动入口。

用法：
    python main.py              # 打开 GUI
    python main.py --self-test  # 运行标准向量自检后退出
    python main.py --help       # 查看参数
"""

from __future__ import annotations

import argparse
import os
import sys

# 针对部分 Windows 环境找不到 Qt 插件的问题，强制指定插件路径
try:
    from PyQt5.QtCore import QLibraryInfo
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = QLibraryInfo.location(QLibraryInfo.PluginsPath)
except ImportError:
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="S-AES 加密实验台",
        description="S-AES 教学实现：基础加密、ASCII 加密、双重/三重加密。",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="运行标准向量和组合关系自检，不打开 GUI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="S-AES 加密实验台 1.0.0",
    )
    return parser


def run_self_test() -> int:
    """在没有 GUI 的情况下验证算法核心和三种扩展。"""
    from saes import (
        double_encrypt,
        encrypt_ascii,
        encrypt_block,
        expand_key,
        triple_encrypt,
    )

    checks: list[tuple[str, bool, str]] = []
    schedule = expand_key(0xA73B)
    expected_words = (0xA7, 0x3B, 0x1C, 0x27, 0x76, 0x51)
    checks.append(
        (
            "密钥扩展 A73B → A7 3B 1C 27 76 51",
            schedule.words == expected_words,
            " ".join(f"{word:02X}" for word in schedule.words),
        )
    )

    ciphertext = encrypt_block(0x6F6B, 0xA73B)
    checks.append(
        ("标准向量 E_A73B(6F6B) = 0738", ciphertext == 0x0738, f"{ciphertext:04X}")
    )

    ascii_result = encrypt_ascii("ok", 0xA73B)
    checks.append(
        ("ASCII 示例 “ok” → 0738", ascii_result.ciphertext_hex == "0738", ascii_result.ciphertext_hex)
    )

    double_result = double_encrypt(0x6F6B, 0x2D55A73B)
    double_expected = encrypt_block(encrypt_block(0x6F6B, 0x2D55), 0xA73B)
    checks.append(
        (
            "双重加密 = E_K2(E_K1(P))",
            double_result.ciphertext == double_expected,
            f"{double_result.ciphertext:04X}",
        )
    )

    triple_result = triple_encrypt(0x6F6B, 0x2D55A73B1C27)
    triple_expected = encrypt_block(
        encrypt_block(encrypt_block(0x6F6B, 0x2D55), 0xA73B), 0x1C27
    )
    checks.append(
        (
            "三重加密 = E_K3(E_K2(E_K1(P)))",
            triple_result.ciphertext == triple_expected,
            f"{triple_result.ciphertext:04X}",
        )
    )

    print("S-AES 自检")
    print("-" * 58)
    all_ok = True
    for name, ok, value in checks:
        status = "通过" if ok else "失败"
        all_ok = all_ok and ok
        print(f"[{status}] {name}  (实际: {value})")
    print("-" * 58)
    print("结果：全部通过" if all_ok else "结果：存在失败项，请检查实现")
    return 0 if all_ok else 1


def run_gui() -> int:
    """延迟导入 PyQt5，保证 --self-test 在没有 GUI 依赖时也可运行。"""
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        print(
            "错误：未找到 PyQt5。请先运行 `python -m pip install -r requirements.txt`。",
            file=sys.stderr,
        )
        return 2

    from saes.gui.app import MainWindow
    from saes.gui.theme import APP_STYLESHEET, UI_FONT

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication([sys.argv[0]])
    app.setApplicationName("S-AES 加密实验台")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    app.setFont(QFont(UI_FONT, 10))
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    return app.exec_()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())