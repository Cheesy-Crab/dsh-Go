# -*- coding: utf-8 -*-
"""BLE 方案设计图 v2：手环 → App（Kotlin）→ 本地接口 → 插件 → agent。"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1180
BG = (247, 249, 252)
INK = (28, 34, 46)
MUTED = (96, 108, 128)
LINE = (150, 164, 184)

PHONE_EDGE = (86, 118, 200)
BAND_FILL = (255, 244, 231)
BAND_EDGE = (214, 140, 40)
APP_FILL = (226, 238, 255)
APP_EDGE = (66, 108, 190)
GREEN = (56, 148, 100)
PLUG_FILL = (241, 235, 255)
PLUG_EDGE = (124, 92, 214)
UI_FILL = (255, 236, 241)
UI_EDGE = (208, 96, 120)
API_FILL = (236, 236, 242)
API_EDGE = (110, 116, 132)
KEY_FILL = (255, 248, 224)
KEY_EDGE = (196, 160, 40)

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
f_title = ImageFont.truetype(FONT_B, 40)
f_sub = ImageFont.truetype(FONT, 18)
f_box = ImageFont.truetype(FONT_B, 22)
f_body = ImageFont.truetype(FONT, 15)
f_small = ImageFont.truetype(FONT, 14)
f_label = ImageFont.truetype(FONT, 14)
f_note_b = ImageFont.truetype(FONT_B, 15)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def box(x, y, w, h, title, lines=(), fill=(255, 255, 255), edge=PHONE_EDGE, radius=14):
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=edge, width=2)
    tw = d.textlength(title, font=f_box)
    d.text((x + (w - tw) / 2, y + 11), title, font=f_box, fill=INK)
    ty = y + 40
    for line in lines:
        lw = d.textlength(line, font=f_body)
        d.text((x + (w - lw) / 2, ty), line, font=f_body, fill=MUTED)
        ty += 21


def arrow(points, label=None, color=LINE, width=3, label_offset=(0, -13)):
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


# ---------------- 标题 ----------------
d.text((60, 34), "健康数据 · BLE 方案", font=f_title, fill=INK)
d.text((60, 88), "手环直连手机，不经过小米云，不需要 passToken —— 原始数据不出手机，只有摘要进模型",
       font=f_sub, fill=MUTED)

# ---------------- 左侧 ----------------
box(60, 170, 280, 92, "小米手环 9", ["私有 GATT 服务", "心率 / 步数 / 睡眠"], BAND_FILL, BAND_EDGE)
box(60, 330, 280, 120, "auth key（一次性）", ["从设备日志或 huami-token 获取", "静态不变，除非重新配对"], KEY_FILL, KEY_EDGE)

# ---------------- 手机 ----------------
d.rounded_rectangle([380, 140, 1210, 980], radius=26, outline=PHONE_EDGE, width=3)
d.text((404, 156), "手机", font=f_sub, fill=PHONE_EDGE)
d.text((404, 182), "dsh-go App 内集成（Kotlin）", font=f_small, fill=PHONE_EDGE)

# App 大框
d.rounded_rectangle([420, 230, 840, 800], radius=18, fill=APP_FILL, outline=APP_EDGE, width=2)
d.text((440, 244), "App 侧（Kotlin）", font=f_box, fill=APP_EDGE)

box(444, 286, 372, 80, "① 蓝牙连接与认证", ["配对 → 握手 → 订阅通知", "断线自动重连"], (255, 255, 255), GREEN)
box(444, 386, 372, 80, "② 协议解析", ["心率采样 / 活动数据 / 睡眠段", "解析成统一结构"], (255, 255, 255), GREEN)
box(444, 486, 372, 80, "③ 前台服务常驻", ["保持 BLE 连接，防被系统杀", "电池优化白名单"], (255, 255, 255), GREEN)
box(444, 586, 372, 80, "④ 本地缓存", ["SQLite：小时心率 + 日聚合", "原始采样不长期保存"], (255, 255, 255), GREEN)
box(444, 690, 372, 92, "⑤ 本地接口", ["127.0.0.1:18765", "随机 token，仅回环"], (255, 255, 255), APP_EDGE)

# 手环 → App（走上方走廊）
arrow([(340, 216), (392, 216), (392, 326), (444, 326)], "BLE 连接", color=BAND_EDGE, label_offset=(0, -20))
# key → App（进入 ① 的侧边）
arrow([(340, 390), (404, 390), (404, 356), (444, 356)], "写入 0600", color=KEY_EDGE, label_offset=(0, 26))

# ---------------- 插件 ----------------
d.rounded_rectangle([920, 230, 1170, 620], radius=18, fill=PLUG_FILL, outline=PLUG_EDGE, width=2)
d.text((940, 244), "插件 dsh-health", font=f_box, fill=PLUG_EDGE)
d.text((940, 278), "tools", font=f_body, fill=PLUG_EDGE)
for i, t in enumerate(["health_today", "health_range", "health_sync"]):
    d.text((940, 304 + i * 22), "· " + t, font=f_small, fill=INK)
d.text((940, 388), "panels", font=f_body, fill=PLUG_EDGE)
d.text((940, 414), "· metric × 3", font=f_small, fill=INK)
d.text((940, 438), "· chart 7 天", font=f_small, fill=INK)
d.text((940, 480), "调度：启动 / 每日 / 手动", font=f_small, fill=MUTED)
d.text((940, 504), "聚合：小时 → 日 → 摘要", font=f_small, fill=MUTED)
d.text((940, 544), "隐私：原始数据不外发", font=f_small, fill=(176, 60, 60))

# 本地接口 → 插件
arrow([(816, 736), (872, 736), (872, 400), (920, 400)], "HTTP + token", color=APP_EDGE, label_offset=(-44, 0))

# agent
box(920, 680, 250, 92, "DSH agent", ["读工具结果给建议", "不接触原始数据"], UI_FILL, UI_EDGE)
arrow([(1045, 620), (1045, 680)], "tools", color=UI_EDGE)

# 面板
box(920, 840, 250, 92, "App 面板", ["原生组件渲染", "metric / chart"], UI_FILL, UI_EDGE)
arrow([(920, 560), (890, 560), (890, 886), (920, 886)], "panels", color=UI_EDGE, label_offset=(0, -20))

# 模型 API
box(1270, 680, 280, 92, "DeepSeek API", ["只收到聚合摘要", "不含原始心率"], API_FILL, API_EDGE)
arrow([(1170, 726), (1270, 726)], "只发摘要", color=(205, 60, 60), label_offset=(0, -14))

# ---------------- 底部要点 ----------------
d.text((60, 1030), "和云 API 方案的区别", font=f_sub, fill=INK)
items = [
    ("没有 passToken", "不用抓包，也没有轮换问题"),
    ("auth key 静态", "配一次，长期有效"),
    ("不走小米云", "小米接口变了也不受影响"),
    ("代价", "要写 App 侧 Kotlin + BLE 协议"),
]
x = 60
for title, desc in items:
    w = max(d.textlength(title, font=f_note_b), d.textlength(desc, font=f_small)) + 34
    d.rounded_rectangle([x, 1066, x + w, 1146], radius=10, fill=(255, 255, 255), outline=(210, 218, 230))
    d.text((x + 17, 1076), title, font=f_note_b, fill=(70, 82, 104))
    d.text((x + 17, 1104), desc, font=f_small, fill=MUTED)
    x += w + 22

out = r"E:\code\dsh-go\docs\health-ble.png"
img.save(out)
print("saved", out, img.size)
