import os
import signal
import subprocess
import time
from threading import Lock

import psutil
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# =========================================
# CONFIG
# =========================================

LLAMA_SERVER_PATH = "/home/pi/llama.cpp/build/bin/llama-server"

MODELS = {
    "tinyllama": {
        "path": "/home/pi/llama.cpp/models/tinyllama.gguf",
        "ctx": 192,
        "temp": 0.1,
        "top_p": 0.8,
        "threads": 3,
    },

    "qwen-coder": {
        "path": "/home/pi/llama.cpp/models/qwen-coder.gguf",
        "ctx": 192,
        "temp": 0.1,
        "top_p": 0.8,
        "threads": 3,
    },

    "dolphin": {
        "path": "/home/pi/llama.cpp/models/dolphin.gguf",
        "ctx": 128,
        "temp": 0.7,
        "top_p": 0.95,
        "threads": 3,
    },
}

LLAMA_PORT = 8080
API_PORT = 5000

current_model = None
llama_process = None
lock = Lock()

# =========================================
# HELPERS
# =========================================

def kill_server():
    global llama_process

    if llama_process:
        try:
            llama_process.terminate()
            llama_process.wait(timeout=10)
        except:
            try:
                llama_process.kill()
            except:
                pass

    # cleanup stray processes
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = " ".join(proc.info["cmdline"])

            if "llama-server" in cmdline:
                os.kill(proc.info["pid"], signal.SIGKILL)

        except:
            pass

    llama_process = None
    time.sleep(2)


def wait_for_server():
    for _ in range(30):
        try:
            r = requests.get(
                f"http://127.0.0.1:{LLAMA_PORT}/health",
                timeout=2
            )

            if r.status_code == 200:
                return True

        except:
            pass

        time.sleep(1)

    return False


def start_model(model_name):
    global current_model
    global llama_process

    if model_name not in MODELS:
        return False, "model not found"

    config = MODELS[model_name]

    kill_server()

    cmd = [
        LLAMA_SERVER_PATH,

        "-m", config["path"],
        "-c", str(config["ctx"]),
        "-t", str(config["threads"]),

        "--host", "0.0.0.0",
        "--port", str(LLAMA_PORT),

        "--temp", str(config["temp"]),
        "--top-p", str(config["top_p"]),

        "-ngl", "0"
    ]

    llama_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ok = wait_for_server()

    if not ok:
        return False, "server failed to start"

    current_model = model_name

    return True, "started"


# =========================================
# API
# =========================================

@app.route("/")
def home():
    return jsonify({
        "service": "Pi Edge LLM Orchestrator",
        "current_model": current_model,
    })


@app.route("/models")
def models():
    return jsonify({
        "models": list(MODELS.keys())
    })


@app.route("/load_model", methods=["POST"])
def load_model():

    data = request.json

    if not data or "model" not in data:
        return jsonify({
            "error": "missing model"
        }), 400

    model_name = data["model"]

    with lock:
        ok, msg = start_model(model_name)

    if not ok:
        return jsonify({
            "success": False,
            "message": msg
        }), 500

    return jsonify({
        "success": True,
        "current_model": current_model
    })


@app.route("/status")
def status():

    ram = psutil.virtual_memory()

    temp = "unknown"

    try:
        temp = subprocess.check_output(
            ["vcgencmd", "measure_temp"]
        ).decode().strip()

    except:
        pass

    return jsonify({
        "current_model": current_model,
        "ram_percent": ram.percent,
        "ram_used_mb": round(ram.used / 1024 / 1024),
        "cpu_percent": psutil.cpu_percent(),
        "temp": temp,
    })


@app.route("/chat", methods=["POST"])
def chat():

    if not current_model:
        return jsonify({
            "error": "no model loaded"
        }), 400

    try:
        payload = request.json

        r = requests.post(
            f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions",
            json=payload,
            timeout=300,
        )

        return jsonify(r.json())

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/unload")
def unload():

    global current_model

    with lock:
        kill_server()
        current_model = None

    return jsonify({
        "success": True
    })


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":

    print("\nPi Edge LLM Orchestrator")
    print("----------------------------")

    print("Available models:")

    for m in MODELS:
        print("-", m)

    print(f"\nAPI running on port {API_PORT}\n")

    app.run(
        host="0.0.0.0",
        port=API_PORT,
        threaded=False,
    )
