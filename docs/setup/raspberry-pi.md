# Raspberry Pi 5 Setup Guide

This guide covers running Live VLM WebUI on Raspberry Pi 5 in CPU-only mode.

## Overview

Raspberry Pi 5 support enables running the WebUI with:
- CPU-only operation (no GPU monitoring)
- Optimized defaults for limited resources
- Restricted model selection for best performance
- Optional YOLO object detection (if resources permit)

## Requirements

### Hardware
- **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- MicroSD card (32GB+ recommended) or NVMe SSD
- USB webcam or Pi Camera Module
- Cooling solution (active cooling recommended for sustained inference)

### Software
- **Raspberry Pi OS** (64-bit, Bookworm or later)
- **Python 3.10+** (included in Raspberry Pi OS)
- **Ollama** for local VLM inference

## Quick Start

### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the recommended model for Pi
ollama pull qwen3-vl:2b-instruct

# Start Ollama server
ollama serve
```

### 2. Install Live VLM WebUI

**Option A: Minimal installation (recommended for Pi)**

```bash
# Install without heavy dependencies
pip install live-vlm-webui

# Or from source with Pi-specific requirements
git clone https://github.com/nvidia-ai-iot/live-vlm-webui.git
cd live-vlm-webui
pip install -r requirements-pi.txt
pip install -e .
```

**Option B: Full installation (if you have 8GB RAM and want YOLO)**

```bash
pip install live-vlm-webui[full]
```

### 3. Run the Server

```bash
# Auto-detects Pi and applies optimized settings
live-vlm-webui

# Or explicitly enable Pi mode
live-vlm-webui --pi-mode
```

### 4. Access the WebUI

Open **`https://localhost:8090`** in your browser (Chromium recommended on Pi).

## Pi Mode Features

When running on Raspberry Pi (auto-detected) or with `--pi-mode`:

| Feature | Default | Pi Mode |
|---------|---------|---------|
| Frame processing interval | 30 frames | 60 frames |
| Recommended model | Any | qwen3-vl:2b-instruct |
| GPU monitoring | Enabled | Disabled (N/A) |
| YOLO detection | Enabled | Disabled by default |
| Max tokens | 512 | 100 |

## Configuration

### Environment Variables

Customize Pi mode behavior with environment variables:

```bash
# Override frame processing interval (default: 60 in Pi mode)
export PI_PROCESS_EVERY=90

# Override max tokens (default: 100 in Pi mode)
export PI_MAX_TOKENS=50

# Force Pi mode on non-Pi hardware (for testing)
export PI_MODE=true

live-vlm-webui
```

### Command-Line Options

```bash
# Explicit Pi mode
live-vlm-webui --pi-mode

# Custom frame interval
live-vlm-webui --pi-mode --process-every 120

# Use specific model
live-vlm-webui --pi-mode --model qwen3-vl:2b-instruct
```

## Performance Tuning

### Recommended Settings for Pi 5

| RAM | Frame Interval | Max Tokens | Notes |
|-----|----------------|------------|-------|
| 4GB | 90-120 | 50-100 | Conservative, stable |
| 8GB | 60-90 | 100-150 | Balanced performance |

### Tips for Best Performance

1. **Use active cooling** - Sustained inference generates heat
2. **Use NVMe SSD** - Faster than microSD for model loading
3. **Close other applications** - Free up RAM for inference
4. **Use Chromium** - Better WebRTC performance than Firefox on Pi
5. **Lower resolution** - Use 640x480 webcam resolution if possible

### Memory Management

Monitor memory usage during operation:

```bash
# Watch memory in real-time
watch -n 1 free -h

# Check for swap usage (should be minimal)
swapon --show
```

If you experience out-of-memory issues:
- Increase swap size (not recommended for microSD)
- Reduce `--process-every` value
- Use a smaller model

## Troubleshooting

### "Model not found" error

Ensure Ollama has the model and is running:

```bash
# Check Ollama status
systemctl status ollama

# List available models
ollama list

# Pull the recommended model
ollama pull qwen3-vl:2b-instruct
```

### Slow performance

1. Check CPU temperature (throttling starts at 80°C):
   ```bash
   vcgencmd measure_temp
   ```

2. Increase frame processing interval:
   ```bash
   live-vlm-webui --pi-mode --process-every 120
   ```

3. Reduce max tokens in the WebUI settings

### Camera not detected

```bash
# List video devices
v4l2-ctl --list-devices

# Test camera
libcamera-hello --camera 0
```

For USB webcams, ensure they're connected before starting the server.

### SSL certificate issues

The server auto-generates SSL certificates. If you see certificate errors:

```bash
# Regenerate certificates
rm -f ~/.config/live-vlm-webui/cert.pem ~/.config/live-vlm-webui/key.pem
live-vlm-webui
```

## Model Recommendations

For Raspberry Pi 5, use lightweight vision models:

| Model | Size | RAM Usage | Quality |
|-------|------|-----------|---------|
| `qwen3-vl:2b-instruct` | ~2GB | ~3GB | Good |
| `moondream2` | ~1.5GB | ~2.5GB | Basic |

**Note:** Larger models (7B+) are not recommended for Pi 5 due to memory constraints.

## Limitations

- **No GPU acceleration** - All inference is CPU-based
- **Limited model selection** - Only small models recommended
- **No YOLO by default** - Object detection disabled to save resources
- **Slower inference** - Expect 5-15 seconds per frame analysis

## Advanced: Enabling YOLO on Pi

If you have 8GB RAM and want object detection:

```bash
# Install ultralytics (large download, ~500MB)
pip install ultralytics

# Run with YOLO enabled (uses more RAM)
live-vlm-webui --pi-mode
```

**Warning:** YOLO significantly increases RAM usage. Monitor memory carefully.

## See Also

- [VLM Backend Setup](./vlm-backends.md) - Detailed Ollama configuration
- [Advanced Configuration](../usage/advanced-configuration.md) - All configuration options
- [Troubleshooting Guide](../troubleshooting.md) - Common issues and solutions
