"""三个加密功能页：基础加密、ASCII 加密、多重加密。"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core import EncryptionTrace, encrypt_block_with_trace
from ..modes import (
    AsciiEncryptionResult,
    MultiEncryptionResult,
    double_encrypt,
    encrypt_ascii,
    escape_bytes,
    triple_encrypt,
)
from ..validators import parse_hex
from .widgets import Card, DataTable, ResultPanel, ScrollPage, make_button


class BaseTab(ScrollPage):
    """所有功能页的公共骨架：滚动容器、状态信号和错误提示。"""

    status_message = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        raise NotImplementedError

    def trigger_encrypt(self) -> None:
        """供主窗口的 Ctrl+Enter 快捷键调用。"""

    def clear_inputs(self) -> None:
        """供主窗口的 Ctrl+L 快捷键调用。"""

    def _notify(self, message: str) -> None:
        self.status_message.emit(message)

    def _make_error_label(self) -> QLabel:
        label = QLabel("")
        label.setObjectName("ErrorLabel")
        label.setTextFormat(Qt.PlainText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.hide()
        return label

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()

    def _hide_error(self) -> None:
        self.error_label.clear()
        self.error_label.hide()


def _add_field(
    grid: QGridLayout,
    row: int,
    label_text: str,
    field: QWidget,
    hint_text: str = "",
) -> int:
    """向表单添加“标签 + 输入框 + 提示”，返回下一行行号。"""

    label = QLabel(label_text)
    label.setObjectName("FieldLabel")
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    grid.addWidget(label, row, 0)

    grid.addWidget(field, row, 1)

    next_row = row + 1
    if hint_text:
        hint = QLabel(hint_text)
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        grid.addWidget(hint, next_row, 1)
        next_row += 1
    return next_row


def _make_form_grid() -> QGridLayout:
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(7)
    grid.setColumnMinimumWidth(0, 132)
    grid.setColumnStretch(1, 1)
    return grid


def _make_button_row(*buttons) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(10)
    for button in buttons:
        row.addWidget(button)
    row.addStretch(1)
    return row


class BasicTab(BaseTab):
    """第 1 关：16 bit 明文 + 16 bit 密钥的 GUI 加密。"""

    def _build(self) -> None:
        intro = QLabel(
            "输入 16 bit 明文和 16 bit 密钥，执行两轮 S-AES 加密。"
            "页面同时展示密钥扩展和 8 个中间状态，便于对照教材附录 D 检查每一步。"
        )
        intro.setObjectName("Hint")
        intro.setWordWrap(True)
        self.page_layout.addWidget(intro)

        input_card = Card("输入", "十六进制，允许 0x 前缀、空格和大小写混用。")
        grid = _make_form_grid()

        self.plaintext_edit = QLineEdit()
        self.plaintext_edit.setObjectName("MonoInput")
        self.plaintext_edit.setPlaceholderText("例如 6F6B")
        self.plaintext_edit.setMaxLength(16)
        self.plaintext_edit.setAccessibleName("16 bit 明文")
        row = _add_field(
            grid, 0, "明文 P（16 bit）", self.plaintext_edit, "4 位十六进制，例如 6F6B。"
        )

        self.key_edit = QLineEdit()
        self.key_edit.setObjectName("MonoInput")
        self.key_edit.setPlaceholderText("例如 A73B")
        self.key_edit.setMaxLength(16)
        self.key_edit.setAccessibleName("16 bit 密钥")
        _add_field(
            grid, row, "密钥 K（16 bit）", self.key_edit, "4 位十六进制，例如 A73B。"
        )

        self.error_label = self._make_error_label()
        input_card.body.addLayout(grid)
        input_card.body.addWidget(self.error_label)

        self.encrypt_button = make_button("加密", "PrimaryButton", "执行 S-AES 加密")
        self.example_button = make_button("载入标准示例", "SecondaryButton", "填入 6F6B / A73B")
        self.clear_button = make_button("清空", "GhostButton", "清空输入和结果")
        self.encrypt_button.clicked.connect(self._encrypt)
        self.example_button.clicked.connect(self.load_example)
        self.clear_button.clicked.connect(self.clear_inputs)
        input_card.body.addLayout(
            _make_button_row(self.encrypt_button, self.example_button, self.clear_button)
        )
        self.page_layout.addWidget(input_card)

        result_row = QHBoxLayout()
        result_row.setSpacing(16)

        result_card = Card("加密结果", "输出为 16 bit 密文。")
        self.result_panel = ResultPanel("密文 C", on_copy=self._notify)
        result_card.body.addWidget(self.result_panel)
        result_row.addWidget(result_card, 1)

        schedule_card = Card("密钥编排", "w0–w5 为 8 bit 字，K0/K1/K2 为 16 bit 轮密钥。")
        self.schedule_table = DataTable(("项目", "值"), mono_columns=(1,))
        self.schedule_table.setMinimumHeight(258)
        schedule_card.body.addWidget(self.schedule_table)
        result_row.addWidget(schedule_card, 1)
        self.page_layout.addLayout(result_row)

        trace_card = Card(
            "中间状态",
            "状态矩阵按列优先存储；行移位交换第 2、4 个半字节；最后一轮不做列混合。",
        )
        self.trace_table = DataTable(
            ("步骤", "十六进制", "二进制"), mono_columns=(1, 2)
        )
        self.trace_table.setMinimumHeight(294)
        trace_card.body.addWidget(self.trace_table)
        self.page_layout.addWidget(trace_card)
        self.page_layout.addStretch(1)

        self.load_example()

    def trigger_encrypt(self) -> None:
        self._encrypt()

    def _encrypt(self) -> None:
        self._hide_error()
        try:
            plaintext = parse_hex(self.plaintext_edit.text(), 4, "明文")
            key = parse_hex(self.key_edit.text(), 4, "密钥")
            trace = encrypt_block_with_trace(plaintext, key)
        except (TypeError, ValueError) as exc:
            self._show_error(str(exc))
            self.result_panel.clear_result()
            self.schedule_table.clear_rows()
            self.trace_table.clear_rows()
            self._notify("基础加密输入有误，请检查提示")
            return

        self._render_trace(trace)
        self._notify(
            f"基础加密完成：{trace.plaintext_hex} → {trace.ciphertext_hex}"
        )

    def _render_trace(self, trace: EncryptionTrace) -> None:
        self.result_panel.set_result(
            trace.ciphertext_hex,
            f"P = {trace.plaintext_hex}　K = {trace.key_hex}　2 轮",
        )
        self.trace_table.set_rows(
            [(step.label, step.hex_value, step.binary_value) for step in trace.steps]
        )

        schedule = trace.schedule
        k0, k1, k2 = schedule.round_keys
        rows = [
            ("K0 = w0 || w1", f"{k0:04X}"),
            ("K1 = w2 || w3", f"{k1:04X}"),
            ("K2 = w4 || w5", f"{k2:04X}"),
            ("w0", f"{schedule.w0:02X}"),
            ("w1", f"{schedule.w1:02X}"),
            ("w2", f"{schedule.w2:02X}"),
            ("w3", f"{schedule.w3:02X}"),
            ("w4", f"{schedule.w4:02X}"),
            ("w5", f"{schedule.w5:02X}"),
        ]
        self.schedule_table.set_rows(rows)

    def load_example(self) -> None:
        self.plaintext_edit.setText("6F6B")
        self.key_edit.setText("A73B")
        self._encrypt()

    def clear_inputs(self) -> None:
        self.plaintext_edit.clear()
        self.key_edit.clear()
        self.result_panel.clear_result()
        self.schedule_table.clear_rows()
        self.trace_table.clear_rows()
        self._hide_error()
        self.plaintext_edit.setFocus()
        self._notify("已清空基础加密页面")


class AsciiTab(BaseTab):
    """第 3 关：ASCII 字符串按 2 Bytes 分组加密。"""

    def _build(self) -> None:
        self._last_result: Optional[AsciiEncryptionResult] = None

        intro = QLabel(
            "ASCII 字符串按每 2 个字节一组转换为 16 bit 分组，再逐组加密。"
            "字节数为奇数时末尾补 1 字节 0x00；密文可能不可打印，因此以转义形式和十六进制展示。"
        )
        intro.setObjectName("Hint")
        intro.setWordWrap(True)
        self.page_layout.addWidget(intro)

        input_card = Card("输入", "仅支持 ASCII（0x00–0x7F）；换行和制表符也属于 ASCII。")
        grid = _make_form_grid()

        self.text_edit = QPlainTextEdit()
        self.text_edit.setObjectName("MonoInput")
        self.text_edit.setPlaceholderText("例如：ok")
        self.text_edit.setFixedHeight(96)
        self.text_edit.setTabChangesFocus(True)
        self.text_edit.setAccessibleName("ASCII 明文")
        row = _add_field(
            grid, 0, "明文（ASCII）", self.text_edit, "每 2 个字符/字节一组；奇数长度末组补 0x00。"
        )

        self.key_edit = QLineEdit()
        self.key_edit.setObjectName("MonoInput")
        self.key_edit.setPlaceholderText("例如 A73B")
        self.key_edit.setMaxLength(16)
        self.key_edit.setAccessibleName("ASCII 加密密钥")
        _add_field(
            grid, row, "密钥 K（16 bit）", self.key_edit, "4 位十六进制，例如 A73B。"
        )

        self.error_label = self._make_error_label()
        input_card.body.addLayout(grid)
        input_card.body.addWidget(self.error_label)

        self.encrypt_button = make_button("加密", "PrimaryButton", "加密 ASCII 字符串")
        self.example_button = make_button("载入示例 ok", "SecondaryButton", "填入 ok / A73B")
        self.clear_button = make_button("清空", "GhostButton", "清空输入和结果")
        self.encrypt_button.clicked.connect(self._encrypt)
        self.example_button.clicked.connect(self.load_example)
        self.clear_button.clicked.connect(self.clear_inputs)
        input_card.body.addLayout(
            _make_button_row(self.encrypt_button, self.example_button, self.clear_button)
        )
        self.page_layout.addWidget(input_card)

        result_card = Card("加密结果", "转义 ASCII 便于观察乱码；十六进制便于复制和比对。")
        panel = QFrame()
        panel.setObjectName("ResultPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(7)

        escaped_header = QHBoxLayout()
        escaped_title = QLabel("密文（转义 ASCII）")
        escaped_title.setObjectName("ResultTitle")
        escaped_header.addWidget(escaped_title)
        escaped_header.addStretch(1)
        self.copy_escaped_button = make_button("复制", "GhostButton", "复制转义 ASCII")
        self.copy_escaped_button.setEnabled(False)
        self.copy_escaped_button.clicked.connect(self._copy_escaped)
        escaped_header.addWidget(self.copy_escaped_button)
        panel_layout.addLayout(escaped_header)

        self.escaped_label = QLabel("—")
        self.escaped_label.setObjectName("AsciiValue")
        self.escaped_label.setTextFormat(Qt.PlainText)
        self.escaped_label.setWordWrap(True)
        self.escaped_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.escaped_label.setMinimumHeight(34)
        panel_layout.addWidget(self.escaped_label)

        hex_header = QHBoxLayout()
        hex_title = QLabel("十六进制")
        hex_title.setObjectName("ResultTitle")
        hex_header.addWidget(hex_title)
        hex_header.addStretch(1)
        self.copy_hex_button = make_button("复制十六进制", "GhostButton", "复制带空格的十六进制")
        self.copy_hex_button.setEnabled(False)
        self.copy_hex_button.clicked.connect(self._copy_hex)
        hex_header.addWidget(self.copy_hex_button)
        panel_layout.addLayout(hex_header)

        self.hex_edit = QPlainTextEdit()
        self.hex_edit.setObjectName("ReadOnlyHex")
        self.hex_edit.setReadOnly(True)
        self.hex_edit.setFixedHeight(64)
        self.hex_edit.setPlaceholderText("加密后显示")
        panel_layout.addWidget(self.hex_edit)

        self.padding_label = QLabel("等待输入")
        self.padding_label.setObjectName("ResultMeta")
        self.padding_label.setTextFormat(Qt.PlainText)
        self.padding_label.setWordWrap(True)
        panel_layout.addWidget(self.padding_label)

        result_card.body.addWidget(panel)
        self.page_layout.addWidget(result_card)

        block_card = Card("分组明细", "每行对应一个 16 bit 分组；末组补零会单独标记。")
        self.block_table = DataTable(
            ("#", "明文字节", "明文 hex", "密文 hex", "备注"),
            mono_columns=(1, 2, 3),
        )
        self.block_table.setMinimumHeight(190)
        block_card.body.addWidget(self.block_table)
        self.page_layout.addWidget(block_card)
        self.page_layout.addStretch(1)

        self.load_example()

    def trigger_encrypt(self) -> None:
        self._encrypt()

    def _encrypt(self) -> None:
        self._hide_error()
        try:
            key = parse_hex(self.key_edit.text(), 4, "密钥")
            result = encrypt_ascii(self.text_edit.toPlainText(), key)
        except (TypeError, ValueError) as exc:
            self._show_error(str(exc))
            self._last_result = None
            self.escaped_label.setText("—")
            self.hex_edit.clear()
            self.padding_label.setText("输入无效，未执行加密")
            self.block_table.clear_rows()
            self.copy_escaped_button.setEnabled(False)
            self.copy_hex_button.setEnabled(False)
            self._notify("ASCII 加密输入有误，请检查提示")
            return

        self._last_result = result
        self.escaped_label.setText(escape_bytes(result.ciphertext))
        self.hex_edit.setPlainText(result.ciphertext_hex_spaced)
        self.copy_escaped_button.setEnabled(True)
        self.copy_hex_button.setEnabled(True)

        if result.padding_length:
            padding_text = (
                f"原始 {result.original_length} 字节，末组补 1 字节 0x00，"
                f"共 {len(result.blocks)} 组。"
            )
        else:
            padding_text = (
                f"原始 {result.original_length} 字节，无需补零，"
                f"共 {len(result.blocks)} 组。"
            )
        self.padding_label.setText(padding_text)

        rows = []
        for block in result.blocks:
            rows.append(
                (
                    str(block.index + 1),
                    escape_bytes(block.plaintext_bytes),
                    block.plaintext_hex,
                    block.ciphertext_hex,
                    "末组补 0x00" if block.padded else "—",
                )
            )
        self.block_table.set_rows(rows)
        self._notify(
            f"ASCII 加密完成：{result.original_length} 字节 → {len(result.blocks)} 组"
        )

    def _copy_escaped(self) -> None:
        if self._last_result is None:
            return
        QApplication.clipboard().setText(escape_bytes(self._last_result.ciphertext))
        self._notify("转义 ASCII 已复制到剪贴板")

    def _copy_hex(self) -> None:
        if self._last_result is None:
            return
        QApplication.clipboard().setText(self._last_result.ciphertext_hex_spaced)
        self._notify("十六进制密文已复制到剪贴板")

    def load_example(self) -> None:
        self.text_edit.setPlainText("ok")
        self.key_edit.setText("A73B")
        self._encrypt()

    def clear_inputs(self) -> None:
        self.text_edit.clear()
        self.key_edit.clear()
        self.escaped_label.setText("—")
        self.hex_edit.clear()
        self.padding_label.setText("等待输入")
        self.block_table.clear_rows()
        self.copy_escaped_button.setEnabled(False)
        self.copy_hex_button.setEnabled(False)
        self._last_result = None
        self._hide_error()
        self.text_edit.setFocus()
        self._notify("已清空 ASCII 加密页面")


class MultiTab(BaseTab):
    """第 4 关：32 bit 双重加密与 48 bit 三重加密。"""

    _DEFAULT_KEYS = {
        "double": "2D55A73B",
        "triple": "2D55A73B1C27",
    }

    def _build(self) -> None:
        self._last_result: Optional[MultiEncryptionResult] = None
        self._last_mode = "double"

        intro = QLabel(
            "双重加密把 32 bit 密钥拆成 K1、K2，执行 E_K2(E_K1(P))；"
            "三重加密把 48 bit 密钥拆成 K1、K2、K3，执行 E_K3(E_K2(E_K1(P)))。"
        )
        intro.setObjectName("Hint")
        intro.setWordWrap(True)
        self.page_layout.addWidget(intro)

        input_card = Card("输入", "分组长度始终为 16 bit，只有密钥长度随模式变化。")
        grid = _make_form_grid()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("双重加密（32 bit 密钥 K1 + K2）", "double")
        self.mode_combo.addItem("三重加密（48 bit 密钥 K1 + K2 + K3）", "triple")
        self.mode_combo.setMinimumWidth(330)
        self.mode_combo.setAccessibleName("多重加密模式")
        row = _add_field(
            grid, 0, "加密模式", self.mode_combo, "双重为 2 次加密；三重为 3 次加密（EEE）。"
        )

        self.plaintext_edit = QLineEdit()
        self.plaintext_edit.setObjectName("MonoInput")
        self.plaintext_edit.setPlaceholderText("例如 6F6B")
        self.plaintext_edit.setMaxLength(16)
        self.plaintext_edit.setAccessibleName("多重加密明文")
        row = _add_field(
            grid, row, "明文 P（16 bit）", self.plaintext_edit, "4 位十六进制，例如 6F6B。"
        )

        self.key_edit = QLineEdit()
        self.key_edit.setObjectName("MonoInput")
        self.key_edit.setPlaceholderText("例如 2D55A73B")
        self.key_edit.setMaxLength(24)
        self.key_edit.setAccessibleName("多重加密密钥")
        row = _add_field(grid, row, "密钥", self.key_edit, "双重 8 位；三重 12 位。")
        self.key_hint = QLabel("")
        self.key_hint.setObjectName("Hint")
        self.key_hint.setWordWrap(True)
        grid.addWidget(self.key_hint, row, 1)

        self.error_label = self._make_error_label()
        input_card.body.addLayout(grid)
        input_card.body.addWidget(self.error_label)

        self.encrypt_button = make_button("加密", "PrimaryButton", "执行多重加密")
        self.example_button = make_button("载入示例", "SecondaryButton", "填入当前模式的示例")
        self.clear_button = make_button("清空", "GhostButton", "清空输入和结果")
        self.encrypt_button.clicked.connect(self._encrypt)
        self.example_button.clicked.connect(self.load_example)
        self.clear_button.clicked.connect(self.clear_inputs)
        input_card.body.addLayout(
            _make_button_row(self.encrypt_button, self.example_button, self.clear_button)
        )
        self.page_layout.addWidget(input_card)

        result_row = QHBoxLayout()
        result_row.setSpacing(16)
        result_card = Card("加密结果", "最终 16 bit 密文。")
        self.result_panel = ResultPanel("密文 C", on_copy=self._notify)
        result_card.body.addWidget(self.result_panel)
        result_row.addWidget(result_card, 1)

        key_card = Card("密钥拆分", "按输入顺序从高位到低位拆分。")
        self.key_table = DataTable(("子密钥", "值"), mono_columns=(1,))
        self.key_table.setMinimumHeight(160)
        key_card.body.addWidget(self.key_table)
        result_row.addWidget(key_card, 1)
        self.page_layout.addLayout(result_row)

        stage_card = Card("分级结果", "每一级都是一个完整的 S-AES 单分组加密。")
        self.stage_table = DataTable(
            ("阶段", "密文", "二进制"), mono_columns=(1, 2)
        )
        self.stage_table.setMinimumHeight(160)
        stage_card.body.addWidget(self.stage_table)
        self.page_layout.addWidget(stage_card)
        self.page_layout.addStretch(1)

        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._update_key_hint()
        self.load_example()

    def trigger_encrypt(self) -> None:
        self._encrypt()

    def _current_mode(self) -> str:
        return str(self.mode_combo.currentData())

    def _on_mode_changed(self) -> None:
        mode = self._current_mode()
        old_default = self._DEFAULT_KEYS.get(self._last_mode, "")
        current_key = self.key_edit.text().strip().upper()
        if not current_key or current_key in (
            old_default,
            f"0X{old_default}",
        ):
            self.key_edit.setText(self._DEFAULT_KEYS[mode])
        self._last_mode = mode
        self._update_key_hint()
        self._hide_error()
        self._notify(f"已切换到{'双重' if mode == 'double' else '三重'}加密")

    def _update_key_hint(self) -> None:
        if self._current_mode() == "double":
            self.key_hint.setText("8 位十六进制：K1 = 前 4 位，K2 = 后 4 位。")
            self.key_edit.setPlaceholderText("例如 2D55A73B")
        else:
            self.key_hint.setText("12 位十六进制：K1、K2、K3 各 4 位。")
            self.key_edit.setPlaceholderText("例如 2D55A73B1C27")

    def _encrypt(self) -> None:
        self._hide_error()
        mode = self._current_mode()
        digits = 8 if mode == "double" else 12
        try:
            plaintext = parse_hex(self.plaintext_edit.text(), 4, "明文")
            key = parse_hex(self.key_edit.text(), digits, "密钥")
            result = (
                double_encrypt(plaintext, key)
                if mode == "double"
                else triple_encrypt(plaintext, key)
            )
        except (TypeError, ValueError) as exc:
            self._show_error(str(exc))
            self._last_result = None
            self.result_panel.clear_result()
            self.key_table.clear_rows()
            self.stage_table.clear_rows()
            self._notify("多重加密输入有误，请检查提示")
            return

        self._last_result = result
        self._render_result(result)
        mode_name = "双重" if result.mode == "double" else "三重"
        self._notify(
            f"{mode_name}加密完成：{plaintext:04X} → {result.ciphertext_hex}"
        )

    def _render_result(self, result: MultiEncryptionResult) -> None:
        mode_name = "双重加密" if result.mode == "double" else "三重加密"
        key_bits = 32 if result.mode == "double" else 48
        key_text = "　".join(
            f"K{index + 1}={part:04X}" for index, part in enumerate(result.key_parts)
        )
        self.result_panel.set_result(
            result.ciphertext_hex,
            f"{mode_name}　{key_bits} bit 密钥　{key_text}",
        )

        self.key_table.set_rows(
            [(f"K{index + 1}", f"{part:04X}") for index, part in enumerate(result.key_parts)]
        )
        self.stage_table.set_rows(
            [
                (label, f"{value:04X}", f"{value:016b}")
                for label, value in zip(result.stage_labels, result.stage_ciphertexts)
            ]
        )

    def load_example(self) -> None:
        mode = self._current_mode()
        self.plaintext_edit.setText("6F6B")
        self.key_edit.setText(self._DEFAULT_KEYS[mode])
        self._encrypt()

    def clear_inputs(self) -> None:
        self.plaintext_edit.clear()
        self.key_edit.clear()
        self.result_panel.clear_result()
        self.key_table.clear_rows()
        self.stage_table.clear_rows()
        self._last_result = None
        self._hide_error()
        self.plaintext_edit.setFocus()
        self._notify("已清空多重加密页面")
