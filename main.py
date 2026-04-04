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

# 初学者术语说明（尽量用生活化语言解释）
# instance（实例）：同一个“模板类”实际创建出来的具体对象。
# widget（控件）：界面里的一个可见部件，例如按钮、文本、下拉框。
# tray（托盘）：屏幕右下角的小图标区域。
# precision（精度）：保留小数位的多少，位数越大变化越细。
# overlay（覆盖层）：覆盖在屏幕上的临时交互界面。
# magnifier（放大镜）：把某一小块区域放大显示，便于精确查看。
# pixel（像素）：屏幕颜色的最小单位点。
# dpr（device pixel ratio，设备像素比）：逻辑坐标和真实像素的比例。
# signal（信号）：Qt 中“发生了某件事”的通知机制。
# slot（槽函数）：收到信号后要执行的处理函数。

# 全局应用程序变量
appInstance = None
lockFile = None  # 添加锁文件的全局引用

# 确保只运行一个实例，使用文件锁而不是socket
def ensureSingleInstance():
    """保证程序同一时间只运行一个窗口实例，避免重复启动。"""
    global lockFile
    
    try:
        # 在临时目录创建一个锁文件
        lockFilePath = os.path.join(tempfile.gettempdir(), "countdown_app.lock")
        
        # 尝试以独占方式打开文件
        lockFile = open(lockFilePath, "w")
        
        # 尝试对文件加锁
        # Windows上使用msvcrt
        if sys.platform == "win32":
            import msvcrt
            try:
                msvcrt.locking(lockFile.fileno(), msvcrt.LK_NBLCK, 1)
                return True  # 锁定成功，这是唯一的实例
            except IOError:
                # 锁定失败，说明已经有实例在运行
                lockFile.close()
                lockFile = None
        else:
            # 非Windows平台使用fcntl
            import fcntl
            try:
                fcntl.flock(lockFile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True  # 锁定成功
            except IOError:
                lockFile.close()
                lockFile = None
                
        # 如果代码执行到这里，说明锁定失败
        # 创建一个临时的QApplication实例，用于显示对话框
        global appInstance
        if appInstance is None:
            appInstance = QApplication(sys.argv)

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
isSingleInstance = ensureSingleInstance()

# 配置文件路径：保存在用户主目录下，避免程序目录无写入权限
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".countdown")
CONFIG_FILE = os.path.join(CONFIG_DIR, "countdown_config.json")

# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)


class ScreenColorPicker(QWidget):
    """全屏取色层：拖动放大镜选颜色，右键确认，Esc 退出。"""

    colorPicked = Signal(QColor)
    canceled = Signal()

    def __init__(self, parent=None):
        super().__init__(None)
        self._owner = parent
        self._dragging = False
        self._accepted = False
        self._cursorPos = QGuiApplication.primaryScreen().geometry().center()
        self._dragOffset = QPoint(0, 0)
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

        self._ringRadius = 18
        self._magnifierSize = 170
        self._magnifierZoom = 10
        self._magnifierRadius = 64
        self.captureBackground()

    def screenAt(self, globalPos):
        return QGuiApplication.screenAt(globalPos) or QGuiApplication.primaryScreen()

    def captureBackground(self):
        self._screen = self.screenAt(self._cursorPos)
        if self._screen is not None:
            self._background = self._screen.grabWindow(0)

    def samplePoint(self):
        screen = self.screenAt(self._cursorPos)
        if screen is None or self._background is None:
            return None, None, None
        screenGeometry = screen.geometry()
        dpr = self._background.devicePixelRatio()
        localX = self._cursorPos.x() - screenGeometry.x()
        localY = self._cursorPos.y() - screenGeometry.y()
        sampleX = int(localX * dpr)
        sampleY = int(localY * dpr)
        return screen, sampleX, sampleY

    def currentColor(self):
        screen, sampleX, sampleY = self.samplePoint()
        if screen is None or sampleX is None or sampleY is None:
            return QColor("#000000")
        pixel = self._background.copy(sampleX, sampleY, 1, 1).toImage()
        if pixel.isNull():
            return QColor("#000000")
        return QColor(pixel.pixel(0, 0))

    def moveCursor(self, pos):
        self._cursorPos = pos
        self.update()

    def magnifierRect(self):
        magnifierDiameter = self._magnifierSize
        magnifierX = self._cursorPos.x() + 26
        magnifierY = self._cursorPos.y() + 26
        if magnifierX + magnifierDiameter > self.width():
            magnifierX = self._cursorPos.x() - magnifierDiameter - 26
        if magnifierY + magnifierDiameter > self.height():
            magnifierY = self._cursorPos.y() - magnifierDiameter - 26
        return QRectF(magnifierX, magnifierY, magnifierDiameter, magnifierDiameter)

    def handleRect(self):
        magnifierRect = self.magnifierRect()
        handleSize = 24
        return QRectF(
            magnifierRect.right() - handleSize * 0.8,
            magnifierRect.bottom() - handleSize * 0.8,
            handleSize,
            handleSize,
        )

    def hitTestDragArea(self, globalPos):
        return self.magnifierRect().contains(globalPos) or self.handleRect().contains(globalPos)

    def confirmSelection(self):
        self._accepted = True
        self.colorPicked.emit(self.currentColor())
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.confirmSelection()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            globalPos = event.globalPosition().toPoint()
            if self.hitTestDragArea(globalPos):
                self._dragging = True
                self._dragOffset = globalPos - self._cursorPos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._cursorPos = event.globalPosition().toPoint() - self._dragOffset
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

        screen = self.screenAt(self._cursorPos)
        if screen is not None and self._background is not None:
            screenshot = self._background
            screenGeometry = screen.geometry()
            dpr = screenshot.devicePixelRatio()
            localX = self._cursorPos.x() - screenGeometry.x()
            localY = self._cursorPos.y() - screenGeometry.y()
            sampleX = int(localX * dpr)
            sampleY = int(localY * dpr)

            painter.fillRect(self.rect(), QColor(15, 23, 42, 42))

            # 放大镜：显示鼠标附近的像素块
            sampleSize = max(14, int(14 * dpr))
            sourceRect = screenshot.rect().adjusted(0, 0, -1, -1)
            sourceX = max(0, min(sourceRect.right() - sampleSize, sampleX - sampleSize // 2))
            sourceY = max(0, min(sourceRect.bottom() - sampleSize, sampleY - sampleSize // 2))
            sample = screenshot.copy(sourceX, sourceY, sampleSize, sampleSize)

            magnifierRect = self.magnifierRect()
            path = QPainterPath()
            path.addEllipse(magnifierRect)
            painter.save()
            painter.setClipPath(path)
            painter.fillRect(magnifierRect, QColor(255, 255, 255, 240))
            painter.drawPixmap(
                magnifierRect.toRect(),
                sample.scaled(
                    magnifierRect.size().toSize(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.FastTransformation
                )
            )
            painter.restore()

            painter.setPen(QPen(QColor(255, 255, 255, 235), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(magnifierRect)
            painter.setPen(QPen(QColor(15, 108, 189, 220), 1))
            painter.drawEllipse(magnifierRect.adjusted(2, 2, -2, -2))

            # 中心放大像素网格
            center = magnifierRect.center()
            pixelSide = self._magnifierRadius / self._magnifierZoom
            centerColor = self.currentColor()
            painter.setPen(QPen(QColor(0, 0, 0, 120), 1))
            painter.drawLine(int(center.x()) - 10, int(center.y()), int(center.x()) + 10, int(center.y()))
            painter.drawLine(int(center.x()), int(center.y()) - 10, int(center.x()), int(center.y()) + 10)

            # 当前颜色提示块
            previewRect = QRectF(magnifierRect.left(), magnifierRect.bottom() + 10, magnifierRect.width(), 28)
            painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
            painter.setBrush(QColor(255, 255, 255, 230))
            painter.drawRoundedRect(previewRect, 10, 10)
            painter.setPen(QColor(32, 31, 30))
            painter.drawText(previewRect.adjusted(12, 0, -12, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f"{centerColor.name().upper()}  右键确认")

        # 取色圈
        ringRadius = self._ringRadius
        ringRect = QRectF(self._cursorPos.x() - ringRadius, self._cursorPos.y() - ringRadius, ringRadius * 2, ringRadius * 2)
        painter.setPen(QPen(QColor(255, 255, 255, 245), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(ringRect)
        painter.setPen(QPen(QColor(15, 108, 189, 235), 2))
        painter.drawEllipse(ringRect.adjusted(3, 3, -3, -3))
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1))
        painter.drawEllipse(QRectF(self._cursorPos.x() - 3, self._cursorPos.y() - 3, 6, 6))

        handleRect = self.handleRect()
        painter.setPen(QPen(QColor(255, 255, 255, 240), 2))
        painter.setBrush(QColor(15, 108, 189, 235))
        painter.drawEllipse(handleRect)
        painter.setPen(QPen(QColor(255, 255, 255, 225), 2))
        painter.drawLine(int(handleRect.center().x()) - 5, int(handleRect.center().y()), int(handleRect.center().x()) + 5, int(handleRect.center().y()))
        painter.drawLine(int(handleRect.center().x()), int(handleRect.center().y()) - 5, int(handleRect.center().x()), int(handleRect.center().y()) + 5)

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
    """设置对话框：统一管理考试日期、显示模式、颜色和窗口位置。"""

    # 基础日期字典（仅保存月日），作为统一数据源
    baseZhongkaoDates = {
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

    baseGaokaoDates = {
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

    def __init__(self, parent=None, examMode="中考"):
        super().__init__(parent)
        FluentStyleSheet.DIALOG.apply(self)

        # 首先设置当前考试模式
        self.currentExamMode = examMode

        # 然后计算考试年份
        self.examYear = self.calculateExamYear()

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
        self.zhongkaoDates = self.convertToFullDates(self.baseZhongkaoDates)
        self.gaokaoDates = self.convertToFullDates(self.baseGaokaoDates)

        # 根据当前模式选择要使用的考试日期数据
        self.examDates = self.zhongkaoDates if examMode == "中考" else self.gaokaoDates
        self._lastNonCustomMode = examMode if examMode in ("中考", "高考") else "中考"

        # 添加自定义文本模板
        self.customTextTemplate = "{time}天后，未来将会怎样？"
        if parent and hasattr(parent, "customTextTemplate") and parent.customTextTemplate:
            self.customTextTemplate = parent.customTextTemplate

        # 显示与外观设置初始值
        self.displayMode = getattr(parent, "displayMode", "watermark") if parent else "watermark"
        self.windowPosition = getattr(parent, "position", "left_top") if parent else "left_top"
        self.displayPrecision = getattr(parent, "precision", 5) if parent else 5
        self.fontScale = getattr(parent, "fontScale", 100) if parent else 100
        self.watermarkColor = getattr(parent, "watermarkColor", DEFAULT_WATERMARK_COLOR) if parent else DEFAULT_WATERMARK_COLOR
        self.visibleColor = getattr(parent, "visibleColor", DEFAULT_VISIBLE_COLOR) if parent else DEFAULT_VISIBLE_COLOR

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 14, 16, 14)

        # 左侧可折叠 Fluent 导航 + 右侧内容页
        selectorLayout = QHBoxLayout()
        selectorLayout.setSpacing(10)
        selectorLayout.setContentsMargins(0, 0, 0, 0)

        self.selectorNav = NavigationInterface(parent=self, showMenuButton=True, collapsible=True)
        self.selectorNav.setExpandWidth(170)
        self.selectorNav.setMinimumExpandWidth(48)
        self.selectorNav.displayModeChanged.connect(self.onSelectorNavModeChanged)
        self.onSelectorNavModeChanged(NavigationDisplayMode.EXPAND)
        selectorLayout.addWidget(self.selectorNav)

        self.selectorStack = QStackedWidget()
        selectorLayout.addWidget(self.selectorStack, 1)
        layout.addLayout(selectorLayout)

        # 按地区选择页
        regionPage = QWidget()
        regionLayout = QVBoxLayout(regionPage)
        regionLayout.setContentsMargins(0, 0, 0, 0)
        regionLayout.setSpacing(12)

        regionBody = QHBoxLayout()
        regionBody.setSpacing(12)

        regionLeftCard = CardWidget()
        regionLeftLayout = QVBoxLayout(regionLeftCard)
        regionLeftLayout.setContentsMargins(12, 10, 12, 12)
        regionLeftLayout.setSpacing(10)

        regionLeftTitle = QLabel("地区与模式")
        regionLeftTitle.setObjectName("sectionTitle")
        regionLeftLayout.addWidget(regionLeftTitle)

        modeCard = CardWidget()
        modeLayout = QHBoxLayout(modeCard)
        modeLayout.setContentsMargins(12, 10, 12, 10)
        modeLayout.setSpacing(14)

        modeLabel = QLabel("模式类型:")
        modeLabel.setStyleSheet("font-weight: 600;")
        modeLayout.addWidget(modeLabel)

        self.examTypeGroup = QButtonGroup(self)

        self.zhongkaoRadio = RadioButton()
        self.zhongkaoRadio.setText("中考")
        self.zhongkaoRadio.setChecked(examMode == "中考")
        self.zhongkaoRadio.toggled.connect(self.onExamTypeChanged)
        self.examTypeGroup.addButton(self.zhongkaoRadio)
        modeLayout.addWidget(self.zhongkaoRadio)

        self.gaokaoRadio = RadioButton()
        self.gaokaoRadio.setText("高考")
        self.gaokaoRadio.setChecked(examMode == "高考")
        self.gaokaoRadio.toggled.connect(self.onExamTypeChanged)
        self.examTypeGroup.addButton(self.gaokaoRadio)
        modeLayout.addWidget(self.gaokaoRadio)

        regionLeftLayout.addWidget(modeCard)

        yearLabel = QLabel("考试年份:")
        regionLeftLayout.addWidget(yearLabel)

        self.regionYearCombo = EditableComboBox()
        self.regionYearCombo.setObjectName("regionYearCombo")
        FluentStyleSheet.COMBO_BOX.apply(self.regionYearCombo)
        currentYear = datetime.datetime.now().year
        yearItems = [str(y) for y in range(currentYear - 8, currentYear + 16)]
        self.regionYearCombo.addItems(yearItems)
        if hasattr(self.regionYearCombo, "lineEdit") and self.regionYearCombo.lineEdit() is not None:
            self.regionYearCombo.lineEdit().setValidator(QIntValidator(1900, 9999, self))
            self.regionYearCombo.lineEdit().setPlaceholderText("可手动输入年份")
            self.regionYearCombo.lineEdit().editingFinished.connect(
                lambda: self.onRegionYearChanged(self.regionYearCombo.currentText())
            )
        yearIndex = self.regionYearCombo.findText(str(self.examYear))
        if yearIndex < 0:
            self.regionYearCombo.addItem(str(self.examYear))
            yearIndex = self.regionYearCombo.findText(str(self.examYear))
        self.regionYearCombo.setCurrentIndex(yearIndex)
        self.regionYearCombo.currentTextChanged.connect(self.onRegionYearChanged)
        regionLeftLayout.addWidget(self.regionYearCombo)

        # 添加省份选择下拉框
        provinceLabel = QLabel("选择省份或城市:")
        regionLeftLayout.addWidget(provinceLabel)

        self.provinceCombo = ComboBox()
        FluentStyleSheet.COMBO_BOX.apply(self.provinceCombo)
        # 下拉框需要列表类型，这里把键集合转成列表
        self.provinceCombo.addItems(list(self.examDates.keys()))
        self.provinceCombo.setCurrentIndex(0)
        self.provinceCombo.currentTextChanged.connect(self.onProvinceSelected)
        regionLeftLayout.addWidget(self.provinceCombo)

        # 添加考试科目选择框
        examTypeLabel = QLabel("考试科目:")
        regionLeftLayout.addWidget(examTypeLabel)

        self.examTypeCombo = ComboBox()
        FluentStyleSheet.COMBO_BOX.apply(self.examTypeCombo)
        self.examTypeCombo.setEnabled(False)  # 初始状态禁用，等待选择省份
        self.examTypeCombo.currentTextChanged.connect(self.onExamTypeSelected)
        regionLeftLayout.addWidget(self.examTypeCombo)

        regionLeftLayout.addStretch(1)

        regionRightCard = CardWidget()
        regionRightLayout = QVBoxLayout(regionRightCard)
        regionRightLayout.setContentsMargins(12, 10, 12, 12)
        regionRightLayout.setSpacing(10)

        regionRightTitle = QLabel("当前选择")
        regionRightTitle.setObjectName("sectionTitle")
        regionRightLayout.addWidget(regionRightTitle)

        self.regionPreviewLabel = QLabel()
        self.regionPreviewLabel.setWordWrap(True)
        self.regionPreviewLabel.setObjectName("hintLabel")
        regionRightLayout.addWidget(self.regionPreviewLabel)

        regionNoteLabel = QLabel("注意：以上考试日期信息来自网络整理，仅供参考。\n"
                  "各地考试安排可能会有调整，请以当地教育部门最新通知为准。")
        regionNoteLabel.setObjectName("noteLabel")
        regionNoteLabel.setWordWrap(True)
        regionRightLayout.addWidget(regionNoteLabel)

        regionRightLayout.addStretch(1)

        regionBody.addWidget(regionLeftCard, 2)
        regionBody.addWidget(regionRightCard, 1)
        regionLayout.addLayout(regionBody)

        self.selectorStack.addWidget(regionPage)

        # 日历选择页
        calendarPage = QWidget()
        calendarLayout = QVBoxLayout(calendarPage)
        calendarLayout.setContentsMargins(0, 0, 0, 0)
        calendarLayout.setSpacing(10)

        self.calendarWidget = FastCalendarPicker()
        self.calendarWidget.setObjectName("calendarStrip")
        self.calendarWidget.setDate(QDate.currentDate().addMonths(3))
        self.calendarWidget.setFixedHeight(36)
        self.calendarWidget.setMaximumWidth(320)
        self.calendarWidget.dateChanged.connect(self.onCalendarDateSelected)

        calendarLayout.addWidget(self.calendarWidget)

        customCard = CardWidget()
        customCardLayout = QVBoxLayout(customCard)
        customCardLayout.setContentsMargins(12, 10, 12, 12)
        customCardLayout.setSpacing(8)

        customTitle = QLabel("自定义文本设置")
        customTitle.setObjectName("sectionTitle")
        customCardLayout.addWidget(customTitle)

        # {time} 是“占位符”，表示程序会在这里自动填入剩余天数。
        customHelpLabel = QLabel("在文本中使用{time}标记来指定倒计时数字的位置")
        customHelpLabel.setWordWrap(True)
        customHelpLabel.setObjectName("hintLabel")
        customCardLayout.addWidget(customHelpLabel)

        self.customModeCheck = CheckBox("启用自定义文本")
        self.customModeCheck.setChecked(examMode == "自定义")
        self.customModeCheck.toggled.connect(self.onCustomModeToggled)
        customCardLayout.addWidget(self.customModeCheck)

        self.customTextInput = LineEdit()
        self.customTextInput.setText(self.customTextTemplate)
        self.customTextInput.setPlaceholderText("例如：距离目标仅剩{time}天")
        FluentStyleSheet.LINE_EDIT.apply(self.customTextInput)
        customCardLayout.addWidget(self.customTextInput)

        self.customCard = customCard
        self.customTextInput.setEnabled(examMode == "自定义")
        calendarLayout.addWidget(customCard)

        calendarLayout.addStretch(1)

        # 日期页就是日历页 + 自定义文本
        self.selectorStack.addWidget(calendarPage)

        # 显示与外观页
        appearancePage = QWidget()
        appearanceLayout = QVBoxLayout(appearancePage)
        appearanceLayout.setContentsMargins(0, 0, 0, 0)
        appearanceLayout.setSpacing(10)

        appearanceCard = CardWidget()
        appearanceCardLayout = QVBoxLayout(appearanceCard)
        appearanceCardLayout.setContentsMargins(12, 10, 12, 12)
        appearanceCardLayout.setSpacing(10)

        appearanceTitle = QLabel("显示与外观")
        appearanceTitle.setObjectName("sectionTitle")
        appearanceCardLayout.addWidget(appearanceTitle)

        modeRow = QHBoxLayout()
        modeRow.addWidget(QLabel("显示模式:"))
        self.watermarkModeRadio = RadioButton()
        self.watermarkModeRadio.setText("水印")
        self.visibleModeRadio = RadioButton()
        self.visibleModeRadio.setText("高可见度")
        self.displayModeGroup = QButtonGroup(self)
        self.displayModeGroup.addButton(self.watermarkModeRadio)
        self.displayModeGroup.addButton(self.visibleModeRadio)
        self.watermarkModeRadio.setChecked(self.displayMode == "watermark")
        self.visibleModeRadio.setChecked(self.displayMode == "visible")
        self.watermarkModeRadio.toggled.connect(self.syncColorControls)
        self.visibleModeRadio.toggled.connect(self.syncColorControls)
        modeRow.addWidget(self.watermarkModeRadio)
        modeRow.addWidget(self.visibleModeRadio)
        modeRow.addStretch(1)
        appearanceCardLayout.addLayout(modeRow)

        precisionRow = QHBoxLayout()
        precisionRow.addWidget(QLabel("精度:"))
        self.precisionCombo = ComboBox()
        FluentStyleSheet.COMBO_BOX.apply(self.precisionCombo)
        for i in range(9):
            self.precisionCombo.addItem(f"{i}位小数")
        self.precisionCombo.setCurrentIndex(max(0, min(8, int(self.displayPrecision))))
        precisionRow.addWidget(self.precisionCombo)
        precisionRow.addStretch(1)
        appearanceCardLayout.addLayout(precisionRow)

        scaleRow = QHBoxLayout()
        scaleRow.addWidget(QLabel("字体缩放:"))
        self.fontScaleSlider = QSlider(Qt.Orientation.Horizontal)
        self.fontScaleSlider.setRange(80, 160)
        self.fontScaleSlider.setValue(max(80, min(160, int(self.fontScale))))
        self.fontScaleValueLabel = QLabel(f"{self.fontScaleSlider.value()}%")
        self.fontScaleSlider.valueChanged.connect(
            lambda v: self.fontScaleValueLabel.setText(f"{v}%")
        )
        scaleRow.addWidget(self.fontScaleSlider, 1)
        scaleRow.addWidget(self.fontScaleValueLabel)
        appearanceCardLayout.addLayout(scaleRow)

        colorRow = QHBoxLayout()
        colorRow.addWidget(QLabel("字体颜色:"))
        self.fontColorButton = ColorPickerButton(QColor(self.getActiveModeColor()), "选择颜色", self)
        self.fontColorButton.colorChanged.connect(self.onFontColorChanged)
        colorRow.addWidget(self.fontColorButton)
        self.pickScreenColorButton = PushButton("从屏幕取色")
        self.pickScreenColorButton.clicked.connect(self.pickColorFromScreen)
        colorRow.addWidget(self.pickScreenColorButton)
        self.restoreDefaultColorsButton = PushButton("恢复默认颜色")
        self.restoreDefaultColorsButton.clicked.connect(self.restoreDefaultColors)
        colorRow.addWidget(self.restoreDefaultColorsButton)
        self.colorPreviewLabel = QLabel(self.getActiveModeColor())
        self.colorPreviewLabel.setObjectName("colorPreview")
        self.updateColorPreview()
        colorRow.addWidget(self.colorPreviewLabel, 1)
        appearanceCardLayout.addLayout(colorRow)

        positionTitle = QLabel("窗口位置")
        positionTitle.setObjectName("sectionTitle")
        appearanceCardLayout.addWidget(positionTitle)

        positionPreview = QFrame()
        positionPreview.setObjectName("positionPreview")
        positionPreview.setFixedSize(280, 170)
        positionLayout = QVBoxLayout(positionPreview)
        positionLayout.setContentsMargins(12, 10, 12, 10)
        positionLayout.setSpacing(10)

        self.positionButtons = {}
        topRow = QHBoxLayout()
        bottomRow = QHBoxLayout()

        self.positionButtons["left_top"] = QPushButton("●")
        self.positionButtons["right_top"] = QPushButton("●")
        self.positionButtons["left_bottom"] = QPushButton("●")
        self.positionButtons["right_bottom"] = QPushButton("●")

        for key, btn in self.positionButtons.items():
            btn.setObjectName("positionDot")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, p=key: self.setWindowPosition(p))

        topRow.addWidget(self.positionButtons["left_top"])
        topRow.addStretch(1)
        topRow.addWidget(self.positionButtons["right_top"])
        bottomRow.addWidget(self.positionButtons["left_bottom"])
        bottomRow.addStretch(1)
        bottomRow.addWidget(self.positionButtons["right_bottom"])

        positionLayout.addLayout(topRow)
        positionLayout.addStretch(1)
        positionLayout.addLayout(bottomRow)
        appearanceCardLayout.addWidget(positionPreview)
        self.refreshPositionButtons()

        appearanceLayout.addWidget(appearanceCard)
        appearanceLayout.addStretch(1)
        self.selectorStack.addWidget(appearancePage)

        self.selectorNav.addItem(
            routeKey="region",
            icon=FIF.APPLICATION,
            text="按地区选择",
            onClick=lambda: self.setSelectorPage(0),
            tooltip="按地区选择"
        )
        self.selectorNav.addItem(
            routeKey="calendar",
            icon=FIF.CALENDAR,
            text="按日期选择",
            onClick=lambda: self.setSelectorPage(1),
            tooltip="按日期选择"
        )
        self.selectorNav.addItem(
            routeKey="display",
            icon=FIF.BRUSH,
            text="显示与外观",
            onClick=lambda: self.setSelectorPage(2),
            tooltip="显示与外观"
        )

        # 全局按钮布局：所有页面都可见
        globalButtonLayout = QHBoxLayout()
        globalButtonLayout.setSpacing(8)
        globalButtonLayout.setContentsMargins(0, 4, 0, 0)

        globalButtonLayout.addStretch(1)

        self.globalSaveButton = PrimaryPushButton()
        self.globalSaveButton.setText("保存")
        self.globalSaveButton.setProperty("class", "accent")
        self.globalSaveButton.setFixedWidth(86)
        self.globalSaveButton.setFixedHeight(32)
        self.globalSaveButton.clicked.connect(self.saveCurrentSelection)
        globalButtonLayout.addWidget(self.globalSaveButton)

        self.globalCloseButton = PushButton()
        self.globalCloseButton.setText("关闭")
        self.globalCloseButton.setFixedWidth(78)
        self.globalCloseButton.setFixedHeight(32)
        self.globalCloseButton.clicked.connect(self.reject)
        globalButtonLayout.addWidget(self.globalCloseButton)

        layout.addLayout(globalButtonLayout)

        # 根据当前选择的模式更新界面状态
        self.updateUiBasedOnMode(examMode)
        self.refreshRegionPreview()

    def updateUiBasedOnMode(self, mode):
        """根据当前选择的模式更新UI元素的可见性"""
        self.selectorNav.setVisible(True)
        self.selectorStack.setVisible(True)

        if mode == "中考" or mode == "高考":
            self.setSelectorPage(0)
            self.customModeCheck.blockSignals(True)
            self.customModeCheck.setChecked(False)
            self.customModeCheck.blockSignals(False)
            self.customTextInput.setEnabled(False)
        else:
            self.setSelectorPage(1)
            self.customModeCheck.blockSignals(True)
            self.customModeCheck.setChecked(True)
            self.customModeCheck.blockSignals(False)
            self.customTextInput.setEnabled(True)
            self.calendarWidget.setDate(self.calendarWidget.date)

    def onCustomModeToggled(self, checked):
        """切换自定义文本模式"""
        if checked:
            if self.currentExamMode in ("中考", "高考"):
                self._lastNonCustomMode = self.currentExamMode
            self.currentExamMode = "自定义"
            self.setWindowTitle("设置自定义倒计时")
            self.setSelectorPage(1)
            self.customTextInput.setEnabled(True)
        else:
            self.currentExamMode = self._lastNonCustomMode
            if self.currentExamMode == "中考":
                self.setWindowTitle("设置中考日期")
            elif self.currentExamMode == "高考":
                self.setWindowTitle("设置高考日期")
            self.customTextInput.setEnabled(False)

    def onSelectorNavModeChanged(self, mode):
        """根据导航模式切换左侧宽度，展开显示文字，收起显示图标"""
        if mode == NavigationDisplayMode.EXPAND:
            self.selectorNav.setFixedWidth(170)
        else:
            self.selectorNav.setFixedWidth(52)

    def setSelectorPage(self, index):
        """切换右侧内容页面"""
        self.selectorStack.setCurrentIndex(index)

    def setWindowPosition(self, position):
        """设置窗口位置并刷新按钮状态"""
        self.windowPosition = position
        self.refreshPositionButtons()

    def refreshPositionButtons(self):
        """刷新位置按钮选中状态"""
        if not hasattr(self, "positionButtons"):
            return
        for key, btn in self.positionButtons.items():
            btn.setChecked(key == self.windowPosition)

    def onFontColorChanged(self, color):
        """Fluent 颜色按钮变化时同步配置"""
        if color.isValid():
            self.setActiveModeColor(color.name())
            self.updateColorPreview()

    def pickColorFromScreen(self):
        """从屏幕任意位置拾取颜色"""
        self.hide()
        self._screen_picker = ScreenColorPicker(self)
        self._screen_picker.colorPicked.connect(self.applyScreenPickedColor)
        self._screen_picker.canceled.connect(self.restoreAfterScreenPick)
        self._screen_picker.show()

    def applyScreenPickedColor(self, color):
        if color.isValid():
            self.setActiveModeColor(color.name())
            if hasattr(self, "fontColorButton"):
                self.fontColorButton.setColor(color)
            self.updateColorPreview()
        self.restoreAfterScreenPick()

    def getActiveModeColor(self):
        return self.watermarkColor if self.watermarkModeRadio.isChecked() else self.visibleColor

    def setActiveModeColor(self, colorHex):
        if self.watermarkModeRadio.isChecked():
            self.watermarkColor = colorHex
        else:
            self.visibleColor = colorHex

    def syncColorControls(self, *_):
        current = self.getActiveModeColor()
        self.fontColorButton.setColor(QColor(current))
        self.updateColorPreview()

    def restoreDefaultColors(self):
        self.watermarkColor = DEFAULT_WATERMARK_COLOR
        self.visibleColor = DEFAULT_VISIBLE_COLOR
        self.syncColorControls()

    def restoreAfterScreenPick(self):
        self.show()
        self.activateWindow()

    def updateColorPreview(self):
        """刷新颜色预览"""
        if not hasattr(self, "colorPreviewLabel"):
            return
        currentColor = self.getActiveModeColor()
        self.colorPreviewLabel.setText(currentColor)
        previewTextColor = "#000000" if QColor(currentColor).lightness() > 150 else "#ffffff"
        self.colorPreviewLabel.setStyleSheet(
            f"background: {currentColor}; color: {previewTextColor}; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 8px; padding: 2px 8px;"
        )

    def onRegionYearChanged(self, yearText):
        """地区页年份变化时更新当前日期"""
        yearText = yearText.strip()
        if not yearText or not yearText.isdigit():
            return

        yearValue = int(yearText)
        if yearValue < 1900 or yearValue > 9999:
            return

        self.examYear = yearValue
        if self.regionYearCombo.findText(str(yearValue)) < 0:
            self.regionYearCombo.addItem(str(yearValue))

        currentExamType = self.examTypeCombo.currentText() if hasattr(self, "examTypeCombo") else ""
        if currentExamType:
            self.onExamTypeSelected(currentExamType)
        else:
            self.refreshRegionPreview()

    def refreshRegionPreview(self):
        """刷新地区页的当前选择预览"""
        if not hasattr(self, "regionPreviewLabel"):
            return

        provinceName = self.provinceCombo.currentText() if hasattr(self, "provinceCombo") else ""
        examType = self.examTypeCombo.currentText() if hasattr(self, "examTypeCombo") else ""
        dateText = self.calendarWidget.date.toString("yyyy年MM月dd日") if hasattr(self, "calendarWidget") else ""

        if provinceName and provinceName != "请选择省份或城市" and examType:
            self.regionPreviewLabel.setText(
                f"年份：{self.examYear}\n"
                f"地区：{provinceName}\n"
                f"科目：{examType}\n"
                f"日期：{dateText}"
            )
        else:
            self.regionPreviewLabel.setText("先选择省份和科目，右侧会显示当前日期与确认入口。")

    @staticmethod
    def calculateExamYear():
        """计算考试年份"""
        currentDate = datetime.datetime.now()
        currentYear = currentDate.year
        return currentYear + 1 if currentDate > datetime.datetime(currentYear, 6, 1) else currentYear

    @staticmethod
    def convertToFullDates(baseDates):
        """将基础日期转换为包含年份的完整日期"""
        fullDates = {}
        currentDate = datetime.datetime.now()

        for province, examTypes in baseDates.items():
            fullDates[province] = {}
            for examType, dateTuple in examTypes.items():
                if dateTuple is None:
                    fullDates[province][examType] = None
                    continue

                month, day = dateTuple
                # 计算正确的年份
                year = currentDate.year

                # 如果当前日期已过这个月日，使用明年
                if currentDate > datetime.datetime(year, month, day):
                    year += 1

                fullDates[province][examType] = QDate(year, month, day)

        return fullDates

    def onExamTypeChanged(self):
        """当选择考试类型（中考/高考/自定义）变化时更新界面"""
        # 重新计算考试年份
        if hasattr(self, "regionYearCombo") and self.regionYearCombo.currentText().isdigit():
            self.examYear = int(self.regionYearCombo.currentText())
        else:
            self.examYear = self.calculateExamYear()

        if self.zhongkaoRadio.isChecked():
            self.currentExamMode = "中考"
            self._lastNonCustomMode = "中考"
            # 使用基础数据重新生成日期
            self.zhongkaoDates = self.convertToFullDates(self.baseZhongkaoDates)
            self.examDates = self.zhongkaoDates
            self.setWindowTitle("设置中考日期")
        elif self.gaokaoRadio.isChecked():
            self.currentExamMode = "高考"
            self._lastNonCustomMode = "高考"
            # 使用基础数据重新生成日期
            self.gaokaoDates = self.convertToFullDates(self.baseGaokaoDates)
            self.examDates = self.gaokaoDates
            self.setWindowTitle("设置高考日期")
        else:  # 自定义模式
            self.currentExamMode = "自定义"
            self.setWindowTitle("设置自定义倒计时")

        # 更新UI组件显示状态
        self.updateUiBasedOnMode(self.currentExamMode)

        if self.currentExamMode in ("中考", "高考") and hasattr(self, "customModeCheck"):
            self.customModeCheck.blockSignals(True)
            self.customModeCheck.setChecked(False)
            self.customModeCheck.blockSignals(False)
            self.customTextInput.setEnabled(False)

        self.refreshRegionPreview()

        if self.currentExamMode != "自定义":
            # 更新省份下拉框
            currentProvince = self.provinceCombo.currentText()
            self.provinceCombo.clear()
            # 下拉框需要列表类型，这里把键集合转成列表
            provinceList = list(self.examDates.keys())
            self.provinceCombo.addItems(provinceList)

            # 尝试保持之前选择的省份（如果新列表中存在）
            index = self.provinceCombo.findText(currentProvince)
            if index >= 0:
                self.provinceCombo.setCurrentIndex(index)
            else:
                self.provinceCombo.setCurrentIndex(0)
                self.examTypeCombo.clear()
                self.examTypeCombo.setEnabled(False)

    def onProvinceSelected(self, provinceName):
        """当选择省份时更新考试类型和日期"""
        if provinceName == "请选择省份或城市":
            self.examTypeCombo.clear()
            self.examTypeCombo.setEnabled(False)
            return

        # 获取该省份/城市的考试类型
        examTypes = self.examDates.get(provinceName, {})

        # 更新考试类型下拉框
        self.examTypeCombo.clear()
        # 下拉框需要列表类型，这里把键集合转成列表
        self.examTypeCombo.addItems(list(examTypes.keys()))

        # 如果有考试类型，启用下拉框
        if examTypes:
            self.examTypeCombo.setEnabled(True)

            # 默认选择第一个考试类型
            if self.examTypeCombo.count() > 0:
                firstExamType = self.examTypeCombo.itemText(0)
                self.onExamTypeSelected(firstExamType)
        else:
            self.examTypeCombo.setEnabled(False)
            self.refreshRegionPreview()

    def onExamTypeSelected(self, examType):
        """当选择考试类型时更新日期"""
        if not examType:
            return

        provinceName = self.provinceCombo.currentText()
        examTypes = self.examDates.get(provinceName, {})
        selectedDate = examTypes.get(examType)

        if selectedDate:
            selectedDate = QDate(self.examYear, selectedDate.month(), selectedDate.day())
            self.calendarWidget.setDate(selectedDate)

        self.refreshRegionPreview()

    def onCalendarDateSelected(self):
        """当在日历中选择日期时更新日期编辑框"""
        self.refreshRegionPreview()

    def getSelectedDate(self):
        """获取用户选择的日期"""
        qdate = self.calendarWidget.date
        return datetime.datetime(qdate.year(), qdate.month(), qdate.day())

    def getSelectedExamType(self):
        """获取用户选择的考试类型"""
        if self.examTypeCombo.isEnabled() and self.examTypeCombo.currentText():
            return self.examTypeCombo.currentText()
        return "文化课"  # 默认返回文化课

    def getSelectedExamMode(self):
        """获取用户选择的考试模式（中考/高考/自定义）"""
        return self.currentExamMode

    def getCustomTextTemplate(self):
        """获取用户输入的自定义文本模板"""
        if self.customModeCheck.isChecked():
            return self.customTextInput.text()
        return None

    def saveCurrentSelection(self):
        """立即保存当前设置到父窗口，但不关闭对话框"""
        parent = self.parent()
        if parent is None or not hasattr(parent, "saveConfig"):
            return

        oldDisplayMode = getattr(parent, "displayMode", "watermark")
        oldPosition = getattr(parent, "position", "left_top")
        oldPrecision = getattr(parent, "precision", 5)
        oldFontScale = getattr(parent, "fontScale", 100)
        oldWatermarkColor = getattr(parent, "watermarkColor", DEFAULT_WATERMARK_COLOR)
        oldVisibleColor = getattr(parent, "visibleColor", DEFAULT_VISIBLE_COLOR)

        selectedDate = self.getSelectedDate()

        currentDate = datetime.datetime.now()
        if selectedDate < currentDate:
            selectedDate = datetime.datetime(
                currentDate.year + 1,
                selectedDate.month,
                selectedDate.day
            )

        parent.targetDate = selectedDate
        parent.examMode = self.getSelectedExamMode()

        if parent.examMode == "自定义":
            parent.customTextTemplate = self.getCustomTextTemplate() or parent.customTextTemplate
            parent.examType = "自定义"
        else:
            parent.examType = self.getSelectedExamType()

        if parent.examMode == "自定义":
            parent.setWindowTitle("自定义倒计时")
        else:
            parent.setWindowTitle(f"{parent.examMode}倒计时")

        # 保存显示与外观设置
        parent.displayMode = "visible" if self.visibleModeRadio.isChecked() else "watermark"
        parent.position = self.windowPosition
        parent.precision = self.precisionCombo.currentIndex()
        parent.fontScale = self.fontScaleSlider.value()
        parent.watermarkColor = self.watermarkColor
        parent.visibleColor = self.visibleColor
        parent.fontColor = self.visibleColor
        if hasattr(parent, "applyCountdownFont") and parent.fontScale != oldFontScale:
            parent.applyCountdownFont()
        if hasattr(parent, "updateTimerInterval") and parent.precision != oldPrecision:
            parent.updateTimerInterval()
        if hasattr(parent, "updatePosition") and parent.position != oldPosition:
            parent.updatePosition()

        appearanceChanges = []
        if parent.displayMode != oldDisplayMode:
            appearanceChanges.append(f"显示模式 {oldDisplayMode} -> {parent.displayMode}")
        if parent.position != oldPosition:
            appearanceChanges.append(f"窗口位置 {oldPosition} -> {parent.position}")
        if parent.precision != oldPrecision:
            appearanceChanges.append(f"精度 {oldPrecision} -> {parent.precision}")
        if parent.fontScale != oldFontScale:
            appearanceChanges.append(f"字体缩放 {oldFontScale}% -> {parent.fontScale}%")
        if parent.watermarkColor != oldWatermarkColor:
            appearanceChanges.append(f"水印颜色 {oldWatermarkColor} -> {parent.watermarkColor}")
        if parent.visibleColor != oldVisibleColor:
            appearanceChanges.append(f"高可见度颜色 {oldVisibleColor} -> {parent.visibleColor}")
        if appearanceChanges:
            print("外观设置已更新: " + "; ".join(appearanceChanges))

        parent.saveConfig()
        if hasattr(parent, "updateCountdown"):
            parent.updateCountdown()
        if hasattr(parent, "updateTrayMenuState"):
            parent.updateTrayMenuState()

    def reject(self):
        """关闭对话框前自动保存当前设置"""
        self.saveCurrentSelection()
        super().reject()

    def closeEvent(self, event):
        """点击右上角关闭按钮时自动保存当前设置"""
        self.saveCurrentSelection()
        super().closeEvent(event)

class CountdownWindow(QMainWindow):
    """主窗口：负责倒计时显示、配置存取、托盘菜单交互。"""

    def __init__(self):
        super().__init__()

        # 初始化实例特性
        self.trayMenu = None
        self.positionMenu = None
        self.displayMenu = None
        self.modeMenu = None
        self.modeActions = {}
        self.pauseAction = None
        self.trayIcon = None
        self.lastDaysLeft = None

        # 设置窗口属性 - 无边框和背景透明，添加鼠标事件穿透标志
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool |
                           Qt.WindowType.WindowTransparentForInput)  # 添加这个标志使鼠标事件穿透窗口
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 默认配置
        self.position = "left_top"  # 默认左上角位置
        self.windowWidth = 300
        self.windowHeight = 80
        self.precision = 5  # 默认5位小数
        self.displayMode = "watermark"  # 默认水印模式
        self.fontScale = 100
        self.watermarkColor = DEFAULT_WATERMARK_COLOR
        self.visibleColor = DEFAULT_VISIBLE_COLOR
        self.fontColor = self.visibleColor
        self.paused = False
        self.examType = "文化课"  # 默认考试类型
        self.examMode = "中考"  # 默认考试模式（中考/高考）
        # 自定义模式的文本模板
        self.customTextTemplate = "{time}天后，未来将会怎样？"
        # 默认目标日期，将在加载配置或用户设定后更改
        self.targetDate = None

        # 加载配置（如果存在）
        self.loadConfig()

        # 如果没有设置目标日期，则提示用户设置
        if self.targetDate is None:
            self.showDateSelectDialog()

        if self.examMode == "自定义":
            self.setWindowTitle("自定义倒计时")
        else:
            self.setWindowTitle(f"{self.examMode}倒计时")

        # 创建中心部件
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        # 设置完全透明背景
        palette = centralWidget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))  # 完全透明
        centralWidget.setAutoFillBackground(True)
        centralWidget.setPalette(palette)

        # 创建布局
        layout = QVBoxLayout(centralWidget)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距

        # 创建标签
        self.countdownLabel = QLabel()
        font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        self.countdownLabel.setFont(font)
        self.countdownLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.countdownLabel.setContentsMargins(0, 0, 0, 0)
        self.countdownLabel.setMargin(0)
        self.applyCountdownFont()
        layout.addWidget(self.countdownLabel)

        # 创建定时器来更新倒计时
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateCountdown)

        # 初始设置窗口位置
        self.updatePosition()

        # 根据精度设置初始更新间隔
        self.updateTimerInterval()

        # 初始更新显示
        self.updateCountdown()

        # 创建系统托盘图标
        self.createTrayIcon()

    @staticmethod
    def convertToFullDates(baseDates):
        """将基础日期转换为包含年份的完整字符串表示"""
        fullDates = {}
        currentDate = datetime.datetime.now()

        for province, examTypes in baseDates.items():
            fullDates[province] = {}
            for examType, dateTuple in examTypes.items():
                if dateTuple is None:
                    fullDates[province][examType] = None
                    continue

                month, day = dateTuple
                # 计算正确的年份
                year = currentDate.year

                # 如果当前日期已过这个月日，使用明年
                if currentDate > datetime.datetime(year, month, day):
                    year += 1

                # 保存为字符串格式，适合JSON存储
                fullDates[province][examType] = f"{year}-{month}-{day}"

        return fullDates

    def loadConfig(self):
        """从配置文件加载设置"""
        if not os.path.exists(CONFIG_FILE):
            print(f"配置文件不存在，将使用默认设置。配置路径: {CONFIG_FILE}")
            self.writeDefaultConfig()
            return

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 检查版本号
            fileVersion = config.get("version", "0")
            if fileVersion < VERSION:
                print(f"检测到新版本({VERSION})，更新配置文件...")
                self.writeDefaultConfig()
                return

            # 版本号相同，加载配置，并尊重配置文件中的日期设置
            self.position = config.get('position', self.position)
            self.precision = config.get('precision', self.precision)
            self.displayMode = config.get('display_mode', self.displayMode)
            self.fontScale = config.get('font_scale', self.fontScale)
            # legacy 表示“旧版本遗留字段”，这里用于兼容历史配置。
            legacyFontColor = config.get('font_color', self.visibleColor)
            self.watermarkColor = config.get('watermark_color', legacyFontColor)
            self.visibleColor = config.get('visible_color', legacyFontColor)
            self.fontColor = self.visibleColor
            self.windowWidth = config.get('window_width', self.windowWidth)
            self.windowHeight = config.get('window_height', self.windowHeight)
            self.examType = config.get('exam_type', self.examType)
            self.examMode = config.get('exam_mode', self.examMode)
            self.customTextTemplate = config.get('custom_text_template', self.customTextTemplate)

            # 尝试加载考试日期列表
            dates = config.get('dates', {})
            # 将加载的日期应用到DateSelectDialog的基础数据中
            if 'zhongkao' in dates and dates['zhongkao']:
                self.updateBaseDatesFromConfig(DateSelectDialog.baseZhongkaoDates, dates['zhongkao'])
            if 'gaokao' in dates and dates['gaokao']:
                self.updateBaseDatesFromConfig(DateSelectDialog.baseGaokaoDates, dates['gaokao'])

            # 加载目标日期 - 完全按照配置文件中的日期，不自动调整
            targetDateStr = config.get('target_date')
            if targetDateStr:
                try:
                    dateParts = list(map(int, targetDateStr.split('-')))
                    self.targetDate = datetime.datetime(dateParts[0], dateParts[1], dateParts[2])
                    print(f"按配置文件加载日期: {self.targetDate.strftime('%Y-%m-%d')}")
                except (ValueError, IndexError) as e:
                    print(f"日期解析错误: {e}，将使用默认日期")
                    self.targetDate = None

            print(f"成功从配置文件加载设置: {CONFIG_FILE}")
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            self.targetDate = None

    @staticmethod
    def updateBaseDatesFromConfig(baseDatesDict, configDatesDict):
        """从配置文件的日期字典更新基础日期字典"""
        for province, examTypes in configDatesDict.items():
            if not isinstance(examTypes, dict):
                continue

            if province not in baseDatesDict or not isinstance(baseDatesDict.get(province), dict):
                baseDatesDict[province] = {}

            for examType, dateStr in examTypes.items():
                if dateStr is None:
                    baseDatesDict[province][examType] = None
                    continue

                try:
                    # 从日期字符串(例如"2024-6-7")提取月和日
                    year, month, day = map(int, dateStr.split('-'))
                    baseDatesDict[province][examType] = (month, day)
                except (ValueError, TypeError) as e:
                    print(f"解析日期'{dateStr}'失败: {e}")
                    continue

    def writeDefaultConfig(self):
        """写入默认配置，包括版本号和考试日期列表"""
        try:
            # 确保配置目录存在
            os.makedirs(CONFIG_DIR, exist_ok=True)

            # 默认考试日期列表 - 使用本类的转换方法
            defaultDates = {
                "zhongkao": self.convertToFullDates(DateSelectDialog.baseZhongkaoDates),
                "gaokao": self.convertToFullDates(DateSelectDialog.baseGaokaoDates)
            }

            # 构建默认配置
            config = {
                "version": VERSION,
                "position": self.position,
                "precision": self.precision,
                "display_mode": self.displayMode,
                "font_scale": self.fontScale,
                "font_color": self.visibleColor,
                "watermark_color": self.watermarkColor,
                "visible_color": self.visibleColor,
                "window_width": self.windowWidth,
                "window_height": self.windowHeight,
                "target_date": None,
                "exam_type": self.examType,
                "exam_mode": self.examMode,
                "custom_text_template": self.customTextTemplate,
                "dates": defaultDates
            }

            # 写入配置文件
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            print(f"默认配置已写入: {CONFIG_FILE}")
        except Exception as e:
            print(f"写入默认配置时出错: {e}")

    def saveConfig(self):
        """保存当前设置到配置文件"""
        try:
            # 确保配置目录存在
            os.makedirs(CONFIG_DIR, exist_ok=True)

            targetDateStr = None
            if self.targetDate:
                targetDateStr = f"{self.targetDate.year}-{self.targetDate.month}-{self.targetDate.day}"

            # 保存所有考试日期列表
            dates = {
                "zhongkao": self.convertToFullDates(DateSelectDialog.baseZhongkaoDates),
                "gaokao": self.convertToFullDates(DateSelectDialog.baseGaokaoDates)
            }

            config = {
                'version': VERSION,  # 添加版本号
                'position': self.position,
                'precision': self.precision,
                'display_mode': self.displayMode,
                'font_scale': self.fontScale,
                'font_color': self.visibleColor,
                'watermark_color': self.watermarkColor,
                'visible_color': self.visibleColor,
                'window_width': self.windowWidth,
                'window_height': self.windowHeight,
                'target_date': targetDateStr,
                'exam_type': self.examType,
                'exam_mode': self.examMode,
                'custom_text_template': self.customTextTemplate,
                'dates': dates  # 保存考试日期列表
            }

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            print(f"设置已保存到配置文件: {CONFIG_FILE}")
        except Exception as e:
            print(f"保存配置文件出错: {e}")

    def resetToFactory(self):
        """恢复出厂设置"""
        try:
            # 重置所有设置为默认值
            self.position = "left_top"
            self.windowWidth = 300
            self.windowHeight = 80
            self.precision = 5
            self.displayMode = "watermark"
            self.fontScale = 100
            self.watermarkColor = DEFAULT_WATERMARK_COLOR
            self.visibleColor = DEFAULT_VISIBLE_COLOR
            self.fontColor = self.visibleColor
            self.paused = False
            self.examType = "文化课"
            self.examMode = "中考"
            self.customTextTemplate = "{time}天后，未来将会怎样？"
            self.targetDate = None

            # 写入默认配置到文件
            self.writeDefaultConfig()

            # 提示用户设置日期
            self.showDateSelectDialog()

            # 更新界面显示
            self.updatePosition()
            self.updateCountdown()

            # 更新托盘菜单选项状态
            self.updateTrayMenuState()

            print("已恢复出厂设置")
        except Exception as e:
            print(f"恢复出厂设置时出错: {e}")

    def updateTrayMenuState(self):
        """更新托盘菜单中的选项状态"""
        # 更新位置菜单项
        for action in self.positionMenu.actions():
            action.setChecked(action.property("position_value") == self.position)

        # 更新显示模式菜单项
        for action in self.displayMenu.actions():
            action.setChecked(action.property("mode_value") == self.displayMode)

        # 更新暂停按钮状态和文本
        if self.pauseAction:
            self.pauseAction.setChecked(self.paused)
            self.pauseAction.setText("恢复更新" if self.paused else "暂停更新")
            self.pauseAction.setIcon(FIF.PLAY.icon() if self.paused else FIF.PAUSE.icon())

        # 更新模式菜单项
        if self.modeMenu:
            for action in self.modeMenu.actions():
                action.setChecked(action.property("mode_value") == self.examMode)

    def showDateSelectDialog(self):
        """显示日期选择对话框"""
        dialog = DateSelectDialog(self, self.examMode)
        if dialog.exec():
            selectedDate = dialog.getSelectedDate()

            # 检查选择的日期是否已过，如果已过则使用明年的相同日期
            currentDate = datetime.datetime.now()
            if selectedDate < currentDate:
                selectedDate = datetime.datetime(
                    currentDate.year + 1,
                    selectedDate.month,
                    selectedDate.day
                )

            self.targetDate = selectedDate
            self.examMode = dialog.getSelectedExamMode()

            if self.examMode == "自定义":
                self.customTextTemplate = dialog.getCustomTextTemplate() or self.customTextTemplate
                self.examType = "自定义"
            else:
                self.examType = dialog.getSelectedExamType()

            # 保存配置
            self.saveConfig()
            print(f"日期设置为: {self.targetDate.strftime('%Y-%m-%d')}，模式: {self.examMode}")

            # 更新窗口标题
            if self.examMode == "自定义":
                self.setWindowTitle("自定义倒计时")
            else:
                self.setWindowTitle(f"{self.examMode}倒计时")
        else:
            # 如果用户取消，则使用默认日期
            if self.targetDate is None:  # 只有在没有现有日期时才设置默认值
                currentDate = datetime.datetime.now()
                if self.examMode == "中考":
                    defaultDate = datetime.datetime(currentDate.year, 6, 24)
                else:  # 高考
                    defaultDate = datetime.datetime(currentDate.year, 6, 7)

                # 如果默认日期已过，使用明年
                if defaultDate < currentDate:
                    defaultDate = datetime.datetime(
                        currentDate.year + 1,
                        defaultDate.month,
                        defaultDate.day
                    )

                self.targetDate = defaultDate
                self.examType = "文化课" if self.examMode == "中考" else "统一科目"
                print(f"用户取消设置，使用默认{self.examMode}日期: {self.targetDate.strftime('%Y-%m-%d')}")

    def createTrayIcon(self):
        """创建系统托盘图标和菜单"""
        # 检查是否支持系统托盘
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("系统不支持系统托盘")
            return

        # 创建托盘图标菜单
        self.trayMenu = CheckableSystemTrayMenu("", self)
        FluentStyleSheet.MENU.apply(self.trayMenu)
        self.trayMenu.setFont(QFont("Segoe UI", 9))

        positionGroup = QActionGroup(self)
        positionGroup.setExclusive(True)
        displayGroup = QActionGroup(self)
        displayGroup.setExclusive(True)
        modeGroup = QActionGroup(self)
        modeGroup.setExclusive(True)

        # 添加位置设置菜单
        self.positionMenu = RoundMenu("窗口位置", self.trayMenu)
        FluentStyleSheet.MENU.apply(self.positionMenu)
        self.trayMenu.addMenu(self.positionMenu)

        # 添加四个位置选项
        positions = [
            ("左上角", "left_top"),
            ("右上角", "right_top"),
            ("左下角", "left_bottom"),
            ("右下角", "right_bottom")
        ]

        for posName, posValue in positions:
            action = QAction(posName, self)
            action.setIcon(FIF.PIN.icon())
            # 使用setProperty而不是setData
            action.setProperty("position_value", posValue)
            action.triggered.connect(self.changePosition)
            action.setCheckable(True)
            action.setChecked(self.position == posValue)
            positionGroup.addAction(action)
            self.positionMenu.addAction(action)

        self.trayMenu.addSeparator()

        # 添加显示模式菜单 - 保存为类属性
        self.displayMenu = RoundMenu("显示模式", self.trayMenu)
        FluentStyleSheet.MENU.apply(self.displayMenu)
        self.trayMenu.addMenu(self.displayMenu)

        # 添加水印模式选项
        watermarkAction = QAction("水印样式", self)
        watermarkAction.setIcon(FIF.BRUSH.icon())
        # 使用setProperty而不是setData
        watermarkAction.setProperty("mode_value", "watermark")
        watermarkAction.triggered.connect(self.changeDisplayMode)
        watermarkAction.setCheckable(True)
        watermarkAction.setChecked(self.displayMode == "watermark")
        displayGroup.addAction(watermarkAction)
        self.displayMenu.addAction(watermarkAction)

        # 添加高辨识度模式选项
        visibleAction = QAction("高辨识度", self)
        visibleAction.setIcon(FIF.VIEW.icon())
        # 使用setProperty而不是setData
        visibleAction.setProperty("mode_value", "visible")
        visibleAction.triggered.connect(self.changeDisplayMode)
        visibleAction.setCheckable(True)
        visibleAction.setChecked(self.displayMode == "visible")
        displayGroup.addAction(visibleAction)
        self.displayMenu.addAction(visibleAction)

        # 添加精度控制菜单项
        precisionMenu = RoundMenu("设置精度", self.trayMenu)
        FluentStyleSheet.MENU.apply(precisionMenu)
        self.trayMenu.addMenu(precisionMenu)

        # 添加不同的精度选项
        for i in range(9):  # 0-8位精度
            action = QAction(f"{i}位小数", self)
            action.setIcon(FIF.CALORIES.icon())
            # 使用setProperty而不是setData
            action.setProperty("precision_value", i)  # 保存精度值
            action.triggered.connect(self.changePrecision)
            precisionMenu.addAction(action)

        self.trayMenu.addSeparator()

        # 添加暂停/恢复选项
        self.pauseAction = QAction("暂停更新", self)
        self.pauseAction.setIcon(FIF.PAUSE.icon())
        self.pauseAction.setCheckable(True)
        self.pauseAction.triggered.connect(self.togglePause)
        self.trayMenu.addAction(self.pauseAction)

        # 添加切换考试类型的选项
        self.modeMenu = RoundMenu("切换模式", self.trayMenu)
        FluentStyleSheet.MENU.apply(self.modeMenu)
        self.trayMenu.addMenu(self.modeMenu)

        # 中考选项
        zhongkaoAction = QAction("中考模式", self)
        zhongkaoAction.setIcon(FIF.CERTIFICATE.icon())
        zhongkaoAction.setProperty("mode_value", "中考")
        zhongkaoAction.triggered.connect(lambda: self.switchExamMode("中考"))
        zhongkaoAction.setCheckable(True)
        zhongkaoAction.setChecked(self.examMode == "中考")
        modeGroup.addAction(zhongkaoAction)
        self.modeMenu.addAction(zhongkaoAction)

        # 高考选项
        gaokaoAction = QAction("高考模式", self)
        gaokaoAction.setIcon(FIF.CERTIFICATE.icon())
        gaokaoAction.setProperty("mode_value", "高考")
        gaokaoAction.triggered.connect(lambda: self.switchExamMode("高考"))
        gaokaoAction.setCheckable(True)
        gaokaoAction.setChecked(self.examMode == "高考")
        modeGroup.addAction(gaokaoAction)
        self.modeMenu.addAction(gaokaoAction)

        # 自定义选项
        customAction = QAction("自定义模式", self)
        customAction.setIcon(FIF.EDIT.icon())
        customAction.setProperty("mode_value", "自定义")
        customAction.triggered.connect(lambda: self.switchExamMode("自定义"))
        customAction.setCheckable(True)
        customAction.setChecked(self.examMode == "自定义")
        modeGroup.addAction(customAction)
        self.modeMenu.addAction(customAction)

        self.modeActions = {
            "中考": zhongkaoAction,
            "高考": gaokaoAction,
            "自定义": customAction,
        }

        self.trayMenu.addSeparator()

        # 添加修改日期的选项
        changeDateAction = QAction("设置", self)
        changeDateAction.setIcon(FIF.SETTING.icon())
        changeDateAction.triggered.connect(self.showDateSelectDialog)
        self.trayMenu.addAction(changeDateAction)

        # 在退出选项前添加恢复出厂设置选项
        factoryResetAction = QAction("恢复出厂设置", self)
        factoryResetAction.setIcon(FIF.ROTATE.icon())
        factoryResetAction.triggered.connect(self.resetToFactory)
        self.trayMenu.addAction(factoryResetAction)

        # 添加退出选项
        quitAction = QAction("退出", self)
        quitAction.setIcon(FIF.POWER_BUTTON.icon())
        quitAction.triggered.connect(QApplication.quit)
        self.trayMenu.addAction(quitAction)

        # 创建托盘图标 - 使用自定义图标，而不依赖系统图标
        self.trayIcon = QSystemTrayIcon(self)

        # 创建一个 Fluent 风格托盘图标
        iconPixmap = QPixmap(16, 16)
        iconPixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(iconPixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 108, 189))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(1, 1, 14, 14, 4, 4)
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.drawEllipse(5, 5, 6, 6)
        painter.setPen(QPen(QColor(15, 108, 189), 1))
        painter.drawLine(8, 8, 10, 6)
        painter.end()

        self.trayIcon.setIcon(QIcon(iconPixmap))
        self.trayIcon.setToolTip("考试倒计时")
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayIcon.activated.connect(self.trayIconActivated)

        # 显示系统托盘图标
        self.trayIcon.show()
        print("系统托盘图标已创建")

    def changePosition(self):
        """根据托盘菜单操作更改窗口位置"""
        action = self.sender()
        if action:
            # 获取新的位置
            newPosition = action.property("position_value")
            if newPosition == self.position:
                return
            oldPosition = self.position
            self.position = newPosition

            # 更新菜单项选中状态
            for act in self.positionMenu.actions():
                act.setChecked(act.property("position_value") == self.position)

            # 更新窗口位置
            self.updatePosition()

            print(f"外观设置更新: 窗口位置 {oldPosition} -> {self.position}")

            # 保存配置
            self.saveConfig()

    def updatePosition(self):
        """根据当前位置设置更新窗口位置"""
        # 获取整个屏幕的几何信息
        screenGeometry = QApplication.primaryScreen().geometry()
        # 获取排除任务栏后的可用屏幕区域
        availableGeometry = QApplication.primaryScreen().availableGeometry()

        # 为左侧和右侧定义不同的边距
        leftMargin = 5   # 左侧边距更小
        rightMargin = 10  # 右侧边距保持不变
        topMargin = 5    # 顶部边距更小
        bottomMargin = 10 # 底部边距保持不变

        if self.position == "left_top":
            # 左上角 - 使用更小的边距，更靠近边缘
            self.setGeometry(leftMargin, topMargin,
                             self.windowWidth, self.windowHeight)
        elif self.position == "right_top":
            # 右上角 - 保持原有边距
            self.setGeometry(screenGeometry.width() - self.windowWidth - rightMargin,
                             topMargin,
                             self.windowWidth, self.windowHeight)
        elif self.position == "left_bottom":
            # 左下角 - 左侧使用更小的边距
            self.setGeometry(leftMargin,
                             availableGeometry.height() + availableGeometry.y() - self.windowHeight - bottomMargin,
                             self.windowWidth, self.windowHeight)
        elif self.position == "right_bottom":
            # 右下角 - 保持原有边距
            self.setGeometry(screenGeometry.width() - self.windowWidth - rightMargin,
                             availableGeometry.height() + availableGeometry.y() - self.windowHeight - bottomMargin,
                             self.windowWidth, self.windowHeight)

    def changeDisplayMode(self):
        """根据托盘菜单操作更改显示模式"""
        action = self.sender()
        if action:
            # 获取新的显示模式
            newMode = action.property("mode_value")
            if newMode == self.displayMode:
                return
            oldMode = self.displayMode
            self.displayMode = newMode

            # 更新菜单项选中状态 - 使用类属性而非findChild
            for act in self.displayMenu.actions():
                act.setChecked(act.property("mode_value") == self.displayMode)

            # 更新显示
            self.updateCountdown()

            print(f"外观设置更新: 显示模式 {oldMode} -> {self.displayMode}")

            # 保存配置
            self.saveConfig()

    def trayIconActivated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单击图标
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def changePrecision(self):
        """根据托盘菜单操作更改精度"""
        action = self.sender()
        if action:
            oldPrecision = self.precision
            newPrecision = action.property("precision_value")
            if newPrecision == oldPrecision:
                return
            self.precision = newPrecision

            # 打印日志以便调试
            print(f"正在切换精度：从 {oldPrecision} 位小数到 {self.precision} 位小数")

            # 强制停止旧定时器
            if self.timer.isActive():
                self.timer.stop()

            # 根据新精度更新定时器间隔
            self.updateTimerInterval()

            # 立即更新显示
            self.updateCountdown()

            # 保存配置
            self.saveConfig()

    def applyCountdownFont(self):
        """根据字体缩放设置应用倒计时字体大小"""
        scaledSize = max(9, int(round(11 * (self.fontScale / 100))))
        self.countdownLabel.setFont(QFont("Segoe UI", scaledSize, QFont.Weight.DemiBold))

    @staticmethod
    def hexToRgb(colorHex):
        """将 #RRGGBB 颜色转换为 RGB 三元组"""
        color = QColor(colorHex)
        if not color.isValid():
            color = QColor("#0f1419")
        return color.red(), color.green(), color.blue()

    def updateTimerInterval(self):
        """根据当前精度计算并设置合适的定时器更新间隔"""
        # 一天 = 86400 秒
        # 对于n位小数，最小变化是 10^(-n) 天 = 10^(-n) * 86400 秒
        # 为了观察到变化，更新间隔应小于这个值

        # 计算当前精度下最小变化的时间（秒）
        changeSeconds = 86400 * (10 ** (-self.precision))

        # 根据精度级别设置不同的比例因子
        # 这里的比例因子可以根据实际需求进行调整
        if self.precision <= 1:
            factor = 0.95
        elif self.precision <= 3:
            factor = 0.95
        else:
            factor = 0.9

        # 计算更新间隔（毫秒）
        interval = int(changeSeconds * factor * 1000)

        # 设置更新间隔的上下限
        minInterval = 10    # 最小10毫秒，避免过于频繁更新
        maxInterval = 60000 # 最大60秒，确保即使是低精度也有合理的更新频率

        interval = max(minInterval, min(interval, maxInterval))

        # 先确保定时器真的停止了
        if self.timer.isActive():
            self.timer.stop()

        # 为了确保重启干净，使用短延迟
        QTimer.singleShot(10, lambda: self.startTimerWithInterval(interval))

        print(f"精度设置为 {self.precision} 位小数，变化时间 {changeSeconds:.6f} 秒，更新间隔设为 {interval} 毫秒")

    def startTimerWithInterval(self, interval):
        """安全地启动定时器，确保旧定时器已停止"""
        try:
            if not self.timer.isActive() and not self.paused:
                self.timer.start(interval)
                print(f"定时器成功启动，间隔: {interval}毫秒")
            elif self.paused:
                print("暂停状态中，定时器未启动")
        except Exception as e:
            print(f"启动定时器时出错: {e}")

    def togglePause(self):
        """切换暂停/恢复状态"""
        self.paused = not self.paused

        if self.paused:
            self.pauseAction.setText("恢复更新")
            self.pauseAction.setIcon(FIF.PLAY.icon())
            # 确保定时器停止
            if self.timer.isActive():
                self.timer.stop()
                print("定时器已暂停")
        else:
            self.pauseAction.setText("暂停更新")
            self.pauseAction.setIcon(FIF.PAUSE.icon())
            # 恢复时重新计算并设置定时器间隔
            self.updateTimerInterval()
            # 恢复时立即更新一次
            self.updateCountdown()
            print("定时器已恢复")

    def switchExamMode(self, newMode=None):
        """切换考试模式（中考/高考/自定义）"""
        # 如果没有指定新模式，则循环切换
        if newMode is None:
            if self.examMode == "中考":
                newMode = "高考"
            elif self.examMode == "高考":
                newMode = "自定义"
            else:
                newMode = "中考"

        # 切换考试模式
        self.examMode = newMode

        # 更新窗口标题
        if self.examMode == "自定义":
            self.setWindowTitle("自定义倒计时")
        else:
            self.setWindowTitle(f"{self.examMode}倒计时")

        # 重置考试类型
        if self.examMode == "中考":
            self.examType = "文化课"
        elif self.examMode == "高考":
            self.examType = "统一科目"
        else:
            self.examType = "自定义"

        # 更新托盘菜单项文字
        for action in self.trayMenu.actions():
            if action.text() == "设置":
                continue

        # 弹出日期选择对话框前保存当前模式
        self.saveConfig()
        self.updateTrayMenuState()

        # 弹出日期选择对话框
        self.showDateSelectDialog()

        # 立即更新显示
        self.updateCountdown()
        self.updateTrayMenuState()

    def updateCountdown(self):
        """更新倒计时显示"""
        try:
            # 如果暂停状态，不更新计算
            if self.paused:
                if self.lastDaysLeft is None:
                    return
                daysLeft = self.lastDaysLeft
            else:
                now = datetime.datetime.now()
                timeLeft = self.targetDate - now
                daysLeft = timeLeft.total_seconds() / (24 * 3600)  # 转换为天数
                self.lastDaysLeft = daysLeft

            # 根据考试模式和类型构建显示文本
            if self.examMode == "自定义":
                # 使用自定义模板，用格式化后的天数替换{time}标记
                timeText = f"{daysLeft:.{self.precision}f}"
                if "{time}" in self.customTextTemplate:
                    text = self.customTextTemplate.replace("{time}", timeText)
                else:
                    # 如果用户没有包含{time}标记，默认添加在文本前面
                    text = f"{timeText} {self.customTextTemplate}"
            elif self.examMode == "中考":
                if self.examType in ["文化课", "地理生物", "体育考试", "英语听说", "理化实验", "英语听力"]:
                    text = f"距离中考{self.examType if self.examType != '文化课' else ''}: {daysLeft:.{self.precision}f} 天"
                else:
                    text = f"距离中考: {daysLeft:.{self.precision}f} 天"
            else:  # 高考
                if self.examType in ["统一科目", "选考科目", "外语", "技术", "外语听说", "等级考科目",
                                   "文理综合", "藏语文", "朝鲜语文", "蒙古语文"]:
                    text = f"距离高考{self.examType if self.examType != '统一科目' else ''}: {daysLeft:.{self.precision}f} 天"
                else:
                    text = f"距离高考: {daysLeft:.{self.precision}f} 天"

            self.countdownLabel.setText(text)

            # 根据当前显示模式应用不同样式
            if self.displayMode == "watermark":
                # Fluent 的轻量展示层：保持透明、弱化背景、保留高可读性
                alpha = 150 if int(daysLeft) % 2 == 0 else 170
                r, g, b = self.hexToRgb(self.watermarkColor)
                self.countdownLabel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                self.countdownLabel.setMinimumSize(0, 0)
                self.countdownLabel.setMaximumSize(16777215, 16777215)
                self.countdownLabel.setStyleSheet(f"""
                    color: rgba({r}, {g}, {b}, {alpha});
                    font-family: 'Segoe UI', 'Microsoft YaHei';
                    font-weight: 600;
                    background: transparent;
                    border: none;
                    padding: 0px;
                """)
            else:
                # Fluent 的强调展示层：更高对比度与更清晰边界
                metrics = QFontMetrics(self.countdownLabel.font())
                textRect = metrics.tightBoundingRect(text)
                textWidth = textRect.width()
                textHeight = textRect.height()
                self.countdownLabel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
                self.countdownLabel.setFixedSize(textWidth + 28, textHeight + 18)
                self.countdownLabel.setStyleSheet(f"""
                    color: {self.visibleColor};
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
        self.saveConfig()

        if self.trayIcon and self.trayIcon.isVisible():
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)

if __name__ == "__main__":
    # 使用全局变量以避免重复创建QApplication
    if appInstance is None:
        appInstance = QApplication(sys.argv)

    setTheme(Theme.AUTO)
    setThemeColor(QColor(15, 108, 189))

    # 确保应用程序不会在最后一个窗口关闭时退出
    appInstance.setQuitOnLastWindowClosed(False)

    window = CountdownWindow()
    window.show()
    sys.exit(appInstance.exec())

# AI-Assisted End: GitHub Copilot - 2025/04

