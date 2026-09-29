# "My payment is failing again": building a support agent that remembers the last ticket

The most expensive sentence in customer support is "Can you tell me which device you're using?" when the customer already told you three weeks ago.

I wanted to see how much of that repetition could be removed with a small amount of code and a real memory layer. So I built a support agent for one workflow: a customer hits a payment failure in an Android app, gets it fixed, and comes back later with a vague follow-up. The agent uses [Hindsight](https://github.com/vectorize-io/hindsight) for persistent memory. The full stack is Python, Streamlit, Hindsight and an LLM API.

[SCREENSHOT: Customer support chat showing first interaction]

## The problem

Most chat agents handle the current conversation fine. The gap appears when the customer returns. Chat history belongs to a session; a ticket from last month is gone. The second conversation begins with "Please tell us which device you're using and what happened when you tried to pay," which is exactly what the customer expects a support team to already know.

Stuffing every past ticket into the prompt is not a fix either. It grows without bound, and most of it is irrelevant to the message in front of you. What I needed was memory that persists, and that is retrieved by relevance to the *new* message. That is the job of a memory layer, and it is the reason for reading up on [what agent memory actually is](https://vectorize.io/what-is-agent-memory) before writing code.

## What the system does

Every customer message goes through the same loop:

1. **Recall** memories from Hindsight for this customer, using the message as the query.
2. Give the LLM the current message plus those recalled memories.
3. Show the reply.
4. **Retain** the interaction back into Hindsight.

The UI makes this visible. Under each agent reply there is a status line for recall and one for retain, and a side panel shows exactly which memories were recalled and passed to the model. Nothing is hidden behind "memory is on".

[SCREENSHOT: Architecture]

## How Hindsight is integrated

I kept the integration in one small file, `memory.py`. Each customer gets their own memory bank, named after the customer ID plus a demo run ID, so recall is scoped to one person and I can start a demo from a clean slate by changing the suffix:

```python
def bank_id(self, customer_id: str) -> str:
    return f"support-{customer_id.lower()}-{self.run_id}"
```

Retaining is one call. I write a plain-text summary of the exchange with a timestamp, and let Hindsight decide what is worth remembering:

```python
self._client.retain(bank_id=bank, content=content, context=context, timestamp=when)
```

Recall is the other half. The query is simply the customer's new message:

```python
resp = self._client.recall(bank_id=self.bank_id(customer_id), query=query, budget="mid", max_tokens=1500)
```

I return failures to the UI as data rather than raising, because the requirement I cared about most was honesty: if Hindsight is unreachable, the interface says "recall failed, answering without memory" instead of quietly acting as if it worked.

[SCREENSHOT: Hindsight memory retained]

## Keeping the agent honest

Recall only helps if the model uses it carefully. The system prompt has a few rules that matter more than any prompt cleverness:

```text
2. Only treat something as remembered if it appears in RECALLED MEMORY. Never invent past tickets,
   dates, or fixes. If there is no RECALLED MEMORY block, behave like a first-time conversation.
...
4. If the customer's current message contradicts a memory, trust the current message and ask a short
   clarifying question.
```

When nothing is recalled, the code passes no memory block at all, so a first-time customer gets a normal first-time reply.

## Before and after

To make the comparison fair, the app has a baseline mode. In it, `recall` is never called and the LLM receives no recalled context. The **Before vs After** tab runs one recall and then asks the same model the same question twice, once with `None` for memories and once with the recalled ones:

```python
st.info(respond(test_msg, customer, [], None))            # without memory
st.success(respond(test_msg, customer, [], rec.memories)) # with Hindsight memory
```

The scenario:

- **Interaction 1.** Customer: "My payment is failing whenever I use the Android app." The agent troubleshoots (clearing the app cache and retrying is the fix the demo settles on). The exchange is retained.
- **Interaction 2, later.** Customer: "My payment is failing again."

Without memory, the model's only context is a CRM profile and a vague sentence, so the sensible reply is to ask what device and what happened. With memory, the prompt also contains the earlier Android payment exchange, so the model can start from the fix that worked before.

[PASTE THE ACTUAL "WITHOUT MEMORY" REPLY FROM YOUR RUN]

[PASTE THE ACTUAL "WITH HINDSIGHT" REPLY FROM YOUR RUN]

[SCREENSHOT: Second interaction with recalled memory]

I am deliberately not quoting replies I have not captured. LLM wording varies, so the screenshots are the evidence.

## A limitation I ran into by design

The first version of my retain step stored each exchange as it happened. That has a flaw: the agent's suggestion is stored alongside the customer's message, but the suggestion is not a confirmed fix. If the customer never says it worked, memory contains a guess dressed as history.

I added a separate "retain resolution" action that stores a confirmed outcome ("Ticket resolved... Confirmed working resolution: ..."). It works, but it is a manual button in the sidebar, which is not how a real support tool would capture outcomes. A better design would detect the customer confirming the fix in chat, or pull the outcome from the ticketing system.

Other honest limits: I have not benchmarked recall quality, the demo data is synthetic, "environment" in the memory panel comes from the CRM profile rather than from Hindsight, and frustration level is only remembered if it appears in the retained text. I also did not add any structured extraction on my side; I relied on what Hindsight returns for the query.

## What I would do next

- Extract structured fields (issue type, platform, app version, outcome) per ticket
- Flag stale memories, for example when the app version changed since the last ticket
- Test recall and retain against a local Hindsight instance in CI

The [Hindsight documentation](https://hindsight.vectorize.io/) covers the retain and recall operations in more depth than I used here, and the repository is worth reading if you are deciding between a memory layer and a bigger prompt.

The takeaway for me is small but concrete: the useful unit of memory in support is not the conversation, it is the ticket outcome. Recall makes it available; retaining it correctly is the harder part.
