"""
考试倒计时程序
AI 开发作品，无人类作者版权声明
遵循 LICENSE 许可证
考试日期数据来源：互联网
"""

# 当前版本号
VERSION = "build8"

# AI-Assisted: GitHub Copilot - 2025/04
# 本程序完全由 AI 开发，遵循 LICENSE 中的规定
# 详细许可证请参阅项目根目录下的 LICENSE 文件
# AI-Assisted Start: GitHub Copilot - 2025/04
import sys
import datetime
import json
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                              QWidget, QSystemTrayIcon, QMenu, QDialog, 
                              QDateEdit, QHBoxLayout, QComboBox,
                              QCalendarWidget, QTabWidget, QPushButton, QFrame,
                              QRadioButton, QButtonGroup, QLineEdit, QGroupBox)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QPalette, QColor, QFont, QIcon, QAction, QPixmap
import socket

# 确保只运行一个实例
def ensure_single_instance():
    try:
        # 尝试绑定一个特定端口，如果能绑定成功则表示没有其它实例在运行
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 45568))  # 使用一个不常用的端口
        # 保持套接字打开状态，直到程序结束
        return sock
    except socket.error:
        print("程序已经在运行中!")
        sys.exit(0)

# 保存套接字引用，防止被垃圾回收
single_instance_socket = ensure_single_instance()
# 配置文件路径 - 改为使用用户目录
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".countdown")
CONFIG_FILE = os.path.join(CONFIG_DIR, "countdown_config.json")

# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)

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

        # 首先设置当前考试模式
        self.current_exam_mode = exam_mode

        # 然后计算考试年份
        self.exam_year = self._calculate_exam_year()

        self.setWindowTitle(f"设置日期和模式")
        self.resize(450, 550)  # 增加高度以适应新控件
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
            QLabel {
                font-family: 'Microsoft YaHei', Arial;
                font-size: 12pt;
                color: #333333;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-size: 11pt;
                min-height: 30px;
            }
            QComboBox::drop-down {
                border: 0px;
                width: 20px;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a86e8;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 1.5ex;
                padding: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QCalendarWidget {
                background-color: white;
                border-radius: 6px;
            }
            QCalendarWidget QToolButton {
                height: 30px;
                width: 150px;
                color: #333333;
                font-size: 12pt;
                icon-size: 24px, 24px;
                background-color: #f8f9fa;
                border: none;
                border-radius: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e8eaed;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 4px;
            }
            QCalendarWidget QSpinBox {
                font-size: 12pt;
                selection-background-color: #4a86e8;
                selection-color: white;
                background-color: white;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 2px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 11pt;
                color: #333333;
                background-color: white;
                selection-background-color: #4a86e8;
                selection-color: white;
                outline: none;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #bbbbbb;
            }
            QCalendarWidget QWidget { 
                alternate-background-color: #f8f9fa; 
            }
            QCalendarWidget QAbstractItemView:item:hover {
                background-color: #e8eaed;
                border-radius: 4px;
            }
            QCalendarWidget QAbstractItemView:item:selected {
                background-color: #4a86e8;
                color: white;
                border-radius: 4px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f8f9fa;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 4px;
                border-bottom: 1px solid #dadce0;
            }
            /* 上一个月按钮样式 */
            QCalendarWidget QToolButton#qt_calendar_prevmonth {
                icon-size: 24px;
                background-color: #f8f9fa;
                border-radius: 18px;
                margin: 3px;
                padding: 3px;
                color: #333333;
                font-weight: bold;
                qproperty-text: "◄";
                qproperty-icon: none;  /* 移除图标，使用文本 */
            }
            /* 下一个月按钮样式 */
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                icon-size: 24px;
                background-color: #f8f9fa;
                border-radius: 18px;
                margin: 3px;
                padding: 3px;
                color: #333333;
                font-weight: bold;
                qproperty-text: "►";
                qproperty-icon: none;  /* 移除图标，使用文本 */
            }
            /* 年份选择按钮样式 */
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                background-color: #f8f9fa;
                color: #333333;
                border-radius: 4px;
                padding: 3px 10px;
                font-weight: bold;
                margin-right: 5px;
            }
            QCalendarWidget QToolButton#qt_calendar_yearbutton::menu-indicator {
                image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23555555' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
                subcontrol-position: right center;
                subcontrol-origin: padding;
                width: 16px;
                height: 16px;
                position: relative;
                left: -3px;
            }
            /* 上一年按钮样式 */
            QCalendarWidget QToolButton#qt_calendar_prevyear {
                icon-size: 25px;
                background-color: #f8f9fa;
                border-radius: 18px;
                margin: 3px;
                padding: 3px;
                color: #333333;
                font-weight: bold;
                qproperty-text: "◄";
                qproperty-icon: none;  /* 移除图标，使用文本 */
            }
            /* 下一年按钮样式 */
            QCalendarWidget QToolButton#qt_calendar_nextyear {
                icon-size: 25px;
                background-color: #f8f9fa;
                border-radius: 18px;
                margin: 3px;
                padding: 3px;
                color: #333333;
                font-weight: bold;
                qproperty-text: "►";
                qproperty-icon: none;  /* 移除图标，使用文本 */
            }
            QCalendarWidget QToolButton#qt_calendar_prevyear:hover,
            QCalendarWidget QToolButton#qt_calendar_nextyear:hover {
                background-color: #e8eaed;
            }
            /* 月份选择按钮样式 */
            QCalendarWidget QToolButton#qt_calendar_monthbutton {
                background-color: #f8f9fa;
                color: #333333;
                border-radius: 4px;
                padding: 3px 10px;
                font-weight: bold;
                margin-right: 5px;
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton::menu-indicator {
                image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23555555' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
                subcontrol-position: right center;
                subcontrol-origin: padding;
                width: 16px;
                height: 16px;
                position: relative;
                left: -3px;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth:hover, 
            QCalendarWidget QToolButton#qt_calendar_nextmonth:hover,
            QCalendarWidget QToolButton#qt_calendar_yearbutton:hover,
            QCalendarWidget QToolButton#qt_calendar_monthbutton:hover {
                background-color: #e8eaed;
            }
            QDateEdit::down-arrow {
                image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234a86e8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='18' rx='2' ry='2'%3E%3C/rect%3E%3Cline x1='16' y1='2' x2='16' y2='6'%3E%3C/line%3E%3Cline x1='8' y1='2' x2='8' y2='6'%3E%3C/line%3E%3Cline x1='3' y1='10' x2='21' y2='10'%3E%3C/line%3E%3C/svg%3E");
                width: 18px;
                height: 18px;
            }
        """)

        # 转换基础日期为完整的 QDate 对象
        self.zhongkao_dates = self._convert_to_full_dates(self.base_zhongkao_dates)
        self.gaokao_dates = self._convert_to_full_dates(self.base_gaokao_dates)

        # 默认激活考试类型
        self.exam_dates = self.zhongkao_dates if exam_mode == "中考" else self.gaokao_dates

        # 添加自定义文本模板
        self.custom_text_template = "{time}天后，未来将会怎样？"
        if parent and hasattr(parent, "custom_text_template") and parent.custom_text_template:
            self.custom_text_template = parent.custom_text_template

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题标签
        info_label = QLabel("设置倒计时日期和模式")
        info_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # 添加考试类型选择
        exam_type_frame = QFrame()
        exam_type_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 10px;")
        exam_type_layout = QHBoxLayout(exam_type_frame)

        exam_type_label = QLabel("模式类型:")
        exam_type_label.setStyleSheet("font-weight: bold;")
        exam_type_layout.addWidget(exam_type_label)

        self.exam_type_group = QButtonGroup(self)

        self.zhongkao_radio = QRadioButton("中考")
        self.zhongkao_radio.setChecked(exam_mode == "中考")
        self.zhongkao_radio.toggled.connect(self.on_exam_type_changed)
        self.exam_type_group.addButton(self.zhongkao_radio)
        exam_type_layout.addWidget(self.zhongkao_radio)

        self.gaokao_radio = QRadioButton("高考")
        self.gaokao_radio.setChecked(exam_mode == "高考")
        self.gaokao_radio.toggled.connect(self.on_exam_type_changed)
        self.exam_type_group.addButton(self.gaokao_radio)
        exam_type_layout.addWidget(self.gaokao_radio)

        # 添加自定义模式单选按钮
        self.custom_radio = QRadioButton("自定义")
        self.custom_radio.setChecked(exam_mode == "自定义")
        self.custom_radio.toggled.connect(self.on_exam_type_changed)
        self.exam_type_group.addButton(self.custom_radio)
        exam_type_layout.addWidget(self.custom_radio)

        layout.addWidget(exam_type_frame)

        # 创建自定义文本输入框组
        self.custom_group = QGroupBox("自定义文本设置")
        self.custom_group.setVisible(exam_mode == "自定义")
        custom_layout = QVBoxLayout(self.custom_group)

        custom_help_label = QLabel("在文本中使用{time}标记来指定倒计时数字的位置")
        custom_help_label.setWordWrap(True)
        custom_help_label.setStyleSheet("font-size: 10pt; color: #666;")
        custom_layout.addWidget(custom_help_label)

        self.custom_text_input = QLineEdit(self.custom_text_template)
        self.custom_text_input.setPlaceholderText("例如：距离目标仅剩{time}天")
        custom_layout.addWidget(self.custom_text_input)

        layout.addWidget(self.custom_group)

        # 创建标签页控件来分隔不同的选择方式
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #e6e6e6;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4a86e8;
            }
        """)
        layout.addWidget(self.tab_widget)

        # 按地区选择的标签页
        region_tab = QWidget()
        region_layout = QVBoxLayout(region_tab)
        region_layout.setSpacing(15)

        # 添加省份选择下拉框
        province_label = QLabel("选择省份或城市:")
        region_layout.addWidget(province_label)

        self.province_combo = QComboBox()
        # 修复类型错误：将dict_keys转换为列表
        self.province_combo.addItems(list(self.exam_dates.keys()))
        self.province_combo.setCurrentIndex(0)
        self.province_combo.currentTextChanged.connect(self.on_province_selected)
        region_layout.addWidget(self.province_combo)

        # 添加考试科目选择框
        exam_type_label = QLabel("考试科目:")
        region_layout.addWidget(exam_type_label)

        self.exam_type_combo = QComboBox()
        self.exam_type_combo.setEnabled(False)  # 初始状态禁用，等待选择省份
        self.exam_type_combo.currentTextChanged.connect(self.on_exam_type_selected)
        region_layout.addWidget(self.exam_type_combo)

        self.tab_widget.addTab(region_tab, "按地区选择")

        # 日历选择的标签页
        calendar_tab = QWidget()
        calendar_layout = QVBoxLayout(calendar_tab)
        calendar_layout.setContentsMargins(10, 15, 10, 15)

        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setGridVisible(True)
        self.calendar_widget.setMinimumDate(QDate.currentDate())
        self.calendar_widget.setSelectedDate(QDate.currentDate().addMonths(3))
        self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar_widget.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.calendar_widget.setFixedHeight(300)  # 设置固定高度使日历更紧凑
        self.calendar_widget.selectionChanged.connect(self.on_calendar_date_selected)

        # 为星期几标题设置中文
        self.calendar_widget.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)

        calendar_layout.addWidget(self.calendar_widget)

        self.tab_widget.addTab(calendar_tab, "日历选择")

        # 选择的日期展示
        date_frame = QFrame()
        date_frame.setFrameShape(QFrame.Shape.StyledPanel)
        date_frame.setStyleSheet("background-color: #e8f0fe; border-radius: 8px; padding: 15px;")
        date_layout = QHBoxLayout(date_frame)
        date_layout.setSpacing(10)

        date_label = QLabel("已选择日期:")
        date_label.setStyleSheet("font-weight: bold;")
        date_layout.addWidget(date_label)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addMonths(3))  # 默认设置为三个月后
        self.date_edit.setMinimumDate(QDate.currentDate())  # 最小日期为当前日期
        self.date_edit.setDisplayFormat("yyyy年MM月dd日")  # 使用中文格式显示日期
        self.date_edit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 5px 30px 5px 12px;  /* 右侧留更多空间放置箭头 */
                font-size: 12pt;
                min-height: 32px;
                background-color: white;
                selection-background-color: #4a86e8;
                selection-color: white;
            }
            QDateEdit:hover {
                border-color: #4a86e8;
                background-color: #f9f9f9;
            }
            QDateEdit:focus {
                border-color: #4a86e8;
                border-width: 2px;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 24px;
                border: none;
                background: transparent;
                margin-right: 4px;
            }
            QDateEdit::down-arrow {
                image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234a86e8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='18' rx='2' ry='2'%3E%3C/rect%3E%3Cline x1='16' y1='2' x2='16' y2='6'%3E%3C/line%3E%3Cline x1='8' y1='2' x2='8' y2='6'%3E%3C/line%3E%3Cline x1='3' y1='10' x2='21' y2='10'%3E%3C/line%3E%3C/svg%3E");
                width: 18px;
                height: 18px;
            }
            /* 控制弹出的日历控件宽度 */
            QCalendarWidget {
                max-width: 300px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                max-width: 300px;
            }
            QCalendarWidget QToolButton {
                height: 30px;
                max-width: 100px;
            }
        """)
        date_layout.addWidget(self.date_edit)

        layout.addWidget(date_frame)

        # 添加提示信息
        note_label = QLabel("注意：以上考试日期信息来自网络整理，仅供参考。\n"
                           "各地考试安排可能会有调整，请以当地教育部门最新通知为准。")
        note_label.setStyleSheet("color: #666; font-size: 10pt;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        # 按钮布局
        button_layout = QHBoxLayout()

        # 自定义确定和取消按钮，替代标准按钮盒
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet("background-color: #f0f0f0; color: #333;")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # 根据当前选择的模式更新界面状态
        self.update_ui_based_on_mode(exam_mode)

    def update_ui_based_on_mode(self, mode):
        """根据当前选择的模式更新UI元素的可见性"""
        is_custom = mode == "自定义"
        self.custom_group.setVisible(is_custom)
        # 保持标签页始终可见，确保日历可用
        self.tab_widget.setVisible(True)
        
        if is_custom:
            # 在自定义模式下，显示日历标签页
            self.tab_widget.setCurrentIndex(1)  # 日历标签页
            self.calendar_widget.setSelectedDate(self.date_edit.date())

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
        self.exam_year = self._calculate_exam_year()

        if self.zhongkao_radio.isChecked():
            self.current_exam_mode = "中考"
            # 使用基础数据重新生成日期
            self.zhongkao_dates = self._convert_to_full_dates(self.base_zhongkao_dates)
            self.exam_dates = self.zhongkao_dates
            self.setWindowTitle("设置中考日期")
        elif self.gaokao_radio.isChecked():
            self.current_exam_mode = "高考"
            # 使用基础数据重新生成日期
            self.gaokao_dates = self._convert_to_full_dates(self.base_gaokao_dates)
            self.exam_dates = self.gaokao_dates
            self.setWindowTitle("设置高考日期")
        else:  # 自定义模式
            self.current_exam_mode = "自定义"
            self.setWindowTitle("设置自定义倒计时")

        # 更新UI组件显示状态
        self.update_ui_based_on_mode(self.current_exam_mode)

        if not self.custom_radio.isChecked():
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

    def on_exam_type_selected(self, exam_type):
        """当选择考试类型时更新日期"""
        if not exam_type:
            return

        province_name = self.province_combo.currentText()
        exam_types = self.exam_dates.get(province_name, {})
        selected_date = exam_types.get(exam_type)

        if selected_date:
            self.date_edit.setDate(selected_date)
            # 同时更新日历视图的选中日期
            self.calendar_widget.setSelectedDate(selected_date)

    def on_calendar_date_selected(self):
        """当在日历中选择日期时更新日期编辑框"""
        selected_date = self.calendar_widget.selectedDate()
        self.date_edit.setDate(selected_date)

    def get_selected_date(self):
        """获取用户选择的日期"""
        qdate = self.date_edit.date()
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
        if self.custom_radio.isChecked():
            return self.custom_text_input.text()
        return None

class CountdownWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化实例特性
        self.tray_menu = None
        self.position_menu = None
        self.display_menu = None
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
        font = QFont("微软雅黑", 11, QFont.Weight.Bold)
        font.setItalic(True)
        self.countdown_label.setFont(font)
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
            self.window_width = config.get('window_width', self.window_width)
            self.window_height = config.get('window_height', self.window_height)
            self.exam_type = config.get('exam_type', self.exam_type)
            self.exam_mode = config.get('exam_mode', self.exam_mode)
            self.custom_text_template = config.get('custom_text_template', self.custom_text_template)

            # 尝试加载考试日期列表
            dates = config.get('dates', {})
            # 这里只是加载，实际使用时会在DateSelectDialog类中重新转换为QDate对象

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

    def create_tray_icon(self):
        """创建系统托盘图标和菜单"""
        # 检查是否支持系统托盘
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("系统不支持系统托盘")
            return

        # 创建托盘图标菜单
        self.tray_menu = QMenu()

        # 添加位置设置菜单
        self.position_menu = self.tray_menu.addMenu("窗口位置")

        # 添加四个位置选项
        positions = [
            ("左上角", "left_top"),
            ("右上角", "right_top"),
            ("左下角", "left_bottom"),
            ("右下角", "right_bottom")
        ]

        for pos_name, pos_value in positions:
            action = QAction(pos_name, self)
            # 使用setProperty而不是setData
            action.setProperty("position_value", pos_value)
            action.triggered.connect(self.change_position)
            action.setCheckable(True)
            action.setChecked(self.position == pos_value)
            self.position_menu.addAction(action)

        # 添加显示模式菜单 - 保存为类属性
        self.display_menu = self.tray_menu.addMenu("显示模式")

        # 添加水印模式选项
        watermark_action = QAction("水印样式", self)
        # 使用setProperty而不是setData
        watermark_action.setProperty("mode_value", "watermark")
        watermark_action.triggered.connect(self.change_display_mode)
        watermark_action.setCheckable(True)
        watermark_action.setChecked(self.display_mode == "watermark")
        self.display_menu.addAction(watermark_action)

        # 添加高辨识度模式选项
        visible_action = QAction("高辨识度", self)
        # 使用setProperty而不是setData
        visible_action.setProperty("mode_value", "visible")
        visible_action.triggered.connect(self.change_display_mode)
        visible_action.setCheckable(True)
        visible_action.setChecked(self.display_mode == "visible")
        self.display_menu.addAction(visible_action)

        # 添加精度控制菜单项
        precision_menu = self.tray_menu.addMenu("设置精度")

        # 添加不同的精度选项
        for i in range(9):  # 0-8位精度
            action = QAction(f"{i}位小数", self)
            # 使用setProperty而不是setData
            action.setProperty("precision_value", i)  # 保存精度值
            action.triggered.connect(self.change_precision)
            precision_menu.addAction(action)

        # 添加暂停/恢复选项
        self.pause_action = QAction("暂停更新", self)
        self.pause_action.setCheckable(True)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.tray_menu.addAction(self.pause_action)

        # 添加切换考试类型的选项
        modes_menu = self.tray_menu.addMenu("切换模式")

        # 中考选项
        zhongkao_action = QAction("中考模式", self)
        zhongkao_action.triggered.connect(lambda: self.switch_exam_mode("中考"))
        zhongkao_action.setCheckable(True)
        zhongkao_action.setChecked(self.exam_mode == "中考")
        modes_menu.addAction(zhongkao_action)

        # 高考选项
        gaokao_action = QAction("高考模式", self)
        gaokao_action.triggered.connect(lambda: self.switch_exam_mode("高考"))
        gaokao_action.setCheckable(True)
        gaokao_action.setChecked(self.exam_mode == "高考")
        modes_menu.addAction(gaokao_action)

        # 自定义选项
        custom_action = QAction("自定义模式", self)
        custom_action.triggered.connect(lambda: self.switch_exam_mode("自定义"))
        custom_action.setCheckable(True)
        custom_action.setChecked(self.exam_mode == "自定义")
        modes_menu.addAction(custom_action)

        # 添加修改日期的选项
        change_date_action = QAction("修改日期设置", self)
        change_date_action.triggered.connect(self.show_date_select_dialog)
        self.tray_menu.addAction(change_date_action)

        # 在退出选项前添加恢复出厂设置选项
        factory_reset_action = QAction("恢复出厂设置", self)
        factory_reset_action.triggered.connect(self.reset_to_factory)
        self.tray_menu.addAction(factory_reset_action)

        # 添加退出选项
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(quit_action)

        # 创建托盘图标 - 使用自定义图标，而不依赖系统图标
        self.tray_icon = QSystemTrayIcon(self)

        # 创建一个简单的自定义图标
        icon_pixmap = QPixmap(16, 16)
        icon_pixmap.fill(Qt.GlobalColor.blue)  # 简单的蓝色图标

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
            # 确保定时器停止
            if self.timer.isActive():
                self.timer.stop()
                print("定时器已暂停")
        else:
            self.pause_action.setText("暂停更新")
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
            if action.text() == "修改日期设置":
                continue

        # 弹出日期选择对话框前保存当前模式
        self.save_config()

        # 弹出日期选择对话框
        self.show_date_select_dialog()

        # 立即更新显示
        self.update_countdown()

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
                # 水印样式
                if int(days_left) % 2 == 0:
                    self.countdown_label.setStyleSheet("""
                        color: rgba(128, 128, 128, 180); 
                        font-weight: bold;
                        font-style: normal;
                        text-shadow: 1px 1px 2px rgba(255, 255, 255, 100);
                        background: transparent;
                        padding: 3px;
                    """)
                else:
                    self.countdown_label.setStyleSheet("""
                        color: rgba(100, 100, 100, 180); 
                        font-weight: bold;
                        font-style: normal;
                        text-shadow: 1px 1px 2px rgba(255, 255, 255, 120);
                        background: transparent;
                        padding: 3px;
                    """)
            else:
                # 高辨识度模式
                self.countdown_label.setStyleSheet("""
                    color: rgba(0, 0, 0, 240); 
                    font-weight: bold;
                    font-style: normal;
                    text-shadow: 0px 0px 3px rgba(255, 255, 255, 200);
                    background: rgba(255, 255, 255, 100);
                    border-radius: 5px;
                    padding: 5px;
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
    app = QApplication(sys.argv)

    # 确保应用程序不会在最后一个窗口关闭时退出
    app.setQuitOnLastWindowClosed(False)

    window = CountdownWindow()
    window.show()
    sys.exit(app.exec())

# AI-Assisted End: GitHub Copilot - 2025/04

