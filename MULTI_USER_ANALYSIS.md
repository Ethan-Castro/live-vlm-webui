# Multi-User Architecture Analysis

## Current State: Single-User Design

The Live VLM WebUI is currently architected as a **single-user, single-session application**. This document explains the current limitations, why multiple users see shared state, and what would be required to support multi-user scenarios.

---

## Why You're Seeing Shared State

When you access from multiple browsers/machines, you observe:
- ✅ **Connection status shows "Connected"** for all clients
- ✅ **VLM output from one user's camera** appears for all users
- ✅ **Settings changes** (prompt, model, processing interval) affect everyone
- ✅ **System stats** are identical across all clients

This is **by design** for single-user scenarios, but creates issues with multiple concurrent users.

---

## Architecture Deep Dive

### 1. Global Shared State (server.py)

The server uses **global singleton instances** shared across all connections:

```python
# Global objects (lines 28-34)
relay = MediaRelay()           # Shared relay for all WebRTC connections
pcs = set()                    # Set of all peer connections
vlm_service = None             # SINGLE VLM service instance
websockets = set()             # All WebSocket connections
gpu_monitor = None             # SINGLE GPU monitor instance
```

**Impact:**
- Only **one VLM service instance** handles all users
- All users share the same model, prompt, and API configuration
- VLM responses are stored in a single shared variable

### 2. VLM Service State (vlm_service.py)

The VLMService maintains **global state** for all users:

```python
class VLMService:
    def __init__(self, ...):
        self.current_response = "Initializing..."  # SHARED across all users
        self.is_processing = False                  # SHARED processing flag
        self._processing_lock = asyncio.Lock()      # SINGLE lock for all requests

        # Metrics are global
        self.last_inference_time = 0.0
        self.total_inferences = 0
```

**Impact:**
- When User A's camera frame is analyzed, the response is stored in `current_response`
- User B accessing simultaneously will see User A's VLM output
- Only **one inference at a time** due to the single lock (`_processing_lock`)
- If lock is busy, frames from other users are dropped

### 3. Broadcasting Mechanism (server.py)

All VLM responses and system stats are **broadcast to ALL WebSocket clients**:

```python
def broadcast_text_update(text: str, metrics: dict):
    """Broadcast to ALL connected WebSocket clients"""
    for ws in websockets:
        asyncio.create_task(ws.send_str(message))

def broadcast_gpu_stats(stats: dict):
    """Broadcast GPU stats to ALL clients"""
    for ws in websockets:
        asyncio.create_task(ws.send_str(message))
```

**Impact:**
- Every VLM response goes to every connected browser
- System stats are identical for all users (which is correct, but no per-user context)

### 4. Video Processing (video_processor.py)

Each WebRTC connection creates its own `VideoProcessorTrack`, BUT:

```python
class VideoProcessorTrack(VideoStreamTrack):
    # CLASS VARIABLE - shared across ALL instances
    process_every_n_frames = 30
    max_frame_latency = 0.0

    def __init__(self, track, vlm_service, text_callback):
        self.vlm_service = vlm_service  # SHARED service instance
        self.text_callback = text_callback  # Broadcasts to ALL
```

**Impact:**
- Each user has their own video track, which is good
- But all tracks share the **same VLM service** and **broadcast callback**
- Processing settings (frame interval) are class variables affecting all users

### 5. WebSocket Session Management (server.py)

WebSocket connections don't have user-specific session IDs:

```python
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    websockets.add(ws)  # Added to global set, no session ID

    # Messages from ANY client affect the GLOBAL vlm_service
    if data.get('type') == 'update_prompt':
        vlm_service.update_prompt(new_prompt, max_tokens)

    if data.get('type') == 'update_model':
        vlm_service.model = new_model
```

**Impact:**
- No concept of "sessions" or "users"
- Settings changes from one user affect all users
- No way to route VLM responses to specific users

---

## Current Limitations Summary

| Aspect | Current State | Multi-User Impact |
|--------|---------------|-------------------|
| **VLM Service** | Single global instance | ❌ Only one model/prompt for everyone |
| **VLM Responses** | Shared `current_response` | ❌ Users see each other's outputs |
| **Processing Lock** | Single lock | ❌ Only one inference at a time |
| **WebSocket Broadcast** | All messages to all clients | ❌ No privacy between users |
| **Settings** | Global configuration | ❌ Changes affect everyone |
| **Session Management** | No session IDs | ❌ Can't distinguish users |
| **Video Tracks** | Per-connection | ✅ Each user has own video stream |
| **WebRTC Peers** | Per-connection | ✅ Video routing works correctly |

---

## What Would Be Required for Multi-User Support

### Level 1: Basic Multi-User (Isolated Sessions)

**Goal:** Each user has their own independent session with isolated VLM outputs.

**Changes Required:**

1. **Session Management**
   - Add session IDs to WebSocket connections
   - Create session-to-user mapping
   - Generate unique session IDs on connection

2. **Per-User VLM State**
   ```python
   # Instead of single global vlm_service
   user_sessions = {
       "session_id_1": {
           "vlm_service": VLMService(...),
           "websocket": ws,
           "video_track": track,
           "settings": {...}
       }
   }
   ```

3. **Targeted Broadcasting**
   ```python
   def send_to_session(session_id, message):
       """Send to specific user's WebSocket"""
       session = user_sessions.get(session_id)
       if session and session["websocket"]:
           asyncio.create_task(session["websocket"].send_str(message))
   ```

4. **Per-Session VideoProcessorTrack**
   ```python
   class VideoProcessorTrack(VideoStreamTrack):
       def __init__(self, track, session_id, user_sessions):
           self.session_id = session_id
           self.user_sessions = user_sessions
           # Use session-specific VLM service
           self.vlm_service = user_sessions[session_id]["vlm_service"]
   ```

**Effort:** ~8-12 hours of development + testing

**Resource Impact:**
- Memory: ~200-500MB per active user (VLM client, track buffers)
- CPU: Scales linearly with active video streams
- VLM Backend: Multiple concurrent inference requests

---

### Level 2: Concurrent Multi-User (Shared VLM Backend)

**Goal:** Multiple users sharing the same VLM backend efficiently.

**Additional Changes:**

1. **Request Queue with Session Context**
   ```python
   class SharedVLMService:
       def __init__(self):
           self.request_queue = asyncio.Queue()
           self.session_responses = {}  # session_id -> response

       async def process_frame(self, session_id, image):
           await self.request_queue.put((session_id, image))

       async def worker(self):
           while True:
               session_id, image = await self.request_queue.get()
               response = await self._analyze(image)
               self.session_responses[session_id] = response
               # Notify only that session
   ```

2. **Rate Limiting Per User**
   - Prevent one user from monopolizing VLM
   - Fair scheduling across users

3. **Per-User Settings with Batching**
   - Allow different prompts per user
   - Batch similar requests for efficiency

**Effort:** ~16-24 hours of development + testing

**Resource Impact:**
- VLM Backend: Can batch requests for better throughput
- Latency: May increase with more concurrent users
- Memory: ~200MB per user + queue overhead

---

### Level 3: Enterprise Multi-User (Scalable Cloud)

**Goal:** Support many users across distributed infrastructure.

**Architecture Changes:**

1. **Stateless Frontend Servers**
   - WebRTC/WebSocket servers don't hold state
   - Session data in Redis/database
   - Horizontal scaling (multiple server instances)

2. **Dedicated VLM Service Layer**
   - Separate VLM inference service (gRPC/REST)
   - Load balancer across multiple VLM backends
   - Queue-based architecture (RabbitMQ/Kafka)

3. **Authentication & Authorization**
   - User accounts and login
   - API keys or JWT tokens
   - Usage quotas and rate limiting

4. **Multi-Tenancy**
   - Per-user or per-organization VLM configurations
   - Usage tracking and billing
   - Resource isolation

5. **Observability**
   - Logging per user session
   - Metrics (Prometheus/Grafana)
   - Distributed tracing

**Effort:** ~4-8 weeks (major architectural rewrite)

**Infrastructure:**
- Multiple frontend servers (load balanced)
- Redis/PostgreSQL for session state
- Multiple VLM backend instances
- Message queue (RabbitMQ/Kafka)
- Monitoring stack

---

## Hosting Scenarios & Recommendations

### Scenario 1: Internal Demo Server (5-10 NVIDIA Employees)

**Current Limitations:**
- ❌ Users will see each other's camera feeds in VLM output
- ❌ One user changing settings affects everyone
- ❌ Only one VLM inference at a time (sequential processing)

**Quick Workaround (No Code Changes):**
1. **Schedule access time slots** - "Alice uses 9-10am, Bob uses 10-11am"
2. **Create instructions** - "Only one person connect at a time"
3. **Deploy multiple instances** - Run 3 separate servers on different ports
   ```bash
   # Instance 1 for User A (port 8090)
   python server.py --port 8090 --model llama-3.2-11b-vision-instruct

   # Instance 2 for User B (port 8091)
   python server.py --port 8091 --model llama-3.2-11b-vision-instruct

   # Instance 3 for User C (port 8092)
   python server.py --port 8092 --model llama-3.2-11b-vision-instruct
   ```
   - Each instance has its own VLM service (isolated)
   - Users access different URLs (https://server:8090, https://server:8091)
   - Works with Docker containers too

**Recommendation:** **Deploy multiple instances** (easiest, no code changes)

**Hosting Options:**
- NVIDIA DGX/workstation with multiple GPUs (assign 1 GPU per instance)
- Cloud VM (AWS g5.2xlarge, Azure NC6s_v3) with GPU
- Internal NVIDIA infrastructure

---

### Scenario 2: Team Demo Server (10-30 Concurrent Users)

**Recommended:** **Level 1 implementation** (basic multi-user)

**Benefits:**
- ✅ Each user has isolated session
- ✅ No interference between users
- ✅ Independent settings per user
- ✅ Privacy of VLM outputs

**Hosting:**
- NVIDIA DGX with A100/H100 (can handle 10-20 concurrent inferences)
- Cloud GPU instance (AWS p4d, Azure ND96asr_v4)
- vLLM backend with tensor parallelism for throughput

**Considerations:**
- VLM backend becomes bottleneck (15-30 inferences/sec with Llama-3.2-11B)
- Higher latency as more users connect
- Monitor GPU VRAM (each user's video track + model)

---

### Scenario 3: Public Demo or Large Organization (100+ Users)

**Recommended:** **Level 3 implementation** (enterprise architecture)

**Architecture:**
```
Load Balancer (HTTPS)
    ↓
Frontend Servers (3-5 instances)
    ↓
Redis (session state)
    ↓
Message Queue (RabbitMQ)
    ↓
VLM Backend Pool (5-10 GPU workers)
```

**Hosting:**
- Kubernetes cluster (EKS, AKS, or on-prem)
- Separate GPU nodes for VLM inference
- Autoscaling based on queue depth

---

## Performance & Resource Estimates

### Single Instance Limits

| Hardware | Max Concurrent Users | Notes |
|----------|---------------------|-------|
| **Jetson Orin (32GB)** | 1-2 users | VLM inference ~500ms-2s, limited VRAM |
| **RTX 4090 (24GB)** | 2-4 users | Good for small team testing |
| **A100 (40GB)** | 5-10 users | Recommended for internal demos |
| **A100 (80GB)** | 10-20 users | Can run larger models + more users |
| **DGX A100 (8x A100)** | 40-80+ users | Enterprise deployment |

*Assumes Llama-3.2-11B-Vision model, 30 FPS video, processing every 30 frames (1 inference/sec per user)*

### Memory Usage Per User

- **Frontend (server.py):** ~50-100MB per WebSocket + WebRTC connection
- **Video buffers:** ~20-50MB per active video track
- **VLM Service instance:** ~100-200MB (OpenAI client, response history)
- **Total per user:** ~200-400MB (excluding VLM model itself)

### VLM Backend Throughput

| Model | Hardware | Throughput | Latency/Request |
|-------|----------|------------|-----------------|
| Llama-3.2-11B-Vision | A100 (40GB) | ~15-30 req/s | ~500-1000ms |
| Phi-3.5-Vision (4B) | A100 (40GB) | ~40-60 req/s | ~200-400ms |
| Llama-3.2-90B-Vision | 8x A100 | ~5-10 req/s | ~1000-2000ms |

*Throughput assumes batching and optimized vLLM configuration*

---

## Security Considerations for Cloud Hosting

### Current Security Posture

1. **No Authentication**
   - Anyone with URL can access
   - No user login or API keys

2. **Self-Signed SSL Certificates**
   - Triggers browser warnings
   - Not suitable for public deployment

3. **No Rate Limiting**
   - Users can spam VLM requests
   - No protection against abuse

4. **No Input Validation**
   - Accepts any WebSocket messages
   - Potential for injection attacks

### Required for Cloud Deployment

1. **Add Authentication**
   ```python
   # JWT token validation
   # API key requirement
   # NVIDIA NGC account integration
   ```

2. **Proper SSL Certificates**
   - Let's Encrypt for public domains
   - Corporate CA certificates for internal

3. **Rate Limiting**
   ```python
   # Per-user: max 60 VLM requests/minute
   # Per-IP: max 10 connections
   ```

4. **Input Validation**
   - Sanitize WebSocket messages
   - Validate WebRTC SDP offers
   - Content-type validation on images

5. **Network Security**
   - CORS policies
   - Firewall rules (only allow 443/8090)
   - VPN/Private endpoint for internal use

---

## Recommended Path Forward

### For Your Use Case (NVIDIA Employee Demos)

**Option A: Quick Solution (No Code Changes)**
1. Deploy **3-5 separate instances** on different ports
2. Create a simple **landing page** with links to each instance
3. Add **basic usage instructions** (don't change others' settings)
4. Host on **internal NVIDIA DGX** or **cloud VM**

**Effort:** 1-2 hours setup
**Supports:** 3-5 concurrent isolated users

---

**Option B: Basic Multi-User (Recommended)**
1. Implement **Level 1 changes** (session management)
2. Add simple **session ID** display in UI
3. Deploy on **single A100 GPU** instance
4. Use **Let's Encrypt SSL** if public or **internal CA** if behind firewall

**Effort:** 8-12 hours development + 2-4 hours deployment
**Supports:** 10-20 concurrent users with good UX

---

**Option C: Enterprise (For Large-Scale Rollout)**
1. Full **Level 3 implementation**
2. Integrate with **NVIDIA NGC accounts**
3. Deploy on **Kubernetes** with autoscaling
4. Add **monitoring and analytics**

**Effort:** 4-8 weeks development + 1-2 weeks deployment
**Supports:** 100+ concurrent users, production-ready

---

## Testing Multi-User Scenarios

### Current Behavior Test

1. Open browser tab A: `https://localhost:8090`
2. Start camera and VLM analysis
3. Open browser tab B (same URL)
4. Observe:
   - Tab B shows "Connected" immediately
   - Tab B sees VLM outputs from Tab A's camera
   - Changing prompt in Tab B affects Tab A

### After Multi-User Implementation

1. Tab A gets `session_id_1`
2. Tab B gets `session_id_2`
3. Each sees only their own VLM outputs
4. Settings are independent
5. Both can run simultaneously without interference

---

## Conclusion

### Current State
- ✅ **Works great for single user**
- ✅ **Perfect for personal use or scheduled demos**
- ❌ **Not suitable for concurrent multi-user access**

### Path to Multi-User
- **Easy:** Deploy multiple instances (5-10 users)
- **Moderate:** Implement session management (10-20 users)
- **Complex:** Full enterprise architecture (100+ users)

### Recommendation for NVIDIA Team
Start with **Option A (multiple instances)** for immediate testing, then assess if you need **Option B (session management)** based on usage patterns.

---

## Questions & Contact

For implementation questions or collaboration:
- Review `server.py` (lines 28-34, 253-373) for global state
- Review `vlm_service.py` (lines 48-49) for shared response
- Review `video_processor.py` (lines 30-33) for class variables

---

*Document created: 2025-11-05*
*Version: 1.0*
*Status: Current architecture analysis*


