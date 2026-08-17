# skyra-jarvis — Project Architecture & Design Specification (PAD)

## 1. Executive Summary & Core Responsibilities
`skyra-jarvis` is the central AI Orchestrator and voice-interactive assistant of the Skyra Tech ecosystem. It manages voice capture, real-time response generation, vector memory, a long-polling Telegram bot client, and coordinates calls to all satellite microservices.

### Core SLA Requirements
* **Startup Boot Benchmarking**: Validate, rank, and cache LLM providers within 5.0 seconds.
* **Failover Recovery**: Transition between rate-limited or dead keys in under 1.5 seconds.
* **Real-time Voice Output**: Process text-to-speech feedback with under 500ms latency.

---

## 2. High-Level Architecture & Lifecycle Diagrams

### ASCII Data Flow Diagram
```text
           [User Input: Voice / Telegram / GUI]
                           │
                           ▼
                    core/brain.py (think)
                           │
  ┌────────────────────────┼────────────────────────┐
  ▼                        ▼                        ▼
Memory Retrieval     Smart Failover        Tool Executions
(Qdrant/JSON Store)  (session_manager.py)  (outbound httpx calls)
  │                        │                        │
  ▼                        ▼                        ▼
Qdrant (Port 6333)   Mutex Lock guarded     Satellite Services:
Semantic Match       Key / Model pointers   - GitHub [Port 8001]
                     to services/llm_client - Google [Port 8002]
                                            - Browser [Port 8004]
                                            - Social [Port 8005]
```

### Component Interaction Matrix

| Source Component | Target Component | Protocol | Payload Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| `main.py` | `core/ui_server.py` | HTTP / WS | JSON | Serves local Webview HUD dashboard on port 8000 |
| `core/brain.py` | `services/smart_failover.py` | Async Call | Python Objects | Initiates request failover monitoring |
| `services/smart_failover.py` | `core/session_manager.py` | Async Lock | Mutex State | Reads and sets current active model/key |
| `services/llm_client.py` | Google/Groq APIs | HTTP/REST | JSON payloads | Sends validated API requests |
| `tools/` | Satellite Services | HTTP/REST | JSON payloads | Dispatches API queries to ports 8001, 8002, 8004, 8005 |

---

## 3. Directory Structure & Code Taxonomy

```text
apps/skyra-jarvis/
├── main.py                  ← System entry point and voice loop loop
├── requirements.txt         ← Core python dependencies
├── dashboard.html           ← Three.js status HUD dashboard
├── latency_cache.json       ← Cached benchmark latencies (24-hour TTL)
├── config/
│   ├── __init__.py          ← Config loading (dotenv)
│   ├── api_keys.json        ← Keys & candidate models mapping
│   └── settings.py          ← Benchmark settings, rate-limit matches
├── core/
│   ├── brain.py             ← Self-correction, Turn Pairing, History Compactor
│   ├── benchmark_engine.py  ← Parallel pre-flight scanner
│   ├── key_model_registry.py← Memory priority lists
│   ├── session_manager.py   ← Key pointer state with asyncio.Lock
│   ├── voice_listener.py    ← Microphone capture & Whisper STT
│   ├── speaker.py           ← RyanNeural TTS voice engine
│   ├── ui_server.py         ← WebSocket event broadcaster
│   └── memory_manager.py    ← Qdrant Vector & JSON Fact Store manager
├── services/
│   ├── llm_client.py        ← Adapter, Unified response and Tool schemas compiler
│   └── smart_failover.py    ← Failover decision engine (Regular and Streaming)
└── tools/
    ├── __init__.py          ← Unified API tool references and lookup maps
    ├── file_tools.py        ← Workspace safe file write/read tools
    ├── terminal_tools.py    ← Sandboxed workspace CLI execution tool
    ├── system_tools.py      ← Desktop OS controls (coordinates, shortcuts, screenshots)
    ├── github_tools.py      ← GitHub API wrapper tool calls
    ├── browser_tools.py     ← Playwright browser web automation tools
    ├── google_tools.py      ← Google Workspace integration tools
    └── social_tools.py      ← Automated social post creators
```

### Lifecycle Scopes
* **Singleton Managers (`session_manager`, `memory_manager`)**: Global state objects containing active pointers, quarantine pools, and vector connection pools. Operation updates are protected by an `asyncio.Lock` to ensure atomic state updates.
* **Request-Scoped Wrapper (`llm_client`)**: Instantiated on-demand during a conversation turn.

---

## 4. Technical Specs & Feature Deep-Dive

### A. Async Parallel Pre-Flight Latency Registry
To minimize boot times under 1.0 second, `benchmark_engine.py` leverages a persistent latency cache:
* **`latency_cache.json`**: Stores sorted benchmark results with a **24-hour TTL (Time-To-Live)**. If the cache is valid, J.A.R.V.I.S. reboots instantly without re-pinging API keys.
* **Async Parallel Scanner**: If the cache is expired, the system initiates parallel pings using `asyncio.gather` backed by a `ThreadPoolExecutor` with **64 worker threads**. All active keys and candidate models are pinged concurrently, completing within a 5.0–10.0 second window.

### B. Dual-Tier Failover & Mid-Stream Resiliency
* **Key-Hop / Quarantine**: Triggered on HTTP 429 / Quota limits. Quarantines the key for **60 seconds**, returning it to `probation_pool` when the cooldown expires.
* **Model-Hop**: Triggered on HTTP 5xx. Shifts model pointer of the same key.
* **Chunk Buffer Accumulator (Mid-Stream Resiliency)**: If a stream is interrupted mid-generation, all already-emitted tokens are stored inside a chunk buffer accumulator. This accumulated text is appended to the prompt history as a partial model turn *before* the smart failover router triggers the fallback model, ensuring generation resumes seamlessly without losing progress.

### C. Turning & Schema Corrections
* **Gemini Turn Pairing**: Group multiple tool responses in a single turn into one `user` block to avoid strict sequence validation errors (`400 INVALID_ARGUMENT`).
* **Groq Fallback Tool Stripping**: Automatically strips the `tools` parameter and retries requests if the fallback model does not support tool calling.
* **Dynamic Tool Response Truncation**: Enforce a maximum token ceiling (**2,000 tokens**) on large tool outputs (such as webpage text from `/browse`) before injecting them into history to prevent context window overflow.
* **Agentic Self-Correction**: If a terminal command execution returns a non-zero exit code or stderr, the tool executor executes a 3-turn repair loop.

### D. Qdrant Vector Memory + JSON Fact Store
Managed by `core/memory_manager.py`:
* **Qdrant Collection**: Connects to port `6333` with a collection schema storing vector embeddings representing conversation history.
* **Embedding Pipeline**: Utilizes local embeddings or API endpoints to vectorize query content.
* **Semantic Search Threshold**: Executes top-k search with a cosine similarity threshold of **0.75** to retrieve relevant context.
* **JSON Fallback Storage**: If the Qdrant service is offline or unreachable, the memory manager falls back to querying and writing facts to local `memory.json` files.

### E. Structured OpenTelemetry HUD Tracing
To visualize latency metrics and failover events on `dashboard.html`, the core generates structured traces:
* **Trace ID Propagation**: Generates a unique Trace ID for each conversation turn.
* **WebSocket HUD Telemetry**: Broadcasts trace events (API pings, model hops, tool completions) formatted as OpenTelemetry-compatible schemas directly over the WebSocket channel.

---

## 5. Security, Environment & Configuration
Exposes no public inbound ports. Serves local WebSocket feed on `127.0.0.1:8000` only. Requires active environmental keys:
* `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3`
* `GROQ_API_KEY_1` ... `GROQ_API_KEY_6`
* `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`

---

## 6. Resilience, Error Handling & Recovery Strategies
* **Microservice REST Circuit Breaking**: Outbound requests to satellite services monitor status codes. If a service times out or fails consecutively, the orchestrator triggers a local circuit breaker, defaulting to verbal failure messages to prevent request hang-ups.
* **Concurrency State Locking**: Mutating pointers are locked to prevent Voice and Telegram client conflicts.

---

## 7. Ecosystem Integration & Dependencies
Dispatches REST API tool requests to local microservices using an **`httpx.AsyncClient`** with a strict **15-second execution timeout**:
* **GitHub Service**: Port `8001`
* **Google Service**: Port `8002`
* **Browser Service**: Port `8004`
* **Social Service**: Port `8005`
