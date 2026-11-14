# -*- coding: utf-8 -*-
"""健康数据接入架构图 v2：把同步器和本地库画进插件边界内。"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1560, 1240
BG = (247, 249, 252)
INK = (28, 34, 46)
MUTED = (96, 108, 128)
LINE = (150, 164, 184)

PHONE_EDGE = (86, 118, 200)
CLOUD_FILL = (255, 244, 231)
CLOUD_EDGE = (214, 140, 40)
GREEN = (56, 148, 100)
PLUG_FILL = (243, 238, 255)
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
    d.text((x + (w - tw) / 2, y + 12), title, font=f_box, fill=INK)
    ty = y + 44
    for line in lines:
        lw = d.textlength(line, font=f_body)
        d.text((x + (w - lw) / 2, ty), line, font=f_body, fill=MUTED)
        ty += 21


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
d.text((60, 38), "健康数据接入架构 · 插件边界", font=f_title, fill=INK)
d.text((60, 92), "同步器和本地库都是插件的组成部分：插件启动同步子进程、拥有并查询自己的数据库",
       font=f_sub, fill=MUTED)

# ---------- 左侧：数据源 ----------
box(60, 170, 300, 80, "小米手环 9", ["传感器 / 屏幕 / 震动"], CLOUD_FILL, CLOUD_EDGE)
box(60, 290, 300, 80, "小米运动健康", ["App 负责同步手环"], CLOUD_FILL, CLOUD_EDGE)
box(60, 410, 300, 96, "小米云 API", ["api-mifit-cn.huami.com", "步数·心率·睡眠·血氧"], (255, 232, 206), CLOUD_EDGE)
arrow([(210, 250), (210, 290)], "BLE")
arrow([(210, 370), (210, 410)], "上传")

# ---------- 手机边界 ----------
d.rounded_rectangle([430, 130, 1180, 1060], radius=24, outline=PHONE_EDGE, width=3)
d.text((452, 146), "手机内（本机模式 · proot）", font=f_sub, fill=PHONE_EDGE)
d.text((452, 170), "远程模式下整个插件不加载", font=f_small, fill=(176, 60, 60))

# ---------- 插件边界 ----------
d.rounded_rectangle([515, 200, 1015, 780], radius=20, outline=PLUG_EDGE, width=3)
d.text((535, 212), "插件 dsh-health", font=f_box, fill=PLUG_EDGE)
d.text((535, 246), "① ② ③ 都在这个边界内", font=f_small, fill=MUTED)

# ① 同步器（子进程）
box(590, 285, 400, 86, "① 同步器（子进程）", ["python3 mi-fitness-bridge sync", "插件按调度启动，退出即结束"], (240, 250, 244), GREEN)


# ② 本地库
box(590, 425, 400, 86, "② 本地库 health.db", ["SQLite · 0600 · 插件数据目录", "插件独占读写"], (240, 250, 244), GREEN)
arrow([(790, 371), (790, 425)], "写入")


# ③ 插件主进程
PY, PH = 552, 195
d.rounded_rectangle([590, PY, 990, PY + PH], radius=14, fill=PLUG_FILL, outline=PLUG_EDGE, width=2)
d.text((590 + (400 - d.textlength("③ 插件主进程（cordis）", font=f_box)) / 2, PY + 11), "③ 插件主进程（cordis）", font=f_box, fill=INK)

d.text((612, PY + 46), "tools", font=f_box, fill=PLUG_EDGE)
for i, t in enumerate(["health_today", "health_range", "health_report"]):
    d.text((612, PY + 78 + i * 24), "· " + t, font=f_small, fill=INK)
d.text((812, PY + 46), "panels", font=f_box, fill=PLUG_EDGE)
for i, t in enumerate(["metric × 3", "chart（7 天）"]):
    d.text((812, PY + 78 + i * 24), "· " + t, font=f_small, fill=INK)
d.text((612, PY + 160), "调度：启动检查 / 每日 03:00 / 手动", font=f_small, fill=MUTED)

arrow([(960, 552), (1002, 552), (1002, 468), (990, 468)], "SQL 查询", color=GREEN, label_offset=(0, 22))
arrow([(600, 552), (556, 552), (556, 350), (590, 350)], "spawn / 调度", color=PLUG_EDGE, label_offset=(0, 44))

# ---------- agent ----------
box(590, 820, 400, 86, "④ DSH agent", ["读工具结果给建议，不接触原始数据"], UI_FILL, UI_EDGE)
arrow([(790, 747), (790, 820)], "tool 调用", color=UI_EDGE)

# ---------- 面板 ----------
box(590, 938, 400, 86, "⑤ App 面板", ["原生组件渲染插件 JSON，不改 Flutter"], UI_FILL, UI_EDGE)
arrow([(590, 700), (500, 700), (500, 980), (590, 980)], "panels 视图", color=UI_EDGE, label_offset=(0, -4))

# ---------- 云端接入 ----------
arrow([(360, 470), (470, 470), (470, 308), (590, 308)], "HTTPS + passToken", color=(214, 140, 40), label_offset=(-40, -22))

# ---------- 模型 API ----------
box(1250, 820, 270, 86, "DeepSeek API", ["只收到摘要数字", "原始数据永不进上下文"], API_FILL, API_EDGE)
arrow([(990, 863), (1250, 863)], "只发摘要", color=(205, 60, 60), label_offset=(0, -14))

# ---------- 底部 ----------
d.text((60, 1090), "隐私红线（代码级约束）", font=f_sub, fill=INK)
items = [
    "① 远程模式不加载：数据不离开手机",
    "② 工具返回值字段白名单",
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
