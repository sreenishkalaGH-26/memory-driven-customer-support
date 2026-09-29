# Architecture

```
                 Customer
                    │
                    ▼
              Streamlit UI (app.py)
                    │
                    ▼
        Support Agent (agent.py)
          │  current message
          ▼
  ╔═══════════════════════════════╗
  ║   HINDSIGHT  RECALL           ║◄──────────┐
  ║   bank: support-<cust>-<run>  ║           │
  ╚═══════════════╤═══════════════╝           │
                  │ relevant memories         │
                  ▼                           │
      LLM (message + recalled memory)         │
                  │                           │
                  ▼                           │
        Personalized response                 │
                  │                           │
                  ▼                           │
  ╔═══════════════════════════════╗           │
  ║   HINDSIGHT  RETAIN           ║           │
  ╚═══════════════╤═══════════════╝           │
                  ▼                           │
      Persistent customer memory ─────────────┘
```
