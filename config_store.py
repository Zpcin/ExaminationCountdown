import datetime
import json
import os

from app_constants import VERSION, CONFIG_DIR, CONFIG_FILE
from dates_data import baseZhongkaoDates, baseGaokaoDates
from countdown_logic import convertToFullDates


def updateBaseDatesFromConfig(baseDatesDict, configDatesDict):
    """从配置文件的日期字典更新基础日期字典。"""
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
                year, month, day = map(int, dateStr.split("-"))
                baseDatesDict[province][examType] = (month, day)
            except (ValueError, TypeError) as e:
                print(f"解析日期'{dateStr}'失败: {e}")
                continue


def loadConfig(window):
    """从配置文件加载设置到窗口对象。"""
    if not os.path.exists(CONFIG_FILE):
        print(f"配置文件不存在，将使用默认设置。配置路径: {CONFIG_FILE}")
        writeDefaultConfig(window)
        return

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        fileVersion = config.get("version", "0")
        if fileVersion < VERSION:
            print(f"检测到新版本({VERSION})，更新配置文件...")
            writeDefaultConfig(window)
            return

        window.position = config.get("position", window.position)
        window.precision = config.get("precision", window.precision)
        window.displayMode = config.get("display_mode", window.displayMode)
        window.fontScale = config.get("font_scale", window.fontScale)
        legacyFontColor = config.get("font_color", window.visibleColor)
        window.watermarkColor = config.get("watermark_color", legacyFontColor)
        window.visibleColor = config.get("visible_color", legacyFontColor)
        window.fontColor = window.visibleColor
        window.windowWidth = config.get("window_width", window.windowWidth)
        window.windowHeight = config.get("window_height", window.windowHeight)
        window.examType = config.get("exam_type", window.examType)
        window.examMode = config.get("exam_mode", window.examMode)
        window.customTextTemplate = config.get("custom_text_template", window.customTextTemplate)

        dates = config.get("dates", {})
        if "zhongkao" in dates and dates["zhongkao"]:
            updateBaseDatesFromConfig(baseZhongkaoDates, dates["zhongkao"])
        if "gaokao" in dates and dates["gaokao"]:
            updateBaseDatesFromConfig(baseGaokaoDates, dates["gaokao"])

        targetDateStr = config.get("target_date")
        if targetDateStr:
            try:
                dateParts = list(map(int, targetDateStr.split("-")))
                window.targetDate = datetime.datetime(dateParts[0], dateParts[1], dateParts[2])
                print(f"按配置文件加载日期: {window.targetDate.strftime('%Y-%m-%d')}")
            except (ValueError, IndexError) as e:
                print(f"日期解析错误: {e}，将使用默认日期")
                window.targetDate = None

        print(f"成功从配置文件加载设置: {CONFIG_FILE}")
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        window.targetDate = None


def writeDefaultConfig(window):
    """写入默认配置，包括版本号和考试日期列表。"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)

        defaultDates = {
            "zhongkao": convertToFullDates(baseZhongkaoDates),
            "gaokao": convertToFullDates(baseGaokaoDates),
        }

        config = {
            "version": VERSION,
            "position": window.position,
            "precision": window.precision,
            "display_mode": window.displayMode,
            "font_scale": window.fontScale,
            "font_color": window.visibleColor,
            "watermark_color": window.watermarkColor,
            "visible_color": window.visibleColor,
            "window_width": window.windowWidth,
            "window_height": window.windowHeight,
            "target_date": None,
            "exam_type": window.examType,
            "exam_mode": window.examMode,
            "custom_text_template": window.customTextTemplate,
            "dates": defaultDates,
        }

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        print(f"默认配置已写入: {CONFIG_FILE}")
    except Exception as e:
        print(f"写入默认配置时出错: {e}")


def saveConfig(window):
    """保存当前设置到配置文件。"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)

        targetDateStr = None
        if window.targetDate:
            targetDateStr = f"{window.targetDate.year}-{window.targetDate.month}-{window.targetDate.day}"

        dates = {
            "zhongkao": convertToFullDates(baseZhongkaoDates),
            "gaokao": convertToFullDates(baseGaokaoDates),
        }

        config = {
            "version": VERSION,
            "position": window.position,
            "precision": window.precision,
            "display_mode": window.displayMode,
            "font_scale": window.fontScale,
            "font_color": window.visibleColor,
            "watermark_color": window.watermarkColor,
            "visible_color": window.visibleColor,
            "window_width": window.windowWidth,
            "window_height": window.windowHeight,
            "target_date": targetDateStr,
            "exam_type": window.examType,
            "exam_mode": window.examMode,
            "custom_text_template": window.customTextTemplate,
            "dates": dates,
        }

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        print(f"设置已保存到配置文件: {CONFIG_FILE}")
    except Exception as e:
        print(f"保存配置文件出错: {e}")
