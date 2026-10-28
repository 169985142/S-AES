"""主窗口：页头、三个加密功能页、快捷键和状态栏。"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QShortcut,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .tabs import AsciiTab, BasicTab, MultiTab


class MainWindow(QMainWindow):
    """S-AES 加密实验台主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"S-AES 加密实验台 v{__version__}")
        self.setMinimumSize(920, 660)
        self._resize_for_screen()

        self._build_ui()
        self._bind_shortcuts()
        self._center_on_screen()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(22, 18, 22, 18)
        body_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        self.tabs.setMovable(False)
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setAccessibleName("功能页面")

        self.basic_tab = BasicTab()
        self.ascii_tab = AsciiTab()
        self.multi_tab = MultiTab()
        self.tabs.addTab(self.basic_tab, "基础加密")
        self.tabs.addTab(self.ascii_tab, "ASCII 加密")
        self.tabs.addTab(self.multi_tab, "多重加密")

        for tab in (self.basic_tab, self.ascii_tab, self.multi_tab):
            tab.status_message.connect(self._show_status)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        body_layout.addWidget(self.tabs)
        root.addWidget(body, 1)

        self.setCentralWidget(central)

        status = QStatusBar()
        status.setSizeGripEnabled(False)
        self.setStatusBar(status)
        status.showMessage("就绪 · 所有计算均在本机完成，不联网")

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(104)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 18, 28, 18)
        layout.setSpacing(18)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        title = QLabel("S-AES 加密实验台")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("16-bit block · 2 rounds · 教学实现　|　只做加密，不做解密")
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setWordWrap(True)
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        layout.addLayout(text_layout, 1)

        badge = QLabel("仅加密 · ENCRYPT ONLY")
        badge.setObjectName("Badge")
        badge.setAlignment(Qt.AlignCenter)
        badge.setToolTip("本程序不提供解密、中间相遇攻击和 CBC 功能")
        layout.addWidget(badge, 0, Qt.AlignVCenter)
        return header

    def _bind_shortcuts(self) -> None:
        self.encrypt_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.encrypt_shortcut.setContext(Qt.WindowShortcut)
        self.encrypt_shortcut.activated.connect(self._encrypt_current)

        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.clear_shortcut.setContext(Qt.WindowShortcut)
        self.clear_shortcut.activated.connect(self._clear_current)

    def _encrypt_current(self) -> None:
        widget = self.tabs.currentWidget()
        if isinstance(widget, (BasicTab, AsciiTab, MultiTab)):
            widget.trigger_encrypt()
        else:
            self._show_status("当前页面没有加密操作")

    def _clear_current(self) -> None:
        widget = self.tabs.currentWidget()
        if isinstance(widget, (BasicTab, AsciiTab, MultiTab)):
            widget.clear_inputs()
        else:
            self._show_status("当前页面没有可清空的输入")

    def _on_tab_changed(self, index: int) -> None:
        title = self.tabs.tabText(index)
        self._show_status(f"当前页面：{title}")

    def _show_status(self, message: str) -> None:
        self.statusBar().showMessage(message, 6000)

    def _resize_for_screen(self) -> None:
        """在常见笔记本屏幕上避免窗口高于任务栏可用区域。"""

        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1080, 820)
            return
        available = screen.availableGeometry()
        width = min(1080, max(920, available.width() - 80))
        height = min(820, max(660, available.height() - 80))
        self.resize(width, height)

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())
