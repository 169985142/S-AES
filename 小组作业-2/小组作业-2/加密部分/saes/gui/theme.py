"""界面配色、字体和 Qt 样式表。

配色取“海军蓝 + 低饱和绿”的极简教学工具风格：
- 深蓝用于标题和主按钮，保证白字对比度；
- 绿色只用于结果和成功状态，避免整页花哨；
- 背景与卡片使用浅灰/白色分层，减少长时间阅读的疲劳。
"""

from typing import Final

UI_FONT: Final[str] = "Microsoft YaHei UI"
MONO_FONT: Final[str] = "Consolas"

COLORS: Final[dict[str, str]] = {
    "background": "#F8FAFC",
    "surface": "#FFFFFF",
    "primary": "#1E3A5F",
    "primary_hover": "#274B75",
    "secondary": "#2563EB",
    "accent": "#047857",
    "accent_soft": "#F0FDF4",
    "text": "#0F172A",
    "muted": "#475569",
    "subtle": "#64748B",
    "border": "#E2E8F0",
    "danger": "#B91C1C",
    "danger_soft": "#FEF2F2",
}

APP_STYLESHEET: Final[str] = f"""
QWidget {{
    background-color: {COLORS["background"]};
    color: {COLORS["text"]};
    font-family: "{UI_FONT}";
    font-size: 10pt;
}}

QMainWindow {{
    background-color: {COLORS["background"]};
}}

QFrame#Header {{
    background-color: {COLORS["primary"]};
    border: none;
    border-bottom: 4px solid {COLORS["accent"]};
}}

QLabel#HeaderTitle {{
    background: transparent;
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 700;
}}

QLabel#HeaderSubtitle {{
    background: transparent;
    color: #CBD5E1;
    font-size: 10pt;
}}

QLabel#Badge {{
    background-color: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.28);
    border-radius: 14px;
    padding: 7px 14px;
    font-size: 9pt;
    font-weight: 600;
    letter-spacing: 1px;
}}

QTabWidget::pane {{
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    background-color: {COLORS["background"]};
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {COLORS["muted"]};
    padding: 11px 20px;
    margin-right: 4px;
    border: none;
    border-bottom: 3px solid transparent;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    color: {COLORS["primary"]};
    background-color: #EEF2F7;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    color: {COLORS["primary"]};
    border-bottom: 3px solid {COLORS["accent"]};
}}

QScrollArea {{
    border: none;
    background-color: {COLORS["background"]};
}}

QFrame#Card {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
}}

QLabel#CardTitle {{
    background: transparent;
    color: {COLORS["primary"]};
    font-size: 13pt;
    font-weight: 700;
}}

QLabel#CardSubtitle {{
    background: transparent;
    color: {COLORS["subtle"]};
    font-size: 9pt;
}}

QLabel#FieldLabel {{
    background: transparent;
    color: {COLORS["text"]};
    font-weight: 600;
}}

QLabel#Hint {{
    background: transparent;
    color: {COLORS["subtle"]};
    font-size: 9pt;
}}

QLabel#ErrorLabel {{
    background-color: {COLORS["danger_soft"]};
    color: {COLORS["danger"]};
    border: 1px solid #FECACA;
    border-radius: 6px;
    padding: 8px 10px;
}}

QLineEdit, QPlainTextEdit {{
    background-color: #FFFFFF;
    color: {COLORS["text"]};
    border: 1px solid #CBD5E1;
    border-radius: 7px;
    padding: 8px 10px;
    selection-background-color: #BFDBFE;
    selection-color: {COLORS["text"]};
}}

QLineEdit:hover, QPlainTextEdit:hover {{
    border-color: #94A3B8;
}}

QLineEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {COLORS["secondary"]};
    padding: 7px 9px;
}}

QLineEdit:disabled, QPlainTextEdit:disabled {{
    background-color: #F1F5F9;
    color: #94A3B8;
}}

QLineEdit#MonoInput, QPlainTextEdit#MonoInput {{
    font-family: "{MONO_FONT}";
    font-size: 11pt;
    letter-spacing: 1px;
}}

QPushButton {{
    background-color: #FFFFFF;
    color: {COLORS["primary"]};
    border: 1px solid #CBD5E1;
    border-radius: 7px;
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #F1F5F9;
    border-color: #94A3B8;
}}

QPushButton:pressed {{
    background-color: #E2E8F0;
}}

QPushButton:focus {{
    border: 2px solid {COLORS["secondary"]};
    padding: 7px 15px;
}}

QPushButton#PrimaryButton {{
    background-color: {COLORS["primary"]};
    color: #FFFFFF;
    border: 1px solid {COLORS["primary"]};
}}

QPushButton#PrimaryButton:hover {{
    background-color: {COLORS["primary_hover"]};
    border-color: {COLORS["primary_hover"]};
}}

QPushButton#PrimaryButton:focus {{
    border: 2px solid #93C5FD;
    padding: 7px 15px;
}}

QPushButton#GhostButton {{
    background-color: transparent;
    color: {COLORS["muted"]};
    border: 1px solid {COLORS["border"]};
    padding: 7px 12px;
}}

QPushButton#GhostButton:hover {{
    background-color: #F8FAFC;
    color: {COLORS["primary"]};
}}

QPushButton:disabled {{
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}}

QFrame#ResultPanel {{
    background-color: {COLORS["accent_soft"]};
    border: 1px solid #A7F3D0;
    border-radius: 9px;
}}

QLabel#ResultTitle {{
    background: transparent;
    color: #047857;
    font-size: 9pt;
    font-weight: 600;
}}

QLabel#ResultValue {{
    background: transparent;
    color: #065F46;
    font-family: "{MONO_FONT}";
    font-size: 19pt;
    font-weight: 700;
    letter-spacing: 2px;
}}

QLabel#ResultMeta {{
    background: transparent;
    color: #047857;
    font-size: 9pt;
}}

QLabel#AsciiValue {{
    background: transparent;
    color: #065F46;
    font-family: "{MONO_FONT}";
    font-size: 11pt;
    font-weight: 600;
}}

QPlainTextEdit#ReadOnlyHex {{
    background-color: #FFFFFF;
    color: {COLORS["text"]};
    border: 1px solid #D1FAE5;
    border-radius: 6px;
    padding: 6px 8px;
    font-family: "{MONO_FONT}";
    font-size: 10pt;
}}

QTableWidget {{
    background-color: #FFFFFF;
    alternate-background-color: #F8FAFC;
    border: 1px solid {COLORS["border"]};
    border-radius: 7px;
    gridline-color: #EEF2F7;
    selection-background-color: #DBEAFE;
    selection-color: {COLORS["text"]};
}}

QTableWidget::item {{
    padding: 7px 8px;
    border: none;
}}

QHeaderView::section {{
    background-color: #F1F5F9;
    color: {COLORS["muted"]};
    border: none;
    border-bottom: 1px solid {COLORS["border"]};
    padding: 8px;
    font-weight: 600;
}}

QTableCornerButton::section {{
    background-color: #F1F5F9;
    border: none;
}}

QComboBox {{
    background-color: #FFFFFF;
    color: {COLORS["text"]};
    border: 1px solid #CBD5E1;
    border-radius: 7px;
    padding: 8px 12px;
    min-height: 22px;
}}

QComboBox:hover {{
    border-color: #94A3B8;
}}

QComboBox:focus {{
    border: 2px solid {COLORS["secondary"]};
    padding: 7px 11px;
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    border: 1px solid {COLORS["border"]};
    selection-background-color: #DBEAFE;
    selection-color: {COLORS["text"]};
    padding: 4px;
}}

QStatusBar {{
    background-color: #FFFFFF;
    color: {COLORS["subtle"]};
    border-top: 1px solid {COLORS["border"]};
    font-size: 9pt;
}}

QStatusBar::item {{
    border: none;
}}

QToolTip {{
    background-color: {COLORS["primary"]};
    color: #FFFFFF;
    border: none;
    padding: 6px 8px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background: #CBD5E1;
    min-height: 32px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""
