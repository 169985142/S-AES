"""可复用界面组件。

这些组件不含算法逻辑，只负责把结果、表格和错误提示以一致的方式
展示出来。功能页可以复用它们，避免每个页面重复写样式和布局。
"""

from typing import Iterable, Optional, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .theme import MONO_FONT


def make_button(
    text: str,
    object_name: str = "SecondaryButton",
    tooltip: str = "",
) -> QPushButton:
    """创建带统一光标、最小高度和可访问名称的按钮。"""

    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setCursor(Qt.PointingHandCursor)
    button.setMinimumHeight(36)
    button.setAccessibleName(text)
    if tooltip:
        button.setToolTip(tooltip)
    return button


class Card(QFrame):
    """带标题和说明的白色内容卡片。"""

    def __init__(
        self, title: str, subtitle: str = "", parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setWordWrap(True)
        outer.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("CardSubtitle")
            subtitle_label.setWordWrap(True)
            outer.addWidget(subtitle_label)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 4, 0, 0)
        self.body.setSpacing(10)
        outer.addLayout(self.body)


class ResultPanel(QFrame):
    """突出显示 16 bit 密文，并提供复制按钮。"""

    def __init__(
        self,
        title: str,
        on_copy=None,
        wrap_value: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("ResultPanel")
        self._on_copy = on_copy
        self._wrap_value = wrap_value

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ResultTitle")
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.copy_button = make_button("复制", "GhostButton", "复制当前结果")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self._copy)
        header.addWidget(self.copy_button)
        layout.addLayout(header)

        self.value_label = QLabel("—")
        self.value_label.setObjectName("ResultValue")
        self.value_label.setTextFormat(Qt.PlainText)
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.value_label.setWordWrap(wrap_value)
        if wrap_value:
            self.value_label.setFont(QFont(MONO_FONT, 10))
        layout.addWidget(self.value_label)

        self.meta_label = QLabel("等待输入")
        self.meta_label.setObjectName("ResultMeta")
        self.meta_label.setTextFormat(Qt.PlainText)
        self.meta_label.setWordWrap(True)
        layout.addWidget(self.meta_label)

    def set_result(self, value: str, meta: str = "") -> None:
        self.value_label.setText(value)
        self.meta_label.setText(meta)
        self.copy_button.setEnabled(bool(value) and value != "—")

    def clear_result(self) -> None:
        self.value_label.setText("—")
        self.meta_label.setText("等待输入")
        self.copy_button.setEnabled(False)

    def _copy(self) -> None:
        text = self.value_label.text()
        if not text or text == "—":
            return
        QApplication.clipboard().setText(text)
        if self._on_copy:
            self._on_copy("结果已复制到剪贴板")


class DataTable(QTableWidget):
    """只读数据表：统一表头、行高、等宽列和选择行为。"""

    def __init__(
        self,
        headers: Sequence[str],
        mono_columns: Iterable[int] = (),
        parent: Optional[QWidget] = None,
    ):
        super().__init__(0, len(headers), parent)
        self._mono_columns = set(mono_columns)
        self.setHorizontalHeaderLabels(list(headers))
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(32)
        self.horizontalHeader().setHighlightSections(False)

        header = self.horizontalHeader()
        if headers:
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)

    def set_rows(self, rows: Sequence[Sequence[str]]) -> None:
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if column_index in self._mono_columns:
                    item.setFont(QFont(MONO_FONT, 10))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.setItem(row_index, column_index, item)

    def clear_rows(self) -> None:
        self.setRowCount(0)


class ScrollPage(QScrollArea):
    """带统一边距和滚动行为的页面容器。"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.content = QWidget()
        self.content.setObjectName("PageContent")
        self.page_layout = QVBoxLayout(self.content)
        self.page_layout.setContentsMargins(24, 22, 24, 24)
        self.page_layout.setSpacing(16)
        self.setWidget(self.content)
