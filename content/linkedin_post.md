Your support bot isn't forgetful. It never had a memory in the first place.

Chat history ends when the session ends, so the customer who returns next week starts from zero.

I built a support agent where every reply starts with a Hindsight recall and ends with a retain.

What I took from it:
• One memory bank per customer keeps recall scoped
• Recall on the raw new message, then pass only what came back to the LLM
• A baseline mode that skips recall makes before/after honest
• A suggestion isn't a fix, so confirmed resolutions get their own retain

Before: "My payment is failing again" → "Which device?"
After: it starts from the earlier Android cache fix.

Repo: [PROJECT_GITHUB_URL]

#AIAgents #AgentMemory #Hindsight #LLM
