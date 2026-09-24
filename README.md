# Laya - System 1 Decision Engine Demo

A comprehensive interactive demo and benchmark suite for [Laya](https://github.com/NandhaKishorM/laya) — the open-source, non-autoregressive **System 1** decision engine.

Unlike generative LLMs (GPT-4, Claude, Llama) that produce text token-by-token with multi-second latency and hallucination risks, Laya evaluates state and returns **typed, calibrated decisions** in a **single forward pass** (sub-40ms).

---

## Key Capabilities

- ⚡ **Ultra-Low Latency**: Sub-40ms inference on GPU (ModernBERT-large decision head).
- 🎯 **Calibrated Confidence**: Outputs statistical probabilities for decisions rather than uncalibrated logits.
- 🧩 **Typed Primitives**:
  - `choice`: Multi-class categorization with calibrated probability distribution.
  - `noul`: Fast boolean (yes/no) classification with certainty score.
  - `score`: Continuous or ordinal scale ranking (e.g., risk level, sentiment, priority).
- 🌐 **Automatic Script & Language Routing**: Built-in router detects language/script and dispatches requests to the optimal checkpoint (English, Multilingual, or Typed-Decisions).
- 🛡️ **Zero Hallucination / Zero JSON Breakage**: Outputs pure structured data directly from the classification head—no JSON parser failures.

---

## Project Structure

```
laya_demo/
├── cli_demo.py          # Rich terminal benchmark, pipeline demo, and interactive REPL
├── server.py            # FastAPI REST backend & Web server
├── templates/
│   └── index.html       # Sleek dashboard for live interactive testing
├── static/
│   ├── app.js           # Interactive UI controller and benchmark runner
│   └── style.css        # Custom styles and animations
├── requirements.txt     # Python dependencies
└── README.md            # Documentation
```

---

## Getting Started

### 1. Set Up Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the CLI Demo & Benchmark

The CLI demo tests real-world scenarios (Billing triage, security intrusion detection, French multilingual routing), runs a 15-iteration speed benchmark, and launches an interactive prompt:

```bash
python cli_demo.py
```

### 3. Launch the Interactive Web Dashboard

To launch the web playground:

```bash
python server.py
```

Then open your browser at **`http://localhost:8000`**.

Features in Web UI:
- **Preset Scenarios**: Customer Support Triage, Security Breach Alert, Multilingual French Query, and Enterprise Lead Scoring.
- **Custom Playground**: Edit state JSON and decision questions schema in real-time.
- **Latency & Routing Inspector**: Live millisecond latency gauge, model checkpoint badge, and calibrated confidence visualization bars.
- **Built-in Benchmark Modal**: Run 15 consecutive inference passes to measure average, P95, min, and max latency.

---

## Decision Primitives Reference

### 1. `choice`
```json
{
  "intent": {
    "type": "choice",
    "instructions": "What is the primary customer intent?",
    "options": ["billing_refund", "account_cancellation", "technical_support"]
  }
}
```

### 2. `noul` (Boolean Decision)
```json
{
  "is_urgent": {
    "type": "noul",
    "instructions": "Does this require immediate escalation?"
  }
}
```

### 3. `score`
```json
{
  "escalation_risk": {
    "type": "score",
    "instructions": "Rate customer churn risk",
    "criteria": ["low", "moderate", "high", "critical"]
  }
}
```

---

## Comparison: System 1 (Laya) vs System 2 (Generative LLMs)

| Feature | Laya (System 1) | Generative LLMs (System 2) |
| :--- | :--- | :--- |
| **Inference Time** | **20 – 40 ms** | 1,200 – 3,000 ms (30-50x slower) |
| **Output Type** | Typed primitives (`choice`, `score`, `noul`) | Free-form generated text tokens |
| **Schema Reliability** | 100% Deterministic (Model Head) | Requires JSON parsing / prompt retries |
| **Confidence** | Calibrated probabilities | Heuristic / Uncalibrated |
| **Cost & Footprint** | ~0.4B parameters (runs on consumer GPU/CPU) | 8B - 70B+ parameters |
