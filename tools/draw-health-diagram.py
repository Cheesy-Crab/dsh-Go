# -*- coding: utf-8 -*-
"""健康数据接入架构图（A 方案：小米云 API + 本机插件）。"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1560, 1240
BG = (247, 249, 252)
INK = (28, 34, 46)
MUTED = (96, 108, 128)
LINE = (150, 164, 184)

PHONE_FILL = (233, 241, 255)
PHONE_EDGE = (86, 118, 200)
CLOUD_FILL = (255, 244, 231)
CLOUD_EDGE = (214, 140, 40)
DB_EDGE = (56, 148, 100)
PLUG_FILL = (241, 235, 255)
PLUG_EDGE = (124, 92, 214)
UI_FILL = (255, 236, 241)
UI_EDGE = (208, 96, 120)
API_FILL = (236, 236, 242)
API_EDGE = (110, 116, 132)

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
f_title = ImageFont.truetype(FONT_B, 38)
f_sub = ImageFont.truetype(FONT, 17)
f_box = ImageFont.truetype(FONT_B, 22)
f_body = ImageFont.truetype(FONT, 15)
f_small = ImageFont.truetype(FONT, 14)
f_label = ImageFont.truetype(FONT, 14)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def box(x, y, w, h, title, lines=(), fill=(255, 255, 255), edge=PHONE_EDGE, radius=14):
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=edge, width=2)
    tw = d.textlength(title, font=f_box)
    d.text((x + (w - tw) / 2, y + 13), title, font=f_box, fill=INK)
    ty = y + 48
    for line in lines:
        lw = d.textlength(line, font=f_body)
        d.text((x + (w - lw) / 2, ty), line, font=f_body, fill=MUTED)
        ty += 22


def head(x, y, text, color):
    d.text((x, y), text, font=f_box, fill=color)


def text_at(x, y, text, color=INK, font=None):
    d.text((x, y), text, font=font or f_small, fill=color)


def arrow(points, label=None, color=LINE, width=3, label_offset=(0, -12)):
    for i in range(len(points) - 1):
        d.line([points[i], points[i + 1]], fill=color, width=width)
    (x1, y1), (x2, y2) = points[-2], points[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 12
    p1 = (x2 - size * math.cos(ang - 0.42), y2 - size * math.sin(ang - 0.42))
    p2 = (x2 - size * math.cos(ang + 0.42), y2 - size * math.sin(ang + 0.42))
    d.polygon([(x2, y2), p1, p2], fill=color)
    if label:
        mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
        lw = d.textlength(label, font=f_label)
        d.rounded_rectangle([mx - lw / 2 - 7, my - 11, mx + lw / 2 + 7, my + 11], radius=7, fill=BG)
        d.text((mx - lw / 2, my - 9), label, font=f_label, fill=(66, 80, 104))


# ---------- 标题 ----------
d.text((60, 38), "健康数据接入架构", font=f_title, fill=INK)
d.text((60, 92), "A 方案：小米运动健康云 API → 本机同步器 → 本地库 → DSH 插件 → 原生面板（原始数据不出手机）",
       font=f_sub, fill=MUTED)

# ---------- 左侧：数据源 ----------
CLOUD_X, CLOUD_W = 60, 300
box(CLOUD_X, 170, CLOUD_W, 80, "小米手环 9", ["传感器 / 屏幕 / 震动"], CLOUD_FILL, CLOUD_EDGE)
box(CLOUD_X, 290, CLOUD_W, 80, "小米运动健康", ["App 负责同步手环"], CLOUD_FILL, CLOUD_EDGE)
box(CLOUD_X, 410, CLOUD_W, 96, "小米云 API", ["api-mifit-cn.huami.com", "步数·心率·睡眠·血氧"], (255, 232, 206), CLOUD_EDGE)

arrow([(210, 250), (210, 290)], "BLE")
arrow([(210, 370), (210, 410)], "上传")

# ---------- 手机边界 ----------
d.rounded_rectangle([430, 130, 1180, 1060], radius=24, outline=PHONE_EDGE, width=3)
d.text((452, 146), "手机内（本机模式 · proot）", font=f_sub, fill=PHONE_EDGE)
d.text((452, 170), "远程模式下本插件不加载", font=f_small, fill=(176, 60, 60))

CX, CW = 590, 400

# ---------- 链路 ----------
box(CX, 210, CW, 96, "① 同步器", ["mi-fitness-bridge（Python 3.12）", "增量拉取，按类型落库"], (234, 248, 239), DB_EDGE)
box(CX, 356, CW, 90, "② 本地库 health.db", ["SQLite · 文件权限 0600", "日聚合 + 小时级心率"], (234, 248, 239), DB_EDGE)

arrow([(358, 458), (500, 458), (500, 258), (590, 258)], "HTTPS + passToken", color=(214, 140, 40), label_offset=(-46, -26))
arrow([(790, 306), (790, 356)], "写入")

# 插件
PLUG_Y, PLUG_H = 496, 250
d.rounded_rectangle([CX, PLUG_Y, CX + CW, PLUG_Y + PLUG_H], radius=14, fill=PLUG_FILL, outline=PLUG_EDGE, width=2)
d.text((CX + (CW - d.textlength("③ 插件 dsh-health", font=f_box)) / 2, PLUG_Y + 13), "③ 插件 dsh-health", font=f_box, fill=INK)
head(CX + 24, PLUG_Y + 52, "tools", PLUG_EDGE)
for i, t in enumerate(["health_today", "health_range", "health_report"]):
    text_at(CX + 24, PLUG_Y + 84 + i * 25, "· " + t, INK, f_body)
head(CX + 236, PLUG_Y + 52, "panels", PLUG_EDGE)
for i, t in enumerate(["metric × 3", "chart（7 天趋势）"]):
    text_at(CX + 236, PLUG_Y + 84 + i * 25, "· " + t, INK, f_body)
text_at(CX + 24, PLUG_Y + 176, "调度：启动检查 / 每日 03:00 / 手动", MUTED)
text_at(CX + 24, PLUG_Y + 202, "隐私：只输出聚合摘要，原始心率不外发", (176, 60, 60))
arrow([(790, 446), (790, 496)], "SQL 查询", color=DB_EDGE)

# agent
box(CX, 790, CW, 88, "④ DSH agent", ["读工具结果给建议，不接触原始数据"], UI_FILL, UI_EDGE)
arrow([(790, 746), (790, 790)], "tool 调用", color=UI_EDGE)

# 面板（agent 下方，箭头走左侧留白）
box(CX, 920, CW, 88, "⑤ App 面板", ["原生组件渲染，不用改 Flutter 代码"], UI_FILL, UI_EDGE)
arrow([(CX, 610), (CX - 70, 610), (CX - 70, 964), (CX, 964)], "panels 视图", color=UI_EDGE, label_offset=(0, -4))

# ---------- 右侧：模型 API ----------
API_X, API_W = 1250, 270
box(API_X, 792, API_W, 88, "DeepSeek API", ["只收到摘要数字", "原始数据永不进上下文"], API_FILL, API_EDGE)
arrow([(CX + CW, 836), (API_X, 836)], "只发摘要", color=(205, 60, 60), label_offset=(0, -14))

# ---------- 底部：隐私红线 ----------
d.text((60, 1090), "隐私红线（代码级约束）", font=f_sub, fill=INK)
items = [
    "① 远程模式不加载：数据不离开手机",
    "② 返回值字段白名单，多余字段不返回",
    "③ 日志只记状态，不记数值",
    "④ 原始心率不落盘，只存小时聚合",
]
x = 60
for it in items:
    lw = d.textlength(it, font=f_small)
    d.rounded_rectangle([x, 1126, x + lw + 28, 1164], radius=10, fill=(255, 255, 255), outline=(210, 218, 230))
    d.text((x + 14, 1135), it, font=f_small, fill=(70, 82, 104))
    x += lw + 44

out = r"E:\code\dsh-go\docs\health-architecture.png"
img.save(out)
print("saved", out, img.size)
