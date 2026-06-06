from flask import Flask, request, jsonify
import threading
import asyncio
import random
import time
import os
import base64
from datetime import datetime
from telegram.ext import Application
from telegram.error import TelegramError

# ===== CONFIG =====
# ===== CONFIG =====
# ===== CONFIG =====
BOT_TOKEN = "8712586807:AAFsxiKFcgzRNjxRGGf8k0nQe5xHYmhu38I"
CHAT_IDS = [-1003918677832]
IMAGE_PATH = "bot_image.jpg"
POINT_IMAGES_DIR = "point_images"
PHOTO_DELAY_SECONDS = 50
PHOTO_DELAY_MODE = "seconds"

# 👇 YEH LINE ADD KARO (STICKER ID)
STICKER_ID = "CAACAgUAAxkBAAMCaiRWjvjHc2C31Q6uEL6Su0peYHAAAjcSAAJ2BdhUkXpqesFXi6w7BA"

os.makedirs(POINT_IMAGES_DIR, exist_ok=True)

app = Flask(__name__)
bot_application = None

state = {
    "running": False,
    "image": None,
    "interval": 10,
    "photo_delay": PHOTO_DELAY_SECONDS,
    "photo_delay_mode": PHOTO_DELAY_MODE,
    "message_template": "💥 ⚓️ HOLD TIGHT TRADERS⏳\nTIME: {time}\n🥇━━━━━━━━━━━━━━━\n💸 OUT: {multiplier}X 🤑\n━━━━━━━━━━━━━━━📱",
    "multiplier_list": [
        {"value": 2.61, "image": None},
        {"value": 5.00, "image": None},
        {"value": 10.00, "image": None},
        {"value": 20.00, "image": None},
        {"value": 50.00, "image": None},
    ],
}

def get_random_point():
    lst = state.get("multiplier_list", [])
    if lst:
        return random.choice(lst)
    return {"value": round(random.uniform(1.0, 20.0), 2), "image": None}

def get_message(multiplier_value):
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    return state["message_template"].replace("{time}", time_str).replace("{multiplier}", str(multiplier_value))

def get_delay_seconds():
    """Returns delay in seconds based on mode"""
    delay_value = state.get("photo_delay", 50)
    mode = state.get("photo_delay_mode", "seconds")
    
    if mode == "minutes":
        return delay_value * 60  # Convert minutes to seconds
    else:
        return delay_value  # Already in seconds

async def send_delayed_photo(chat_id, image_path, multiplier_value, delay_seconds):
    global bot_application
    try:
        mode = state.get("photo_delay_mode", "seconds")
        if mode == "minutes":
            print(f"[⏰] Waiting {delay_seconds//60} minutes for {multiplier_value}X photo...")
        else:
            print(f"[⏰] Waiting {delay_seconds} seconds for {multiplier_value}X photo...")
        
        await asyncio.sleep(delay_seconds)
        
        if bot_application and os.path.exists(image_path):
            # PEHLE IMAGE BHEJO
            with open(image_path, "rb") as img:
                await bot_application.bot.send_photo(chat_id=chat_id, photo=img)
            print(f"[📸] {multiplier_value}X photo sent!")
            
            # 👇 YE LINES YAHAN LAGAO (FUNCTION KE ANDAR) 👇
            await asyncio.sleep(1)
            if STICKER_ID:
                await bot_application.bot.send_sticker(chat_id=chat_id, sticker=STICKER_ID)
                print(f"[🎮] Sticker sent after image!")
            # 👆 YE LINES YAHAN LAGAO
            
        else:
            print(f"[❌] Failed to send photo")
    except Exception as e:
        print(f"[❌] Error: {e}")
async def send_message(bot_app):
    global bot_application
    bot_application = bot_app
    
    point = get_random_point()
    multiplier_value = point["value"]
    point_image_path = point.get("image")
    caption = get_message(multiplier_value)
    delay_seconds = get_delay_seconds()

    for chat_id in CHAT_IDS:
        try:
            # STEP 1: Prediction message
            print(f"[📢] Sending prediction for {multiplier_value}X...")
            if state["image"] and os.path.exists(IMAGE_PATH):
                with open(IMAGE_PATH, "rb") as img:
                    await bot_app.bot.send_photo(chat_id=chat_id, photo=img, caption=caption)
            else:
                await bot_app.bot.send_message(chat_id=chat_id, text=caption)
            
            print(f"[✅] Prediction sent: {multiplier_value}X")
            
            # 👇👇👇 STICKER BHEJNE KI LINE (ADD THIS) 👇👇👇
            # Sticker bhejo
            if STICKER_ID:
                await bot_app.bot.send_sticker(chat_id=chat_id, sticker=STICKER_ID)
                print(f"[🎮] Sticker sent!")
                await asyncio.sleep(0.5)
            # 👆👆👆
            
            # Warning message
            await bot_app.bot.send_message(chat_id=chat_id, text="📌 💯\nENTER NOW का स्टीकर आने के बाद ही Game को Refresh करके फिर बेट लगानी है । 👏👏")
            
            # GO GO message
            await bot_app.bot.send_message(chat_id=chat_id, text="⚡ GO GO ⚡")
            
            # Point photo with delay
            if point_image_path and os.path.exists(point_image_path):
                asyncio.create_task(send_delayed_photo(chat_id, point_image_path, multiplier_value, delay_seconds))
            
        except TelegramError as e:
            print(f"[❌] Error: {e}")

async def run_bot_loop():
    global bot_application
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_application = bot_app
    async with bot_app:
        await bot_app.start()
        await bot_app.updater.start_polling(allowed_updates=[])
        print("[✅] Bot started!")
        while state["running"]:
            await send_message(bot_app)
            interval_secs = state["interval"] * 60
            for _ in range(interval_secs):
                if not state["running"]:
                    break
                await asyncio.sleep(1)
        await bot_app.updater.stop()
        await bot_app.stop()
    print("[🛑] Bot stopped!")

def bot_thread_func():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot_loop())
    loop.close()

# ===== API ROUTES =====
@app.route("/api/start", methods=["POST"])
def start_bot():
    if state["running"]:
        return jsonify({"status": "already_running"})
    state["running"] = True
    t = threading.Thread(target=bot_thread_func, daemon=True)
    t.start()
    return jsonify({"status": "started"})

@app.route("/api/stop", methods=["POST"])
def stop_bot():
    state["running"] = False
    return jsonify({"status": "stopped"})

@app.route("/api/status", methods=["GET"])
def get_status():
    safe_list = [{"value": p["value"], "has_image": bool(p.get("image") and os.path.exists(p["image"]))} for p in state["multiplier_list"]]
    return jsonify({
        "running": state["running"],
        "has_image": state["image"] is not None,
        "interval": state["interval"],
        "photo_delay": state.get("photo_delay", 50),
        "photo_delay_mode": state.get("photo_delay_mode", "seconds"),
        "message_template": state["message_template"],
        "multiplier_list": safe_list,
    })

@app.route("/api/update_photo_delay", methods=["POST"])
def update_photo_delay():
    data = request.json
    delay_value = int(data.get("delay", 50))
    mode = data.get("mode", "seconds")
    
    if delay_value < 1:
        delay_value = 1
    
    state["photo_delay"] = delay_value
    state["photo_delay_mode"] = mode
    
    return jsonify({"status": "updated", "delay": delay_value, "mode": mode})

@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    data = request.json
    img_data = data.get("image")
    if not img_data:
        return jsonify({"error": "No image"}), 400
    if "," in img_data:
        img_data = img_data.split(",")[1]
    with open(IMAGE_PATH, "wb") as f:
        f.write(base64.b64decode(img_data))
    state["image"] = img_data
    return jsonify({"status": "image_saved"})

@app.route("/api/remove_image", methods=["POST"])
def remove_image():
    state["image"] = None
    if os.path.exists(IMAGE_PATH):
        os.remove(IMAGE_PATH)
    return jsonify({"status": "image_removed"})

@app.route("/api/update_message", methods=["POST"])
def update_message():
    data = request.json
    state["message_template"] = data.get("template", state["message_template"])
    return jsonify({"status": "updated"})

@app.route("/api/update_interval", methods=["POST"])
def update_interval():
    data = request.json
    mins = int(data.get("interval", 10))
    if mins < 1: mins = 1
    state["interval"] = mins
    return jsonify({"status": "updated", "interval": state["interval"]})

@app.route("/api/update_multipliers", methods=["POST"])
def update_multipliers():
    data = request.json
    lst = data.get("multipliers", [])
    new_list = []
    for item in lst:
        try:
            val = round(float(item["value"]), 2)
            if val <= 0:
                continue
            img_b64 = item.get("image")
            img_path = None
            if img_b64:
                safe_name = str(val).replace(".", "_")
                img_path = os.path.join(POINT_IMAGES_DIR, f"{safe_name}.jpg")
                raw = img_b64.split(",")[1] if "," in img_b64 else img_b64
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(raw))
            else:
                safe_name = str(val).replace(".", "_")
                old_path = os.path.join(POINT_IMAGES_DIR, f"{safe_name}.jpg")
                if os.path.exists(old_path):
                    img_path = old_path
            new_list.append({"value": val, "image": img_path})
        except Exception as e:
            print(f"Error: {e}")
    state["multiplier_list"] = new_list
    safe = [{"value": p["value"], "has_image": bool(p["image"] and os.path.exists(p["image"]))} for p in new_list]
    return jsonify({"status": "updated", "multiplier_list": safe})

@app.route("/api/upload_point_image", methods=["POST"])
def upload_point_image():
    data = request.json
    value = data.get("value")
    img_b64 = data.get("image")
    if not value or not img_b64:
        return jsonify({"error": "value aur image dono chahiye"}), 400
    try:
        val = round(float(value), 2)
        safe_name = str(val).replace(".", "_")
        img_path = os.path.join(POINT_IMAGES_DIR, f"{safe_name}.jpg")
        raw = img_b64.split(",")[1] if "," in img_b64 else img_b64
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(raw))
        for point in state["multiplier_list"]:
            if point["value"] == val:
                point["image"] = img_path
                break
        return jsonify({"status": "image_saved", "value": val})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/remove_point_image", methods=["POST"])
def remove_point_image():
    data = request.json
    value = data.get("value")
    if not value:
        return jsonify({"error": "value chahiye"}), 400
    try:
        val = round(float(value), 2)
        safe_name = str(val).replace(".", "_")
        img_path = os.path.join(POINT_IMAGES_DIR, f"{safe_name}.jpg")
        if os.path.exists(img_path):
            os.remove(img_path)
        for point in state["multiplier_list"]:
            if point["value"] == val:
                point["image"] = None
                break
        return jsonify({"status": "image_removed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return HTML_PAGE

HTML_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bot Admin Panel</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: #0a0e1a;
    color: #c8d8f0;
    font-family: Arial, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 30px 16px;
  }
  h1 { color: #00d4ff; margin-bottom: 10px; }
  .card {
    background: #0f1628;
    border: 1px solid #1e2d4a;
    border-radius: 16px;
    padding: 24px;
    width: 100%;
    max-width: 500px;
    margin-bottom: 18px;
  }
  .card-title {
    font-size: 0.7rem;
    letter-spacing: 3px;
    color: #4a6080;
    margin-bottom: 18px;
  }
  .status-row { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
  .status-dot {
    width: 14px; height: 14px;
    border-radius: 50%;
    background: #ff3b5c;
  }
  .status-dot.active { background: #00ff88; }
  .btn-row { display: flex; gap: 12px; }
  button {
    padding: 12px;
    border: none;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    flex: 1;
  }
  .btn-start { background: #00ff88; color: #001a0a; }
  .btn-stop { background: #ff3b5c; color: white; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .delay-row, .interval-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  input, select {
    background: #0a0e1a;
    border: 1px solid #1e2d4a;
    color: #00d4ff;
    padding: 10px;
    border-radius: 8px;
  }
  .btn-save {
    background: transparent;
    border: 1px solid #00d4ff;
    color: #00d4ff;
    padding: 8px 16px;
    flex: 0;
  }
  .quick-btns { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
  .quick-btn {
    background: rgba(0,212,255,0.05);
    border: 1px solid #1e2d4a;
    color: #c8d8f0;
    padding: 6px 12px;
    font-size: 0.8rem;
    flex: 0;
  }
  .mult-add-row { display: flex; gap: 10px; margin-bottom: 14px; }
  .mult-input { flex: 1; }
  .btn-add-mult { background: #00c853; color: white; flex: 0; }
  .point-card {
    background: rgba(0,255,136,0.04);
    border: 1px solid rgba(0,255,136,0.2);
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
  }
  .point-card-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .point-value-badge {
    background: rgba(0,255,136,0.1);
    border: 1px solid rgba(0,255,136,0.3);
    color: #00ff88;
    padding: 6px 12px;
    border-radius: 8px;
    font-weight: bold;
  }
  .img-status-tag {
    font-size: 0.7rem;
    padding: 3px 8px;
    border-radius: 4px;
  }
  .has-img { background: rgba(0,255,136,0.1); color: #00ff88; }
  .no-img { background: rgba(255,107,53,0.1); color: #ff6b35; }
  .btn-del-point {
    margin-left: auto;
    background: transparent;
    border: 1px solid rgba(255,59,92,0.3);
    color: #ff3b5c;
    padding: 4px 10px;
    flex: 0;
  }
  .btn-save-mult, .btn-save-msg {
    width: 100%;
    margin-top: 12px;
    background: linear-gradient(135deg,#003d1a,#004d20);
    border: 1px solid #00ff88;
    color: #00ff88;
  }
  .msg-editor {
    width: 100%;
    background: #0a0e1a;
    border: 1px solid #1e2d4a;
    color: #c8d8f0;
    padding: 12px;
    border-radius: 10px;
    min-height: 100px;
  }
  .preview-box {
    background: #0a0e1a;
    border: 1px solid rgba(0,212,255,0.15);
    border-radius: 10px;
    padding: 12px;
    margin-top: 12px;
    font-size: 0.8rem;
  }
  .upload-area {
    border: 2px dashed #1e2d4a;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    cursor: pointer;
    position: relative;
  }
  .upload-area input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
  }
  #preview-area { display: none; margin-top: 14px; }
  #preview-area img { width: 100%; border-radius: 10px; max-height: 150px; }
  .toast {
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%) translateY(80px);
    background: #0f1628;
    border: 1px solid #00d4ff;
    color: #00d4ff;
    padding: 10px 20px;
    border-radius: 8px;
    transition: transform 0.3s;
    z-index: 999;
  }
  .toast.show { transform: translateX(-50%) translateY(0); }
  .timing-info {
    font-size: 0.7rem;
    color: #4a6080;
    padding: 6px 10px;
    background: rgba(0,212,255,0.04);
    border-radius: 6px;
    margin-top: 10px;
  }
  .mode-select {
    background: #0a0e1a;
    border: 1px solid #1e2d4a;
    color: #00d4ff;
    padding: 10px;
    border-radius: 8px;
    cursor: pointer;
  }
</style>
</head>
<body>

<h1>⚡ BOT PANEL</h1>

<div class="card">
  <div class="card-title">// BOT STATUS</div>
  <div class="status-row">
    <div class="status-dot" id="status-dot"></div>
    <span id="status-text">OFFLINE</span>
  </div>
  <div class="btn-row">
    <button class="btn-start" id="btn-start" onclick="startBot()">▶ START</button>
    <button class="btn-stop" id="btn-stop" onclick="stopBot()" disabled>■ STOP</button>
  </div>
</div>

<div class="card">
  <div class="card-title">// PHOTO DELAY</div>
  <div class="delay-row">
    <input type="number" id="delay-val" value="50" min="1" max="999" style="width:100px;">
    <select id="delay-mode" class="mode-select">
      <option value="seconds">Seconds</option>
      <option value="minutes">Minutes</option>
    </select>
    <button class="btn-save" onclick="savePhotoDelay()">SAVE</button>
  </div>
  <div class="quick-btns">
    <button class="quick-btn" onclick="setDelay(10, 'seconds')">10 Sec</button>
    <button class="quick-btn" onclick="setDelay(30, 'seconds')">30 Sec</button>
    <button class="quick-btn" onclick="setDelay(50, 'seconds')">50 Sec</button>
    <button class="quick-btn" onclick="setDelay(60, 'seconds')">60 Sec</button>
    <button class="quick-btn" onclick="setDelay(5, 'minutes')">5 Min</button>
    <button class="quick-btn" onclick="setDelay(10, 'minutes')">10 Min</button>
    <button class="quick-btn" onclick="setDelay(11, 'minutes')">11 Min</button>
    <button class="quick-btn" onclick="setDelay(15, 'minutes')">15 Min</button>
    <button class="quick-btn" onclick="setDelay(30, 'minutes')">30 Min</button>
    <button class="quick-btn" onclick="setDelay(60, 'minutes')">60 Min</button>
  </div>
  <div class="timing-info" id="delay-info">⏱ Prediction turant jayega, photo <span id="delay-display">50</span> <span id="delay-unit">seconds</span> BAAD jayegi</div>
</div>

<div class="card">
  <div class="card-title">// MESSAGE INTERVAL</div>
  <div class="interval-row">
    <input type="number" id="interval-val" value="10" min="1" style="width:80px;">
    <span>MINUTES</span>
    <button class="btn-save" onclick="saveInterval()">SAVE</button>
  </div>
  <div class="quick-btns">
    <button class="quick-btn" onclick="setInterval_(1)">1 Min</button>
    <button class="quick-btn" onclick="setInterval_(5)">5 Min</button>
    <button class="quick-btn" onclick="setInterval_(10)">10 Min</button>
    <button class="quick-btn" onclick="setInterval_(30)">30 Min</button>
    <button class="quick-btn" onclick="setInterval_(60)">60 Min</button>
  </div>
</div>

<div class="card">
  <div class="card-title">// PREDICTION POINTS</div>
  <div class="mult-add-row">
    <input type="number" class="mult-input" id="mult-new-val" placeholder="2.61" step="0.01">
    <button class="btn-add-mult" onclick="addMultiplier()">+ ADD</button>
  </div>
  <div id="mult-list"></div>
  <button class="btn-save-mult" onclick="saveMultipliers()">💾 SAVE LIST</button>
  <button class="btn-save-mult" onclick="clearMultipliers()" style="margin-top:5px;">🗑 CLEAR ALL</button>
</div>

<div class="card">
  <div class="card-title">// MESSAGE TEMPLATE</div>
  <textarea class="msg-editor" id="msg-template"></textarea>
  <div class="preview-box" id="msg-preview"></div>
  <button class="btn-save-msg" onclick="saveMessage()">💾 SAVE MESSAGE</button>
</div>

<div class="card">
  <div class="card-title">// DEFAULT IMAGE</div>
  <div class="upload-area" id="upload-area">
    <input type="file" accept="image/*" onchange="handleImageUpload(this)">
    <div>📷 CLICK TO UPLOAD DEFAULT IMAGE</div>
  </div>
  <div id="preview-area">
    <img id="preview-img" src="">
    <button class="btn-save-mult" onclick="removeImage()" style="margin-top:10px;">🗑 REMOVE IMAGE</button>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let multList = [];

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function renderMultList() {
  const container = document.getElementById('mult-list');
  if (multList.length === 0) {
    container.innerHTML = '<div style="color:#4a6080;padding:20px;text-align:center;">No points added</div>';
    return;
  }
  container.innerHTML = multList.map((item, i) => {
    const hasImg = item.hasImage || item.image;
    return `
      <div class="point-card">
        <div class="point-card-top">
          <span class="point-value-badge">${item.value}X</span>
          <span class="img-status-tag ${hasImg ? 'has-img' : 'no-img'}">${hasImg ? '📸 PHOTO SET' : '⚠ NO PHOTO'}</span>
          <input type="file" accept="image/*" id="file-${i}" style="display:none;" onchange="uploadPointImage(${i}, this)">
          <button class="quick-btn" onclick="document.getElementById('file-${i}').click()">${hasImg ? 'CHANGE' : 'ADD PHOTO'}</button>
          <button class="btn-del-point" onclick="deletePoint(${i})">✕ DELETE</button>
        </div>
      </div>
    `;
  }).join('');
}

async function uploadPointImage(i, input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async function(e) {
    const res = await fetch('/api/upload_point_image', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({value: multList[i].value, image: e.target.result})
    });
    if (res.ok) {
      multList[i].hasImage = true;
      renderMultList();
      showToast('Photo uploaded!');
    }
  };
  reader.readAsDataURL(file);
}

function deletePoint(i) {
  multList.splice(i, 1);
  renderMultList();
}

function addMultiplier() {
  const inp = document.getElementById('mult-new-val');
  const val = parseFloat(inp.value);
  if (isNaN(val) || val <= 0) { showToast('Invalid number'); return; }
  const rounded = Math.round(val * 100) / 100;
  if (multList.find(m => m.value === rounded)) { showToast('Already exists'); return; }
  multList.push({value: rounded, hasImage: false});
  multList.sort((a,b) => a.value - b.value);
  inp.value = '';
  renderMultList();
}

function clearMultipliers() {
  multList = [];
  renderMultList();
}

async function saveMultipliers() {
  const payload = multList.map(m => ({value: m.value, image: null}));
  const res = await fetch('/api/update_multipliers', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({multipliers: payload})
  });
  const data = await res.json();
  if (data.multiplier_list) {
    multList = data.multiplier_list.map(m => ({value: m.value, hasImage: m.has_image}));
    renderMultList();
  }
  showToast('Saved!');
}

async function savePhotoDelay() {
  const delay = document.getElementById('delay-val').value;
  const mode = document.getElementById('delay-mode').value;
  const res = await fetch('/api/update_photo_delay', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({delay: parseInt(delay), mode: mode})
  });
  const data = await res.json();
  document.getElementById('delay-display').textContent = data.delay;
  document.getElementById('delay-unit').textContent = data.mode;
  document.getElementById('delay-info').innerHTML = `⏱ Prediction turant jayega, photo <span id="delay-display">${data.delay}</span> <span id="delay-unit">${data.mode}</span> BAAD jayegi`;
  showToast(`Delay updated: ${data.delay} ${data.mode}`);
}

function setDelay(value, mode) {
  document.getElementById('delay-val').value = value;
  document.getElementById('delay-mode').value = mode;
  savePhotoDelay();
}

function setInterval_(min) {
  document.getElementById('interval-val').value = min;
  saveInterval();
}

async function saveInterval() {
  const val = document.getElementById('interval-val').value;
  await fetch('/api/update_interval', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({interval: val})
  });
  showToast('Interval saved!');
}

async function saveMessage() {
  const tpl = document.getElementById('msg-template').value;
  await fetch('/api/update_message', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({template: tpl})
  });
  showToast('Message saved!');
  updatePreview();
}

function updatePreview() {
  const tpl = document.getElementById('msg-template').value;
  const now = new Date();
  const hours = now.getHours() % 12 || 12;
  const mins = String(now.getMinutes()).padStart(2,'0');
  const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
  const timeStr = `${hours}:${mins} ${ampm}`;
  document.getElementById('msg-preview').textContent = tpl.replace('{time}', timeStr).replace('{multiplier}', '2.61');
}

function handleImageUpload(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async function(e) {
    document.getElementById('preview-img').src = e.target.result;
    document.getElementById('preview-area').style.display = 'block';
    document.getElementById('upload-area').style.display = 'none';
    await fetch('/api/upload_image', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({image: e.target.result})
    });
    showToast('Default image uploaded!');
  };
  reader.readAsDataURL(file);
}

async function removeImage() {
  await fetch('/api/remove_image', {method: 'POST'});
  document.getElementById('preview-area').style.display = 'none';
  document.getElementById('upload-area').style.display = 'block';
  showToast('Image removed');
}

async function startBot() {
  await fetch('/api/start', {method: 'POST'});
  showToast('Bot started!');
  updateStatus();
}

async function stopBot() {
  await fetch('/api/stop', {method: 'POST'});
  showToast('Bot stopped!');
  updateStatus();
}

async function updateStatus() {
  const res = await fetch('/api/status');
  const data = await res.json();
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  const btnStart = document.getElementById('btn-start');
  const btnStop = document.getElementById('btn-stop');
  
  if (data.running) {
    dot.classList.add('active');
    txt.textContent = 'LIVE 🟢';
    btnStart.disabled = true;
    btnStop.disabled = false;
  } else {
    dot.classList.remove('active');
    txt.textContent = 'OFFLINE';
    btnStart.disabled = false;
    btnStop.disabled = true;
  }
  
  document.getElementById('interval-val').value = data.interval;
  document.getElementById('delay-val').value = data.photo_delay || 50;
  document.getElementById('delay-mode').value = data.photo_delay_mode || 'seconds';
  document.getElementById('delay-display').textContent = data.photo_delay || 50;
  document.getElementById('delay-unit').textContent = data.photo_delay_mode || 'seconds';
  
  if (document.getElementById('msg-template').value === '') {
    document.getElementById('msg-template').value = data.message_template;
    updatePreview();
  }
  
  if (multList.length === 0 && data.multiplier_list && data.multiplier_list.length > 0) {
    multList = data.multiplier_list.map(m => ({value: m.value, hasImage: m.has_image}));
    renderMultList();
  }
  
  if (data.has_image) {
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('preview-area').style.display = 'block';
  }
}

document.getElementById('msg-template').addEventListener('input', updatePreview);
updateStatus();
setInterval(updateStatus, 3000);
</script>
</body>
</html>
'''

if __name__ == "__main__":
    print("=" * 50)
    print("  BOT ADMIN PANEL CHAL RAHA HAI!")
    print("  Browser mein kholo: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
