# Implementation Roadmap

This document tracks the development plan for Live VLM WebUI features.

## Phase 1: UI/UX Improvements 🎨

### 1.1 Separate Video and Text Overlay ⭐ Priority
**Status:** Planned
**Complexity:** Low
**Impact:** High

**Current:** Text burned into video frames
**Target:** Independent HTML elements for better flexibility

**Implementation:**
- Remove OpenCV text overlay from `video_processor.py`
- Add HTML div overlay positioned absolutely over video
- Use WebSocket or SSE to push text updates from server to client
- Benefits: Better styling, no video quality degradation, easier to screenshot text

**Files to modify:**
- `video_processor.py` - Remove `_add_text_overlay()`
- `server.py` - Add WebSocket/SSE endpoint for text updates
- `index.html` - Add overlay div, WebSocket client

---

### 1.2 Interactive Prompt Editor ⭐ Priority
**Status:** Planned
**Complexity:** Low
**Impact:** High

**Current:** Fixed prompt via CLI argument
**Target:** Dynamic prompt changes via UI

**Implementation:**
- Add text area in UI for custom prompt
- Add dropdown with preset prompts:
  - Scene description
  - Object detection
  - Safety monitoring
  - Activity recognition
  - OCR / Text reading
  - Emotion detection
  - Accessibility description
- Send prompt updates via WebSocket/HTTP POST
- Update `vlm_service.update_prompt()` on the fly

**Files to modify:**
- `index.html` - Add prompt editor UI
- `server.py` - Add endpoint to update prompt
- `vlm_service.py` - Already has `update_prompt()` method

---

### 1.3 Inference Latency Metrics
**Status:** Planned
**Complexity:** Low
**Impact:** Medium

**Current:** No performance metrics displayed
**Target:** Show ms per frame, FPS, queue depth

**Implementation:**
- Add timing instrumentation:
  - Frame capture → VLM request time
  - VLM processing time
  - Total round-trip time
- Display metrics in UI:
  - Current latency
  - Average latency (rolling window)
  - Min/Max latency
  - Frames processed per second
- Store metrics for benchmark mode

**Files to modify:**
- `vlm_service.py` - Add timing decorators
- `video_processor.py` - Track frame timing
- `index.html` - Display metrics panel

---

## Phase 2: Backend Integration 🔧

### 2.1 Model Selection Dropdown
**Status:** Planned
**Complexity:** Medium
**Impact:** High

**Implementation:**
- Query `/v1/models` endpoint on startup and periodically
- Display available models in dropdown
- Switch model on the fly (may require new VLM service instance)
- Show model metadata (size, capabilities)

**API Endpoints to support:**
- vLLM: `GET /v1/models`
- SGLang: `GET /v1/models`
- Ollama: `GET /api/tags`

**Files to modify:**
- `server.py` - Add model discovery endpoint
- `vlm_service.py` - Support model switching
- `index.html` - Add model selector UI

---

### 2.2 Cloud Model Support (OpenAI, Anthropic, etc.)
**Status:** Partially implemented
**Complexity:** Low
**Impact:** Medium

**Current:** Works with any OpenAI-compatible API
**Target:** UI for API key management, cloud-specific features

**Implementation:**
- Add settings panel for:
  - API endpoint URL
  - API key (secure storage)
  - Model selection
- Support multiple providers:
  - OpenAI (gpt-4-vision-preview)
  - Anthropic Claude (vision)
  - Google Gemini (vision)
- Handle rate limits and quotas

**Files to modify:**
- `index.html` - Add settings modal
- `server.py` - Secure API key handling
- `vlm_service.py` - Provider-specific adaptations

---

### 2.3 Live GPU Utilization Stats ⭐ Priority
**Status:** Planned
**Complexity:** Medium-High
**Impact:** High (Jetson showcase feature)

**Implementation:**
- **NVIDIA GPUs** (Jetson, DGX, Desktop):
  - Use `pynvml` (NVIDIA Management Library)
  - Metrics: GPU utilization %, memory used/total, temperature, power

- **Apple Silicon** (Mac):
  - Use `powermetrics` or `IOKit` bindings
  - Metrics: GPU usage, memory bandwidth

- **AMD GPUs**:
  - Use `rocm-smi` or `/sys/class/drm/` readings

- **CPU fallback**:
  - Use `psutil` for CPU/RAM when no GPU

**Display:**
- Real-time graphs (GPU %, memory)
- Current values
- Historical data (last 60s)

**Files to create:**
- `gpu_monitor.py` - Platform detection and monitoring
- `static/gpu-stats.js` - Chart.js visualization

**Files to modify:**
- `requirements.txt` - Add `pynvml`, `psutil`
- `server.py` - Add GPU stats endpoint (WebSocket/SSE)
- `index.html` - Add stats panel

---

## Phase 3: Advanced Features 🚀

### 3.1 Benchmark Mode
**Status:** Planned
**Complexity:** High
**Impact:** High (Killer feature for Jetson vs DGX)

**Features:**
- Record metrics over time:
  - Inference latency distribution
  - GPU utilization
  - Memory usage
  - Throughput (frames/sec)
- Compare configurations:
  - Different models
  - Different hardware
  - Different batch sizes/parameters
- Export results:
  - JSON data
  - CSV for spreadsheets
  - Markdown report
  - Charts/graphs

**Implementation:**
- Add benchmark recording mode
- Store time-series data
- Generate comparison reports
- Create shareable benchmark URLs

**Files to create:**
- `benchmark.py` - Recording and analysis
- `templates/report.html` - Benchmark report template

---

### 3.2 Side-by-Side Model Comparison
**Status:** Planned
**Complexity:** Very High
**Impact:** Very High (Differentiation feature)

**Features:**
- Run 2-4 models simultaneously on same video feed
- Display results side-by-side in grid
- Compare:
  - Response quality
  - Latency
  - GPU usage per model
- Record which model user prefers (A/B testing)

**Implementation:**
- Multiple VLM service instances
- Grid layout in UI
- Synchronized frame feeding
- Aggregate statistics

**Challenges:**
- Resource usage (multiple models)
- UI complexity
- Fair comparison (same frames)

---

## Technical Decisions

### WebSocket vs Server-Sent Events (SSE)
**Recommendation:** SSE for unidirectional data (GPU stats, text updates)
- Simpler than WebSocket
- Built-in reconnection
- Works with HTTP/2

**Use WebSocket for:** Bidirectional control (prompt changes, model selection)

### State Management
- Keep VLM service stateful on server
- UI sends control messages
- Server broadcasts state changes

### Performance Monitoring
- Use `time.perf_counter()` for precise timing
- Rolling window statistics (last 100 frames)
- Separate thread/task for GPU monitoring

---

## Development Priorities for Jetson/DGX Showcase

**Highest Priority (Jetson differentiation):**
1. Live GPU stats with platform detection
2. Benchmark mode with hardware comparison
3. Inference latency metrics

**High Priority (Usability):**
1. Separate video/text overlay
2. Interactive prompt editor
3. Model selection

**Medium Priority (Advanced use):**
1. Cloud model support
2. Side-by-side comparison

---

## Next Steps

1. Create GitHub issues for each feature
2. Start with Phase 1.1 (Separate overlay) - clean foundation
3. Add Phase 2.3 (GPU stats) - showcase Jetson
4. Build out remaining features iteratively

Would you like to start implementing any specific feature?

