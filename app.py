import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import LLMError, respond  # noqa: E402
from demo_data import CUSTOMERS, SEED_HISTORY  # noqa: E402
from memory import SupportMemory, build_retain_content  # noqa: E402

st.set_page_config(page_title="Memory-Driven Support Agent", page_icon="🧠", layout="wide")

# ---------------- session state ----------------
ss = st.session_state
ss.setdefault("run_id", os.getenv("DEMO_RUN_ID", "demo1"))
ss.setdefault("chats", {})  # customer_id -> [{"role","text","trace"}]
ss.setdefault("last_recall", {})  # customer_id -> RecallOutcome-like dict


def get_memory() -> SupportMemory:
    if "mem" not in ss or ss.mem.run_id != ss.run_id:
        ss.mem = SupportMemory(ss.run_id)
    return ss.mem


mem = get_memory()

# ---------------- sidebar ----------------
with st.sidebar:
    st.title("🧠 Support Agent")
    cid = st.selectbox(
        "Customer",
        list(CUSTOMERS),
        format_func=lambda c: f"{CUSTOMERS[c]['name']} ({c})",
    )
    customer = CUSTOMERS[cid]
    st.caption(f"Platform: {customer['platform']} · Plan: {customer['plan']}")

    mode = st.radio(
        "Agent mode",
        ["With Hindsight memory", "Without memory (baseline)"],
        help="Baseline never calls recall and never gives recalled context to the LLM.",
    )
    use_memory = mode.startswith("With")

    st.divider()
    ok, detail = mem.health()
    st.markdown(("🟢 Hindsight connected" if ok else "🔴 Hindsight unavailable"))
    st.caption(detail)
    st.caption(f"Memory bank: `{mem.bank_id(cid)}`")

    if st.button("Load demo history for other customers"):
        prog = st.progress(0.0)
        failures = []
        items = [(c, h) for c, hs in SEED_HISTORY.items() for h in hs]
        for i, (c, h) in enumerate(items):
            r = mem.retain(c, CUSTOMERS[c]["name"], h["content"], h["when"], context="historical support ticket")
            if not r.ok:
                failures.append(r.error)
            prog.progress((i + 1) / len(items))
        if failures:
            st.error(failures[0])
        else:
            st.success(f"Retained {len(items)} past tickets in Hindsight.")

    if st.button("Start a fresh demo run (empty memory)"):
        ss.run_id = datetime.now().strftime("r%H%M%S")
        ss.chats, ss.last_recall = {}, {}
        st.rerun()

    st.divider()
    st.markdown("**Close ticket and retain resolution**")
    resolution = st.text_input(
        "Confirmed resolution",
        value="Cleared Android app cache, restarted the app and retried the payment; it worked." if cid == "CUST-1001" else "",
    )
    if st.button("Retain resolution"):
        if not resolution.strip():
            st.warning("Type the resolution first.")
        else:
            now = datetime.now()
            content = (
                f"Ticket resolved on {now:%Y-%m-%d %H:%M} for {customer['name']} (ID {cid}, platform: "
                f"{customer['platform']}). Confirmed working resolution: {resolution.strip()}"
            )
            r = mem.retain(cid, customer["name"], content, now, context="confirmed ticket resolution")
            st.success("🧠 Resolution retained in Hindsight") if r.ok else st.error(r.error)

# ---------------- main ----------------
st.header("Memory-Driven Customer Support Agent")
st.caption("Flow per message:  ① Hindsight RECALL  →  ② LLM support agent (message + recalled memory)  →  ③ Hindsight RETAIN")

tab_chat, tab_ba = st.tabs(["💬 Support chat", "⚖️ Before vs After memory"])

# ---- chat tab ----
with tab_chat:
    left, right = st.columns([3, 2], gap="large")
    chat = ss.chats.setdefault(cid, [])

    with left:
        st.subheader(f"Customer: {customer['name']}")
        for m in chat:
            with st.chat_message("user" if m["role"] == "customer" else "assistant"):
                st.write(m["text"])
                if m.get("trace"):
                    t = m["trace"]
                    st.caption(t["recall"])
                    st.caption(t["retain"])
        msg = st.chat_input("Type the customer's message")

    if msg is not None:
        if not msg.strip():
            left.warning("Please enter a message.")
        else:
            history = [(("customer" if m["role"] == "customer" else "agent"), m["text"]) for m in chat]
            chat.append({"role": "customer", "text": msg})
            now = datetime.now()

            # ① RECALL
            recalled, recall_note = [], "⚪ Memory mode is OFF: Hindsight recall was skipped"
            if use_memory:
                rec = mem.recall(cid, msg)
                if not rec.ok:
                    recall_note = f"⚠️ Hindsight recall failed, answering without memory: {rec.error}"
                elif rec.memories:
                    recalled = rec.memories
                    recall_note = f"🧠 Hindsight Memory Recalled: {len(recalled)} relevant memor{'y' if len(recalled)==1 else 'ies'}"
                else:
                    recall_note = "🔎 Hindsight recall ran: no relevant memory yet (first-time customer)"
                ss.last_recall[cid] = {"query": msg, "memories": recalled, "note": recall_note}

            # ② LLM
            try:
                reply = respond(msg, customer, history, recalled)
            except LLMError as e:
                reply = None
                st.error(str(e))

            if reply is None:
                chat.pop()  # do not keep an unanswered message or retain half a turn
            else:
                # ③ RETAIN
                retain_note = "⚪ Memory mode is OFF: nothing retained"
                if use_memory:
                    r = mem.retain(cid, customer["name"], build_retain_content(customer, cid, msg, reply, now), now)
                    retain_note = "🧠 Memory retained in Hindsight" if r.ok else f"⚠️ Hindsight retain failed: {r.error}"
                chat.append({"role": "agent", "text": reply, "trace": {"recall": recall_note, "retain": retain_note}})
                st.rerun()

    with right:
        st.subheader("🧠 Customer memory")
        st.markdown(f"**Customer:** {customer['name']}  \n**Environment (CRM profile):** {customer['platform']}")
        lr = ss.last_recall.get(cid)
        if not use_memory:
            st.info("Baseline mode: the agent receives no recalled memory.")
        elif not lr:
            st.info("Send a message to see what Hindsight recalls for this customer.")
        else:
            st.markdown(f"**{lr['note']}**")
            st.caption(f"Recall query: “{lr['query']}”")
            for m in lr["memories"]:
                with st.container(border=True):
                    st.write(m["text"])
                    st.caption(f"type: {m['type']}" + (f" · {m['when']}" if m["when"] else ""))
            if lr["memories"]:
                st.caption("These exact memories were included in the agent's prompt.")

# ---- before / after tab ----
with tab_ba:
    st.subheader("Same message, same LLM. Only the recalled memory differs.")
    st.caption("Runs recall once, then asks the agent twice: with no context (baseline) and with the recalled Hindsight context. Nothing is retained here.")
    test_msg = st.text_input("Returning customer's message", value="My payment is failing again.")
    if st.button("Run comparison", type="primary"):
        if not test_msg.strip():
            st.warning("Please enter a message.")
        else:
            rec = mem.recall(cid, test_msg)
            c1, c2 = st.columns(2, gap="large")
            try:
                with c1:
                    st.markdown("### ❌ Without memory")
                    st.info(respond(test_msg, customer, [], None))
                with c2:
                    st.markdown("### ✅ With Hindsight memory")
                    if not rec.ok:
                        st.error(rec.error)
                    elif not rec.memories:
                        st.warning("Hindsight returned no memories for this customer. Complete the first interaction (and retain it) first.")
                    else:
                        st.success(f"🧠 {len(rec.memories)} memory item(s) recalled")
                        st.success(respond(test_msg, customer, [], rec.memories))
                        with st.expander("Recalled memory given to the agent"):
                            for m in rec.memories:
                                st.write("• " + m["text"])
            except LLMError as e:
                st.error(str(e))
