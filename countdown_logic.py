import datetime

from PySide6.QtCore import QDate
from PySide6.QtGui import QColor


def calculateExamYear():
    """根据当前日期计算下一次考试默认年份。"""
    currentDate = datetime.datetime.now()
    currentYear = currentDate.year
    return currentYear + 1 if currentDate > datetime.datetime(currentYear, 6, 1) else currentYear


def convertToFullDates(baseDates):
    """把只有月日的基础日期转成带年份的 QDate。"""
    fullDates = {}
    currentDate = datetime.datetime.now()

    for province, examTypes in baseDates.items():
        fullDates[province] = {}
        for examType, dateTuple in examTypes.items():
            if dateTuple is None:
                fullDates[province][examType] = None
                continue

            month, day = dateTuple
            year = currentDate.year
            if currentDate > datetime.datetime(year, month, day):
                year += 1

            fullDates[province][examType] = QDate(year, month, day)

    return fullDates


def buildCountdownText(daysLeft, precision, examMode, examType, customTextTemplate):
    """生成倒计时显示文本。"""
    if examMode == "自定义":
        timeText = f"{daysLeft:.{precision}f}"
        if "{time}" in customTextTemplate:
            return customTextTemplate.replace("{time}", timeText)
        return f"{timeText} {customTextTemplate}"

    if examMode == "中考":
        if examType in ["文化课", "地理生物", "体育考试", "英语听说", "理化实验", "英语听力"]:
            suffix = examType if examType != "文化课" else ""
            return f"距离中考{suffix}: {daysLeft:.{precision}f} 天"
        return f"距离中考: {daysLeft:.{precision}f} 天"

    if examType in ["统一科目", "选考科目", "外语", "技术", "外语听说", "等级考科目", "文理综合", "藏语文", "朝鲜语文", "蒙古语文"]:
        suffix = examType if examType != "统一科目" else ""
        return f"距离高考{suffix}: {daysLeft:.{precision}f} 天"
    return f"距离高考: {daysLeft:.{precision}f} 天"


def hexToRgb(colorHex):
    """把 #RRGGBB 转成 RGB 三元组。"""
    color = QColor(colorHex)
    if not color.isValid():
        color = QColor("#0f1419")
    return color.red(), color.green(), color.blue()


def calculateTimerInterval(precision):
    """根据精度计算定时器更新间隔。"""
    changeSeconds = 86400 * (10 ** (-precision))
    if precision <= 3:
        factor = 0.95
    else:
        factor = 0.9

    interval = int(changeSeconds * factor * 1000)
    minInterval = 10
    maxInterval = 60000
    interval = max(minInterval, min(interval, maxInterval))
    return interval, changeSeconds
