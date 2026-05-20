# Raspberry Pi Edge LLM Orchestrator

A lightweight edge AI orchestration server for dynamically serving local LLMs on constrained Raspberry Pi hardware using llama.cpp.

GitHub Repository:

[edge_llm_manager GitHub Repository](https://github.com/write2taran/edge_llm_manager?utm_source=chatgpt.com)

Main Orchestrator File:

[edge_llm_manager.py](https://github.com/write2taran/edge_llm_manager/blob/main/edge_llm_manager.py?utm_source=chatgpt.com)

---

# Overview

This project turns a Raspberry Pi into a lightweight local AI inference server capable of:

* running fully offline
* serving LLMs over LAN
* dynamically switching models
* exposing REST APIs
* supporting multiple devices
* operating under severe RAM constraints

The system was specifically designed for constrained ARM hardware like the Raspberry Pi 3B+.

Instead of permanently loading multiple models into memory, the orchestrator dynamically unloads and reloads models depending on workload type.

This approach is significantly more practical on low-memory hardware.

---

# Features

* Fully local/private inference
* Dynamic model switching
* REST API serving
* Multi-device LAN access
* Lightweight orchestration layer
* llama.cpp backend
* Raspberry Pi optimized
* Headless SSH workflow compatible
* Low-memory deployment strategy
* Thermal/RAM monitoring endpoints

---

# Hardware Used

* Raspberry Pi 3B+
* 1GB RAM
* Raspberry Pi OS Lite
* ARM64
* Headless SSH setup
* zram swap enabled
* Tuned swappiness

---

# Architecture

```text
Laptop / Phone / Desktop
            ↓
Edge LLM Orchestrator API
            ↓
Dynamic Model Manager
            ↓
llama.cpp server
            ↓
Selected GGUF Model
```

---

# Why This Project Exists

Most Raspberry Pi AI demos focus only on:

> “Can an LLM run?”

This project focuses on:

* deployment engineering
* constrained systems optimization
* ARM inference infrastructure
* practical edge serving
* runtime orchestration

The emphasis is:

* stability
* usability
* deployment realism
* resource efficiency

---

# Raspberry Pi OS Setup

Recommended:

* Raspberry Pi OS Lite
* 64-bit version

Update system:

```bash
sudo apt update
sudo apt upgrade -y
```

Install required packages:

```bash
sudo apt install git cmake build-essential python3-pip -y
```

---

# Clone llama.cpp

```bash
cd ~

git clone https://github.com/ggml-org/llama.cpp

cd llama.cpp
```

Official Repository:

[llama.cpp GitHub Repository](https://github.com/ggml-org/llama.cpp?utm_source=chatgpt.com)

---

# Build llama.cpp

Build with server support enabled:

```bash
cmake -B build -DLLAMA_BUILD_SERVER=ON

cmake --build build -j2
```

For Raspberry Pi 3B+:

* `-j2` is safer than higher thread counts
* reduces RAM pressure during linking

Verify build:

```bash
ls build/bin
```

You should see:

```text
llama-server
llama-cli
llama-bench
```

---

# Download Models

Create models directory:

```bash
mkdir -p ~/llama.cpp/models
```

Recommended small models for Pi 3B+:

| Model              | Best Use                 |
| ------------------ | ------------------------ |
| TinyLlama 1.1B     | General assistant        |
| Qwen2.5 Coder 0.5B | Coding                   |
| Qwen 1.5B          | More capable but heavier |

Important:

* use GGUF quantized models
* Q4 quantizations recommended
* avoid large 7B models on Pi 3B+

---

# Example Model Files

Example filenames:

```text
tinyllama.gguf
qwen_coder_0_5b.gguf
qwen1_5b.gguf
```

Place them inside:

```text
~/llama.cpp/models
```

---

# Install Python Dependencies

Raspberry Pi OS may block normal pip installs.

Use:

```bash
pip3 install flask requests psutil --break-system-packages
```

---

# Download The Orchestrator

Inside Raspberry Pi:

```bash
cd ~/llama.cpp
```

Download directly from GitHub:

```bash
wget https://raw.githubusercontent.com/write2taran/edge_llm_manager/main/edge_llm_manager.py
```

Or clone repository:

```bash
git clone https://github.com/write2taran/edge_llm_manager
```

---

# Run The Orchestrator

```bash
python3 edge_llm_manager.py
```

Expected startup:

```text
Pi Edge LLM Orchestrator

Available models:
- tinyllama
- qwen-coder
- qwen1.5b

API running on port 5000
```

---

# Find Raspberry Pi IP

Run:

```bash
hostname -I
```

Example:

```text
192.168.1.6
```

---

# Test Local API On Pi

Inside Raspberry Pi:

```bash
curl http://127.0.0.1:5000/models
```

Expected:

```json
{"models":["tinyllama","qwen-coder","qwen1.5b"]}
```

---

# Test From Laptop/Desktop

Replace IP with your Pi IP.

Example:

```bash
curl http://192.168.1.6:5000/models
```

---

# Load A Model

## Windows CMD

```powershell
curl -X POST http://192.168.1.6:5000/load_model -H "Content-Type: application/json" -d "{\"model\":\"tinyllama\"}"
```

## Linux/macOS

```bash
curl -X POST http://192.168.1.6:5000/load_model \
-H "Content-Type: application/json" \
-d '{"model":"tinyllama"}'
```

Expected:

```json
{"success":true,"current_model":"tinyllama"}
```

Initial model loading may take:

* 10–30 seconds
* depending on SD card speed and RAM pressure

---

# Send Chat Requests

## Windows CMD

```powershell
curl http://192.168.1.6:5000/chat -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Explain edge AI in one sentence\"}]}"
```

## Linux/macOS

```bash
curl http://192.168.1.6:5000/chat \
-H "Content-Type: application/json" \
-d '{
  "messages":[
    {
      "role":"user",
      "content":"Explain edge AI in one sentence"
    }
  ]
}'
```

---

# Get System Status

```bash
curl http://192.168.1.6:5000/status
```

Returns:

* current model
* RAM usage
* CPU usage
* temperature

Example:

```json
{
  "current_model":"tinyllama",
  "ram_percent":82,
  "ram_used_mb":812,
  "cpu_percent":96,
  "temp":"temp=48.0'C"
}
```

---

# Unload Current Model

```bash
curl http://192.168.1.6:5000/unload
```

---

# How To Add Your Own Models

Open:

```bash
nano edge_llm_manager.py
```

Find:

```python
MODELS = {}
```

Add a new model entry.

Example:

```python
"my-model": {
    "path": "/home/pi/llama.cpp/models/my_model.gguf",
    "ctx": 192,
    "temp": 0.1,
    "top_p": 0.8,
    "threads": 3,
},
```

Then restart orchestrator:

```bash
python3 edge_llm_manager.py
```

---

# Understanding Model Parameters

| Parameter | Meaning          |
| --------- | ---------------- |
| path      | GGUF model path  |
| ctx       | Context size     |
| temp      | Temperature      |
| top_p     | Sampling control |
| threads   | CPU threads      |

---

# Recommended Settings For Pi 3B+

Recommended stable values:

```python
ctx = 128-192
threads = 2-3
temp = 0.0-0.2
top_p = 0.8
```

These significantly improve:

* stability
* coherence
* RAM behavior
* thermal consistency

---

# Thermal Monitoring

Check temperature:

```bash
watch -n 1 vcgencmd measure_temp
```

Check throttling:

```bash
watch -n 1 vcgencmd get_throttled
```

Check RAM:

```bash
watch -n 1 free -h
```

Check CPU:

```bash
htop
```

---

# Important Deployment Notes

This system intentionally prioritizes:

* stability
* low memory usage
* deterministic behavior

over:

* maximum throughput
* concurrency
* large model support

The Raspberry Pi 3B+ is heavily constrained:

* 1GB RAM
* limited thermals
* ARM CPU only

Dynamic model orchestration is significantly more practical than persistent multi-model loading.

---

# Engineering Insights

Key findings during deployment:

* Conservative decoding dramatically improved usability of small models.
* Context size tuning had major effects on stability.
* Real deployment behavior differed from synthetic benchmarks.
* Thermal environment significantly impacted sustained inference behavior.
* TinyLlama provided the best balance of responsiveness and reliability.
* Dynamic orchestration worked better than persistent multi-model loading on 1GB systems.

---

# Recommended Future Improvements

* Streaming token responses
* Authentication layer
* Web dashboard
* Queue system
* Automatic idle model unloading
* Power consumption benchmarking
* Multi-Pi distributed inference
* WebSocket support

---

# Example Use Cases

* Local coding assistant
* Offline AI assistant
* LAN AI server
* Edge AI experimentation
* ARM deployment testing
* Privacy-focused inference
* Educational systems engineering
* Lightweight AI infrastructure

---

# Final Notes

This project is not intended to compete with GPU servers.

The focus is:

* constrained systems engineering
* edge AI deployment
* efficient local inference
* lightweight orchestration

The goal is practical and stable AI infrastructure on minimal hardware.
