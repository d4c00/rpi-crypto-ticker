# Copyright (c) 2026 length <me@length.cc> (https://github.com/d4c00)
# Licensed under the MIT License.

import os
import sys
import time
import socket
import requests
import ST7789
import threading
import functools
from PIL import Image, ImageDraw, ImageFont

print = functools.partial(print, flush=True)

def systemd_notify(msg):
    addr = os.getenv("NOTIFY_SOCKET")
    if not addr: return
    try:
        if addr.startswith("@"): addr = "\0" + addr[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
            s.sendto(msg.encode(), addr)
    except: pass

disp = ST7789.ST7789()
disp.Init()
disp.SPI.max_speed_hz = 8000000 
disp.GPIO_BL_PIN.frequency = 1024 
disp.bl_DutyCycle(3) 

FONT_PATH = "Font/Georama-Regular.ttf"

PAIRS = [
    ("BTCUSDT", "BTC/USDT", "btc"),
    ("ETHUSDT", "ETH/USDT", "eth"),
    ("ETHBTC",  "ETH/BTC",  "ethbtc"), 
]

SCREEN_W, SCREEN_H = 240, 240

font_cache = {}
def get_font(size):
    if size not in font_cache:
        font_cache[size] = ImageFont.truetype(FONT_PATH, size)
    return font_cache[size]

icon_cache = {}
def get_icon(name, size):
    key = f"{name}_{size}"
    if key not in icon_cache:
        try:
            img = Image.open(f"img/{name}.png").convert("RGBA").resize((size, size))
            icon_cache[key] = img
        except: icon_cache[key] = None
    return icon_cache[key]

def format_prices(price_dict):
    if not price_dict: return {}
    formatted = {}
    for symbol in [p[0] for p in PAIRS]:
        if symbol in price_dict:
            p_float = float(price_dict[symbol])
            if p_float >= 10:
                formatted[symbol] = f"{p_float:.1f}"
            else:
                if p_float >= 1:
                    formatted[symbol] = f"{p_float:.2f}"
                else:
                    s_str = f"{p_float:.15f}"
                    _, decimal_part = s_str.split('.')
                    idx = 0
                    while idx < len(decimal_part) and decimal_part[idx] == '0':
                        idx += 1
                    precision = idx + 3
                    formatted[symbol] = f"{p_float:.{precision}f}"
    return formatted

current_frame = Image.new("RGB", (SCREEN_W, SCREEN_H), (0, 0, 0)).rotate(270)
frame_lock = threading.Lock()
frame_updated = threading.Event() 
last_prices = {} 

def api_worker():
    MARGIN = 3
    global current_frame, last_prices
    
    symbols_str = ",".join([f'"{p[0]}"' for p in PAIRS])
    url = f'https://api.binance.com/api/v3/ticker/price?symbols=[{symbols_str}]'
    
    N = len(PAIRS)
    if N == 0: return

    MAX_ROW_H = 80
    row_H = min(SCREEN_H // N, MAX_ROW_H)
    total_list_H = N * row_H
    available_H = SCREEN_H - (MARGIN * 2)
    base_y = MARGIN + (available_H - total_list_H) // 2

    name_font_size = max(10, min(int(row_H * 0.32), 24))
    name_font = get_font(name_font_size)
    icon_size = max(12, min(int(row_H * 0.30), 26))

    price_max_W = SCREEN_W - (MARGIN * 2)
    price_max_H = row_H - name_font_size - 6
    
    bg_template = Image.new("RGB", (SCREEN_W, SCREEN_H), (0, 0, 0))
        
    while True:
        try:
            r = requests.get(url, timeout=4.0)
            
            if r.status_code == 200:
                print(f"API Success: Status 200. Updating display and petting watchdog.")
                data = r.json()
                temp = {item['symbol']: item['price'] for item in data}
                
                if temp != last_prices:
                    last_prices = temp 
                    canvas = bg_template.copy()
                    draw = ImageDraw.Draw(canvas)
                    f_prices = format_prices(temp)

                    test_size = 10
                    best_price_size = test_size
                    while test_size <= 100:
                        fnt = get_font(test_size)
                        max_w, max_h = 0, 0
                        for p in PAIRS:
                            if p[0] in f_prices:
                                bbox = fnt.getbbox(f_prices[p[0]])
                                w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
                                if w > max_w: max_w = w
                                if h > max_h: max_h = h
                        if max_w >= price_max_W or max_h >= price_max_H:
                            best_price_size = max(10, test_size - 1)
                            break
                        best_price_size = test_size
                        test_size += 1
                    
                    price_font = get_font(best_price_size)
                    internal_spacing = -max(2, int(best_price_size * 0.1))

                    for i, (symbol, display_name, icon_name) in enumerate(PAIRS):
                        if symbol not in f_prices: continue
                        y_row_top = base_y + i * row_H
                        content_total_H = name_font_size + best_price_size + internal_spacing
                        v_padding = max(0, (row_H - content_total_H) // 2)
                        icon = get_icon(icon_name, icon_size)
                        if icon:
                            icon_y = y_row_top + v_padding + (name_font_size - icon_size) // 2 + 4
                            canvas.paste(icon, (6, icon_y), icon)
                        name_x = 6 + icon_size + 6 if icon else 6
                        name_y = y_row_top + v_padding
                        draw.text((name_x, name_y), display_name, fill=(150, 150, 150), font=name_font)
                        price_y = name_y + name_font_size + internal_spacing
                        draw.text((6, price_y), f_prices[symbol], fill=(255, 255, 255), font=price_font)
                        
                    ready_to_push = canvas.rotate(270)
                    with frame_lock:
                        current_frame = ready_to_push
                    frame_updated.set() 

                systemd_notify("WATCHDOG=1")
            else:
                print(f"API Warning: Received status code {r.status_code}. Watchdog skipped.")

        except Exception as e:
            print(f"API Error Exception: {str(e)}")

        time.sleep(5) 

threading.Thread(target=api_worker, daemon=True).start()

try:
    systemd_notify("READY=1")
    print("Service started successfully.")
    disp.ShowImage(current_frame)
    while True:
        if frame_updated.wait(timeout=1.0):
            with frame_lock:
                disp.ShowImage(current_frame)
            frame_updated.clear() 
except KeyboardInterrupt:
    print("Process killed by user.")
    disp.module_exit()
