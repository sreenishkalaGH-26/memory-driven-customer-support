# Team video script (screen recording + voiceover, ~3:30)

Before recording: run `streamlit run app.py`, confirm the sidebar shows "🟢 Hindsight connected", click **Start a fresh demo run**, select **Priya Sharma**. Do a dry run so the LLM replies are ones you are happy to show.

**00:00–00:20 · The problem**
Screen: title slide or the app header.
VO: "Support agents usually know what's in the current conversation. The problem starts when the customer comes back later and has to explain everything again. I built a support agent that uses Hindsight memory to avoid that."

**00:20–00:50 · Without memory (baseline)**
Screen: sidebar, switch Agent mode to "Without memory (baseline)". Open the **Before vs After** tab. Type "My payment is failing again." and run the comparison, pointing only at the left "Without memory" column.
VO: "This is the baseline. The agent has no recalled context, so a message like 'my payment is failing again' gives it nothing to work with. It has to ask basic questions."
(If Hindsight has no memory yet, the right column will say so; that's fine, say "there's nothing stored yet.")

**00:50–01:30 · First interaction**
Screen: switch back to "With Hindsight memory". Chat tab. Send: "My payment is failing whenever I use the Android app." Show the reply and the recall line ("no relevant memory yet").
VO: "First conversation with Priya. Before answering, the app calls Hindsight recall. She's new, so nothing comes back. The agent troubleshoots. Clearing the app cache and retrying is the fix we walk through."

**01:30–01:55 · Memory retained**
Screen: point at "🧠 Memory retained in Hindsight" under the reply. Send "I cleared the cache and the payment went through." Then click **Retain resolution**.
VO: "After each reply the interaction is written back with Hindsight retain, and I also store the confirmed resolution, because a suggestion isn't a fix until the customer says it worked."

**01:55–02:15 · Time passes**
Screen: optionally click Refresh/keep the same Hindsight bank (do NOT click "Start a fresh demo run"). Say the customer returns later.
VO: "Later, the same customer comes back. She doesn't repeat any details."

**02:15–03:00 · Second interaction, recall and personalized reply**
Screen: send "My payment is failing again." Show the recall line and the memory panel with the recalled items, then the reply.
VO: "Recall runs first. The panel shows exactly what Hindsight returned, and that's what the LLM received. The reply builds on the earlier Android payment issue and the fix that worked."
Then Before vs After tab, run the comparison, show both columns.
VO: "Same model, same message. The only difference is the recalled memory."

**03:00–03:25 · Architecture**
Screen: README architecture diagram.
VO: "Streamlit UI, a small support agent, Hindsight recall before the LLM, Hindsight retain after it. One memory bank per customer. The memory is Hindsight, not a Python variable."

**03:25–03:45 · Conclusion and honesty**
VO: "The important part isn't that the agent answers a support question. It's that it remembers what happened before and uses it when the customer returns. It's a prototype: synthetic data, no benchmarks, and confirmed resolutions are captured with a manual button."
