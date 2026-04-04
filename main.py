"""
考试倒计时程序
AI 开发作品，无人类作者版权声明
遵循 LICENSE 许可证
考试日期数据来源：互联网
"""

# 数据与兼容版本号
VERSION = "build9"
DEFAULT_WATERMARK_COLOR = "#201f1e"
DEFAULT_VISIBLE_COLOR = "#0f1419"

# AI-Assisted: GitHub Copilot - 2025/04
# 本程序完全由 AI 开发，遵循 LICENSE 中的规定
# 详细许可证请参阅项目根目录下的 LICENSE 文件
# AI-Assisted Start: GitHub Copilot - 2025/04
import sys
import datetime
import json
import os
import tempfile  # 导入tempfile用于创建锁文件
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                              QWidget, QSystemTrayIcon, QMenu, QDialog,
                              QHBoxLayout, QComboBox,
                              QStackedWidget, QPushButton, QFrame,
                              QRadioButton, QButtonGroup, QLineEdit,
                              QMessageBox, QSizePolicy, QSlider)
from PySide6.QtCore import Qt, QTimer, QDate, Signal, QRectF, QPoint
from PySide6.QtGui import QPalette, QColor, QFont, QIcon, QAction, QActionGroup, QPixmap, QPainter, QPen, QIntValidator, QFontMetrics, QGuiApplication, QPainterPath
from qfluentwidgets import (
    CardWidget,
    CheckableSystemTrayMenu,
    CheckBox,
    ComboBox,
    ColorPickerButton,
    EditableComboBox,
    FastCalendarPicker,
    FluentStyleSheet,
    FluentIcon as FIF,
    LineEdit,
    NavigationDisplayMode,
    NavigationInterface,
    RoundMenu,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    Theme,
    setTheme,
    setThemeColor,
)

# 全局应用程序变量
app_instance = None
lock_file = None  # 添加锁文件的全局引用

# 确保只运行一个实例，使用文件锁而不是socket
def ensure_single_instance():
    global lock_file
    
    try:
        # 在临时目录创建一个锁文件
        lock_file_path = os.path.join(tempfile.gettempdir(), "countdown_app.lock")
        
        # 尝试以独占方式打开文件
        lock_file = open(lock_file_path, "w")
        
        # 尝试对文件加锁
        # Windows上使用msvcrt
        if sys.platform == "win32":
            import msvcrt
            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                return True  # 锁定成功，这是唯一的实例
            except IOError:
                # 锁定失败，说明已经有实例在运行
                lock_file.close()
                lock_file = None
        else:
            # 非Windows平台使用fcntl
            import fcntl
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True  # 锁定成功
            except IOError:
                lock_file.close()
                lock_file = None
                
        # 如果代码执行到这里，说明锁定失败
        # 创建一个临时的QApplication实例，用于显示对话框
        global app_instance
        if app_instance is None:
            app_instance = QApplication(sys.argv)

        # 显示对话框提醒用户
        QMessageBox.information(None, "程序已在运行",
                              "考试倒计时程序已经在运行中!\n\n请检查系统托盘区域是否有该程序图标。",
                              QMessageBox.StandardButton.Ok)

        print("程序已经在运行中，退出本实例。")
        sys.exit(0)
        
    except Exception as e:
        print(f"检查单例实例时出错: {e}")
        # 出错时也允许程序继续运行
        return True

# 检查是否为单一实例
is_single_instance = ensure_single_instance()

# 配置文件路径 - 改为使用用户目录
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".countdown")
CONFIG_FILE = os.path.join(CONFIG_DIR, "countdown_config.json")

# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)


class ScreenColorPicker(QWidget):
    """全屏取色层：可拖动取色圈并显示放大镜预览"""

    colorPicked = Signal(QColor)
    canceled = Signal()

    def __init__(self, parent=None):
        super().__init__(None)
        self._owner = parent
        self._dragging = False
        self._accepted = False
        self._cursor_pos = QGuiApplication.primaryScreen().geometry().center()
        self._drag_offset = QPoint(0, 0)
        self._background = None
        self._screen = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setWindowOpacity(1.0)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        self._ring_radius = 18
        self._magnifier_size = 170
        self._magnifier_zoom = 10
        self._magnifier_radius = 64
        self._capture_background()

    def _screen_at(self, global_pos):
        return QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()

    def _capture_background(self):
        self._screen = self._screen_at(self._cursor_pos)
        if self._screen is not None:
            self._background = self._screen.grabWindow(0)

    def _sample_point(self):
        screen = self._screen_at(self._cursor_pos)
        if screen is None or self._background is None:
            return None, None, None
        screen_geometry = screen.geometry()
        dpr = self._background.devicePixelRatio()
        local_x = self._cursor_pos.x() - screen_geometry.x()
        local_y = self._cursor_pos.y() - screen_geometry.y()
        sample_x = int(local_x * dpr)
        sample_y = int(local_y * dpr)
        return screen, sample_x, sample_y

    def _current_color(self):
        screen, sample_x, sample_y = self._sample_point()
        if screen is None or sample_x is None or sample_y is None:
            return QColor("#000000")
        pixel = self._background.copy(sample_x, sample_y, 1, 1).toImage()
        if pixel.isNull():
            return QColor("#000000")
        return QColor(pixel.pixel(0, 0))

    def _move_cursor(self, pos):
        self._cursor_pos = pos
        self.update()

    def _magnifier_rect(self):
        magnifier_diameter = self._magnifier_size
        magnifier_x = self._cursor_pos.x() + 26
        magnifier_y = self._cursor_pos.y() + 26
        if magnifier_x + magnifier_diameter > self.width():
            magnifier_x = self._cursor_pos.x() - magnifier_diameter - 26
        if magnifier_y + magnifier_diameter > self.height():
            magnifier_y = self._cursor_pos.y() - magnifier_diameter - 26
        return QRectF(magnifier_x, magnifier_y, magnifier_diameter, magnifier_diameter)

    def _handle_rect(self):
        magnifier_rect = self._magnifier_rect()
        handle_size = 24
        return QRectF(
            magnifier_rect.right() - handle_size * 0.8,
            magnifier_rect.bottom() - handle_size * 0.8,
            handle_size,
            handle_size,
        )

    def _hit_test_drag_area(self, global_pos):
        return self._magnifier_rect().contains(global_pos) or self._handle_rect().contains(global_pos)

    def _confirm_selection(self):
        self._accepted = True
        self.colorPicked.emit(self._current_color())
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._confirm_selection()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            if self._hit_test_drag_area(global_pos):
                self._dragging = True
                self._drag_offset = global_pos - self._cursor_pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._cursor_pos = event.globalPosition().toPoint() - self._drag_offset
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.update()

    def leaveEvent(self, event):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        screen = self._screen_at(self._cursor_pos)
        if screen is not None and self._background is not None:
            screenshot = self._background
            screen_geometry = screen.geometry()
            dpr = screenshot.devicePixelRatio()
            local_x = self._cursor_pos.x() - screen_geometry.x()
            local_y = self._cursor_pos.y() - screen_geometry.y()
            sample_x = int(local_x * dpr)
            sample_y = int(local_y * dpr)

            painter.fillRect(self.rect(), QColor(15, 23, 42, 42))

            # 放大镜：显示鼠标附近的像素块
            sample_size = max(14, int(14 * dpr))
            source_rect = screenshot.rect().adjusted(0, 0, -1, -1)
            source_x = max(0, min(source_rect.right() - sample_size, sample_x - sample_size // 2))
            source_y = max(0, min(source_rect.bottom() - sample_size, sample_y - sample_size // 2))
            sample = screenshot.copy(source_x, source_y, sample_size, sample_size)

            magnifier_rect = self._magnifier_rect()
            path = QPainterPath()
            path.addEllipse(magnifier_rect)
            painter.save()
            painter.setClipPath(path)
            painter.fillRect(magnifier_rect, QColor(255, 255, 255, 240))
            painter.drawPixmap(
                magnifier_rect.toRect(),
                sample.scaled(
                    magnifier_rect.size().toSize(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.FastTransformation
                )
            )
            painter.restore()

            painter.setPen(QPen(QColor(255, 255, 255, 235), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(magnifier_rect)
            painter.setPen(QPen(QColor(15, 108, 189, 220), 1))
            painter.drawEllipse(magnifier_rect.adjusted(2, 2, -2, -2))

            # 中心放大像素网格
            center = magnifier_rect.center()
            pixel_side = self._magnifier_radius / self._magnifier_zoom
            center_color = self._current_color()
            painter.setPen(QPen(QColor(0, 0, 0, 120), 1))
            painter.drawLine(int(center.x()) - 10, int(center.y()), int(center.x()) + 10, int(center.y()))
            painter.drawLine(int(center.x()), int(center.y()) - 10, int(center.x()), int(center.y()) + 10)

            # 当前颜色提示块
            preview_rect = QRectF(magnifier_rect.left(), magnifier_rect.bottom() + 10, magnifier_rect.width(), 28)
            painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
            painter.setBrush(QColor(255, 255, 255, 230))
            painter.drawRoundedRect(preview_rect, 10, 10)
            painter.setPen(QColor(32, 31, 30))
            painter.drawText(preview_rect.adjusted(12, 0, -12, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f"{center_color.name().upper()}  右键确认")

        # 取色圈
        ring_radius = self._ring_radius
        ring_rect = QRectF(self._cursor_pos.x() - ring_radius, self._cursor_pos.y() - ring_radius, ring_radius * 2, ring_radius * 2)
        painter.setPen(QPen(QColor(255, 255, 255, 245), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(ring_rect)
        painter.setPen(QPen(QColor(15, 108, 189, 235), 2))
        painter.drawEllipse(ring_rect.adjusted(3, 3, -3, -3))
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1))
        painter.drawEllipse(QRectF(self._cursor_pos.x() - 3, self._cursor_pos.y() - 3, 6, 6))

        handle_rect = self._handle_rect()
        painter.setPen(QPen(QColor(255, 255, 255, 240), 2))
        painter.setBrush(QColor(15, 108, 189, 235))
        painter.drawEllipse(handle_rect)
        painter.setPen(QPen(QColor(255, 255, 255, 225), 2))
        painter.drawLine(int(handle_rect.center().x()) - 5, int(handle_rect.center().y()), int(handle_rect.center().x()) + 5, int(handle_rect.center().y()))
        painter.drawLine(int(handle_rect.center().x()), int(handle_rect.center().y()) - 5, int(handle_rect.center().x()), int(handle_rect.center().y()) + 5)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.canceled.emit()
            self.close()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if not self._accepted:
            self.canceled.emit()
        super().closeEvent(event)

class DateSelectDialog(QDialog):
    """日期选择对话框"""

    # 创建基础日期字典（月份和日期）- 改为类变量
    base_zhongkao_dates = {
        "请选择省份或城市": {"文化课": None},
        "北京": {
            "文化课": (6, 24),
            "地理生物": (6, 26),
            "体育考试": (4, 15)
        },
        "上海": {
            "文化课": (6, 14),
            "英语听说": (5, 17),
            "理化实验": (5, 17)
        },
        "天津": {
            "文化课": (6, 21),
            "英语听力": (5, 24)
        },
        "重庆": {"文化课": (6, 12)},
        "河北": {"文化课": (6, 21)},
        "山西": {"文化课": (6, 20)},
        "内蒙古-呼和浩特": {"文化课": (6, 25)},
        "内蒙古-赤峰": {"文化课": (6, 26)},
        "辽宁": {"文化课": (6, 21)},
        "吉林-初三": {"文化课": (6, 27)},
        "吉林-初二": {"地理生物": (6, 30)},
        "黑龙江-哈尔滨": {"文化课": (6, 25)},
        "黑龙江-绥化": {"文化课": (6, 25)},
        "江苏-南京": {"文化课": (6, 17)},
        "江苏-宿迁": {"文化课": (6, 15)},
        "江苏-连云港": {"文化课": (6, 14)},
        "浙江": {"文化课": (6, 21)},
        "浙江-杭州": {"文化课": (6, 18)},
        "山东-济南": {"文化课": (6, 13)},
        "山东-淄博": {"文化课": (6, 14)},
        "安徽": {"文化课": (6, 14)},
        "福建": {"文化课": (6, 19)},
        "江西": {"文化课": (6, 16)},
        "河南": {"文化课": (6, 22)},
        "湖北-武汉": {"文化课": (6, 20)},
        "湖北-荆州": {"文化课": (6, 20)},
        "湖南": {"文化课": (6, 18)},
        "广东-深圳": {"文化课": (6, 26)},
        "广东-广州": {"文化课": (6, 30)},
        "广西": {"文化课": (6, 24)},
        "海南": {"文化课": (6, 25)},
        "四川-成都": {"文化课": (6, 13)},
        "四川-凉山": {"文化课": (6, 13)},
        "云南": {"文化课": (6, 16)},
        "贵州": {"文化课": (6, 21)},
        "西藏": {"文化课": (7, 3)},
        "陕西": {"文化课": (6, 22)},
        "甘肃": {"文化课": (6, 16)},
        "青海": {"文化课": (6, 16)},
        "宁夏": {"文化课": (6, 28)},
        "新疆": {"文化课": (6, 22)},
    }

    base_gaokao_dates = {
        "请选择省份或城市": {"统一科目": None},
        "新疆": {
            "统一科目": (6, 7),
            "文理综合": (6, 8),
            "外语": (6, 8)
        },
        "西藏": {
            "统一科目": (6, 7),
            "文理综合": (6, 8),
            "外语": (6, 8),
            "藏语文": (6, 9)
        },
        "广东": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "江苏": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "河北": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "湖南": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "重庆": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "辽宁": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8),
            "朝鲜语文": (6, 10)
        },
        "黑龙江": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "江西": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "北京": {
            "统一科目": (6, 7),
            "等级考科目": (6, 9),
            "外语": (6, 8)
        },
        "天津": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "上海": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8),
            "外语听说": (6, 9)
        },
        "浙江": {
            "统一科目": (6, 7),
            "技术": (6, 8),
            "外语": (6, 8),
            "选考科目": (6, 9)
        },
        "山东": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "海南": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "安徽": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "福建": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "甘肃": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "贵州": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "河南": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "湖北": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "吉林": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "内蒙古": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8),
            "蒙古语文": (6, 10)
        },
        "宁夏": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "青海": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "陕西": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "四川": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "云南": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
        "广西": {
            "统一科目": (6, 7),
            "选考科目": (6, 9),
            "外语": (6, 8)
        },
    }

    def __init__(self, parent=None, exam_mode="中考"):
        super().__init__(parent)
        FluentStyleSheet.DIALOG.apply(self)

        # 首先设置当前考试模式
        self.current_exam_mode = exam_mode

        # 然后计算考试年份
        self.exam_year = self._calculate_exam_year()

        self.setWindowTitle("设置日期和模式")
        self.resize(780, 520)
        self.setStyleSheet("""
            QLabel#dialogTitle {
                font-size: 18px;
                font-weight: 600;
            }
            QLabel#sectionTitle {
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#hintLabel,
            QLabel#noteLabel {
                font-size: 12px;
                color: #666666;
            }
            #calendarStrip {
                border: 1px solid #d2d0ce;
                border-radius: 8px;
                background-color: #ffffff;
                padding: 0 10px;
            }
            #regionYearCombo {
                border: 1px solid #d2d0ce;
                border-radius: 8px;
                background-color: #ffffff;
                padding: 2px 8px;
            }
            #regionYearCombo QLineEdit {
                border: none;
                background: transparent;
                padding: 0;
                margin: 0;
            }
            #positionPreview {
                border: 1px solid #d2d0ce;
                border-radius: 16px;
                background: rgba(250, 249, 248, 0.9);
            }
            QPushButton#positionDot {
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
                border-radius: 11px;
                border: 1px solid #c8c6c4;
                background: #ffffff;
                font-size: 10px;
                color: #9a9a9a;
            }
            QPushButton#positionDot:checked {
                background: #0f6cbd;
                border: 1px solid #0f6cbd;
                color: #ffffff;
            }
            QLabel#colorPreview {
                border: 1px solid #d2d0ce;
                border-radius: 8px;
                min-height: 26px;
                padding: 2px 8px;
            }
        """)

        # 转换基础日期为完整的 QDate 对象
        self.zhongkao_dates = self._convert_to_full_dates(self.base_zhongkao_dates)
        self.gaokao_dates = self._convert_to_full_dates(self.base_gaokao_dates)

        # 默认激活考试类型
        self.exam_dates = self.zhongkao_dates if exam_mode == "中考" else self.gaokao_dates
        self._last_non_custom_mode = exam_mode if exam_mode in ("中考", "高考") else "中考"

        # 添加自定义文本模板
        self.custom_text_template = "{time}天后，未来将会怎样？"
        if parent and hasattr(parent, "custom_text_template") and parent.custom_text_template:
            self.custom_text_template = parent.custom_text_template

        # 显示与外观设置初始值
        self.display_mode = getattr(parent, "display_mode", "watermark") if parent else "watermark"
        self.window_position = getattr(parent, "position", "left_top") if parent else "left_top"
        self.display_precision = getattr(parent, "precision", 5) if parent else 5
        self.font_scale = getattr(parent, "font_scale", 100) if parent else 100
        self.watermark_color = getattr(parent, "watermark_color", DEFAULT_WATERMARK_COLOR) if parent else DEFAULT_WATERMARK_COLOR
        self.visible_color = getattr(parent, "visible_color", DEFAULT_VISIBLE_COLOR) if parent else DEFAULT_VISIBLE_COLOR

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 14, 16, 14)

        # 左侧可折叠 Fluent 导航 + 右侧内容页
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(10)
        selector_layout.setContentsMargins(0, 0, 0, 0)

        self.selector_nav = NavigationInterface(parent=self, showMenuButton=True, collapsible=True)
        self.selector_nav.setExpandWidth(170)
        self.selector_nav.setMinimumExpandWidth(48)
        self.selector_nav.displayModeChanged.connect(self._on_selector_nav_mode_changed)
        self._on_selector_nav_mode_changed(NavigationDisplayMode.EXPAND)
        selector_layout.addWidget(self.selector_nav)

        self.selector_stack = QStackedWidget()
        selector_layout.addWidget(self.selector_stack, 1)
        layout.addLayout(selector_layout)

        # 按地区选择页
        region_page = QWidget()
        region_layout = QVBoxLayout(region_page)
        region_layout.setContentsMargins(0, 0, 0, 0)
        region_layout.setSpacing(12)

        region_body = QHBoxLayout()
        region_body.setSpacing(12)

        region_left_card = CardWidget()
        region_left_layout = QVBoxLayout(region_left_card)
        region_left_layout.setContentsMargins(12, 10, 12, 12)
        region_left_layout.setSpacing(10)

        region_left_title = QLabel("地区与模式")
        region_left_title.setObjectName("sectionTitle")
        region_left_layout.addWidget(region_left_title)

        mode_card = CardWidget()
        mode_layout = QHBoxLayout(mode_card)
        mode_layout.setContentsMargins(12, 10, 12, 10)
        mode_layout.setSpacing(14)

        mode_label = QLabel("模式类型:")
        mode_label.setStyleSheet("font-weight: 600;")
        mode_layout.addWidget(mode_label)

        self.exam_type_group = QButtonGroup(self)

        self.zhongkao_radio = RadioButton()
        self.zhongkao_radio.setText("中考")
        self.zhongkao_radio.setChecked(exam_mode == "中考")
        self.zhongkao_radio.toggled.connect(self.on_exam_type_changed)
        self.exam_type_group.addButton(self.zhongkao_radio)
        mode_layout.addWidget(self.zhongkao_radio)

        self.gaokao_radio = RadioButton()
        self.gaokao_radio.setText("高考")
        self.gaokao_radio.setChecked(exam_mode == "高考")
        self.gaokao_radio.toggled.connect(self.on_exam_type_changed)
        self.exam_type_group.addButton(self.gaokao_radio)
        mode_layout.addWidget(self.gaokao_radio)

        region_left_layout.addWidget(mode_card)

        year_label = QLabel("考试年份:")
        region_left_layout.addWidget(year_label)

        self.region_year_combo = EditableComboBox()
        self.region_year_combo.setObjectName("regionYearCombo")
        FluentStyleSheet.COMBO_BOX.apply(self.region_year_combo)
        current_year = datetime.datetime.now().year
        year_items = [str(y) for y in range(current_year - 8, current_year + 16)]
        self.region_year_combo.addItems(year_items)
        if hasattr(self.region_year_combo, "lineEdit") and self.region_year_combo.lineEdit() is not None:
            self.region_year_combo.lineEdit().setValidator(QIntValidator(1900, 9999, self))
            self.region_year_combo.lineEdit().setPlaceholderText("可手动输入年份")
            self.region_year_combo.lineEdit().editingFinished.connect(
                lambda: self.on_region_year_changed(self.region_year_combo.currentText())
            )
        year_index = self.region_year_combo.findText(str(self.exam_year))
        if year_index < 0:
            self.region_year_combo.addItem(str(self.exam_year))
            year_index = self.region_year_combo.findText(str(self.exam_year))
        self.region_year_combo.setCurrentIndex(year_index)
        self.region_year_combo.currentTextChanged.connect(self.on_region_year_changed)
        region_left_layout.addWidget(self.region_year_combo)

        # 添加省份选择下拉框
        province_label = QLabel("选择省份或城市:")
        region_left_layout.addWidget(province_label)

        self.province_combo = ComboBox()
        FluentStyleSheet.COMBO_BOX.apply(self.province_combo)
        # 修复类型错误：将dict_keys转换为列表
        self.province_combo.addItems(list(self.exam_dates.keys()))
        self.province_combo.setCurrentIndex(0)
        self.province_combo.currentTextChanged.connect(self.on_province_selected)
        region_left_layout.addWidget(self.province_combo)

        # 添加考试科目选择框
        exam_type_label = QLabel("考试科目:")
        region_left_layout.addWidget(exam_type_label)

        self.exam_type_combo = ComboBox()
        FluentStyleSheet.COMBO_BOX.apply(self.exam_type_combo)
        self.exam_type_combo.setEnabled(False)  # 初始状态禁用，等待选择省份
        self.exam_type_combo.currentTextChanged.connect(self.on_exam_type_selected)
        region_left_layout.addWidget(self.exam_type_combo)

        region_left_layout.addStretch(1)

        region_right_card = CardWidget()
        region_right_layout = QVBoxLayout(region_right_card)
        region_right_layout.setContentsMargins(12, 10, 12, 12)
        region_right_layout.setSpacing(10)

        region_right_title = QLabel("当前选择")
        region_right_title.setObjectName("sectionTitle")
        region_right_layout.addWidget(region_right_title)

        self.region_preview_label = QLabel()
        self.region_preview_label.setWordWrap(True)
        self.region_preview_label.setObjectName("hintLabel")
        region_right_layout.addWidget(self.region_preview_label)

        region_note_label = QLabel("注意：以上考试日期信息来自网络整理，仅供参考。\n"
                  "各地考试安排可能会有调整，请以当地教育部门最新通知为准。")
        region_note_label.setObjectName("noteLabel")
        region_note_label.setWordWrap(True)
        region_right_layout.addWidget(region_note_label)

        region_right_layout.addStretch(1)

        region_body.addWidget(region_left_card, 2)
        region_body.addWidget(region_right_card, 1)
        region_layout.addLayout(region_body)

        self.selector_stack.addWidget(region_page)

        # 日历选择页
        calendar_page = QWidget()
        calendar_layout = QVBoxLayout(calendar_page)
        calendar_layout.setContentsMargins(0, 0, 0, 0)
        calendar_layout.setSpacing(10)

        self.calendar_widget = FastCalendarPicker()
        self.calendar_widget.setObjectName("calendarStrip")
        self.calendar_widget.setDate(QDate.currentDate().addMonths(3))
        self.calendar_widget.setFixedHeight(36)
        self.calendar_widget.setMaximumWidth(320)
        self.calendar_widget.dateChanged.connect(self.on_calendar_date_selected)

        calendar_layout.addWidget(self.calendar_widget)

        custom_card = CardWidget()
        custom_card_layout = QVBoxLayout(custom_card)
        custom_card_layout.setContentsMargins(12, 10, 12, 12)
        custom_card_layout.setSpacing(8)

        custom_title = QLabel("自定义文本设置")
        custom_title.setObjectName("sectionTitle")
        custom_card_layout.addWidget(custom_title)

        custom_help_label = QLabel("在文本中使用{time}标记来指定倒计时数字的位置")
        custom_help_label.setWordWrap(True)
        custom_help_label.setObjectName("hintLabel")
        custom_card_layout.addWidget(custom_help_label)

        self.custom_mode_check = CheckBox("启用自定义文本")
        self.custom_mode_check.setChecked(exam_mode == "自定义")
        self.custom_mode_check.toggled.connect(self.on_custom_mode_toggled)
        custom_card_layout.addWidget(self.custom_mode_check)

        self.custom_text_input = LineEdit()
        self.custom_text_input.setText(self.custom_text_template)
        self.custom_text_input.setPlaceholderText("例如：距离目标仅剩{time}天")
        FluentStyleSheet.LINE_EDIT.apply(self.custom_text_input)
        custom_card_layout.addWidget(self.custom_text_input)

        self.custom_card = custom_card
        self.custom_text_input.setEnabled(exam_mode == "自定义")
        calendar_layout.addWidget(custom_card)

        calendar_layout.addStretch(1)

        # 日期页就是日历页 + 自定义文本
        self.selector_stack.addWidget(calendar_page)

        # 显示与外观页
        appearance_page = QWidget()
        appearance_layout = QVBoxLayout(appearance_page)
        appearance_layout.setContentsMargins(0, 0, 0, 0)
        appearance_layout.setSpacing(10)

        appearance_card = CardWidget()
        appearance_card_layout = QVBoxLayout(appearance_card)
        appearance_card_layout.setContentsMargins(12, 10, 12, 12)
        appearance_card_layout.setSpacing(10)

        appearance_title = QLabel("显示与外观")
        appearance_title.setObjectName("sectionTitle")
        appearance_card_layout.addWidget(appearance_title)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("显示模式:"))
        self.watermark_mode_radio = RadioButton()
        self.watermark_mode_radio.setText("水印")
        self.visible_mode_radio = RadioButton()
        self.visible_mode_radio.setText("高可见度")
        self.display_mode_group = QButtonGroup(self)
        self.display_mode_group.addButton(self.watermark_mode_radio)
        self.display_mode_group.addButton(self.visible_mode_radio)
        self.watermark_mode_radio.setChecked(self.display_mode == "watermark")
        self.visible_mode_radio.setChecked(self.display_mode == "visible")
        self.watermark_mode_radio.toggled.connect(self._sync_color_controls)
        self.visible_mode_radio.toggled.connect(self._sync_color_controls)
        mode_row.addWidget(self.watermark_mode_radio)
        mode_row.addWidget(self.visible_mode_radio)
        mode_row.addStretch(1)
        appearance_card_layout.addLayout(mode_row)

        precision_row = QHBoxLayout()
        precision_row.addWidget(QLabel("精度:"))
        self.precision_combo = ComboBox()
        FluentStyleSheet.COMBO_BOX.apply(self.precision_combo)
        for i in range(9):
            self.precision_combo.addItem(f"{i}位小数")
        self.precision_combo.setCurrentIndex(max(0, min(8, int(self.display_precision))))
        precision_row.addWidget(self.precision_combo)
        precision_row.addStretch(1)
        appearance_card_layout.addLayout(precision_row)

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("字体缩放:"))
        self.font_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_scale_slider.setRange(80, 160)
        self.font_scale_slider.setValue(max(80, min(160, int(self.font_scale))))
        self.font_scale_value_label = QLabel(f"{self.font_scale_slider.value()}%")
        self.font_scale_slider.valueChanged.connect(
            lambda v: self.font_scale_value_label.setText(f"{v}%")
        )
        scale_row.addWidget(self.font_scale_slider, 1)
        scale_row.addWidget(self.font_scale_value_label)
        appearance_card_layout.addLayout(scale_row)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("字体颜色:"))
        self.font_color_button = ColorPickerButton(QColor(self._get_active_mode_color()), "选择颜色", self)
        self.font_color_button.colorChanged.connect(self.on_font_color_changed)
        color_row.addWidget(self.font_color_button)
        self.pick_screen_color_button = PushButton("从屏幕取色")
        self.pick_screen_color_button.clicked.connect(self.pick_color_from_screen)
        color_row.addWidget(self.pick_screen_color_button)
        self.restore_default_colors_button = PushButton("恢复默认颜色")
        self.restore_default_colors_button.clicked.connect(self._restore_default_colors)
        color_row.addWidget(self.restore_default_colors_button)
        self.color_preview_label = QLabel(self._get_active_mode_color())
        self.color_preview_label.setObjectName("colorPreview")
        self._update_color_preview()
        color_row.addWidget(self.color_preview_label, 1)
        appearance_card_layout.addLayout(color_row)

        position_title = QLabel("窗口位置")
        position_title.setObjectName("sectionTitle")
        appearance_card_layout.addWidget(position_title)

        position_preview = QFrame()
        position_preview.setObjectName("positionPreview")
        position_preview.setFixedSize(280, 170)
        position_layout = QVBoxLayout(position_preview)
        position_layout.setContentsMargins(12, 10, 12, 10)
        position_layout.setSpacing(10)

        self.position_buttons = {}
        top_row = QHBoxLayout()
        bottom_row = QHBoxLayout()

        self.position_buttons["left_top"] = QPushButton("●")
        self.position_buttons["right_top"] = QPushButton("●")
        self.position_buttons["left_bottom"] = QPushButton("●")
        self.position_buttons["right_bottom"] = QPushButton("●")

        for key, btn in self.position_buttons.items():
            btn.setObjectName("positionDot")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, p=key: self.set_window_position(p))

        top_row.addWidget(self.position_buttons["left_top"])
        top_row.addStretch(1)
        top_row.addWidget(self.position_buttons["right_top"])
        bottom_row.addWidget(self.position_buttons["left_bottom"])
        bottom_row.addStretch(1)
        bottom_row.addWidget(self.position_buttons["right_bottom"])

        position_layout.addLayout(top_row)
        position_layout.addStretch(1)
        position_layout.addLayout(bottom_row)
        appearance_card_layout.addWidget(position_preview)
        self._refresh_position_buttons()

        appearance_layout.addWidget(appearance_card)
        appearance_layout.addStretch(1)
        self.selector_stack.addWidget(appearance_page)

        self.selector_nav.addItem(
            routeKey="region",
            icon=FIF.APPLICATION,
            text="按地区选择",
            onClick=lambda: self.set_selector_page(0),
            tooltip="按地区选择"
        )
        self.selector_nav.addItem(
            routeKey="calendar",
            icon=FIF.CALENDAR,
            text="按日期选择",
            onClick=lambda: self.set_selector_page(1),
            tooltip="按日期选择"
        )
        self.selector_nav.addItem(
            routeKey="display",
            icon=FIF.BRUSH,
            text="显示与外观",
            onClick=lambda: self.set_selector_page(2),
            tooltip="显示与外观"
        )

        # 全局按钮布局：所有页面都可见
        global_button_layout = QHBoxLayout()
        global_button_layout.setSpacing(8)
        global_button_layout.setContentsMargins(0, 4, 0, 0)

        global_button_layout.addStretch(1)

        self.global_save_button = PrimaryPushButton()
        self.global_save_button.setText("保存")
        self.global_save_button.setProperty("class", "accent")
        self.global_save_button.setFixedWidth(86)
        self.global_save_button.setFixedHeight(32)
        self.global_save_button.clicked.connect(self.save_current_selection)
        global_button_layout.addWidget(self.global_save_button)

        self.global_close_button = PushButton()
        self.global_close_button.setText("关闭")
        self.global_close_button.setFixedWidth(78)
        self.global_close_button.setFixedHeight(32)
        self.global_close_button.clicked.connect(self.reject)
        global_button_layout.addWidget(self.global_close_button)

        layout.addLayout(global_button_layout)

        # 根据当前选择的模式更新界面状态
        self.update_ui_based_on_mode(exam_mode)
        self._refresh_region_preview()

    def update_ui_based_on_mode(self, mode):
        """根据当前选择的模式更新UI元素的可见性"""
        self.selector_nav.setVisible(True)
        self.selector_stack.setVisible(True)

        if mode == "中考" or mode == "高考":
            self.set_selector_page(0)
            self.custom_mode_check.blockSignals(True)
            self.custom_mode_check.setChecked(False)
            self.custom_mode_check.blockSignals(False)
            self.custom_text_input.setEnabled(False)
        else:
            self.set_selector_page(1)
            self.custom_mode_check.blockSignals(True)
            self.custom_mode_check.setChecked(True)
            self.custom_mode_check.blockSignals(False)
            self.custom_text_input.setEnabled(True)
            self.calendar_widget.setDate(self.calendar_widget.date)

    def on_custom_mode_toggled(self, checked):
        """切换自定义文本模式"""
        if checked:
            if self.current_exam_mode in ("中考", "高考"):
                self._last_non_custom_mode = self.current_exam_mode
            self.current_exam_mode = "自定义"
            self.setWindowTitle("设置自定义倒计时")
            self.set_selector_page(1)
            self.custom_text_input.setEnabled(True)
        else:
            self.current_exam_mode = self._last_non_custom_mode
            if self.current_exam_mode == "中考":
                self.setWindowTitle("设置中考日期")
            elif self.current_exam_mode == "高考":
                self.setWindowTitle("设置高考日期")
            self.custom_text_input.setEnabled(False)

    def _on_selector_nav_mode_changed(self, mode):
        """根据导航模式切换左侧宽度，展开显示文字，收起显示图标"""
        if mode == NavigationDisplayMode.EXPAND:
            self.selector_nav.setFixedWidth(170)
        else:
            self.selector_nav.setFixedWidth(52)

    def set_selector_page(self, index):
        """切换右侧内容页面"""
        self.selector_stack.setCurrentIndex(index)

    def set_window_position(self, position):
        """设置窗口位置并刷新按钮状态"""
        self.window_position = position
        self._refresh_position_buttons()

    def _refresh_position_buttons(self):
        """刷新位置按钮选中状态"""
        if not hasattr(self, "position_buttons"):
            return
        for key, btn in self.position_buttons.items():
            btn.setChecked(key == self.window_position)

    def on_font_color_changed(self, color):
        """Fluent 颜色按钮变化时同步配置"""
        if color.isValid():
            self._set_active_mode_color(color.name())
            self._update_color_preview()

    def pick_color_from_screen(self):
        """从屏幕任意位置拾取颜色"""
        self.hide()
        self._screen_picker = ScreenColorPicker(self)
        self._screen_picker.colorPicked.connect(self._apply_screen_picked_color)
        self._screen_picker.canceled.connect(self._restore_after_screen_pick)
        self._screen_picker.show()

    def _apply_screen_picked_color(self, color):
        if color.isValid():
            self._set_active_mode_color(color.name())
            if hasattr(self, "font_color_button"):
                self.font_color_button.setColor(color)
            self._update_color_preview()
        self._restore_after_screen_pick()

    def _get_active_mode_color(self):
        return self.watermark_color if self.watermark_mode_radio.isChecked() else self.visible_color

    def _set_active_mode_color(self, color_hex):
        if self.watermark_mode_radio.isChecked():
            self.watermark_color = color_hex
        else:
            self.visible_color = color_hex

    def _sync_color_controls(self, *_):
        current = self._get_active_mode_color()
        self.font_color_button.setColor(QColor(current))
        self._update_color_preview()

    def _restore_default_colors(self):
        self.watermark_color = DEFAULT_WATERMARK_COLOR
        self.visible_color = DEFAULT_VISIBLE_COLOR
        self._sync_color_controls()

    def _restore_after_screen_pick(self):
        self.show()
        self.activateWindow()

    def _update_color_preview(self):
        """刷新颜色预览"""
        if not hasattr(self, "color_preview_label"):
            return
        current_color = self._get_active_mode_color()
        self.color_preview_label.setText(current_color)
        preview_text_color = "#000000" if QColor(current_color).lightness() > 150 else "#ffffff"
        self.color_preview_label.setStyleSheet(
            f"background: {current_color}; color: {preview_text_color}; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 8px; padding: 2px 8px;"
        )

    def on_region_year_changed(self, year_text):
        """地区页年份变化时更新当前日期"""
        year_text = year_text.strip()
        if not year_text or not year_text.isdigit():
            return

        year_value = int(year_text)
        if year_value < 1900 or year_value > 9999:
            return

        self.exam_year = year_value
        if self.region_year_combo.findText(str(year_value)) < 0:
            self.region_year_combo.addItem(str(year_value))

        current_exam_type = self.exam_type_combo.currentText() if hasattr(self, "exam_type_combo") else ""
        if current_exam_type:
            self.on_exam_type_selected(current_exam_type)
        else:
            self._refresh_region_preview()

    def _refresh_region_preview(self):
        """刷新地区页的当前选择预览"""
        if not hasattr(self, "region_preview_label"):
            return

        province_name = self.province_combo.currentText() if hasattr(self, "province_combo") else ""
        exam_type = self.exam_type_combo.currentText() if hasattr(self, "exam_type_combo") else ""
        date_text = self.calendar_widget.date.toString("yyyy年MM月dd日") if hasattr(self, "calendar_widget") else ""

        if province_name and province_name != "请选择省份或城市" and exam_type:
            self.region_preview_label.setText(
                f"年份：{self.exam_year}\n"
                f"地区：{province_name}\n"
                f"科目：{exam_type}\n"
                f"日期：{date_text}"
            )
        else:
            self.region_preview_label.setText("先选择省份和科目，右侧会显示当前日期与确认入口。")

    @staticmethod
    def _calculate_exam_year():
        """计算考试年份"""
        current_date = datetime.datetime.now()
        current_year = current_date.year
        return current_year + 1 if current_date > datetime.datetime(current_year, 6, 1) else current_year

    @staticmethod
    def _convert_to_full_dates(base_dates):
        """将基础日期转换为包含年份的完整日期"""
        full_dates = {}
        current_date = datetime.datetime.now()

        for province, exam_types in base_dates.items():
            full_dates[province] = {}
            for exam_type, date_tuple in exam_types.items():
                if date_tuple is None:
                    full_dates[province][exam_type] = None
                    continue

                month, day = date_tuple
                # 计算正确的年份
                year = current_date.year

                # 如果当前日期已过这个月日，使用明年
                if current_date > datetime.datetime(year, month, day):
                    year += 1

                full_dates[province][exam_type] = QDate(year, month, day)

        return full_dates

    def on_exam_type_changed(self):
        """当选择考试类型（中考/高考/自定义）变化时更新界面"""
        # 重新计算考试年份
        if hasattr(self, "region_year_combo") and self.region_year_combo.currentText().isdigit():
            self.exam_year = int(self.region_year_combo.currentText())
        else:
            self.exam_year = self._calculate_exam_year()

        if self.zhongkao_radio.isChecked():
            self.current_exam_mode = "中考"
            self._last_non_custom_mode = "中考"
            # 使用基础数据重新生成日期
            self.zhongkao_dates = self._convert_to_full_dates(self.base_zhongkao_dates)
            self.exam_dates = self.zhongkao_dates
            self.setWindowTitle("设置中考日期")
        elif self.gaokao_radio.isChecked():
            self.current_exam_mode = "高考"
            self._last_non_custom_mode = "高考"
            # 使用基础数据重新生成日期
            self.gaokao_dates = self._convert_to_full_dates(self.base_gaokao_dates)
            self.exam_dates = self.gaokao_dates
            self.setWindowTitle("设置高考日期")
        else:  # 自定义模式
            self.current_exam_mode = "自定义"
            self.setWindowTitle("设置自定义倒计时")

        # 更新UI组件显示状态
        self.update_ui_based_on_mode(self.current_exam_mode)

        if self.current_exam_mode in ("中考", "高考") and hasattr(self, "custom_mode_check"):
            self.custom_mode_check.blockSignals(True)
            self.custom_mode_check.setChecked(False)
            self.custom_mode_check.blockSignals(False)
            self.custom_text_input.setEnabled(False)

        self._refresh_region_preview()

        if self.current_exam_mode != "自定义":
            # 更新省份下拉框
            current_province = self.province_combo.currentText()
            self.province_combo.clear()
            # 修复类型错误：将dict_keys转换为列表
            province_list = list(self.exam_dates.keys())
            self.province_combo.addItems(province_list)

            # 尝试保持之前选择的省份（如果新列表中存在）
            index = self.province_combo.findText(current_province)
            if index >= 0:
                self.province_combo.setCurrentIndex(index)
            else:
                self.province_combo.setCurrentIndex(0)
                self.exam_type_combo.clear()
                self.exam_type_combo.setEnabled(False)

    def on_province_selected(self, province_name):
        """当选择省份时更新考试类型和日期"""
        if province_name == "请选择省份或城市":
            self.exam_type_combo.clear()
            self.exam_type_combo.setEnabled(False)
            return

        # 获取该省份/城市的考试类型
        exam_types = self.exam_dates.get(province_name, {})

        # 更新考试类型下拉框
        self.exam_type_combo.clear()
        # 修复类型错误：将dict_keys转换为列表
        self.exam_type_combo.addItems(list(exam_types.keys()))

        # 如果有考试类型，启用下拉框
        if exam_types:
            self.exam_type_combo.setEnabled(True)

            # 默认选择第一个考试类型
            if self.exam_type_combo.count() > 0:
                first_exam_type = self.exam_type_combo.itemText(0)
                self.on_exam_type_selected(first_exam_type)
        else:
            self.exam_type_combo.setEnabled(False)
            self._refresh_region_preview()

    def on_exam_type_selected(self, exam_type):
        """当选择考试类型时更新日期"""
        if not exam_type:
            return

        province_name = self.province_combo.currentText()
        exam_types = self.exam_dates.get(province_name, {})
        selected_date = exam_types.get(exam_type)

        if selected_date:
            selected_date = QDate(self.exam_year, selected_date.month(), selected_date.day())
            self.calendar_widget.setDate(selected_date)

        self._refresh_region_preview()

    def on_calendar_date_selected(self):
        """当在日历中选择日期时更新日期编辑框"""
        self._refresh_region_preview()

    def get_selected_date(self):
        """获取用户选择的日期"""
        qdate = self.calendar_widget.date
        return datetime.datetime(qdate.year(), qdate.month(), qdate.day())

    def get_selected_exam_type(self):
        """获取用户选择的考试类型"""
        if self.exam_type_combo.isEnabled() and self.exam_type_combo.currentText():
            return self.exam_type_combo.currentText()
        return "文化课"  # 默认返回文化课

    def get_selected_exam_mode(self):
        """获取用户选择的考试模式（中考/高考/自定义）"""
        return self.current_exam_mode

    def get_custom_text_template(self):
        """获取用户输入的自定义文本模板"""
        if self.custom_mode_check.isChecked():
            return self.custom_text_input.text()
        return None

    def save_current_selection(self):
        """立即保存当前设置到父窗口，但不关闭对话框"""
        parent = self.parent()
        if parent is None or not hasattr(parent, "save_config"):
            return

        selected_date = self.get_selected_date()

        current_date = datetime.datetime.now()
        if selected_date < current_date:
            selected_date = datetime.datetime(
                current_date.year + 1,
                selected_date.month,
                selected_date.day
            )

        parent.target_date = selected_date
        parent.exam_mode = self.get_selected_exam_mode()

        if parent.exam_mode == "自定义":
            parent.custom_text_template = self.get_custom_text_template() or parent.custom_text_template
            parent.exam_type = "自定义"
        else:
            parent.exam_type = self.get_selected_exam_type()

        if parent.exam_mode == "自定义":
            parent.setWindowTitle("自定义倒计时")
        else:
            parent.setWindowTitle(f"{parent.exam_mode}倒计时")

        # 保存显示与外观设置
        parent.display_mode = "visible" if self.visible_mode_radio.isChecked() else "watermark"
        parent.position = self.window_position
        parent.precision = self.precision_combo.currentIndex()
        parent.font_scale = self.font_scale_slider.value()
        parent.watermark_color = self.watermark_color
        parent.visible_color = self.visible_color
        parent.font_color = self.visible_color
        if hasattr(parent, "apply_countdown_font"):
            parent.apply_countdown_font()
        if hasattr(parent, "update_timer_interval"):
            parent.update_timer_interval()
        if hasattr(parent, "update_position"):
            parent.update_position()

        parent.save_config()
        if hasattr(parent, "update_countdown"):
            parent.update_countdown()
        if hasattr(parent, "_update_tray_menu_state"):
            parent._update_tray_menu_state()

    def reject(self):
        """关闭对话框前自动保存当前设置"""
        self.save_current_selection()
        super().reject()

    def closeEvent(self, event):
        """点击右上角关闭按钮时自动保存当前设置"""
        self.save_current_selection()
        super().closeEvent(event)

class CountdownWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化实例特性
        self.tray_menu = None
        self.position_menu = None
        self.display_menu = None
        self.mode_menu = None
        self.mode_actions = {}
        self.pause_action = None
        self.tray_icon = None
        self.last_days_left = None

        # 设置窗口属性 - 无边框和背景透明，添加鼠标事件穿透标志
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool |
                           Qt.WindowType.WindowTransparentForInput)  # 添加这个标志使鼠标事件穿透窗口
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 默认配置
        self.position = "left_top"  # 默认左上角位置
        self.window_width = 300
        self.window_height = 80
        self.precision = 5  # 默认5位小数
        self.display_mode = "watermark"  # 默认水印模式
        self.font_scale = 100
        self.watermark_color = DEFAULT_WATERMARK_COLOR
        self.visible_color = DEFAULT_VISIBLE_COLOR
        self.font_color = self.visible_color
        self.paused = False
        self.exam_type = "文化课"  # 默认考试类型
        self.exam_mode = "中考"  # 默认考试模式（中考/高考）
        # 自定义模式的文本模板
        self.custom_text_template = "{time}天后，未来将会怎样？"
        # 默认目标日期，将在加载配置或用户设定后更改
        self.target_date = None

        # 加载配置（如果存在）
        self.load_config()

        # 如果没有设置目标日期，则提示用户设置
        if self.target_date is None:
            self.show_date_select_dialog()

        if self.exam_mode == "自定义":
            self.setWindowTitle("自定义倒计时")
        else:
            self.setWindowTitle(f"{self.exam_mode}倒计时")

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 设置完全透明背景
        palette = central_widget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))  # 完全透明
        central_widget.setAutoFillBackground(True)
        central_widget.setPalette(palette)

        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距

        # 创建标签
        self.countdown_label = QLabel()
        font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        self.countdown_label.setFont(font)
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.countdown_label.setContentsMargins(0, 0, 0, 0)
        self.countdown_label.setMargin(0)
        self.apply_countdown_font()
        layout.addWidget(self.countdown_label)

        # 创建定时器来更新倒计时
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)

        # 初始设置窗口位置
        self.update_position()

        # 根据精度设置初始更新间隔
        self.update_timer_interval()

        # 初始更新显示
        self.update_countdown()

        # 创建系统托盘图标
        self.create_tray_icon()

    @staticmethod
    def _convert_to_full_dates(base_dates):
        """将基础日期转换为包含年份的完整字符串表示"""
        full_dates = {}
        current_date = datetime.datetime.now()

        for province, exam_types in base_dates.items():
            full_dates[province] = {}
            for exam_type, date_tuple in exam_types.items():
                if date_tuple is None:
                    full_dates[province][exam_type] = None
                    continue

                month, day = date_tuple
                # 计算正确的年份
                year = current_date.year

                # 如果当前日期已过这个月日，使用明年
                if current_date > datetime.datetime(year, month, day):
                    year += 1

                # 保存为字符串格式，适合JSON存储
                full_dates[province][exam_type] = f"{year}-{month}-{day}"

        return full_dates

    def load_config(self):
        """从配置文件加载设置"""
        if not os.path.exists(CONFIG_FILE):
            print(f"配置文件不存在，将使用默认设置。配置路径: {CONFIG_FILE}")
            self.write_default_config()
            return

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 检查版本号
            file_version = config.get("version", "0")
            if file_version < VERSION:
                print(f"检测到新版本({VERSION})，更新配置文件...")
                self.write_default_config()
                return

            # 版本号相同，加载配置，并尊重配置文件中的日期设置
            self.position = config.get('position', self.position)
            self.precision = config.get('precision', self.precision)
            self.display_mode = config.get('display_mode', self.display_mode)
            self.font_scale = config.get('font_scale', self.font_scale)
            legacy_font_color = config.get('font_color', self.visible_color)
            self.watermark_color = config.get('watermark_color', legacy_font_color)
            self.visible_color = config.get('visible_color', legacy_font_color)
            self.font_color = self.visible_color
            self.window_width = config.get('window_width', self.window_width)
            self.window_height = config.get('window_height', self.window_height)
            self.exam_type = config.get('exam_type', self.exam_type)
            self.exam_mode = config.get('exam_mode', self.exam_mode)
            self.custom_text_template = config.get('custom_text_template', self.custom_text_template)

            # 尝试加载考试日期列表
            dates = config.get('dates', {})
            # 将加载的日期应用到DateSelectDialog的基础数据中
            if 'zhongkao' in dates and dates['zhongkao']:
                self._update_base_dates_from_config(DateSelectDialog.base_zhongkao_dates, dates['zhongkao'])
            if 'gaokao' in dates and dates['gaokao']:
                self._update_base_dates_from_config(DateSelectDialog.base_gaokao_dates, dates['gaokao'])

            # 加载目标日期 - 完全按照配置文件中的日期，不自动调整
            target_date_str = config.get('target_date')
            if target_date_str:
                try:
                    date_parts = list(map(int, target_date_str.split('-')))
                    self.target_date = datetime.datetime(date_parts[0], date_parts[1], date_parts[2])
                    print(f"按配置文件加载日期: {self.target_date.strftime('%Y-%m-%d')}")
                except (ValueError, IndexError) as e:
                    print(f"日期解析错误: {e}，将使用默认日期")
                    self.target_date = None

            print(f"成功从配置文件加载设置: {CONFIG_FILE}")
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            self.target_date = None

    @staticmethod
    def _update_base_dates_from_config(base_dates_dict, config_dates_dict):
        """从配置文件的日期字典更新基础日期字典"""
        for province, exam_types in config_dates_dict.items():
            if not isinstance(exam_types, dict):
                continue

            if province not in base_dates_dict or not isinstance(base_dates_dict.get(province), dict):
                base_dates_dict[province] = {}

            for exam_type, date_str in exam_types.items():
                if date_str is None:
                    base_dates_dict[province][exam_type] = None
                    continue

                try:
                    # 从日期字符串(例如"2024-6-7")提取月和日
                    year, month, day = map(int, date_str.split('-'))
                    base_dates_dict[province][exam_type] = (month, day)
                except (ValueError, TypeError) as e:
                    print(f"解析日期'{date_str}'失败: {e}")
                    continue

    def write_default_config(self):
        """写入默认配置，包括版本号和考试日期列表"""
        try:
            # 确保配置目录存在
            os.makedirs(CONFIG_DIR, exist_ok=True)

            # 默认考试日期列表 - 使用本类的转换方法
            default_dates = {
                "zhongkao": self._convert_to_full_dates(DateSelectDialog.base_zhongkao_dates),
                "gaokao": self._convert_to_full_dates(DateSelectDialog.base_gaokao_dates)
            }

            # 构建默认配置
            config = {
                "version": VERSION,
                "position": self.position,
                "precision": self.precision,
                "display_mode": self.display_mode,
                "font_scale": self.font_scale,
                "font_color": self.visible_color,
                "watermark_color": self.watermark_color,
                "visible_color": self.visible_color,
                "window_width": self.window_width,
                "window_height": self.window_height,
                "target_date": None,
                "exam_type": self.exam_type,
                "exam_mode": self.exam_mode,
                "custom_text_template": self.custom_text_template,
                "dates": default_dates
            }

            # 写入配置文件
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            print(f"默认配置已写入: {CONFIG_FILE}")
        except Exception as e:
            print(f"写入默认配置时出错: {e}")

    def save_config(self):
        """保存当前设置到配置文件"""
        try:
            # 确保配置目录存在
            os.makedirs(CONFIG_DIR, exist_ok=True)

            target_date_str = None
            if self.target_date:
                target_date_str = f"{self.target_date.year}-{self.target_date.month}-{self.target_date.day}"

            # 保存所有考试日期列表
            dates = {
                "zhongkao": self._convert_to_full_dates(DateSelectDialog.base_zhongkao_dates),
                "gaokao": self._convert_to_full_dates(DateSelectDialog.base_gaokao_dates)
            }

            config = {
                'version': VERSION,  # 添加版本号
                'position': self.position,
                'precision': self.precision,
                'display_mode': self.display_mode,
                'font_scale': self.font_scale,
                'font_color': self.visible_color,
                'watermark_color': self.watermark_color,
                'visible_color': self.visible_color,
                'window_width': self.window_width,
                'window_height': self.window_height,
                'target_date': target_date_str,
                'exam_type': self.exam_type,
                'exam_mode': self.exam_mode,
                'custom_text_template': self.custom_text_template,
                'dates': dates  # 保存考试日期列表
            }

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            print(f"设置已保存到配置文件: {CONFIG_FILE}")
        except Exception as e:
            print(f"保存配置文件出错: {e}")

    def reset_to_factory(self):
        """恢复出厂设置"""
        try:
            # 重置所有设置为默认值
            self.position = "left_top"
            self.window_width = 300
            self.window_height = 80
            self.precision = 5
            self.display_mode = "watermark"
            self.font_scale = 100
            self.watermark_color = DEFAULT_WATERMARK_COLOR
            self.visible_color = DEFAULT_VISIBLE_COLOR
            self.font_color = self.visible_color
            self.paused = False
            self.exam_type = "文化课"
            self.exam_mode = "中考"
            self.custom_text_template = "{time}天后，未来将会怎样？"
            self.target_date = None

            # 写入默认配置到文件
            self.write_default_config()

            # 提示用户设置日期
            self.show_date_select_dialog()

            # 更新界面显示
            self.update_position()
            self.update_countdown()

            # 更新托盘菜单选项状态
            self._update_tray_menu_state()

            print("已恢复出厂设置")
        except Exception as e:
            print(f"恢复出厂设置时出错: {e}")

    def _update_tray_menu_state(self):
        """更新托盘菜单中的选项状态"""
        # 更新位置菜单项
        for action in self.position_menu.actions():
            action.setChecked(action.property("position_value") == self.position)

        # 更新显示模式菜单项
        for action in self.display_menu.actions():
            action.setChecked(action.property("mode_value") == self.display_mode)

        # 更新暂停按钮状态和文本
        if self.pause_action:
            self.pause_action.setChecked(self.paused)
            self.pause_action.setText("恢复更新" if self.paused else "暂停更新")
            self.pause_action.setIcon(FIF.PLAY.icon() if self.paused else FIF.PAUSE.icon())

        # 更新模式菜单项
        if self.mode_menu:
            for action in self.mode_menu.actions():
                action.setChecked(action.property("mode_value") == self.exam_mode)

    def show_date_select_dialog(self):
        """显示日期选择对话框"""
        dialog = DateSelectDialog(self, self.exam_mode)
        if dialog.exec():
            selected_date = dialog.get_selected_date()

            # 检查选择的日期是否已过，如果已过则使用明年的相同日期
            current_date = datetime.datetime.now()
            if selected_date < current_date:
                selected_date = datetime.datetime(
                    current_date.year + 1,
                    selected_date.month,
                    selected_date.day
                )

            self.target_date = selected_date
            self.exam_mode = dialog.get_selected_exam_mode()

            if self.exam_mode == "自定义":
                self.custom_text_template = dialog.get_custom_text_template() or self.custom_text_template
                self.exam_type = "自定义"
            else:
                self.exam_type = dialog.get_selected_exam_type()

            # 保存配置
            self.save_config()
            print(f"日期设置为: {self.target_date.strftime('%Y-%m-%d')}，模式: {self.exam_mode}")

            # 更新窗口标题
            if self.exam_mode == "自定义":
                self.setWindowTitle("自定义倒计时")
            else:
                self.setWindowTitle(f"{self.exam_mode}倒计时")
        else:
            # 如果用户取消，则使用默认日期
            if self.target_date is None:  # 只有在没有现有日期时才设置默认值
                current_date = datetime.datetime.now()
                if self.exam_mode == "中考":
                    default_date = datetime.datetime(current_date.year, 6, 24)
                else:  # 高考
                    default_date = datetime.datetime(current_date.year, 6, 7)

                # 如果默认日期已过，使用明年
                if default_date < current_date:
                    default_date = datetime.datetime(
                        current_date.year + 1,
                        default_date.month,
                        default_date.day
                    )

                self.target_date = default_date
                self.exam_type = "文化课" if self.exam_mode == "中考" else "统一科目"
                print(f"用户取消设置，使用默认{self.exam_mode}日期: {self.target_date.strftime('%Y-%m-%d')}")

    def create_tray_icon(self):
        """创建系统托盘图标和菜单"""
        # 检查是否支持系统托盘
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("系统不支持系统托盘")
            return

        # 创建托盘图标菜单
        self.tray_menu = CheckableSystemTrayMenu("", self)
        FluentStyleSheet.MENU.apply(self.tray_menu)
        self.tray_menu.setFont(QFont("Segoe UI", 9))

        position_group = QActionGroup(self)
        position_group.setExclusive(True)
        display_group = QActionGroup(self)
        display_group.setExclusive(True)
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)

        # 添加位置设置菜单
        self.position_menu = RoundMenu("窗口位置", self.tray_menu)
        FluentStyleSheet.MENU.apply(self.position_menu)
        self.tray_menu.addMenu(self.position_menu)

        # 添加四个位置选项
        positions = [
            ("左上角", "left_top"),
            ("右上角", "right_top"),
            ("左下角", "left_bottom"),
            ("右下角", "right_bottom")
        ]

        for pos_name, pos_value in positions:
            action = QAction(pos_name, self)
            action.setIcon(FIF.PIN.icon())
            # 使用setProperty而不是setData
            action.setProperty("position_value", pos_value)
            action.triggered.connect(self.change_position)
            action.setCheckable(True)
            action.setChecked(self.position == pos_value)
            position_group.addAction(action)
            self.position_menu.addAction(action)

        self.tray_menu.addSeparator()

        # 添加显示模式菜单 - 保存为类属性
        self.display_menu = RoundMenu("显示模式", self.tray_menu)
        FluentStyleSheet.MENU.apply(self.display_menu)
        self.tray_menu.addMenu(self.display_menu)

        # 添加水印模式选项
        watermark_action = QAction("水印样式", self)
        watermark_action.setIcon(FIF.BRUSH.icon())
        # 使用setProperty而不是setData
        watermark_action.setProperty("mode_value", "watermark")
        watermark_action.triggered.connect(self.change_display_mode)
        watermark_action.setCheckable(True)
        watermark_action.setChecked(self.display_mode == "watermark")
        display_group.addAction(watermark_action)
        self.display_menu.addAction(watermark_action)

        # 添加高辨识度模式选项
        visible_action = QAction("高辨识度", self)
        visible_action.setIcon(FIF.VIEW.icon())
        # 使用setProperty而不是setData
        visible_action.setProperty("mode_value", "visible")
        visible_action.triggered.connect(self.change_display_mode)
        visible_action.setCheckable(True)
        visible_action.setChecked(self.display_mode == "visible")
        display_group.addAction(visible_action)
        self.display_menu.addAction(visible_action)

        # 添加精度控制菜单项
        precision_menu = RoundMenu("设置精度", self.tray_menu)
        FluentStyleSheet.MENU.apply(precision_menu)
        self.tray_menu.addMenu(precision_menu)

        # 添加不同的精度选项
        for i in range(9):  # 0-8位精度
            action = QAction(f"{i}位小数", self)
            action.setIcon(FIF.CALORIES.icon())
            # 使用setProperty而不是setData
            action.setProperty("precision_value", i)  # 保存精度值
            action.triggered.connect(self.change_precision)
            precision_menu.addAction(action)

        self.tray_menu.addSeparator()

        # 添加暂停/恢复选项
        self.pause_action = QAction("暂停更新", self)
        self.pause_action.setIcon(FIF.PAUSE.icon())
        self.pause_action.setCheckable(True)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.tray_menu.addAction(self.pause_action)

        # 添加切换考试类型的选项
        self.mode_menu = RoundMenu("切换模式", self.tray_menu)
        FluentStyleSheet.MENU.apply(self.mode_menu)
        self.tray_menu.addMenu(self.mode_menu)

        # 中考选项
        zhongkao_action = QAction("中考模式", self)
        zhongkao_action.setIcon(FIF.CERTIFICATE.icon())
        zhongkao_action.setProperty("mode_value", "中考")
        zhongkao_action.triggered.connect(lambda: self.switch_exam_mode("中考"))
        zhongkao_action.setCheckable(True)
        zhongkao_action.setChecked(self.exam_mode == "中考")
        mode_group.addAction(zhongkao_action)
        self.mode_menu.addAction(zhongkao_action)

        # 高考选项
        gaokao_action = QAction("高考模式", self)
        gaokao_action.setIcon(FIF.CERTIFICATE.icon())
        gaokao_action.setProperty("mode_value", "高考")
        gaokao_action.triggered.connect(lambda: self.switch_exam_mode("高考"))
        gaokao_action.setCheckable(True)
        gaokao_action.setChecked(self.exam_mode == "高考")
        mode_group.addAction(gaokao_action)
        self.mode_menu.addAction(gaokao_action)

        # 自定义选项
        custom_action = QAction("自定义模式", self)
        custom_action.setIcon(FIF.EDIT.icon())
        custom_action.setProperty("mode_value", "自定义")
        custom_action.triggered.connect(lambda: self.switch_exam_mode("自定义"))
        custom_action.setCheckable(True)
        custom_action.setChecked(self.exam_mode == "自定义")
        mode_group.addAction(custom_action)
        self.mode_menu.addAction(custom_action)

        self.mode_actions = {
            "中考": zhongkao_action,
            "高考": gaokao_action,
            "自定义": custom_action,
        }

        self.tray_menu.addSeparator()

        # 添加修改日期的选项
        change_date_action = QAction("设置", self)
        change_date_action.setIcon(FIF.SETTING.icon())
        change_date_action.triggered.connect(self.show_date_select_dialog)
        self.tray_menu.addAction(change_date_action)

        # 在退出选项前添加恢复出厂设置选项
        factory_reset_action = QAction("恢复出厂设置", self)
        factory_reset_action.setIcon(FIF.ROTATE.icon())
        factory_reset_action.triggered.connect(self.reset_to_factory)
        self.tray_menu.addAction(factory_reset_action)

        # 添加退出选项
        quit_action = QAction("退出", self)
        quit_action.setIcon(FIF.POWER_BUTTON.icon())
        quit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(quit_action)

        # 创建托盘图标 - 使用自定义图标，而不依赖系统图标
        self.tray_icon = QSystemTrayIcon(self)

        # 创建一个 Fluent 风格托盘图标
        icon_pixmap = QPixmap(16, 16)
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 108, 189))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(1, 1, 14, 14, 4, 4)
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.drawEllipse(5, 5, 6, 6)
        painter.setPen(QPen(QColor(15, 108, 189), 1))
        painter.drawLine(8, 8, 10, 6)
        painter.end()

        self.tray_icon.setIcon(QIcon(icon_pixmap))
        self.tray_icon.setToolTip("考试倒计时")
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)

        # 显示系统托盘图标
        self.tray_icon.show()
        print("系统托盘图标已创建")

    def change_position(self):
        """根据托盘菜单操作更改窗口位置"""
        action = self.sender()
        if action:
            # 获取新的位置
            self.position = action.property("position_value")

            # 更新菜单项选中状态
            for act in self.position_menu.actions():
                act.setChecked(act.property("position_value") == self.position)

            # 更新窗口位置
            self.update_position()

            # 保存配置
            self.save_config()

    def update_position(self):
        """根据当前位置设置更新窗口位置"""
        # 获取整个屏幕的几何信息
        screen_geometry = QApplication.primaryScreen().geometry()
        # 获取排除任务栏后的可用屏幕区域
        available_geometry = QApplication.primaryScreen().availableGeometry()

        # 为左侧和右侧定义不同的边距
        left_margin = 5   # 左侧边距更小
        right_margin = 10  # 右侧边距保持不变
        top_margin = 5    # 顶部边距更小
        bottom_margin = 10 # 底部边距保持不变

        if self.position == "left_top":
            # 左上角 - 使用更小的边距，更靠近边缘
            self.setGeometry(left_margin, top_margin,
                             self.window_width, self.window_height)
        elif self.position == "right_top":
            # 右上角 - 保持原有边距
            self.setGeometry(screen_geometry.width() - self.window_width - right_margin,
                             top_margin,
                             self.window_width, self.window_height)
        elif self.position == "left_bottom":
            # 左下角 - 左侧使用更小的边距
            self.setGeometry(left_margin,
                             available_geometry.height() + available_geometry.y() - self.window_height - bottom_margin,
                             self.window_width, self.window_height)
        elif self.position == "right_bottom":
            # 右下角 - 保持原有边距
            self.setGeometry(screen_geometry.width() - self.window_width - right_margin,
                             available_geometry.height() + available_geometry.y() - self.window_height - bottom_margin,
                             self.window_width, self.window_height)

    def change_display_mode(self):
        """根据托盘菜单操作更改显示模式"""
        action = self.sender()
        if action:
            # 获取新的显示模式
            self.display_mode = action.property("mode_value")

            # 更新菜单项选中状态 - 使用类属性而非findChild
            for act in self.display_menu.actions():
                act.setChecked(act.property("mode_value") == self.display_mode)

            # 更新显示
            self.update_countdown()

            # 保存配置
            self.save_config()

    def tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单击图标
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def change_precision(self):
        """根据托盘菜单操作更改精度"""
        action = self.sender()
        if action:
            old_precision = self.precision
            self.precision = action.property("precision_value")

            # 打印日志以便调试
            print(f"正在切换精度：从 {old_precision} 位小数到 {self.precision} 位小数")

            # 强制停止旧定时器
            if self.timer.isActive():
                self.timer.stop()

            # 根据新精度更新定时器间隔
            self.update_timer_interval()

            # 立即更新显示
            self.update_countdown()

            # 保存配置
            self.save_config()

    def apply_countdown_font(self):
        """根据字体缩放设置应用倒计时字体大小"""
        scaled_size = max(9, int(round(11 * (self.font_scale / 100))))
        self.countdown_label.setFont(QFont("Segoe UI", scaled_size, QFont.Weight.DemiBold))

    @staticmethod
    def _hex_to_rgb(color_hex):
        """将 #RRGGBB 颜色转换为 RGB 三元组"""
        color = QColor(color_hex)
        if not color.isValid():
            color = QColor("#0f1419")
        return color.red(), color.green(), color.blue()

    def update_timer_interval(self):
        """根据当前精度计算并设置合适的定时器更新间隔"""
        # 一天 = 86400 秒
        # 对于n位小数，最小变化是 10^(-n) 天 = 10^(-n) * 86400 秒
        # 为了观察到变化，更新间隔应小于这个值

        # 计算当前精度下最小变化的时间（秒）
        change_seconds = 86400 * (10 ** (-self.precision))

        # 根据精度级别设置不同的比例因子
        # 这里的比例因子可以根据实际需求进行调整
        if self.precision <= 1:
            factor = 0.95
        elif self.precision <= 3:
            factor = 0.95
        else:
            factor = 0.9

        # 计算更新间隔（毫秒）
        interval = int(change_seconds * factor * 1000)

        # 设置更新间隔的上下限
        min_interval = 10    # 最小10毫秒，避免过于频繁更新
        max_interval = 60000 # 最大60秒，确保即使是低精度也有合理的更新频率

        interval = max(min_interval, min(interval, max_interval))

        # 先确保定时器真的停止了
        if self.timer.isActive():
            self.timer.stop()

        # 为了确保重启干净，使用短延迟
        QTimer.singleShot(10, lambda: self._start_timer_with_interval(interval))

        print(f"精度设置为 {self.precision} 位小数，变化时间 {change_seconds:.6f} 秒，更新间隔设为 {interval} 毫秒")

    def _start_timer_with_interval(self, interval):
        """安全地启动定时器，确保旧定时器已停止"""
        try:
            if not self.timer.isActive() and not self.paused:
                self.timer.start(interval)
                print(f"定时器成功启动，间隔: {interval}毫秒")
            elif self.paused:
                print("暂停状态中，定时器未启动")
        except Exception as e:
            print(f"启动定时器时出错: {e}")

    def toggle_pause(self):
        """切换暂停/恢复状态"""
        self.paused = not self.paused

        if self.paused:
            self.pause_action.setText("恢复更新")
            self.pause_action.setIcon(FIF.PLAY.icon())
            # 确保定时器停止
            if self.timer.isActive():
                self.timer.stop()
                print("定时器已暂停")
        else:
            self.pause_action.setText("暂停更新")
            self.pause_action.setIcon(FIF.PAUSE.icon())
            # 恢复时重新计算并设置定时器间隔
            self.update_timer_interval()
            # 恢复时立即更新一次
            self.update_countdown()
            print("定时器已恢复")

    def switch_exam_mode(self, new_mode=None):
        """切换考试模式（中考/高考/自定义）"""
        # 如果没有指定新模式，则循环切换
        if new_mode is None:
            if self.exam_mode == "中考":
                new_mode = "高考"
            elif self.exam_mode == "高考":
                new_mode = "自定义"
            else:
                new_mode = "中考"

        # 切换考试模式
        self.exam_mode = new_mode

        # 更新窗口标题
        if self.exam_mode == "自定义":
            self.setWindowTitle("自定义倒计时")
        else:
            self.setWindowTitle(f"{self.exam_mode}倒计时")

        # 重置考试类型
        if self.exam_mode == "中考":
            self.exam_type = "文化课"
        elif self.exam_mode == "高考":
            self.exam_type = "统一科目"
        else:
            self.exam_type = "自定义"

        # 更新托盘菜单项文字
        for action in self.tray_menu.actions():
            if action.text() == "设置":
                continue

        # 弹出日期选择对话框前保存当前模式
        self.save_config()
        self._update_tray_menu_state()

        # 弹出日期选择对话框
        self.show_date_select_dialog()

        # 立即更新显示
        self.update_countdown()
        self._update_tray_menu_state()

    def update_countdown(self):
        """更新倒计时显示"""
        try:
            # 如果暂停状态，不更新计算
            if self.paused:
                if self.last_days_left is None:
                    return
                days_left = self.last_days_left
            else:
                now = datetime.datetime.now()
                time_left = self.target_date - now
                days_left = time_left.total_seconds() / (24 * 3600)  # 转换为天数
                self.last_days_left = days_left

            # 根据考试模式和类型构建显示文本
            if self.exam_mode == "自定义":
                # 使用自定义模板，用格式化后的天数替换{time}标记
                time_text = f"{days_left:.{self.precision}f}"
                if "{time}" in self.custom_text_template:
                    text = self.custom_text_template.replace("{time}", time_text)
                else:
                    # 如果用户没有包含{time}标记，默认添加在文本前面
                    text = f"{time_text} {self.custom_text_template}"
            elif self.exam_mode == "中考":
                if self.exam_type in ["文化课", "地理生物", "体育考试", "英语听说", "理化实验", "英语听力"]:
                    text = f"距离中考{self.exam_type if self.exam_type != '文化课' else ''}: {days_left:.{self.precision}f} 天"
                else:
                    text = f"距离中考: {days_left:.{self.precision}f} 天"
            else:  # 高考
                if self.exam_type in ["统一科目", "选考科目", "外语", "技术", "外语听说", "等级考科目",
                                   "文理综合", "藏语文", "朝鲜语文", "蒙古语文"]:
                    text = f"距离高考{self.exam_type if self.exam_type != '统一科目' else ''}: {days_left:.{self.precision}f} 天"
                else:
                    text = f"距离高考: {days_left:.{self.precision}f} 天"

            self.countdown_label.setText(text)

            # 根据当前显示模式应用不同样式
            if self.display_mode == "watermark":
                # Fluent 的轻量展示层：保持透明、弱化背景、保留高可读性
                alpha = 150 if int(days_left) % 2 == 0 else 170
                r, g, b = self._hex_to_rgb(self.watermark_color)
                self.countdown_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                self.countdown_label.setMinimumSize(0, 0)
                self.countdown_label.setMaximumSize(16777215, 16777215)
                self.countdown_label.setStyleSheet(f"""
                    color: rgba({r}, {g}, {b}, {alpha});
                    font-family: 'Segoe UI', 'Microsoft YaHei';
                    font-weight: 600;
                    background: transparent;
                    border: none;
                    padding: 0px;
                """)
            else:
                # Fluent 的强调展示层：更高对比度与更清晰边界
                metrics = QFontMetrics(self.countdown_label.font())
                text_rect = metrics.tightBoundingRect(text)
                text_width = text_rect.width()
                text_height = text_rect.height()
                self.countdown_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
                self.countdown_label.setFixedSize(text_width + 28, text_height + 18)
                self.countdown_label.setStyleSheet(f"""
                    color: {self.visible_color};
                    font-family: 'Segoe UI', 'Microsoft YaHei';
                    font-weight: 700;
                    background: rgba(250, 249, 248, 225);
                    border: 1px solid rgba(210, 208, 206, 180);
                    border-radius: 6px;
                    padding: 4px 10px;
                """)
        except KeyboardInterrupt:
            print("更新被用户中断")
        except Exception as e:
            print(f"更新过程中出现错误: {repr(e)}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """重写关闭事件，当关闭窗口时隐藏而不是退出，并保存配置"""
        # 保存当前配置
        self.save_config()

        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)

if __name__ == "__main__":
    # 使用全局变量以避免重复创建QApplication
    if app_instance is None:
        app_instance = QApplication(sys.argv)

    setTheme(Theme.AUTO)
    setThemeColor(QColor(15, 108, 189))

    # 确保应用程序不会在最后一个窗口关闭时退出
    app_instance.setQuitOnLastWindowClosed(False)

    window = CountdownWindow()
    window.show()
    sys.exit(app_instance.exec())

# AI-Assisted End: GitHub Copilot - 2025/04

