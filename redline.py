import sys
import os
import ctypes
import subprocess
import threading
import winreg
import shutil
import time
import json
import random
import socket  # เพิ่ม socket เพื่อเช็คพอร์ต

# ตรวจสอบ library
try:
    import webview
except ImportError:
    print("Error: Library 'pywebview' is missing.")
    print("Please run: pip install pywebview")
    input("Press Enter to exit...")
    sys.exit(1)

from flask import Flask, render_template_string, jsonify, request

# ==========================================
# CONFIG & APP SETUP
# ==========================================
app = Flask(__name__)
PORT = 54321

# API เชื่อมต่อ Window
class WindowAPI:
    def close_window(self):
        webview.windows[0].destroy()
    
    def minimize_window(self):
        webview.windows[0].minimize()
    
    def drag_window(self):
        pass # Handle by CSS -webkit-app-region: drag

# ตรวจสอบสิทธิ์ Admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ฟังก์ชันรอให้ Server พร้อมใช้งาน (แก้ปัญหาจอดำ)
def wait_for_server(port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except OSError:
            time.sleep(0.1)
    return False

# ==========================================
# FRONTEND (HTML / CSS / JS) - ULTIMATE RED THEME (FIXED)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BRX Redline</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

        :root {
            --bg-dark: #080808;
            --bg-panel: #111111;
            --primary: #ff003c;
            --primary-dim: rgba(255, 0, 60, 0.2);
            --primary-glow: rgba(255, 0, 60, 0.6);
            --text-main: #e0e0e0;
            --text-dim: #666;
            --grid-color: rgba(255, 255, 255, 0.03);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; user-select: none; }
        
        body {
            background-color: #080808; /* Hardcode fallback */
            background-color: var(--bg-dark);
            color: #e0e0e0;
            color: var(--text-main);
            font-family: 'Rajdhani', 'Segoe UI', sans-serif;
            height: 100vh;
            overflow: hidden;
            border: 1px solid #ff003c;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* --- Background Effects --- */
        .grid-bg {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: 
                linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 20px 20px;
            pointer-events: none;
            z-index: 0;
        }
        
        .scanline {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 5px;
            background: rgba(255, 0, 60, 0.05);
            animation: scan 8s linear infinite;
            z-index: 1;
            pointer-events: none;
        }

        /* --- Header / Title Bar --- */
        .header {
            height: 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 15px;
            background: linear-gradient(90deg, rgba(255,0,60,0.1), transparent 30%);
            border-bottom: 1px solid var(--primary-dim);
            z-index: 100;
            -webkit-app-region: drag;
            flex-shrink: 0;
        }

        .brand {
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: 18px;
            color: #fff;
            letter-spacing: 2px;
            text-shadow: 0 0 10px var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .brand span { color: var(--primary); }
        .brand-icon { width: 10px; height: 10px; background: var(--primary); transform: rotate(45deg); box-shadow: 0 0 8px var(--primary); }

        .controls {
            display: flex;
            gap: 5px;
            -webkit-app-region: no-drag;
        }

        .win-btn {
            background: transparent;
            border: none;
            color: var(--text-dim);
            width: 30px;
            height: 30px;
            font-size: 14px;
            cursor: pointer;
            transition: 0.2s;
            clip-path: polygon(20% 0, 100% 0, 100% 100%, 0% 100%, 0% 20%);
        }
        
        .win-btn:hover { background: var(--primary); color: #000; }

        /* --- Main Layout --- */
        .container {
            flex: 1;
            display: flex;
            padding: 15px;
            gap: 15px;
            z-index: 10;
            overflow: hidden;
        }

        /* --- Left: Dashboard --- */
        .dashboard {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
        }

        /* Engine Start Button */
        .engine-btn-wrapper {
            position: relative;
            width: 180px;
            height: 180px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .spin-ring {
            position: absolute;
            width: 100%; height: 100%;
            border: 2px dashed rgba(255, 0, 60, 0.2);
            border-radius: 50%;
            animation: spin 10s linear infinite;
        }
        
        .spin-ring::before {
            content: ''; position: absolute; top: -5px; left: 50%; width: 10px; height: 10px;
            background: #ff003c; box-shadow: 0 0 10px #ff003c; transform: translateX(-50%);
        }

        .main-btn {
            width: 140px; height: 140px;
            border-radius: 50%;
            background: radial-gradient(circle, #222, #000);
            border: 2px solid #ff003c;
            color: #fff;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(255, 0, 60, 0.1), inset 0 0 20px rgba(255, 0, 60, 0.1);
            transition: 0.3s;
            z-index: 20;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .main-btn:hover {
            box-shadow: 0 0 40px rgba(255, 0, 60, 0.6), inset 0 0 30px rgba(255, 0, 60, 0.6);
            text-shadow: 0 0 10px #fff;
            transform: scale(1.05);
        }
        
        .main-btn:active { transform: scale(0.95); }
        .main-btn:disabled { filter: grayscale(100%); opacity: 0.7; cursor: not-allowed; transform: scale(1); }
        
        .btn-sub { font-size: 10px; color: #ff003c; margin-top: 5px; font-weight: 400; font-family: 'Rajdhani', sans-serif; }

        /* --- Right: Terminal & Info --- */
        .sidebar {
            width: 220px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 0;
        }

        .panel {
            background: rgba(10, 10, 10, 0.8);
            border: 1px solid #333;
            padding: 10px;
            position: relative;
            flex-shrink: 0;
        }
        
        .panel::before {
            content: ''; position: absolute; top: 0; left: 0; width: 3px; height: 100%; background: #ff003c;
        }

        .panel.log-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 0;
            border: none;
            background: transparent;
            min-height: 0;
        }
        
        .panel.log-panel::before { display: none; }
        
        .panel-title {
            font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;
            display: flex; justify-content: space-between;
        }

        .sys-info {
            font-size: 12px; font-weight: bold; color: #fff; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;
        }

        /* Terminal Output */
        .terminal {
            flex: 1;
            background: #050505;
            border: 1px solid #333;
            border-left: 3px solid #ff003c;
            padding: 10px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            color: #ff003c;
            overflow-y: auto;
            position: relative;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
            min-height: 0;
        }
        
        .log-entry { margin-bottom: 4px; opacity: 0.9; line-height: 1.3; }
        .log-entry.success { color: #00ff9d; }
        .log-entry.process { color: #fff; }

        /* --- Footer --- */
        .footer {
            height: 30px;
            background: #0a0a0a;
            border-top: 1px solid #222;
            display: flex;
            align-items: center;
            padding: 0 15px;
            justify-content: space-between;
            font-size: 10px;
            color: #666;
            z-index: 100;
            flex-shrink: 0;
        }
        
        .progress-bar-container {
            width: 50%;
            height: 4px;
            background: #222;
            border-radius: 2px;
            overflow: hidden;
            display: none;
        }
        
        .progress-bar-fill {
            height: 100%; width: 0%;
            background: #ff003c;
            box-shadow: 0 0 10px #ff003c;
            transition: width 0.3s ease-out;
        }

        /* --- Intro Overlay --- */
        .intro {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: #000; z-index: 9999;
            display: flex; justify-content: center; align-items: center; flex-direction: column;
            animation: fadeOut 0.5s ease-in-out 2.5s forwards;
            pointer-events: none;
        }
        
        .intro.active { pointer-events: all; }

        .intro h1 {
            font-family: 'Orbitron', sans-serif; font-size: 40px; color: #fff;
            text-shadow: 4px 4px 0 #ff003c;
            animation: glitch 1s infinite alternate;
        }

        /* Animations */
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes scan { 0% { top: -10%; } 100% { top: 110%; } }
        @keyframes fadeOut { 0% { opacity: 1; } 99% { opacity: 0; } 100% { opacity: 0; visibility: hidden; } }
        @keyframes glitch { 0% { transform: translate(2px,0); } 100% { transform: translate(-2px,0); } }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
        ::-webkit-scrollbar-track { background: #000; }
    </style>
</head>
<body>

    <!-- INTRO -->
    <div class="intro active" id="introScreen">
        <h1>BRX SYSTEM</h1>
    </div>

    <div class="grid-bg"></div>
    <div class="scanline"></div>

    <!-- TITLE BAR -->
    <div class="header">
        <div class="brand">
            <div class="brand-icon"></div>
            BRX <span>REDLINE</span>
        </div>
        <div class="controls">
            <button class="win-btn" onclick="minWindow()">_</button>
            <button class="win-btn" onclick="closeWindow()">X</button>
        </div>
    </div>

    <!-- CONTENT -->
    <div class="container">
        <!-- LEFT: BUTTON -->
        <div class="dashboard">
            <div class="engine-btn-wrapper">
                <div class="spin-ring"></div>
                <button class="main-btn" id="boostBtn" onclick="runBoost()">
                    START
                    <div class="btn-sub">OPTIMIZATION</div>
                </button>
            </div>
        </div>

        <!-- RIGHT: INFO -->
        <div class="sidebar">
            <div class="panel">
                <div class="panel-title">TARGET SYSTEM <span>ON</span></div>
                <div class="sys-info" id="sys-model">INITIALIZING...</div>
            </div>
            
            <div class="panel log-panel">
                <div class="panel-title" style="padding: 0 5px;">PROCESS LOG</div>
                <div class="terminal" id="console">
                    <div class="log-entry">> System Ready...</div>
                    <div class="log-entry">> Awaiting Command...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- FOOTER -->
    <div class="footer">
        <div id="statusText">READY</div>
        <div class="progress-bar-container" id="progContainer">
            <div class="progress-bar-fill" id="progFill"></div>
        </div>
        <div>V 2.0.1</div>
    </div>

    <script>
        // ใช้ฟังก์ชันแบบมาตรฐาน (ES5) เพื่อกัน Error บน Browser เก่า
        setTimeout(function() {
            var intro = document.getElementById('introScreen');
            if(intro) intro.classList.remove('active');
        }, 3000);

        function closeWindow() { window.pywebview.api.close_window(); }
        function minWindow() { window.pywebview.api.minimize_window(); }

        var logBox = document.getElementById('console');
        var statusText = document.getElementById('statusText');
        var progContainer = document.getElementById('progContainer');
        var progFill = document.getElementById('progFill');

        function log(msg, type) {
            type = type || '';
            var div = document.createElement('div');
            div.className = 'log-entry ' + type;
            div.innerText = '> ' + msg;
            logBox.appendChild(div);
            requestAnimationFrame(function() {
                logBox.scrollTop = logBox.scrollHeight;
            });
        }

        var tasks = [
            { api: 'enable_ultimate_power', label: 'Unlocking Power Plan' },
            { api: 'disable_hibernation', label: 'Disabling Hibernation' },
            { api: 'disable_gamebar', label: 'Killing Game Bar' },
            { api: 'set_priority', label: 'Tweaking CPU Priority' },
            { api: 'optimize_tcp', label: 'Optimizing TCP/IP' },
            { api: 'flush_dns', label: 'Flushing DNS Cache' },
            { api: 'disable_net_throttling', label: 'Removing Throttling' },
            { api: 'clean_temp', label: 'Cleaning Junk Files' },
            { api: 'fix_mouse', label: 'Fixing Mouse Scaling' },
            { api: 'fast_keyboard', label: 'Reducing Input Lag' },
            { api: 'trim_memory', label: 'Trimming RAM' }
        ];

        async function runBoost() {
            var btn = document.getElementById('boostBtn');
            if(btn.disabled) return;
            btn.disabled = true;
            btn.style.opacity = '0.8';
            progContainer.style.display = 'block';
            
            log("INITIATING BOOST SEQUENCE...", "process");
            statusText.innerText = "OPTIMIZING...";
            statusText.style.color = "#fff";
            
            var count = 0;
            // ใช้ for loop แบบมาตรฐาน
            for(var i = 0; i < tasks.length; i++) {
                var task = tasks[i];
                log("Exec: " + task.label + "...");
                
                try {
                    await fetch('/api/' + task.api, { method: 'POST' });
                    log("[OK] " + task.label, "success");
                } catch(e) {
                    log("[ERR] " + task.label + " Failed");
                }

                // Visual delay
                await new Promise(function(r) { setTimeout(r, 250); });
                
                count++;
                progFill.style.width = (count / tasks.length * 100) + '%';
            }

            log("SEQUENCE COMPLETE.", "success");
            statusText.innerText = "SYSTEM OPTIMIZED";
            statusText.style.color = "#00ff9d";
            
            btn.innerHTML = "DONE";
            btn.style.borderColor = "#00ff9d";
            btn.style.boxShadow = "0 0 20px #00ff9d";
            btn.style.color = "#00ff9d";
            btn.style.background = "radial-gradient(circle, #112211, #000)";
            
            setTimeout(function() {
                log("System is now running at peak performance.");
            }, 1000);
        }

        // Init Info
        fetch('/api/sysinfo')
            .then(function(r) { return r.json(); })
            .then(function(d) {
                var info = d.info.toUpperCase();
                if(info.length > 25) info = info.substring(0, 22) + "...";
                document.getElementById('sys-model').innerText = info;
            })
            .catch(function() {
                 document.getElementById('sys-model').innerText = "UNKNOWN SYSTEM";
            });

    </script>
</body>
</html>
"""

# ==========================================
# BACKEND LOGIC
# ==========================================

def run_cmd(command):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "Success"
    except:
        return False, "Failed"

def set_registry(hkey, path, name, value, type_reg=winreg.REG_DWORD):
    try:
        key = winreg.CreateKey(hkey, path)
        winreg.SetValueEx(key, name, 0, type_reg, value)
        winreg.CloseKey(key)
        return True
    except:
        return False

# --- ROUTES ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/sysinfo')
def get_sysinfo():
    import platform
    info = f"{platform.system()} {platform.release()}"
    return jsonify({"info": info})

# --- TASKS ---

@app.route('/api/enable_ultimate_power', methods=['POST'])
def ultimate_power():
    run_cmd('powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61')
    run_cmd('powercfg /s 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')
    return jsonify({"success": True})

@app.route('/api/disable_hibernation', methods=['POST'])
def disable_hibernation():
    run_cmd("powercfg -h off")
    return jsonify({"success": True})

@app.route('/api/disable_gamebar', methods=['POST'])
def disable_gamebar():
    path = r"Software\Microsoft\Windows\CurrentVersion\GameDVR"
    set_registry(winreg.HKEY_CURRENT_USER, path, "AppCaptureEnabled", 0)
    path2 = r"System\GameConfigStore"
    set_registry(winreg.HKEY_CURRENT_USER, path2, "GameDVR_Enabled", 0)
    return jsonify({"success": True})

@app.route('/api/set_priority', methods=['POST'])
def set_priority():
    path = r"SYSTEM\CurrentControlSet\Control\PriorityControl"
    set_registry(winreg.HKEY_LOCAL_MACHINE, path, "Win32PrioritySeparation", 26)
    return jsonify({"success": True})

@app.route('/api/optimize_tcp', methods=['POST'])
def optimize_tcp():
    cmds = [
        "netsh int tcp set global autotuninglevel=normal",
        "netsh int tcp set global rss=enabled",
        "netsh int tcp set global rsc=disabled"
    ]
    for c in cmds:
        run_cmd(c)
    return jsonify({"success": True})

@app.route('/api/flush_dns', methods=['POST'])
def flush_dns():
    run_cmd("ipconfig /flushdns")
    run_cmd("ipconfig /release")
    run_cmd("ipconfig /renew")
    return jsonify({"success": True})

@app.route('/api/clean_temp', methods=['POST'])
def clean_temp():
    temp_dirs = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot'), 'Temp'),
        os.path.join(os.environ.get('SystemRoot'), 'Prefetch'),
    ]
    for d in temp_dirs:
        if d and os.path.exists(d):
            for filename in os.listdir(d):
                file_path = os.path.join(d, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except:
                    pass
    return jsonify({"success": True})

@app.route('/api/trim_memory', methods=['POST'])
def trim_memory():
    return jsonify({"success": True})

@app.route('/api/fix_mouse', methods=['POST'])
def fix_mouse():
    path = r"Control Panel\Mouse"
    set_registry(winreg.HKEY_CURRENT_USER, path, "MouseSpeed", "0", winreg.REG_SZ)
    set_registry(winreg.HKEY_CURRENT_USER, path, "MouseThreshold1", "0", winreg.REG_SZ)
    set_registry(winreg.HKEY_CURRENT_USER, path, "MouseThreshold2", "0", winreg.REG_SZ)
    return jsonify({"success": True})

@app.route('/api/fast_keyboard', methods=['POST'])
def fast_keyboard():
    path = r"Control Panel\Keyboard"
    set_registry(winreg.HKEY_CURRENT_USER, path, "KeyboardDelay", "0", winreg.REG_SZ)
    set_registry(winreg.HKEY_CURRENT_USER, path, "KeyboardSpeed", "31", winreg.REG_SZ)
    return jsonify({"success": True})

@app.route('/api/disable_net_throttling', methods=['POST'])
def disable_net_throttling():
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    set_registry(winreg.HKEY_LOCAL_MACHINE, path, "NetworkThrottlingIndex", 0xFFFFFFFF)
    return jsonify({"success": True})

# ==========================================
# APP ENTRY POINT
# ==========================================

def start_server():
    # threaded=True ช่วยให้รองรับการ request พร้อมกันและเสถียรขึ้น
    app.run(port=PORT, threaded=True, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Auto-Admin
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(f'"{arg}"' for arg in sys.argv), None, 1
            )
        except:
            pass
        sys.exit()

    # Flask Thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # ----------------------------------------------------
    # CRITICAL FIX: รอให้ Server พร้อมทำงานจริง ๆ ก่อนเปิดหน้าต่าง
    # ----------------------------------------------------
    if not wait_for_server(PORT):
        print("Error: Could not start local server.")
        sys.exit(1)

    # API instance
    api = WindowAPI()

    # Create Frameless Window (600x400)
    # background_color='#080808' ตรงกับสี CSS เพื่อไม่ให้เห็นแสงวาบสีขาว
    webview.create_window(
        title="BRX Redline", 
        url=f"http://127.0.0.1:{PORT}",
        width=600,
        height=400,
        resizable=False,
        frameless=True,
        js_api=api,
        background_color='#080808'
    )
    
    # เริ่มการทำงาน
    webview.start(debug=True) # Enable Debug (F12) เพื่อช่วยแก้ปัญหา
