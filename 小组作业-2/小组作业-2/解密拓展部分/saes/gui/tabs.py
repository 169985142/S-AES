"""图形界面的各个标签页：基础、ASCII、多重、CBC、攻击。"""
from typing import Optional
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget, QCheckBox
)

from ..core import EncryptionTrace, encrypt_block_with_trace, decrypt_block_with_trace
from ..modes import (
    AsciiEncryptionResult, MultiEncryptionResult, CBCResult,
    double_encrypt, encrypt_ascii, escape_bytes, triple_encrypt,
    cbc_encrypt, cbc_decrypt, meet_in_the_middle_attack
)
from ..validators import parse_hex
from .widgets import Card, DataTable, ResultPanel, ScrollPage, make_button


class BaseTab(ScrollPage):
    status_message = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None: raise NotImplementedError

    def trigger_encrypt(self) -> None: pass

    def clear_inputs(self) -> None: pass

    def _notify(self, message: str) -> None: self.status_message.emit(message)

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


def _add_field(grid: QGridLayout, row: int, label_text: str, field: QWidget, hint_text: str = "") -> int:
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
    for button in buttons: row.addWidget(button)
    row.addStretch(1)
    return row


class BasicTab(BaseTab):
    def _build(self) -> None:
        intro = QLabel("输入 16 bit 数据和密钥，执行单分组加密或解密。展示 8 个中间状态。")
        intro.setObjectName("Hint")
        intro.setWordWrap(True)
        self.page_layout.addWidget(intro)

        input_card = Card("输入", "十六进制，允许 0x 前缀、空格和大小写混用。")
        grid = _make_form_grid()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("加密 (Encrypt)", "encrypt")
        self.mode_combo.addItem("解密 (Decrypt)", "decrypt")
        self.mode_combo.currentIndexChanged.connect(self.load_example)
        row = _add_field(grid, 0, "操作模式", self.mode_combo)

        self.plaintext_edit = QLineEdit()
        self.plaintext_edit.setObjectName("MonoInput")
        self.plaintext_edit.setMaxLength(16)
        row = _add_field(grid, row, "输入数据", self.plaintext_edit, "4 位十六进制。")

        self.key_edit = QLineEdit()
        self.key_edit.setObjectName("MonoInput")
        self.key_edit.setMaxLength(16)
        _add_field(grid, row, "密钥 K", self.key_edit, "4 位十六进制。")

        self.error_label = self._make_error_label()
        input_card.body.addLayout(grid)
        input_card.body.addWidget(self.error_label)

        self.encrypt_button = make_button("执行", "PrimaryButton")
        self.example_button = make_button("载入示例", "SecondaryButton")
        self.clear_button = make_button("清空", "GhostButton")
        self.encrypt_button.clicked.connect(self._encrypt)
        self.example_button.clicked.connect(self.load_example)
        self.clear_button.clicked.connect(self.clear_inputs)
        input_card.body.addLayout(_make_button_row(self.encrypt_button, self.example_button, self.clear_button))
        self.page_layout.addWidget(input_card)

        result_row = QHBoxLayout()
        result_row.setSpacing(16)
        result_card = Card("结果", "输出为 16 bit 结果。")
        self.result_panel = ResultPanel("密文 C", on_copy=self._notify)
        result_card.body.addWidget(self.result_panel)
        result_row.addWidget(result_card, 1)

        schedule_card = Card("密钥编排", "w0–w5 为 8 bit 字。")
        self.schedule_table = DataTable(("项目", "值"), mono_columns=(1,))
        self.schedule_table.setMinimumHeight(258)
        schedule_card.body.addWidget(self.schedule_table)
        result_row.addWidget(schedule_card, 1)
        self.page_layout.addLayout(result_row)

        trace_card = Card("中间状态", "每轮变换后的状态。")
        self.trace_table = DataTable(("步骤", "十六进制", "二进制"), mono_columns=(1, 2))
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
            val = parse_hex(self.plaintext_edit.text(), 4, "输入数据")
            key = parse_hex(self.key_edit.text(), 4, "密钥")
            is_enc = self.mode_combo.currentData() == "encrypt"
            trace = encrypt_block_with_trace(val, key) if is_enc else decrypt_block_with_trace(val, key)
        except Exception as exc:
            self._show_error(str(exc))
            self.result_panel.clear_result()
            self.schedule_table.clear_rows()
            self.trace_table.clear_rows()
            self._notify("输入有误")
            return

        is_enc = self.mode_combo.currentData() == "encrypt"
        self.result_panel.title_label.setText("密文 C" if is_enc else "明文 P")
        self.result_panel.set_result(trace.ciphertext_hex, f"P = {trace.plaintext_hex}　K = {trace.key_hex}")
        self.trace_table.set_rows([(s.label, s.hex_value, s.binary_value) for s in trace.steps])
        k0, k1, k2 = trace.schedule.round_keys
        s = trace.schedule
        self.schedule_table.set_rows([
            ("K0 = w0 || w1", f"{k0:04X}"), ("K1 = w2 || w3", f"{k1:04X}"), ("K2 = w4 || w5", f"{k2:04X}"),
            ("w0", f"{s.w0:02X}"), ("w1", f"{s.w1:02X}"), ("w2", f"{s.w2:02X}"),
            ("w3", f"{s.w3:02X}"), ("w4", f"{s.w4:02X}"), ("w5", f"{s.w5:02X}")
        ])
        self._notify("执行完成")

    def load_example(self) -> None:
        is_enc = self.mode_combo.currentData() == "encrypt"
        self.plaintext_edit.setText("6F6B" if is_enc else "0738")
        self.plaintext_edit.setPlaceholderText("例如 6F6B" if is_enc else "例如 0738")
        self.key_edit.setText("A73B")
        self._encrypt()

    def clear_inputs(self) -> None:
        self.plaintext_edit.clear()
        self.key_edit.clear()
        self.result_panel.clear_result()
        self.schedule_table.clear_rows()
        self.trace_table.clear_rows()
        self._hide_error()


class AsciiTab(BaseTab):
    def _build(self) -> None:
        intro = QLabel("ASCII 字符串按 2 字节分组加密。奇数补 0x00。")
        intro.setObjectName("Hint")
        self.page_layout.addWidget(intro)
        input_card = Card("输入")
        grid = _make_form_grid()
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFixedHeight(96)
        self.text_edit.setTabChangesFocus(True)
        row = _add_field(grid, 0, "明文（ASCII）", self.text_edit)
        self.key_edit = QLineEdit("A73B")
        _add_field(grid, row, "密钥 K", self.key_edit)
        self.error_label = self._make_error_label()
        input_card.body.addLayout(grid)
        input_card.body.addWidget(self.error_label)
        self.btn = make_button("加密", "PrimaryButton")
        self.btn.clicked.connect(self._encrypt)
        input_card.body.addLayout(_make_button_row(self.btn))
        self.page_layout.addWidget(input_card)
        self.result_panel = ResultPanel("密文", wrap_value=True)
        result_card = Card("输出")
        result_card.body.addWidget(self.result_panel)
        self.page_layout.addWidget(result_card)
        self.page_layout.addStretch(1)
        self.load_example()

    def _encrypt(self):
        self._hide_error()
        try:
            key = parse_hex(self.key_edit.text(), 4, "密钥")
            result = encrypt_ascii(self.text_edit.toPlainText(), key)
            self.result_panel.set_result(escape_bytes(result.ciphertext), f"Hex: {result.ciphertext_hex_spaced}")
        except Exception as e:
            self._show_error(str(e))

    def load_example(self):
        self.text_edit.setPlainText("ok")
        self._encrypt()


class MultiTab(BaseTab):
    def _build(self) -> None:
        input_card = Card("多重加密")
        grid = _make_form_grid()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("双重加密 (32 bit)", "double")
        self.mode_combo.addItem("三重加密 (48 bit)", "triple")
        row = _add_field(grid, 0, "模式", self.mode_combo)
        self.plaintext_edit = QLineEdit("6F6B")
        row = _add_field(grid, row, "明文 P", self.plaintext_edit)
        self.key_edit = QLineEdit("2D55A73B1C27")
        _add_field(grid, row, "密钥", self.key_edit)
        input_card.body.addLayout(grid)
        self.btn = make_button("加密", "PrimaryButton")
        self.btn.clicked.connect(self._encrypt)
        input_card.body.addLayout(_make_button_row(self.btn))
        self.page_layout.addWidget(input_card)
        self.result_panel = ResultPanel("最终密文")
        res_card = Card("输出")
        res_card.body.addWidget(self.result_panel)
        self.page_layout.addWidget(res_card)
        self.page_layout.addStretch(1)
        self.load_example()

    def _encrypt(self):
        try:
            p = parse_hex(self.plaintext_edit.text(), 4, "明文")
            digits = 8 if self.mode_combo.currentData() == "double" else 12
            k = parse_hex(self.key_edit.text(), digits, "密钥")
            res = double_encrypt(p, k) if digits == 8 else triple_encrypt(p, k)
            self.result_panel.set_result(res.ciphertext_hex,
                                         "分级: " + " -> ".join(f"{x:04X}" for x in res.stage_ciphertexts))
        except Exception as e:
            self.result_panel.set_result("错误", str(e))

    def load_example(self):
        is_d = self.mode_combo.currentData() == "double"
        self.key_edit.setText("2D55A73B" if is_d else "2D55A73B1C27")
        self._encrypt()


class CbcTab(BaseTab):
    def _build(self) -> None:
        intro = QLabel("CBC 工作模式。支持加密解密，并可演示篡改密文对解密结果的影响。")
        intro.setObjectName("Hint")
        self.page_layout.addWidget(intro)
        input_card = Card("CBC 参数")
        grid = _make_form_grid()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("加密", "encrypt")
        self.mode_combo.addItem("解密", "decrypt")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        _add_field(grid, 0, "模式", self.mode_combo)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFixedHeight(64)
        self.text_edit.setPlaceholderText("输入 ASCII 字符串")
        _add_field(grid, 1, "明文/密文", self.text_edit)
        self.key_edit = QLineEdit("A73B")
        _add_field(grid, 2, "密钥 K", self.key_edit)
        self.iv_edit = QLineEdit("0000")
        _add_field(grid, 3, "初始向量 IV", self.iv_edit)
        self.tamper_check = QCheckBox("演示：篡改第一个密文分组的末位")
        self.tamper_check.setVisible(False)
        grid.addWidget(self.tamper_check, 4, 0, 1, 2)
        self.error_label = self._make_error_label()
        input_card.body.addLayout(grid)
        input_card.body.addWidget(self.error_label)
        self.btn = make_button("执行", "PrimaryButton")
        self.btn.clicked.connect(self._run)
        input_card.body.addLayout(_make_button_row(self.btn))
        self.page_layout.addWidget(input_card)
        self.result_panel = ResultPanel("结果")
        result_card = Card("输出")
        result_card.body.addWidget(self.result_panel)
        self.page_layout.addWidget(result_card)
        self.page_layout.addStretch(1)

    def _on_mode_changed(self):
        is_dec = self.mode_combo.currentData() == "decrypt"
        self.tamper_check.setVisible(is_dec)
        self.text_edit.setPlaceholderText("输入十六进制字符串" if is_dec else "输入 ASCII 字符串")

    def _run(self):
        self._hide_error()
        try:
            key = parse_hex(self.key_edit.text(), 4, "密钥")
            iv = parse_hex(self.iv_edit.text(), 4, "IV")
            if self.mode_combo.currentData() == "encrypt":
                text = self.text_edit.toPlainText()
                if not text: raise ValueError("请输入明文")
                data = text.encode('ascii')
                if len(data) % 2 != 0: data += b'\x00'
                res = cbc_encrypt(data, key, iv)
                out_hex = " ".join(f"{c:04X}" for _, c in res.blocks)
                self.result_panel.title_label.setText("密文 (CBC)")
                self.result_panel.set_result(out_hex, "转义显示")
            else:
                hex_str = self.text_edit.toPlainText().replace(" ", "").strip()
                if not hex_str: raise ValueError("请输入密文")
                data = bytes.fromhex(hex_str)
                tamper = 0 if self.tamper_check.isChecked() else -1
                res = cbc_decrypt(data, key, iv, tamper)
                dec_bytes = b"".join(p.to_bytes(2, 'big') for _, p in res.blocks)
                self.result_panel.title_label.setText("解密明文")
                self.result_panel.set_result(escape_bytes(dec_bytes), "若开启篡改，数据尾部大概率乱码")
        except Exception as e:
            self._show_error(str(e))


class AttackTab(BaseTab):
    def _build(self) -> None:
        intro = QLabel("中间相遇攻击：给定明文和双重加密的密文，破解 K1 和 K2。")
        intro.setObjectName("Hint")
        self.page_layout.addWidget(intro)

        card = Card("输入")
        grid = _make_form_grid()
        self.p_edit = QLineEdit("6F6B")
        _add_field(grid, 0, "已知明文 P", self.p_edit)
        self.c_edit = QLineEdit("")
        _add_field(grid, 1, "已知密文 C", self.c_edit, "可手动输入，或在下方生成")
        card.body.addLayout(grid)

        self.btn_run = make_button("执行攻击 (约需1-2秒)", "PrimaryButton")
        self.btn_run.clicked.connect(self._attack)

        self.btn_gen = make_button("随机生成密钥并加密", "SecondaryButton")
        self.btn_gen.clicked.connect(self._gen_test)

        card.body.addLayout(_make_button_row(self.btn_run, self.btn_gen))
        self.page_layout.addWidget(card)

        self.res_panel = ResultPanel("破解结果", wrap_value=True)
        res_card = Card("输出")
        res_card.body.addWidget(self.res_panel)
        self.page_layout.addWidget(res_card)

    def _gen_test(self):
        import random
        k1, k2 = random.randint(0, 0xFFFF), random.randint(0, 0xFFFF)
        p = int(self.p_edit.text(), 16)
        c = double_encrypt(p, (k1 << 16) | k2).ciphertext
        self.c_edit.setText(f"{c:04X}")
        self.res_panel.set_result(f"真实 K1={k1:04X} K2={k2:04X}", "请点击左侧执行攻击")

    def _attack(self):
        try:
            p = parse_hex(self.p_edit.text(), 4, "明文")
            c = parse_hex(self.c_edit.text(), 4, "密文")
            self.res_panel.set_result("正在计算...", "请稍候")
            QApplication.processEvents()
            res = meet_in_the_middle_attack(p, c)
            if res:
                k1, k2 = res
                self.res_panel.set_result(f"破解成功！\nK1 = {k1:04X}\nK2 = {k2:04X}", "验证无误")
            else:
                self.res_panel.set_result("破解失败", "未找到匹配的密钥对")
        except Exception as e:
            self.res_panel.set_result("错误", str(e))