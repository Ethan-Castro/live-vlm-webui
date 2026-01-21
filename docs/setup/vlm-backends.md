# Setting Up VLM Backends

This guide covers different VLM backend options to power your Live VLM WebUI.

## Option A: Ollama (Easiest)

**Best for:** Quick start, easy model management, beginners

```bash
# Install ollama from https://ollama.ai/download
# Pull a vision model
ollama pull qwen3-vl:2b-instruct

# Start ollama server
ollama serve
```

**Recommended Models:**
- `qwen3-vl:2b-instruct` - Very fast, great for edge devices
- `ministral-3:3b` - Latest Mistral compact vision model
- `gemma3:4b` - Google's capable multimodal model
- `moondream` - Tiny, efficient vision model for edge

---

## Option B: vLLM (Recommended for Performance)

**Best for:** Production deployments, high throughput, GPU optimization

```bash
# Install vLLM
pip install vllm

# Start vLLM server with a vision model
python -m vllm.entrypoints.openai.api_server \
  --model microsoft/Phi-3.5-vision-instruct \
  --port 8000 \
  --trust-remote-code
```

### vLLM on Jetson Thor (Docker)

For NVIDIA Jetson Thor, use the official vLLM container:

```bash
# Pull and run vLLM container
docker run --rm -it \
  --network host \
  --shm-size=16g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --runtime=nvidia \
  --name=vllm \
  -v $HOME/data/models/huggingface:/root/.cache/huggingface \
  -v $HOME/data/vllm_cache:/root/.cache/vllm \
  nvcr.io/nvidia/vllm:25.10-py3

# Inside the container:
vllm serve microsoft/Phi-3.5-vision-instruct --trust-remote-code
```

**Recommended Vision Models:**
```bash
# Smaller, faster (4B parameters)
vllm serve microsoft/Phi-3.5-vision-instruct --trust-remote-code
```

---

## Option C: SGLang (For Complex Reasoning)

**Best for:** Complex prompts, structured outputs, research

```bash
# Install SGLang
pip install "sglang[all]"

# Start SGLang server
python -m sglang.launch_server \
  --model-path microsoft/Phi-3.5-vision-instruct \
  --port 30000 \
  --trust-remote-code
```

---

## Option D: NVIDIA API Catalog (Cloud)

**Best for:** No local GPU, cloud-based inference, instant access

**1. Get your API Key:**
- Visit [NVIDIA API Catalog](https://build.nvidia.com/)
- Sign in with your NVIDIA account (free)
- Navigate to a vision model (e.g., [Phi-3.5 Vision](https://build.nvidia.com/microsoft/phi-3-5-vision-instruct))
- Click "Get API Key"

**2. Test with curl:**
```bash
curl -X POST "https://ai.api.nvidia.com/v1/gr/microsoft/phi-3-5-vision-instruct/chat/completions" \
  -H "Authorization: Bearer nvapi-YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "microsoft/phi-3-5-vision-instruct",
    "messages": [
      {
        "role": "user",
        "content": "What is in this image? <img src=\"data:image/png;base64,...\" />"
      }
    ],
    "max_tokens": 512
  }'
```

**3. Configure in WebUI:**
- **API Base URL**: `https://ai.api.nvidia.com/v1/gr`
- **API Key**: `nvapi-YOUR_KEY_HERE`
- **Model**: `microsoft/phi-3-5-vision-instruct`

**Available Vision Models:**
- `microsoft/phi-3.5-vision-instruct` - Fast, 4.2B parameters
- `nvidia/neva-22b` - NVIDIA's vision model

**Notes:**
- Free tier available with rate limits
- No local GPU required
- Keep your API key secure!

---

## Performance Comparison

| Backend | Setup Difficulty | Speed | Quality | GPU Required |
|---------|-----------------|-------|---------|--------------|
| **Ollama** | ⭐ Easy | 🟢 Fast | 🟢 Good | Yes (local) |
| **vLLM** | ⭐⭐ Medium | 🟢🟢 Fastest | 🟢🟢 Excellent | Yes (local) |
| **SGLang** | ⭐⭐ Medium | 🟢 Fast | 🟢🟢 Excellent | Yes (local) |
| **NVIDIA API** | ⭐ Easy | 🟡 Medium | 🟢🟢🟢 Best | No |

---

## Port Reference

| Backend | Default Port | API Base URL |
|---------|-------------|--------------|
| **Ollama** | 11434 | `http://localhost:11434/v1` |
| **vLLM** | 8000 | `http://localhost:8000/v1` |
| **SGLang** | 30000 | `http://localhost:30000/v1` |
| **NVIDIA API** | - | `https://ai.api.nvidia.com/v1/gr` |

