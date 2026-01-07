import os
import io
import base64
import json
import time
import threading
import cv2
import numpy as np
import pyautogui
import urllib.request
import urllib.parse
from flask import Flask, render_template_string, jsonify, request, send_file
from PIL import Image

# พยายาม Import webview
try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False
    print("Suggestion: pip install pywebview to run as standalone app")

app = Flask(__name__)

# ==========================================
# CONFIG
# ==========================================
# ลิงก์ไฟล์ Key (GitHub Raw)
KEY_DB_URL = "https://raw.githubusercontent.com/meguyZ/key/refs/heads/main/key.txt"

SCAN_ROI = None 
SCREEN_SIZE = (1920, 1080)
IS_ACTIVATED = False 

# ไอคอน (Chip Gold)
ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAACXBIWXMAAAsTAAALEwEAmpwYAAAJUElEQVR4nO1baWxUVRb+7qv2qj2yCZCdIqsiWwAJsgi0gC0i0SIyCgyd0RGW/tAYdTRiTPiH0RgT/2jEmBiTjCB0ArbQDtA2QMImWwLZQ7YQsshakqWyVlX13r33jfdqS5VOW6lK6Zt4k1ep9913z/nOueece+6LCAH/x/8R8D8OQJ+D0Ocg9DkIfQ5Cn4PQ5yC0cADKy8s1Ho/H09PT4+no6DB1dnZOVVdXj+/q6popCII+PDy8dNeuXW133XWXe8yYMS15eXktBQUFzfPnz28pKirqLC0tbU1LS2s9d+5c17Zt27qKi4t7/q+AlJaW+mpqanJqamoy6+rqcnp6emYIgpCh1WqjDAbDRJvNNsVkMk0xm81TdTqdXqVS8bIsC4IgnBcE4bggCMc5jjvGcdwxURSPy7LcJgjCXo7j9maz2T0yMjKroqKi+b777msuLS3tCgqAEydOZJ8+fTq/rq4ur7Ozc67BYJhtNBpnR0REFDgcjmyHw5HtcDiyrVZrDofDkQ1wgiD0yLKsFwShV5KkXkmSegVBeCWO4w4LgnDAarXu0+l0++Li4mqLiopqS0pK2oMCoKqqKufMmTMLe3t7l4SFhS1wOp2LwsPDl4SFhS2wWq15FoulkOO4QlmWK4ODgw+IoqhXq9W90dHRR4xG436DwXCguLjYHRQAR44cybxy5crKzs7OVeHh4avg/PDAwMAlFoul0GKxFIaFhS2xWq2LnU5noU6n0ymKUiVJ0u6IiIgDGRkZle+++25rUAAcPHgw89KlS6u7urpuDw8PXx0REbGqvb19TXt7+xqLxbIE/tBotGmaN29eS3Fxcee9997rCQqAgwcPZl68eHF1d3f3mra2trXw/urVq9e2t7evaWtrW9Pe3r6mtrZ2bVxcXF1BQUHrgw8+2H7LLbe4gwLg4MGDmefPn1/d09OzJiIiopTjuHJBED7u7e39uLe39+Pe3t6Pe3t7P7ZarQcsFsseTdN7NBrNHpPJtGfixIltixYtamttbe31KwBlZWW+M2fOrO7p6Vnb1ta21mKxLFUUpVqSpA97e3s/6u3t/bC3t/dDnuf3iKLYI4rivYIg7BEE4WNRFO8VRfFjURT36HS63bGxsZWTJk1qmzNnTntbW1uvXwA0Nzfn9/T0rO3o6FgXERFRqihKjSRJtfA63E9g3iOK4u2iKG7jef42URRvE0Vxi8FguC0uLq5y8uTJrXPmzOnwGwBnzpzJ7+zsXNfe3r4uIiKiTFGUWkmS/sHz/G1wXRTFm3menwX3E5hbg8FwOzY2tmratGmtc+fO7fQLgObm5vyOjo517e3t6yIiIsoURfmXJEn18DrcT2Bms9lsg8FwOyYmpnLatGmtc+fO7fQLgObm5oK2trb1HR0d6yMiIsoVRfmXJEn1PM/P4nmeR0QYDIY5BoPh9piYmKpp06a1zZ07t9MvAJqbmwva2trWd3R03B4REbGcoqh/SZI0C15HROA4zhwVFVUZExNTNW3atLa5c+d2+gVAc3NzcXt7+/qOjo71ERERyymK+pckSbPhdeQCSZLag8Fwd0xMTNWMGTNa586d2+kXAM3NzcXt7e3rOzs710dERJSr1eoGjuPMkiTNhNcREQRBMGs0mrsjIiKqZsyY0TZv3ryOtrY2v94BR48ezbxw4cLqrq6uNeHh4aUcxy2UJOkfgiCYJUm6Aa8jImiaNms0mrs1Gs3dGRkZlQsXLmx78MEH24MC4PDhw5mXLl1a3dXVtTwiImKpxWJZJghCnSRJs+B1GIzjuFmj0dwdHh5eNXPmzLaFCxe2PfTQQ+1BAXDo0KHMK1eurO7q6lodFha2zGazLZUkqU6SpNnwOgxWqVRmjUZzd3h4eNXMmTPbFi5c2Pbwwz4DUFZW5quqqsqpqqrKqa6uzmlubp5hMBhmGwyG2QaDYbZOp9NHRUUdk2W5juf52o6Ojj/KsnxcFMWjPM8f43n+GM/zR3meP6bVak/ExMRUzJw5s23hwoVtDz/8cHtQABw+fDhz3759K7u6ulbHxMQsttlsSyVJ+ofPAGg0mnujI0K7w8PDqxYuXNi2aNGi9qAAOHz4cObFixdXd3V1rYmIiCjVarULJElq8BkAjuPMGo3m7vDwsKoFCxa0Lly4sD0oAA4fPpx58eLF1V1dXeXh4eHLdDrdQo7jGp1OZzYIgjk8PNwcHh5u1mg0Zp1OZ9ZoNGaDwWAODw83R0VFWTQajVWtVltVKpVVkqRyURTLJUn6h9Vq3W8wGO6OioqqmjFjRtu8efM62tra/HoHlJWV+aqqqnKqq6tzqqqqcpqbm2fo9fqZBoNhtk6nm63T6XRxcXF1kiQd4Xn+Q3gdwYhOp7szIiKiKiaGqoyJiamKiYmp0uv1M3U6nU6tVveKonhSkiRreHj4AZ1Od2dUVFTVrFmz2ubNm9fR1tbm1ztg//79mZcvX17d1dW1JiIiolSv1y+QJKnR4XBkOxwOCxHBbrdb7Ha7xW63WxwOh8XhcFgcDofF4XBYHA6HxeFwWBwOh8XhcFgcDofF4XBYHA6HxeFwWBwOh8XhcFgcDofF4XBYHA6HxeFwWBwOh8XhcFgcDofF4XBYHA6HxeFwWBwOh8XhcFgcDofF4XBYHA6HxeFwWOx2u8Vut1vsdrtFkiSLy+WyuFwui8vlsrhcLqvL5bK63W6r2+22ut1uq9vttnZ3d/9Bp9PdmZiYWDV9+vS2uXPndvoVgP3790+rqKgoP3PmjG9gYOAKl8u11Ol0LnE6nUscDscSh8OxxOFwLHE4HEscDscSh8OxxOFwLHE4HEscDscSh8OxxOFwLHE4HEscDscSh8OxxOFwLHE4HEscDscSh8OxxOFwLHE4HEscDscSh8OxxOFwLHE4HEscDscSh8OxxOFwLHE4HEscDscSp9O5xOl0LnE6nUscDscSl8u1xO12L3E4HEs4jisMCwvbZDAY7o6Nja2aNm1a25w5czr+4wD8H4Q+B6HPQehzEPochD4Hoc9B6HMQ+hyEPgehz0HocxD6HIQ+B6HPQehzEPochD4Hoc9B6HMQ+hyEPgehz0HocxD6HIQ+B6HPQehzEPochP4L9tX/AcJvYq8AAAAASUVORK5CYII="

def create_icon_file():
    try:
        if not os.path.exists("app_icon.png"):
            with open("app_icon.png", "wb") as f:
                f.write(base64.b64decode(ICON_BASE64))
        return os.path.abspath("app_icon.png")
    except Exception as e:
        return None

ICON_PATH = create_icon_file()

# ==========================================
# WEB INTERFACE
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>BACCARAT VISION AI - V.11 (Online Key)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@200;300;400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: { sans: ['Kanit', 'sans-serif'] },
                    colors: { neon: "#00f3ff" },
                    animation: { 'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite' }
                }
            }
        }
    </script>
    <style>
        ::-webkit-scrollbar { width: 0px; background: transparent; }
        body { -webkit-user-select: none; user-select: none; overflow-x: hidden; background-color: #020617; }
        .bg-cyber {
            background-image: radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.15) 0%, transparent 50%),
                              radial-gradient(circle at 0% 100%, rgba(59, 130, 246, 0.15) 0%, transparent 50%);
            background-attachment: fixed;
        }
        .glass-card {
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        }
        .glow-box-p { box-shadow: 0 0 25px rgba(59, 130, 246, 0.6); }
        .glow-box-b { box-shadow: 0 0 25px rgba(239, 68, 68, 0.6); }
        .btn-press:active { transform: scale(0.96); }
        #selection-modal { display: none; }
        canvas { cursor: crosshair; }
        #login-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: #020617; z-index: 100;
            display: flex; flex-direction: column; justify-content: center; items-center;
            transition: opacity 0.5s ease;
        }
    </style>
</head>
<body class="text-slate-100 min-h-screen bg-cyber">

    <!-- LOGIN SCREEN (SIMPLE) -->
    <div id="login-overlay">
        <div class="glass-card p-8 rounded-3xl w-80 text-center animate__animated animate__fadeInDown shadow-2xl border border-indigo-500/30 relative overflow-hidden">
            <div class="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 bg-indigo-500/30 blur-[50px] rounded-full pointer-events-none"></div>

            <div class="w-20 h-20 bg-gradient-to-tr from-yellow-400 to-amber-600 rounded-2xl mx-auto mb-6 flex items-center justify-center shadow-lg shadow-amber-500/20 relative z-10">
                <i class="fa-solid fa-key text-4xl text-white"></i>
            </div>
            
            <h2 class="text-2xl font-black text-white mb-1 relative z-10">VISION AI</h2>
            <p class="text-[10px] text-slate-400 mb-6 relative z-10">ONLINE ACTIVATION</p>
            
            <div class="relative z-10 space-y-3">
                <input type="password" id="license-key" placeholder="Enter License Key..." 
                    class="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3 text-center text-white placeholder-slate-600 focus:outline-none focus:border-amber-500 transition-colors tracking-widest text-sm font-bold">
                
                <button onclick="verifyKey()" id="btn-login" class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold py-3 rounded-xl shadow-lg transition-all btn-press">
                    <i class="fa-solid fa-unlock mr-2"></i> UNLOCK
                </button>
            </div>
            
            <p id="login-msg" class="text-[10px] text-red-400 mt-4 h-4"></p>
        </div>
        <div class="absolute bottom-5 text-[10px] text-slate-600">Secure Access System</div>
    </div>

    <!-- MAIN APP -->
    <div style="-webkit-app-region: drag; height: 30px; position: absolute; top:0; left:0; right:0; z-index: 50;"></div>

    <nav class="fixed top-0 w-full z-40 glass-card border-b-0 px-5 py-4 flex justify-between items-center rounded-b-3xl">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-400 to-yellow-600 flex items-center justify-center shadow-lg animate-pulse-slow">
                <i class="fa-solid fa-layer-group text-white"></i>
            </div>
            <div>
                <h1 class="text-xl font-black tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-amber-200 to-yellow-500">VISION AI</h1>
                <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <p class="text-[10px] text-emerald-400 font-bold tracking-widest uppercase">VIP ACTIVE</p>
                </div>
            </div>
        </div>
        <button onclick="window.location.reload()" class="w-10 h-10 rounded-full bg-slate-800/50 hover:bg-slate-700 flex items-center justify-center transition-all border border-white/10">
            <i class="fa-solid fa-power-off text-red-400"></i>
        </button>
    </nav>

    <main class="pt-28 pb-32 px-5 max-w-md mx-auto flex flex-col gap-5 h-full">
        <!-- Status -->
        <div id="status-card" class="glass-card rounded-2xl p-3 flex justify-between items-center animate__animated animate__fadeInDown hover:bg-slate-800/40 transition-colors">
            <div class="flex items-center gap-3">
                <div id="status-dot" class="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,1)]"></div>
                <span id="status-text" class="text-xs font-bold text-slate-400 tracking-wide">NO TARGET</span>
            </div>
            <div class="text-[10px] text-slate-600 font-mono">ID: <span id="session-id">LOADING...</span></div>
        </div>

        <!-- Setup Grid -->
        <div class="grid grid-cols-2 gap-3 animate__animated animate__fadeInUp">
            <button onclick="autoDetectROI()" id="btn-auto-lock" class="group relative overflow-hidden rounded-2xl bg-slate-800 border border-slate-700/50 p-4 shadow-lg btn-press transition-all hover:border-indigo-500/50">
                <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative flex flex-col items-center justify-center gap-2">
                    <i class="fa-solid fa-wand-magic-sparkles text-2xl text-indigo-400 group-hover:scale-110 transition-transform"></i>
                    <span id="auto-lock-text" class="text-xs font-bold text-slate-300">AUTO LOCK</span>
                </div>
            </button>
            <button onclick="openSelectionModal()" id="btn-manual-roi" class="group rounded-2xl bg-slate-800 border border-slate-700/50 p-4 shadow-lg btn-press transition-all hover:border-emerald-500/50">
                <div class="flex flex-col items-center justify-center gap-2">
                    <i class="fa-solid fa-crop-simple text-2xl text-slate-500 group-hover:text-emerald-400 transition-colors"></i>
                    <span class="text-xs font-bold text-slate-300">MANUAL</span>
                </div>
            </button>
        </div>

        <!-- Prediction Box -->
        <div class="glass-card rounded-[30px] p-6 relative overflow-hidden animate__animated animate__zoomIn shadow-2xl flex-grow flex flex-col justify-center min-h-[260px]">
            <div id="prediction-box" class="absolute inset-0 bg-slate-900/40 transition-all duration-500"></div>
            <div class="relative z-10 flex flex-col items-center justify-center h-full gap-4">
                <span class="text-[9px] font-black tracking-[0.4em] text-slate-600 uppercase">Recommendation</span>
                <h2 id="pred-side" class="text-8xl font-black text-slate-800 tracking-tighter transition-all duration-300 scale-100 select-none" style="-webkit-text-stroke: 1px rgba(255,255,255,0.05);">WAIT</h2>
                <div class="w-full space-y-1 mt-2">
                    <div class="flex justify-between text-[10px] font-bold px-2 uppercase tracking-wider">
                        <span id="text-p" class="text-blue-500/80">Player 0%</span>
                        <span id="text-b" class="text-red-500/80">Banker 0%</span>
                    </div>
                    <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden flex w-full">
                        <div id="bar-p" class="h-full bg-blue-500 shadow-[0_0_10px_#3b82f6] transition-all duration-500 w-1/2"></div>
                        <div id="bar-b" class="h-full bg-red-500 shadow-[0_0_10px_#ef4444] transition-all duration-500 w-1/2"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scan Controls -->
        <div class="fixed bottom-6 left-5 right-5 z-30 grid grid-cols-[1fr_2fr] gap-3">
            <button onclick="analyzeScreen()" id="btn-scan" class="glass-card bg-slate-800 hover:bg-slate-700 text-white h-16 rounded-2xl font-bold shadow-lg btn-press flex flex-col justify-center items-center gap-1 border-b-4 border-slate-950">
                <i class="fa-solid fa-camera text-xl"></i>
                <span class="text-[10px]">SCAN</span>
            </button>
            <button onclick="toggleAuto()" id="btn-auto" class="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white h-16 rounded-2xl font-bold shadow-lg shadow-cyan-500/20 btn-press border-b-4 border-cyan-800 flex justify-center items-center gap-3 relative overflow-hidden group">
                <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                <i class="fa-solid fa-robot text-2xl animate-bounce"></i>
                <div class="flex flex-col items-start leading-tight">
                    <span class="text-sm">START AUTO</span>
                    <span class="text-[10px] opacity-70 font-normal">AI MODE</span>
                </div>
            </button>
        </div>
    </main>

    <!-- Selection Modal -->
    <div id="selection-modal" class="fixed inset-0 z-[60] bg-black/95 flex flex-col items-center justify-center animate__animated animate__fadeIn">
        <h2 class="text-2xl font-bold text-white mb-2">🎯 ลากครอบพื้นที่</h2>
        <div id="canvas-wrapper" class="relative border-2 border-emerald-500 rounded-lg overflow-hidden touch-none">
            <canvas id="screen-canvas"></canvas>
        </div>
        <div class="flex gap-4 mt-8 w-full max-w-sm px-6">
            <button onclick="closeModal()" class="flex-1 py-4 rounded-xl bg-slate-800 text-slate-300 font-bold">ยกเลิก</button>
            <button onclick="confirmSelection()" class="flex-1 py-4 rounded-xl bg-emerald-600 text-white font-bold shadow-lg shadow-emerald-500/40">บันทึก ✅</button>
        </div>
    </div>
    <audio id="sound-alert" src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"></audio>

    <script>
        let autoInterval = null;
        let lastPrediction = "WAIT";

        // --- Verify Key with GitHub Text File ---
        async function verifyKey() {
            const keyInput = document.getElementById('license-key');
            const msg = document.getElementById('login-msg');
            const btn = document.getElementById('btn-login');
            // Trim whitespace, do NOT force uppercase as per user example keys
            const key = keyInput.value.trim();
            if(!key) return;

            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> CHECKING...';
            
            try {
                const res = await fetch('/verify_key', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key: key})
                });
                const data = await res.json();
                
                if (data.status === 'valid') {
                    msg.className = "text-[10px] text-emerald-400 mt-4 h-4";
                    msg.innerText = "ACCESS GRANTED";
                    setTimeout(() => {
                        const overlay = document.getElementById('login-overlay');
                        overlay.style.opacity = '0';
                        setTimeout(() => overlay.style.display = 'none', 500);
                    }, 500);
                } else {
                    msg.innerText = data.msg || "INVALID KEY";
                    btn.innerHTML = '<i class="fa-solid fa-unlock mr-2"></i> UNLOCK';
                    keyInput.classList.add('border-red-500');
                    setTimeout(() => keyInput.classList.remove('border-red-500'), 1000);
                }
            } catch (e) {
                msg.innerText = "NETWORK ERROR";
                btn.innerHTML = '<i class="fa-solid fa-exclamation-triangle mr-2"></i> ERROR';
            }
        }

        // --- Rest of the app logic ---
        document.getElementById('session-id').innerText = Math.random().toString(36).substr(2, 6).toUpperCase();
        async function autoDetectROI() {
            const btn = document.getElementById('btn-auto-lock');
            const txt = document.getElementById('auto-lock-text');
            const originalHTML = txt.innerHTML;
            btn.classList.add('border-indigo-500'); txt.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> SCANNING...';
            try {
                await new Promise(r => setTimeout(r, 1500));
                const res = await fetch('/auto_lock_roi');
                const data = await res.json();
                if (data.status === 'ok') { setStatus(true); alert("✅ AI FOUND TARGET!"); }
                else if (data.status === 'locked') { window.location.reload(); }
                else { alert("❌ TARGET NOT FOUND"); }
            } catch (e) { alert("Error: " + e); }
            finally { btn.classList.remove('border-indigo-500'); txt.innerHTML = originalHTML; }
        }

        const modal = document.getElementById('selection-modal');
        const canvas = document.getElementById('screen-canvas');
        const ctx = canvas.getContext('2d');
        let imgObj = new Image(); let isDrawing = false; let startX, startY, endX, endY;

        async function openSelectionModal() {
            const btn = document.getElementById('btn-manual-roi');
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            try {
                const res = await fetch('/capture_for_selection');
                const data = await res.json();
                if(data.status === 'locked') { window.location.reload(); return; }
                imgObj.onload = function() {
                    const margin = 40; const maxWidth = window.innerWidth - margin; const maxHeight = window.innerHeight * 0.7;
                    canvas.width = imgObj.width; canvas.height = imgObj.height;
                    canvas.style.width = '100%'; canvas.style.height = 'auto';
                    canvas.style.maxWidth = maxWidth + 'px'; canvas.style.maxHeight = maxHeight + 'px';
                    ctx.drawImage(imgObj, 0, 0); modal.style.display = 'flex';
                };
                imgObj.src = 'data:image/jpeg;base64,' + data.image;
            } catch (e) { alert("Error: " + e); }
            finally { btn.innerHTML = '<div class="flex flex-col items-center justify-center gap-2"><i class="fa-solid fa-crop-simple text-2xl text-slate-500 group-hover:text-emerald-400 transition-colors"></i><span class="text-xs font-bold text-slate-300">MANUAL</span></div>'; }
        }
        function closeModal() { modal.style.display = 'none'; }
        function getPos(e) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width; const scaleY = canvas.height / rect.height;
            const clientX = e.clientX || e.touches[0].clientX; const clientY = e.clientY || e.touches[0].clientY;
            return { x: (clientX - rect.left) * scaleX, y: (clientY - rect.top) * scaleY };
        }
        ['mousedown', 'touchstart'].forEach(evt => canvas.addEventListener(evt, e => { const pos = getPos(e); startX = pos.x; startY = pos.y; isDrawing = true; }));
        ['mousemove', 'touchmove'].forEach(evt => canvas.addEventListener(evt, e => {
            if (!isDrawing) return; e.preventDefault();
            const pos = getPos(e); endX = pos.x; endY = pos.y;
            ctx.drawImage(imgObj, 0, 0);
            ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'; ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.clearRect(startX, startY, endX - startX, endY - startY);
            ctx.drawImage(imgObj, startX, startY, endX - startX, endY - startY, startX, startY, endX - startX, endY - startY);
            ctx.strokeStyle = '#00f3ff'; ctx.lineWidth = 5; ctx.strokeRect(startX, startY, endX - startX, endY - startY);
        }));
        ['mouseup', 'touchend'].forEach(evt => canvas.addEventListener(evt, () => isDrawing = false));

        async function confirmSelection() {
            if (startX === undefined) return;
            let x = Math.min(startX, endX), y = Math.min(startY, endY), w = Math.abs(endX - startX), h = Math.abs(endY - startY);
            const res = await fetch('/set_roi', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({x, y, w, h}) });
            const data = await res.json();
            if (data.status === 'ok') { closeModal(); setStatus(true); }
        }

        function setStatus(locked) {
            const dot = document.getElementById('status-dot'); const text = document.getElementById('status-text');
            if (locked) { dot.className = "w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981] animate-pulse"; text.innerText = "AREA LOCKED"; text.className = "text-xs font-bold text-emerald-400 tracking-wide"; }
            else { dot.className = "w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_#ef4444]"; text.innerText = "NO TARGET"; text.className = "text-xs font-bold text-slate-500 tracking-wide"; }
        }
        async function analyzeScreen() {
            try {
                const response = await fetch('/analyze');
                const data = await response.json();
                if(data.status === 'locked') { return; } 
                if (data.recommendation !== 'WAIT' && data.recommendation !== lastPrediction) { document.getElementById('sound-alert').play().catch(()=>{}); }
                lastPrediction = data.recommendation; updateUI(data);
            } catch (error) { console.error(error); } 
        }
        function updateUI(data) {
            const predSide = document.getElementById('pred-side'); const box = document.getElementById('prediction-box');
            const barP = document.getElementById('bar-p'); const barB = document.getElementById('bar-b');
            const textP = document.getElementById('text-p'); const textB = document.getElementById('text-b');
            const total = data.p_score + data.b_score; let p_percent = 50; if (total > 0) p_percent = Math.round((data.p_score / total) * 100);
            barP.style.width = p_percent + '%'; barB.style.width = (100 - p_percent) + '%';
            textP.innerText = `Player ${p_percent}%`; textB.innerText = `Banker ${100 - p_percent}%`;
            predSide.className = "text-8xl font-black text-slate-700 tracking-tighter transition-all duration-300 scale-100";
            box.className = "absolute inset-0 bg-slate-900/40 transition-all duration-500";
            if (data.recommendation === 'P') {
                predSide.innerText = 'PLAYER'; predSide.className = "text-6xl font-black text-blue-500 tracking-tighter transition-all duration-300 scale-110 drop-shadow-[0_0_30px_rgba(59,130,246,0.8)]";
                box.className = "absolute inset-0 bg-blue-900/20 glow-box-p transition-all duration-500";
            } else if (data.recommendation === 'B') {
                predSide.innerText = 'BANKER'; predSide.className = "text-6xl font-black text-red-500 tracking-tighter transition-all duration-300 scale-110 drop-shadow-[0_0_30px_rgba(239,68,68,0.8)]";
                box.className = "absolute inset-0 bg-red-900/20 glow-box-b transition-all duration-500";
            } else { predSide.innerText = 'WAIT'; }
        }
        function toggleAuto() {
            const btn = document.getElementById('btn-auto');
            if (autoInterval) {
                clearInterval(autoInterval); autoInterval = null;
                btn.innerHTML = '<i class="fa-solid fa-robot text-2xl animate-bounce"></i><div class="flex flex-col items-start leading-tight"><span class="text-sm">START AUTO</span><span class="text-[10px] opacity-70 font-normal">AI MODE</span></div>';
                btn.classList.remove('from-red-600', 'to-orange-600', 'animate-pulse'); btn.classList.add('from-blue-600', 'to-cyan-600');
            } else {
                analyzeScreen(); autoInterval = setInterval(analyzeScreen, 1000);
                btn.innerHTML = '<i class="fa-solid fa-pause text-2xl"></i><div class="flex flex-col items-start leading-tight"><span class="text-sm">STOP</span><span class="text-[10px] opacity-70 font-normal">RUNNING...</span></div>';
                btn.classList.remove('from-blue-600', 'to-cyan-600'); btn.classList.add('from-red-600', 'to-orange-600', 'animate-pulse');
            }
        }
    </script>
</body>
"""

# ==========================================
# BACKEND ROUTING
# ==========================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/icon.png')
def get_icon():
    if os.path.exists(ICON_PATH):
        return send_file(ICON_PATH, mimetype='image/png')
    return "No Icon", 404

@app.route('/verify_key', methods=['POST'])
def verify_key():
    global IS_ACTIVATED
    data = request.json
    user_key = data.get('key', '').strip()
    
    if not user_key:
         return jsonify({"status": "invalid", "msg": "Empty Key"})

    try:
        # Fetch keys from GitHub
        with urllib.request.urlopen(KEY_DB_URL) as response:
            raw_data = response.read().decode('utf-8')
            
        # Parse keys (split by newlines, strip spaces)
        valid_keys = [k.strip() for k in raw_data.splitlines() if k.strip()]
        
        if user_key in valid_keys:
            IS_ACTIVATED = True
            return jsonify({"status": "valid"})
        else:
            return jsonify({"status": "invalid", "msg": "Key Not Found"})
            
    except Exception as e:
        print(f"Network Error: {e}")
        return jsonify({"status": "invalid", "msg": "Network Error"})

@app.route('/capture_for_selection')
def capture_for_selection():
    if not IS_ACTIVATED: return jsonify({"status": "locked"})
    try:
        screenshot = pyautogui.screenshot()
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        base64_img = base64.b64encode(buffer).decode('utf-8')
        return jsonify({"image": base64_img, "width": frame.shape[1], "height": frame.shape[0]})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/set_roi', methods=['POST'])
def set_roi():
    if not IS_ACTIVATED: return jsonify({"status": "locked"})
    global SCAN_ROI
    data = request.json
    try:
        x, y, w, h = int(data['x']), int(data['y']), int(data['w']), int(data['h'])
        if w > 0 and h > 0:
            SCAN_ROI = (x, y, w, h)
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "msg": "Invalid area"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/auto_lock_roi')
def auto_lock_roi():
    if not IS_ACTIVATED: return jsonify({"status": "locked"})
    global SCAN_ROI
    try:
        screenshot = pyautogui.screenshot()
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([100, 120, 50]), np.array([140, 255, 255])) + \
               cv2.inRange(hsv, np.array([0, 120, 50]), np.array([10, 255, 255])) + \
               cv2.inRange(hsv, np.array([170, 120, 50]), np.array([180, 255, 255]))
        kernel = np.ones((15, 15), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_rect = None; max_area = 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area > 5000 and w > 100 and h > 50:
                if area > max_area:
                    max_area = area; best_rect = (x, y, w, h)
        if best_rect:
            SCAN_ROI = best_rect
            return jsonify({"status": "ok", "roi": best_rect})
        return jsonify({"status": "error", "msg": "Not found"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/analyze')
def analyze():
    if not IS_ACTIVATED: return jsonify({"status": "locked"})
    global SCAN_ROI
    try:
        if SCAN_ROI:
            x, y, w, h = SCAN_ROI
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
        else:
            screenshot = pyautogui.screenshot()
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_blue = cv2.inRange(hsv, np.array([100, 120, 50]), np.array([140, 255, 255]))
        mask_red = cv2.inRange(hsv, np.array([0, 120, 50]), np.array([10, 255, 255])) + \
                   cv2.inRange(hsv, np.array([170, 120, 50]), np.array([180, 255, 255]))
        blue_pixels = cv2.countNonZero(mask_blue)
        red_pixels = cv2.countNonZero(mask_red)
        total = blue_pixels + red_pixels
        recommendation = "WAIT"
        if total > 50: 
            diff_ratio = abs(blue_pixels - red_pixels) / total
            if diff_ratio > 0.10: 
                recommendation = "P" if blue_pixels > red_pixels else "B"
        return jsonify({"p_score": int(blue_pixels), "b_score": int(red_pixels), "recommendation": recommendation})
    except Exception as e:
        return jsonify({"error": str(e), "recommendation": "WAIT"})

def start_server():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    print("--- BACCARAT CLIENT ---")
    if HAS_WEBVIEW:
        t = threading.Thread(target=start_server)
        t.daemon = True
        t.start()
        time.sleep(1)
        webview.create_window("Vision AI Pro", "http://127.0.0.1:5000", width=420, height=800, resizable=True)
        webview.start()
    else:
        app.run(debug=True, port=5000)
